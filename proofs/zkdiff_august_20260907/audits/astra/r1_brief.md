> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

# Engineering brief: the leanest honest zero-knowledge diffusion demo (round 1)

You are GPT-6 Astra at ultra, acting as the programme's engineering reviewer. Read-only, offline; the remote development machine, Lambda and the GPU are not
reachable to you. Give a ranked plan with numbers, sources checked, and explicit uncertainty flags.

## The order
Objective set on 7 September 2026: a minimal diffusion execution proof using the whole sensor frame, allowing downscaling. So: at least one zero-knowledge proof that a diffusion model, conditioned on the emitted pattern, produced its
verdict on a real ZeeBeam row, with the whole sensor frame in view (zero crop; downscaling the whole frame is allowed, cropping is not
preferred), at the least possible cost in engineering time, GPU money and proving time. It is a demonstration, not the 259-row campaign.
Nothing hand-built from physics (neural throughout); no claim beyond execution binding.

## What exists (read these)
- ZeeBeam paper, the joined relation and its proving numbers: (on-box) zeebeam.md
  Section on the frozen integer networks (r32 coupling discriminator, PTQ v2: requantisation, int64 accumulation; uncr64 pose classifier) about
  lines 290-345 and 574-600; ceremony costs about lines 370-425: 4.15 billion instructions per row, SP1 6.4.0 CUDA prover on one Lambda
  A100-SXM4-40GB, 54.6 GPU-hours for 259 rows (about 13 GPU-minutes per row), about 26 GB GPU memory, executor 61.5 s per row on the host.
- The positive diffusion result, zero crop: (repository root) notes/zeebeam_nocrop_diffusion_8seed_20260830.md
  and its audited claim (repository root) audits/diffusion_8seed_audit/CLAIM_DRAFT.md:
  eight from-scratch ARM-C uncropped diffusion models (out_size 768x896, full frame area-resized), evaluated under the frozen evaluator
  (offsets [-2,+2,-15,+15,+30], t=150, one denoising pass per conditioning), AUROC exactly 1.0 in 13 of 16 session-by-seed cells, at least
  0.9992 in all, on sessions d2 (n=1200) and v10 (n=500).
- The frozen evaluator and the local audit bundle: (on-box) nocrop8seed_20260831 (bin/armc_pubproto_eval.py);
  the no-crop ladder: (on-box) nocrop_ladder.py; other local ARM-C material under
  (on-box) zeebeam and (on-box) armc-*. Establish from the code what the ARM-C
  architecture is (parameter count, layers, norms, attention or not, conditioning path); the Truth Beam README describes the Phase G verifier
  as a 39.77 M-parameter epsilon-prediction U-Net with a ControlNet-style hint, which may or may not be the ARM-C architecture.
- Data: 712 development rows of the August session (all available for training and evaluation; the sealed 288 stay sealed), plus the
  public Truth Beam sessions d2 and v10 used by the eight-seed result. Trained eight-seed checkpoints and the corpus sit on the Lambda
  persistent filesystem; a partial copy is on R2.
- Compute: Lambda 8xA100 80GB at $22.32/h, 8xA100 40GB $15.92/h, 1xA100 40GB $1.99/h, 8xH100 SXM5 $31.92/h (capacity varies), 1xH100;
  the development machine has an RTX 5090 24 GB when docked and 16 cores; the current pipeline is SP1 6.4.0 with the CUDA prover.

## Questions
1. The statement. What is the leanest statement that is honestly "a zero-knowledge diffusion demo" and not a toy? Proposal to critique: for
   one real uncropped row, given the committed frame (hash), the committed emitted pattern for the correct row and for one wrong row, and the
   committed model weights (hash), the circuit runs the frozen integer denoiser once per conditioning at the evaluator's timestep and outputs
   the two residuals (or their difference and sign), binding the frame to the session tree leaf and, if cheap, the pattern to the drand-seeded
   chain state as ZeeBeam already does. Say what to drop and what must stay for the demo to be credible.
2. The network. Rank: (a) integerise the existing eight-seed ARM-C model at 768x896; (b) train a new small, integer-friendly, conv-only
   diffusion denoiser on the whole frame downscaled (candidates 96x112, 128x160, 192x224), same protocol, and prove that; (c) anything
   leaner that is still a diffusion model. For each, estimate MACs per denoising pass, SP1 instructions (state your MAC-to-instruction
   factor and why), GPU proving hours at the paper's measured rate, executor time, and GPU memory. Name the resolution and width you would
   actually build.
3. The proving stack. SP1 as used (no convolution precompile; the single-pass executor is a bottleneck at trillions of instructions) against
   alternatives you consider credible for this team in days, not months (an SP1 precompile for int matmul, RISC Zero, Jolt, a
   sumcheck/GKR zkML prover for convolutions with its output committed into the SP1 relation). Recommend one, with the reason and the risk.
4. Integerisation. Reuse of the r32 PTQ v2 recipe for convolutions; what to do about normalisation layers, activations, timestep embedding
   and the conditioning path so the integer network's verdicts match the float network on the held-out frames. Quantisation-aware training
   from the start if the network is new.
5. The plan. Cheapest-first gates with go/no-go tests, cost and wall time per gate, and the failure condition at each: G0 no GPU spend
   (the development machine or one A100 hour): does the separation survive at the chosen resolution and in integers? G1 execute the guest on one row on the development machine's
   CPU: measured instruction count. G2 prove one row (which instance; hours; dollars). G3 audit, receipt, publish (repository, data layer,
   descriptive publication title). Total in engineering days, GPU dollars and wall clock, with a range.
6. Claims. Exactly what the demo may and may not say, in the vocabulary the ZeeBeam paper already uses (execution binding; not proof of
   physical capture; the learned score means what the frozen evaluator defines).
7. What not to do: list the tempting detours that would make this the 259-row campaign or a research programme.

## Return
A ranked plan (best first) with the numbers, the least costly initial experiment, the GPU choice, the risks, and a `VERDICT:`
line stating whether a lean demo is achievable within about one week of engineering and under about $1,000 of GPU time [state your own
bounds if different]. Flag every estimate. Sources checked per claim. Distinguish automated assistance from authorship; use the approved filing-date notice.
