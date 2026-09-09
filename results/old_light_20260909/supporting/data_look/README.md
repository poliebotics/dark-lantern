---
version: 1.1
date: 2026-09-09
status: the data-look desk's alignment record for the fifteen old sessions, as used by the ARM-I and statistic desks
author: Cathal Ryan Hynes (author of record); drafted with BOSUN, the project's automated research assistant
---

# The data-look alignment record

On 9 September 2026 a desk read the fifteen old sessions frame by frame to establish how each was cropped, processed and
aligned: for every session it fitted the homography from displayed-emission pixels to recording pixels by maximising the
per-pixel temporal correlation between the recording series and the warped emission series (Powell over the eight corner
coordinates, coarse to fine; two orientations tried), then a per-pixel gain and offset model whose residual outliers mark
motion. `alignment_table.md` and `.csv` carry the per-session geometry (orientation, scale, rotation, keystone, area
fraction), photometry and temporal behaviour (drift, the fraction of frames with a person or motion in the beam);
`<session>_stats.json` the full numbers and per-frame series, `session_timing_2023.json` the 2023 loop timing, and the
two `verify_2023_chain_*.json` the recomputed 2023 hash chains. The homographies themselves (`<session>_H_full.npy`) and the
per-frame Perlin parameters of the 2024 sessions are in `../../armi_cross_configuration/kit/H/` and `kit/perlin/`, where
the ARM-I kit consumed them; the alignment atlas (one panel per session: the mean recording, brightened, with the fitted
emission rectangle) and the by-era overlay are on the data layer under `supporting/data_look/`. The desk's per-session
contact and diagnostic sheets, gain, offset, mean and standard-deviation maps, run logs and report stay on-box
(`../../REDACTION.md`).

Findings on which the results rest: the 2023 rig held one alignment for 26 days (the projection rotated by a half turn in the
camera, 0.83 camera pixels per displayed-emission pixel, 12 to 16 percent vertical keystone, the beam 51 percent of the
frame); the 2024 rig held one alignment across its seven sessions (upright, 2.40 camera pixels per emission pixel, keystone
within 0.4 percent, the beam 49 percent of the frame, no measurable drift within a session); the same bookshelf appears in
both, seen steeply from above in 2023 and frontally in 2024; a masked participant moves through the beam in most sessions
(17 to 28 of every 64 frames in 2024). The desk's reading of the 2026 contact sheet as showing the same shelving was wrong
and is corrected in `../../AUDIT_TRAIL.md`.

## Log

| Version | Date | Author | Change |
|---|---|---|---|
| 1.0 | 2026-09-09 | BOSUN | First version. |
| 1.1 | 2026-09-09 | BOSUN | authorship line, 9 September 2026. |
