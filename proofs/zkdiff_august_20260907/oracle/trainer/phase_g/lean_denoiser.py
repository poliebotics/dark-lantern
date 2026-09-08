"""LeanDenoiser (arch "zk2"): the dense conv-only conditional epsilon-denoiser Astra specified for the lean zero-knowledge demo
(review of 2026-09-07): four levels at widths (16, 32, 64, 64) by default, two 3x3 convolutions per encoder level, stride-2
convolution for downsampling, nearest-neighbour upsampling with skip concatenation, two convolutions per decoder level, a
four-channel epsilon head, ReLU everywhere, NO normalisation and NO attention; the second convolution of the deepest level
uses dilation 4. Input: the 4 noisy CFA channels and the 14-channel ARM-C hint (12 XOF octave channels + 2 coordinates),
concatenated. The timestep enters as one learned per-channel bias per level from a sinusoidal embedding (a constant vector at
the evaluator's fixed timestep, so the guest carries folded biases only).

Quantisation-aware training (--qat): fake-quantised int8 weights (symmetric, per output channel, straight-through estimator)
and int16 activations (symmetric, per layer, scale tracked as a running maximum). These follow the r32 PTQ-v2 semantics
(integer weights, int16 activations, int64 accumulation, per-channel requantisation) so the exported integer network is the
network that was trained. forward(C_t, E, t) as the other models. BOSUN, 2026-09-07."""
from __future__ import annotations
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from .diffusion_diagnostic_model import coord_grid


class _FakeQuant(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, scale, qmax):
        return torch.clamp(torch.round(x / scale), -qmax, qmax) * scale

    @staticmethod
    def backward(ctx, g):
        return g, None, None            # straight-through


def fq_weight(w: torch.Tensor, bits: int = 8) -> torch.Tensor:
    qmax = 2 ** (bits - 1) - 1
    scale = w.detach().abs().amax(dim=tuple(range(1, w.dim())), keepdim=True).clamp_min(1e-8) / qmax
    return _FakeQuant.apply(w, scale, qmax)


class QConv(nn.Conv2d):
    """Conv2d with optional fake-quantised weights (int8 per out-channel) and fake-quantised int16 output activations."""
    def __init__(self, *a, qat: bool = False, **k):
        super().__init__(*a, **k)
        self.qat = qat
        self.register_buffer("act_absmax", torch.zeros(()))

    def forward(self, x):
        w = fq_weight(self.weight) if self.qat else self.weight
        y = F.conv2d(x, w, self.bias, self.stride, self.padding, self.dilation, self.groups)
        if self.qat:
            with torch.no_grad():
                cur = y.detach().abs().amax()
                self.act_absmax.copy_(torch.maximum(self.act_absmax * 0.99, cur) if self.training else torch.maximum(self.act_absmax, cur))
            scale = (self.act_absmax.clamp_min(1e-6) / 32767.0)
            y = _FakeQuant.apply(y, scale, 32767)
        return y


class LeanTimeEmb(nn.Module):
    def __init__(self, dim: int, out_dims: list[int]):
        super().__init__()
        self.dim = dim
        self.mlp = nn.Sequential(nn.Linear(dim, dim * 2), nn.ReLU())
        self.heads = nn.ModuleList([nn.Linear(dim * 2, d) for d in out_dims])

    def forward(self, t: torch.Tensor) -> list[torch.Tensor]:
        half = self.dim // 2
        dt = self.mlp[0].weight.dtype
        t = t.to(dt)
        freqs = torch.exp(-math.log(10000) * torch.arange(half, device=t.device, dtype=dt) / half)
        ang = t[:, None] * freqs[None, :]
        h = self.mlp(torch.cat([torch.sin(ang), torch.cos(ang)], dim=1))
        return [hd(h) for hd in self.heads]


class LeanDenoiser(nn.Module):
    def __init__(self, in_ch: int = 4, base_ch: int = 16, channel_mults: tuple[int, ...] = (1, 2, 4, 4),
                 attn_at=None, cond_drop_prob: float = 0.2, hint_in_ch: int = 14, qat: bool = False, t_dim: int = 32):
        super().__init__()
        assert len(channel_mults) == 4
        self.in_ch, self.base_ch, self.cond_drop_prob, self.hint_in_ch, self.qat = in_ch, base_ch, cond_drop_prob, hint_in_ch, qat
        self.channel_mults = tuple(channel_mults); self.attn_at = (False,) * 4
        chs = [base_ch * m for m in channel_mults]
        Q = lambda *a, **k: QConv(*a, qat=qat, **k)
        self.stem = Q(in_ch + hint_in_ch, chs[0], 3, padding=1)
        self.enc = nn.ModuleList(); self.down = nn.ModuleList()
        prev = chs[0]
        for i, c in enumerate(chs):
            d = 4 if i == len(chs) - 1 else 1
            self.enc.append(nn.ModuleList([Q(prev, c, 3, padding=1), Q(c, c, 3, padding=d, dilation=d)]))
            self.down.append(Q(c, c, 3, stride=2, padding=1) if i < len(chs) - 1 else nn.Identity())
            prev = c
        self.dec = nn.ModuleList()
        for i in reversed(range(len(chs) - 1)):
            c = chs[i]
            self.dec.append(nn.ModuleList([Q(prev + c, c, 3, padding=1), Q(c, c, 3, padding=1)]))
            prev = c
        self.head = Q(prev, in_ch, 3, padding=1)
        nn.init.zeros_(self.head.weight); nn.init.zeros_(self.head.bias)
        self.t_dim = t_dim
        self.t_emb = LeanTimeEmb(t_dim, chs + [chs[i] for i in reversed(range(len(chs) - 1))])

    @staticmethod
    def _build_hint(E: torch.Tensor) -> torch.Tensor:
        B, _, H, W = E.shape
        coord = coord_grid(H, W, E.device, E.dtype).unsqueeze(0).expand(B, 2, -1, -1)
        return torch.cat([E, coord], dim=1)

    def forward(self, C_t: torch.Tensor, E: torch.Tensor, t: torch.Tensor, force_uncond: bool = False) -> torch.Tensor:
        B = C_t.shape[0]
        if force_uncond:
            E_eff = torch.zeros_like(E)
        elif self.training and self.cond_drop_prob > 0:
            mask = (torch.rand(B, device=E.device) < self.cond_drop_prob).float().view(B, 1, 1, 1)
            E_eff = E * (1.0 - mask)
        else:
            E_eff = E
        tb = self.t_emb(t)                                   # per-level bias vectors
        x = F.relu(self.stem(torch.cat([C_t, self._build_hint(E_eff)], dim=1)))
        skips = []; k = 0
        for i, (blocks, down) in enumerate(zip(self.enc, self.down)):
            x = F.relu(blocks[0](x) + tb[k].unsqueeze(-1).unsqueeze(-1)); k += 1
            x = F.relu(blocks[1](x))
            if i < len(self.enc) - 1:
                skips.append(x); x = F.relu(down(x))
        for blocks, skip in zip(self.dec, reversed(skips)):
            x = F.interpolate(x, size=skip.shape[-2:], mode="nearest")
            x = torch.cat([x, skip], dim=1)
            x = F.relu(blocks[0](x) + tb[k].unsqueeze(-1).unsqueeze(-1)); k += 1
            x = F.relu(blocks[1](x))
        return self.head(x)
