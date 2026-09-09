#!/usr/bin/env python3
"""Train-free emission-capture coupling statistic on the old Truth Beam sessions (CPU desk, 2026-09-09).

STATISTIC: copied verbatim from the repository's `results/train_free_coupling_20260906/scripts/coupling_stat.py` (grid, corr, mismatch construction). For each pair,
downsample emission E and capture B to g x g cells (mean colour per cell), remove each image's per-channel mean, divide by
its per-channel std, mean over channels of the Pearson correlation of the two grids; g in {4, 8, 16, 32, 64}. Matched pair
versus one seeded random mismatch (capture of another frame of the same session; random.seed(0), one shuffle per grid per
session in the reference's order). AUROC matched vs mismatched, paired fraction matched > mismatched.

ADAPTATIONS (loaders and geometry only, each documented in REPORT.md):
  L1 2023 emission: stored float (1024,1024,3) in cv2 channel order (displayed as BGR through cv2), clipped/rounded to uint8
     as cv2.imwrite did, channel-reversed to RGB. Report (1536,2048,3) uint8 from gxipy convert("RGB"): used as stored.
  L2 2024 emission: (1080,1920,3) uint8 RGB as stored. Recording (4600,5320,3) uint8 stored BGR (cv2.cvtColor BGRA2BGR):
     channel-reversed to RGB.
  G1 orientation: the emission may appear rotated 180 degrees in the camera; decided per session on the first
     min(4, n) frames (grid 8, projected-region crop), both correlations recorded.
  G2 projected-region crop: emission-blind. The per-pixel temporal std of the recording over the session's frames marks
     the projector-lit region (the emission changes every frame, the room does not); background-relative threshold,
     largest component, protrusion rows/columns removed, one RANSAC line per side (see projected_quad_from_std);
     perspective warp of that quad to the displayed-emission aspect (2023 1920x1200, 2024 1920x1080). Full-frame
     variant: the whole recording, no crop, same orientation and channel handling.
"""
import json, os, random, re, glob
import numpy as np
import cv2
from sklearn.metrics import roc_auc_score

cv2.setNumThreads(4)
GRIDS = (4, 8, 16, 32, 64)


