"""ZkUNet: an epsilon-prediction U-Net with the DiffusionDiagnosticUNet interface whose every inference-time
operation is integer-friendly for a zkVM guest: 3x3/1x1 convolutions, ReLU, BatchNorm (folded into the
convolutions after training), additive skip/hint injections, 2x2 average pooling (a shift in fixed point),
nearest-neighbour upsampling (exact), channel concatenation. No attention, no GroupNorm, no SiLU/GELU. The
timestep enters as a per-channel bias from a small MLP on a sinusoidal embedding; at the evaluator's fixed
timestep it is a constant vector, so the guest carries only folded biases.

Conditioning enters through the ControlNet-style spatial hint path exactly as in ARM-C (12 XOF octave
channels + 2 coordinate channels = 14), never as FiLM on E.  forward(C_t, E, t) as the parent model.
BOSUN, 2026-09-07, for the lean zero-knowledge diffusion demonstration."""
from __future__ import annotations
import math
from typing import Sequence
import torch
import torch.nn as nn
import torch.nn.functional as F
from .diffusion_diagnostic_model import coord_grid


class ZkTimeEmb(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.dim = dim
        self.mlp = nn.Sequential(nn.Linear(dim, dim * 4), nn.ReLU(), nn.Linear(dim * 4, dim * 4))

    def forward(self, t: torch.Tensor) -> torch.Tensor:
        half = self.dim // 2
        dt = self.mlp[0].weight.dtype
        t = t.to(dt)
        freqs = torch.exp(-math.log(10000) * torch.arange(half, device=t.device, dtype=dt) / half)
        ang = t[:, None] * freqs[None, :]
        return self.mlp(torch.cat([torch.sin(ang), torch.cos(ang)], dim=1))


class ZkResBlock(nn.Module):
    """conv3x3 -> BN -> ReLU -> (+ t bias) -> conv3x3 -> BN, plus identity or 1x1 skip; ReLU after the sum."""
    def __init__(self, in_ch: int, out_ch: int, t_dim: int):
        super().__init__()
        self.conv1 = nn.Conv2d(in_ch, out_ch, 3, padding=1)
        self.bn1 = nn.BatchNorm2d(out_ch)
        self.t_proj = nn.Linear(t_dim, out_ch)
        self.conv2 = nn.Conv2d(out_ch, out_ch, 3, padding=1)
        self.bn2 = nn.BatchNorm2d(out_ch)
        self.skip = nn.Conv2d(in_ch, out_ch, 1) if in_ch != out_ch else nn.Identity()

    def forward(self, x: torch.Tensor, t_emb: torch.Tensor) -> torch.Tensor:
        h = F.relu(self.bn1(self.conv1(x)))
        h = h + self.t_proj(F.relu(t_emb)).unsqueeze(-1).unsqueeze(-1)
        h = self.bn2(self.conv2(h))
        return F.relu(h + self.skip(x))


class ZkHintEncoder(nn.Module):
    """Four strided conv stages over the hint stack, matching the U-Net levels (/2, /4, /8, /16)."""
    def __init__(self, hint_in_ch: int, chs: Sequence[int]):
        super().__init__()
        assert len(chs) == 4
        stages = []
        prev = hint_in_ch
        for c in chs:
            stages.append(nn.Sequential(nn.Conv2d(prev, c, 3, stride=2, padding=1), nn.BatchNorm2d(c), nn.ReLU()))
            prev = c
        self.stages = nn.ModuleList(stages)

    def forward(self, hint: torch.Tensor):
        outs = []
        x = hint
        for s in self.stages:
            x = s(x); outs.append(x)
        return tuple(outs)


class ZkUNet(nn.Module):
    def __init__(self, in_ch: int = 4, base_ch: int = 16, channel_mults: tuple[int, ...] = (1, 2, 4, 4),
                 attn_at: tuple[bool, ...] | None = None, cond_drop_prob: float = 0.2, hint_in_ch: int = 14):
        super().__init__()
        assert len(channel_mults) == 4, "the hint encoder is wired for 4 levels"
        self.in_ch, self.base_ch, self.cond_drop_prob, self.hint_in_ch = in_ch, base_ch, cond_drop_prob, hint_in_ch
        self.channel_mults = tuple(channel_mults); self.attn_at = (False, False, False, False)
        self.t_dim = base_ch
        self.t_emb = ZkTimeEmb(base_ch)
        chs = [base_ch * m for m in channel_mults]
        self.in_conv = nn.Conv2d(in_ch, base_ch, 3, padding=1)
        self.hint_encoder = ZkHintEncoder(hint_in_ch, chs)
        self.adapters = nn.ModuleList([nn.Conv2d(c, c, 1) for c in chs])
        for a in self.adapters:
            nn.init.zeros_(a.weight); nn.init.zeros_(a.bias)          # zero-conv: hint contributes nothing at init
        self.downs = nn.ModuleList(); prev = base_ch
        for c in chs:
            self.downs.append(nn.ModuleList([ZkResBlock(prev, c, self.t_dim * 4), ZkResBlock(c, c, self.t_dim * 4)])); prev = c
        self.mid_a = ZkResBlock(prev, prev, self.t_dim * 4); self.mid_b = ZkResBlock(prev, prev, self.t_dim * 4)
        self.ups = nn.ModuleList()
        for i in reversed(range(len(chs))):
            c = chs[i]
            self.ups.append(nn.ModuleList([ZkResBlock(prev + c, c, self.t_dim * 4), ZkResBlock(c, c, self.t_dim * 4)])); prev = c
        self.out_conv = nn.Conv2d(base_ch, in_ch, 3, padding=1)
        nn.init.zeros_(self.out_conv.weight); nn.init.zeros_(self.out_conv.bias)

    @staticmethod
    def _build_hint(E: torch.Tensor) -> torch.Tensor:
        """ARM-C hint: the 12 octave channels plus 2 coordinate channels (14)."""
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
        hint_features = self.hint_encoder(self._build_hint(E_eff))
        t_emb = self.t_emb(t)
        x = self.in_conv(C_t)
        skips = []
        for i, blocks in enumerate(self.downs):
            for blk in blocks:
                x = blk(x, t_emb)
            h_i = hint_features[i]
            if h_i.shape[-2:] != x.shape[-2:]:
                h_i = F.interpolate(h_i, size=x.shape[-2:], mode="nearest")
            x = x + self.adapters[i](h_i)
            skips.append(x)
            x = F.avg_pool2d(x, 2)
        x = self.mid_a(x, t_emb); x = self.mid_b(x, t_emb)
        for blocks, skip in zip(self.ups, reversed(skips)):
            x = F.interpolate(x, size=skip.shape[-2:], mode="nearest")
            x = torch.cat([x, skip], dim=1)
            for blk in blocks:
                x = blk(x, t_emb)
        return self.out_conv(x)