# ----- statistic, verbatim from the reference (grid takes an array instead of a PIL image) -----
def grid(img, g):
    a = np.asarray(img, dtype=np.float32)
    h, w, _ = a.shape
    a = a[: (h // g) * g, : (w // g) * g]
    cells = a.reshape(g, (h // g), g, (w // g), 3).mean(axis=(1, 3))  # g x g x 3
    cells = cells - cells.mean(axis=(0, 1), keepdims=True)
    cells = cells / (cells.std(axis=(0, 1), keepdims=True) + 1e-6)
    return cells


def corr(a, b):
    return float(np.mean([np.corrcoef(a[..., c].ravel(), b[..., c].ravel())[0, 1] for c in range(3)]))


def mismatch_partners(names_by_session, seed=0):
    """Reproduce the reference's partner construction: random.seed(0) once, then for each grid in GRIDS order and each
    session in insertion order, one shuffle; partner = shuffled[i] unless it is the frame itself, then shuffled[i+1]."""
    random.seed(seed)
    partners = {}
    for g in GRIDS:
        partners[g] = {}
        for s, ns in names_by_session.items():
            shuffled = ns[:]
            random.shuffle(shuffled)
            partners[g][s] = [m if m != n else shuffled[(i + 1) % len(shuffled)] for i, (n, m) in enumerate(zip(ns, shuffled))]
    return partners


# ----- loaders -----
def index_of(path):
    return int(re.match(r"(\d+)_", os.path.basename(path)).group(1))


def list_2023_session(session_dir):
    em = {index_of(p): p for p in glob.glob(os.path.join(session_dir, "emissions", "*.npy"))}
    rp = {index_of(p): p for p in glob.glob(os.path.join(session_dir, "reports", "*.npy"))}
    return [(i, em[i], rp[i]) for i in sorted(set(em) & set(rp))]


def load_2023_emission(path):
    e = np.load(path)
    e = np.clip(np.round(e), 0, 255).astype(np.uint8)  # cv2.imwrite's float -> 8-bit conversion
    return np.ascontiguousarray(e[..., ::-1])  # cv2 BGR order -> RGB


def load_2023_report(path):
    return np.load(path)  # RGB uint8 as stored


def load_2024_recording(rec):
    return np.ascontiguousarray(rec[..., ::-1])  # stored BGR -> RGB


# ----- geometry -----
def order_corners(pts):
    pts = np.asarray(pts, dtype=np.float64)
    c = pts.mean(axis=0)
    ang = np.arctan2(pts[:, 1] - c[1], pts[:, 0] - c[0])
    pts = pts[np.argsort(ang)]  # counter-clockwise in image coords (y down) = TL, TR, BR, BL after rolling
    s = pts.sum(axis=1)
    tl = int(np.argmin(s))
    pts = np.roll(pts, -tl, axis=0)
    # ensure order TL, TR, BR, BL (image coords: TR has larger x than BL)
    if pts[1][0] < pts[3][0]:
        pts = pts[[0, 3, 2, 1]]
    return pts


def _ransac_line(pts, tol, n_iter=400, seed=0):
    """Robust 2D line through pts (N x 2): RANSAC on point pairs, least-squares refit on the inliers. Returns (p, u)."""
    rng = np.random.default_rng(seed); pts = np.asarray(pts, np.float64); n = len(pts)
    if n < 2:
        return None
    best, best_in = -1, None
    for _ in range(n_iter):
        i, j = rng.choice(n, 2, replace=False)
        d = pts[j] - pts[i]; L = np.linalg.norm(d)
        if L < 1e-9:
            continue
        u = d / L; nrm = np.array([-u[1], u[0]])
        dist = np.abs((pts - pts[i]) @ nrm); inl = dist < tol
        if inl.sum() > best:
            best, best_in = inl.sum(), inl
    P = pts[best_in]; c = P.mean(axis=0)
    _, _, vt = np.linalg.svd(P - c, full_matrices=False)
    return c, vt[0], int(best), n


def projected_quad_from_std(std_map, k_bg=2.5, min_area_frac=0.05):
    """Emission-blind projected-region estimate from the temporal std map (working scale).
    1. threshold relative to the frame-border background: thr = max(k_bg * median_border, median_border + 6 * MAD_border);
       closing, hole fill, largest connected component;
    2. per-row left/right extents and per-column top/bottom extents of the component, after zeroing rows narrower than
       0.7 of the median row width (before the top/bottom extents) and columns shorter than 0.7 of the median column
       height (before the left/right extents), and dropping extents within 2 percent of the frame border;
    3. one RANSAC line per side (tolerance 1 percent of min(h, w)), so lit objects protruding above or beside the region
       are rejected as outliers; corners are the intersections of adjacent side lines;
    4. fallback (any side with under 45 percent inliers): convex hull + approxPolyDP to 4 vertices.
    Returns quad (4x2, TL TR BR BL), component mask and diagnostics; the caller rescales to full resolution."""
    from skimage.measure import label, regionprops
    from scipy import ndimage
    S = std_map.astype(np.float32); h, w = S.shape
    b = max(int(0.04 * min(h, w)), 2)
    border = np.r_[S[:b].ravel(), S[-b:].ravel(), S[:, :b].ravel(), S[:, -b:].ravel()]
    bg = float(np.median(border)); mad = float(np.median(np.abs(border - bg)))
    thr = max(k_bg * bg, bg + 6 * mad)
    mask = S > thr
    mask = ndimage.binary_closing(mask, iterations=max(3, int(0.01 * min(h, w))))
    mask = ndimage.binary_fill_holes(mask)
    mask = ndimage.binary_opening(mask, iterations=2)
    lab = label(mask); props = sorted(regionprops(lab), key=lambda rp: rp.area, reverse=True)
    if not props or props[0].area < min_area_frac * mask.size:
        raise RuntimeError("no projected region found")
    comp = lab == props[0].label
    # row widths and column heights of the component; rows narrower than half the median width and columns shorter
    # than half the median height are protrusions (lit objects above or beside the region) and are removed before the
    # perpendicular extents are taken; extents on the frame border are dropped (a clipped protrusion is a straight line)
    rw = comp.sum(axis=1); ch = comp.sum(axis=0)
    medw = np.median(rw[rw > 0]); medh = np.median(ch[ch > 0])
    comp_rows = comp.copy(); comp_rows[rw < 0.7 * medw, :] = False
    comp_cols = comp.copy(); comp_cols[:, ch < 0.7 * medh] = False
    left, right, top, bottom = [], [], [], []
    m = max(3, int(0.02 * min(h, w)))
    for y in np.where(comp_cols.any(axis=1))[0]:
        xx = np.where(comp_cols[y])[0]
        if xx[0] >= m: left.append((xx[0], y))
        if xx[-1] < w - m: right.append((xx[-1], y))
    for x in np.where(comp_rows.any(axis=0))[0]:
        yy = np.where(comp_rows[:, x])[0]
        if yy[0] >= m: top.append((x, yy[0]))
        if yy[-1] < h - m: bottom.append((x, yy[-1]))
    tol = max(0.01 * min(h, w), 1.5)
    fits = {name: _ransac_line(pts, tol) for name, pts in (("top", top), ("right", right), ("bottom", bottom), ("left", left))}
    inl = {k: (v[2] / v[3] if v else 0.0) for k, v in fits.items()}
    method = "extents+RANSAC"
    quad = None
    if all(v and inl[k] >= 0.45 for k, v in fits.items()):
        def meet(a, bb):
            (p, u, _, _), (q, v, _, _) = a, bb
            ts = np.linalg.solve(np.array([u, -v]).T, q - p); return p + ts[0] * u
        try:
            quad = order_corners(np.array([meet(fits["left"], fits["top"]), meet(fits["top"], fits["right"]),
                                           meet(fits["right"], fits["bottom"]), meet(fits["bottom"], fits["left"])]))
        except np.linalg.LinAlgError:
            quad = None
    if quad is None:
        cnts, _ = cv2.findContours(comp.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        hull = cv2.convexHull(max(cnts, key=cv2.contourArea)); peri = cv2.arcLength(hull, True)
        method = "hull+approxPolyDP fallback"
        for frac in np.arange(0.005, 0.15, 0.0025):
            ap = cv2.approxPolyDP(hull, frac * peri, True)
            if len(ap) == 4:
                quad = order_corners(ap.reshape(4, 2)); break
            if len(ap) < 4:
                break
        if quad is None:
            quad = order_corners(cv2.boxPoints(cv2.minAreaRect(hull))); method = "minAreaRect fallback"
    inside = np.zeros(S.shape, np.uint8); cv2.fillConvexPoly(inside, np.round(quad).astype(np.int32), 1)
    excess = np.clip(S - bg, 0, None)
    diag = {"bg_median": bg, "bg_mad": mad, "threshold": float(thr), "component_area_frac": float(props[0].area / mask.size),
            "method": method, "side_inlier_frac": inl, "quad_area_frac_working": float(cv2.contourArea(quad.astype(np.float32)) / mask.size),
            "excess_std_captured_frac": float(excess[inside == 1].sum() / max(excess.sum(), 1e-6)),
            "std_in_quad_mean": float(S[inside == 1].mean()), "std_out_quad_mean": float(S[inside == 0].mean()),
            "touches_edge": bool(quad.min() <= 1 or quad[:, 0].max() >= w - 2 or quad[:, 1].max() >= h - 2)}
    return quad, comp, diag


def warp_quad(img, quad_full, out_wh):
    W, H = out_wh
    dst = np.array([[0, 0], [W - 1, 0], [W - 1, H - 1], [0, H - 1]], dtype=np.float32)
    Hm = cv2.getPerspectiveTransform(quad_full.astype(np.float32), dst)
    return cv2.warpPerspective(img, Hm, (W, H), flags=cv2.INTER_LINEAR)  # warpPerspective has no area filter; linear, then the grid averages cells


def orient(E, deg):
    return E if deg == 0 else np.ascontiguousarray(E[::-1, ::-1])


# ----- evaluation -----
def auroc(matched, mismatched):
    y = [1] * len(matched) + [0] * len(mismatched)
    return float(roc_auc_score(y, list(matched) + list(mismatched)))


def paired_frac(matched, mismatched):
    return float(sum(1 for a, b in zip(matched, mismatched) if a > b) / len(matched))


def bootstrap_ci(matched, mismatched, n_boot=1000, seed=1):
    """Frame-level bootstrap: each frame carries its matched and its mismatched score; resample frames with replacement."""
    rng = np.random.default_rng(seed)
    m = np.asarray(matched); mm = np.asarray(mismatched); n = len(m)
    y = np.r_[np.ones(n), np.zeros(n)]
    au, pf = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        sc = np.r_[m[idx], mm[idx]]
        if len(np.unique(y)) < 2:
            continue
        au.append(roc_auc_score(y, sc)); pf.append(np.mean(m[idx] > mm[idx]))
    return {"auroc_ci95": [float(np.percentile(au, 2.5)), float(np.percentile(au, 97.5))],
            "paired_ci95": [float(np.percentile(pf, 2.5)), float(np.percentile(pf, 97.5))], "n_boot": len(au)}


def shuffled_label_control(matched, mismatched, n_perm=1000, seed=2):
    """Permute the matched/mismatched labels over the pooled scores: one seeded shuffle (the headline control) and the
    2.5/97.5 percentiles of 1000 permutations (the null band)."""
    rng = np.random.default_rng(seed)
    sc = np.r_[matched, mismatched]; n = len(matched)
    y = np.r_[np.ones(n), np.zeros(n)]
    first = None; vals = []
    for k in range(n_perm):
        yp = rng.permutation(y)
        v = roc_auc_score(yp, sc)
        if k == 0:
            first = float(v)
        vals.append(v)
    return {"one_shuffle_auroc": first, "perm_mean": float(np.mean(vals)), "perm_ci95": [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))], "n_perm": n_perm}
