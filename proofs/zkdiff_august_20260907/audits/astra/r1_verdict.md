> Public audit copy, 8 September 2026. Personal identifiers, private instructions and development infrastructure have been
> redacted; scientific findings are preserved. Findings describe the revision reviewed at the time and may be superseded; see
> AUDIT_TRAIL.md.
> Paths are package-relative where the file is in this package and marked (on-box) or (repository root) where it is not; line
> numbers are as at audit time and may have moved.

**Build a new 96×112, width-16 conditional diffusion denoiser with quantisation-aware training, then prove two evaluations using the existing SP1 6.4.0 CUDA/Groth16 stack.** Use the docked 5090 for training and one A100-SXM4-40GB for proving. The engineering uncertainty is whether the small integer model retains conditioning separation. Its projected proving bill is modest.

Flags throughout: **[checked]** local source or archived measurement; **[derived]** arithmetic from those sources or the specified design; **[estimate]** unmeasured forecast; **[unknown]** unresolved. Prices below are supplied by your brief, not checked online.

### Ranked network plan

| Rank | Route | Decision |
|---|---|---|
| **1** | **(b) New dense, conv-only diffusion denoiser, 96×112, widths 16/32/64/64** | Best balance of engineering simplicity, capacity and proving cost. Build this first. |
| Fallback within 1 | Same network at 128×160; ultimately 192×224 | Increase resolution only after a recorded low-resolution failure. These are contingencies, not parallel training arms. |
| **2** | **(c) Depthwise-separable version of the same denoiser** | About five times fewer MACs, but less demonstrated capacity and another kernel to validate. Saving a few proving dollars does not justify starting here. |
| **3** | **(a) Integerise existing ARM-C at 768×896** | Exclude from the one-week demo. Both the integerisation work and projected SP1 execution are too large. |

**What ARM-C actually is [checked].** The source and recorded checkpoint architecture establish **39,772,420 parameters**, base width 96, channel multipliers `(1,2,4,4)`, 18 residual blocks, 58 convolutions, 20 linear layers, 44 GroupNorm layers and three global attention blocks. It uses SiLU, GELU, softmax, bilinear interpolation and a sinusoidal timestep MLP. It shares the Phase G backbone, but ARM-C’s hint has **12 XOF octave channels plus two coordinate channels**, rather than Phase G’s 11-channel layout. The frozen evaluator explicitly selects the attention locations. Model source (on-box: `diffusion_diagnostic_model.py.ref` line 86), checkpoint architecture records (on-box: `checkpoint_args.jsonl` line 1), evaluator construction (on-box: `armc_pubproto_eval.py` line 83).

**The network I would build [design].** Feed four noisy CFA channels, twelve spatial XOF channels and two coordinates into a four-level U-Net. Use two convolutions per encoder level, stride-two convolution for downsampling, nearest-neighbour upsampling, skip concatenation, two convolutions per decoder level and a four-channel epsilon head. Use ReLU and no normalisation or attention. Set the second deepest convolution to dilation 4, padding 4.

That gives **15 convolutions, 305,060 spatial parameters and 412,532,736 MACs per pass [derived]**. A small learned timestep embedding brings training parameters to approximately **0.33 million**; specialise its contributions to constants when exporting timestep 150. The theoretical maximum receptive field is **123×123**, covering the 96×112 input from central outputs. Every sensor pixel enters the full-frame reduction, although that does not establish what the network learns to use.

Train on actual captured data using the cosine diffusion schedule, timesteps 0–999 and epsilon-prediction MSE. Proving only timestep 150 is an honest specialisation of that trained diffusion model. A network fitted solely to one fixed noisy example would not provide the same credibility. Existing diffusion schedule (on-box: `diffusion_diagnostic_model.py.ref` line 317), training objective (on-box: `train_armc_xof.py.ref` line 397).

### Cost arithmetic

A small correction to the brief: **54.6 GPU-hours covers the 257 fleet proofs**. The two final ceremony proofs add approximately 0.446 hours. The measured reference row executed **4,149,712,293 instructions in 61.5 seconds**. Paper measurements (on-box: `zeebeam.md` line 331), fleet totals (on-box: `zeebeam.md` line 414).

The resulting conversion factors are:

\[
T_{\rm proof}\approx0.0512\text{ A100-hours per billion instructions},
\qquad
T_{\rm execute}\approx14.82\text{ seconds per billion instructions}.
\]

**These are extrapolation coefficients, not measured diffusion throughput.**

The existing r32 network requires **4,792,576 dense MACs [derived]** and its measured scoring region costs **338,997,588 instructions [checked]**: approximately **70.7 instructions/MAC**. This includes indexing, padding, checked accumulation, reduction and requantisation. I use **40–100 instructions/MAC [estimate]**, centred near 71, until G1 replaces it with a measurement. A factor of 4–10 would assume substantial optimisation absent from the current implementation. r32 layouts and integer kernel (on-box: `lib.rs` line 86).

The following ranges use **two conditioning passes**, plus **6–8 billion instructions [estimate]** for raw-frame processing, pattern binding and retained relation machinery. They are sensitivity ranges, not confidence intervals.

| Network | MACs/pass **[derived]** | Instructions for demo **[estimate]** | A100 proving hours **[estimate]** | Executor at paper host rate **[estimate]** | Proving dollars at $1.99/h **[estimate]** |
|---|---:|---:|---:|---:|---:|
| **Dense 96×112, width 16** | **0.413 B** | **39–91 B** | **2.0–4.6 h** | **10–22 min** | **$4–9** |
| Dense 128×160, width 16 | 0.786 B | 69–165 B | 3.5–8.5 h | 17–41 min | $7–17 |
| Dense 192×224, width 16 | 1.650 B | 138–338 B | 7.1–17.3 h | 34–84 min | $14–35 |
| Separable 96×112, width 16 | 0.085 B | 13–25 B | 0.66–1.28 h | 3–6 min | $1.3–2.6 |
| Existing ARM-C 768×896 | **2,043.7 B** | **163.5–408.8 T, MAC subtotal only** | **8,370–20,930 h, before extra operations** | **28–70 days** | **$16,700–41,700, before extras** |

The full ARM-C count is **2.044 trillion MACs per pass [derived]**: 1.861 trillion convolution MACs, 183.1 billion attention-product MACs and 2.1 million linear MACs. GroupNorm, softmax, activations and interpolation are additional work. Consequently, its table entry supplies no upper bound. Forward scale schedule (on-box: `diffusion_diagnostic_model.py.ref` line 281).

**Memory:** for the small candidates, provision **26–35 GiB of prover VRAM [estimate] on a 40GB A100**. The archived observations were 25,615–27,279 MiB, explicitly snapshots rather than peaks. Smaller neural activations do not proportionally shrink SP1’s proving workspace. The 24GB 5090’s fit for this prover configuration is **[unknown]**. GPU observation record (on-box: `GPU_MEMORY_OBSERVATIONS.md` line 10).

Full ARM-C prover memory has **no defensible fit estimate from these records [unknown]**. One materialised int64 attention matrix alone would occupy approximately **3.45 GiB [derived]**, before its other tensors and prover workspaces. An 80GB instance would not establish feasibility merely by being larger.

### The statement that must be proved

The proposed two-conditioning statement is the right size. Make it precise:

> For pinned session root and context, row indices \(r,u\), raw-frame commitment, emitted-pattern commitments, integer-model identity, preprocessing specification and noise identity, the guest derives the whole-frame input, evaluates the frozen conditional diffusion denoiser at timestep 150 under both conditions, and outputs the integer residual difference \(D>0\).

Use

\[
R_c=\sum_j\bigl(f_\theta(x_{150},c,150)_j-\epsilon_j\bigr)^2,
\qquad D=R_{\rm wrong}-R_{\rm correct}.
\]

Publish both sums if convenient, otherwise the difference and sign. Publish their common scale and denominator, \(4HWQ_\epsilon^2\); division is unnecessary inside the guest.

The essential bindings are these:

| Must stay | Why |
|---|---|
| **Hash the complete raw frame and verify its session membership** | A session leaf commits the raw hash, not the new denoiser’s input tensor. |
| **Derive the full-frame reduction inside the guest** | A host-supplied thumbnail with its own hash does not prove that it represents the committed uncropped frame. |
| **Bind both conditioning rows and require a declared nonzero offset** | A correct condition and an arbitrary adversarial condition would be a weaker demonstration. |
| **Bind the actual integer weights, scales, architecture and arithmetic semantics** | The original float-checkpoint hash alone does not identify the executed integer function. |
| **Use one pinned noise tensor and one noisy frame for both passes** | Otherwise the prover can change more than the conditioning. |
| **Compute residuals with checked bounds and verify a final ZK proof** | A positive host-side score or SP1 execution receipt is insufficient. |

These requirements follow directly from the existing session leaf and the frozen scorer. Leaf definition (on-box: `zeebeam.md` line 226), relation table (on-box: `zeebeam.md` line 293), noise and residual computation (on-box: `armc_pubproto_eval.py` line 108).

**The important conditioning correction:** ARM-C never loads the rendered RGB tile. It derives four XOF octave grids from \(S_r\), resizes them and concatenates twelve channels. Membership of \(S_r\) and an emission hash does not, by itself, prove that rendering \(S_r\) produces that hash. Actual conditioning loader (on-box: `train_armc_xof.py.ref` line 120).

For this brief, **retain render-and-hash equality for both patterns**. Two renders add approximately **4.28 billion measured-style instructions**, corresponding to about **13 proving minutes or $0.44 [estimate]**. That is inexpensive enough to preserve the requested emitted-pattern binding. The renderer is existing protocol computation, not a hand-built physical model supplying the learned answer.

Reuse the previous-row drand/advance check if straightforward. The relevant beacon is the predecessor’s: the current row’s beacon affects the following pattern. The existing predecessor leg costs only **6.73 million instructions [checked]**. Temporal indexing (on-box: `zeebeam.md` line 91), cost table (on-box: `zeebeam.md` line 331).

Drop any requirement for a new Zcash transaction, complete-session proving, pose validation or another r32 experiment. However, **do not spend engineering days stripping already-working legs out of the guest**. Keeping the existing pose and r32 evaluations costs approximately two proving minutes at the reference rate. Extending the working joined guest may be cheaper than constructing a minimal replacement.

The new model and arithmetic require the description **“integer diffusion evaluator adapted from the frozen ARM-C protocol.”** The original evaluator compares the correct residual with the **mean of five wrong residuals**. A two-pass proof establishes one specified comparison, not that aggregate statistic or the eight-seed AUROC.

### Proving stack

| Rank | Stack | Days-scale assessment |
|---|---|---|
| **1** | **Existing SP1 6.4.0 CUDA, ending in Groth16** | Reuses the working guest, build, oracle, verifier and demonstrated GPU configuration. Recommended. |
| **2, conditional** | External convolution sumcheck/GKR prover | Credible only if a compatible, working implementation is already available. None was established locally. |
| **3** | RISC Zero | A Rust port is plausible, but several days of migration and validation **[estimate]** buys no measured speed advantage here. |
| **4** | Jolt | Current applicable capabilities and performance were not verified offline **[unknown]**. Exclude from the committed schedule. |
| **5** | New SP1 integer-matmul precompile | A constrained proving-system implementation, including memory interactions and integration, is a weeks-scale risk **[estimate]**. |

The local SP1 syscall enumeration contains no convolution or matmul precompile. Its deferred verification interface verifies SP1 proofs, not arbitrary GKR proofs. SP1 6.4.0 syscall source (on-box: `syscall_code.rs` line 45).

An external prover’s output hash **cannot simply be committed into SP1 and treated as proved inference**. SP1 must verify the external proof, or the final verifier must check both proofs and all shared identities. Signed ranges, requantisation, rounding and nonlinear operations must remain constrained. Bare GKR also supplies no automatic zero-knowledge guarantee.

Use the existing explicit **`.groth16()`** path and check the returned mode. Local wrapper source was checked for proof randomisation; the deployed binary and program key must still be pinned. Publishing only a Core or Compressed artifact would not meet this demo’s chosen ZK construction. Existing ceremony (on-box: `ceremony.rs` line 180), local mode audit (on-box: `REPORT.md` line 87).

### Integerisation

Reuse **r32 PTQ-v2 semantics**, not its numerical scales: int8 weights, int16 activations, checked int64 accumulation, per-output-channel multipliers, shift 30, signed round-to-nearest-even and explicit clamping. Bounds must cover the accumulator multiplied by its requantisation multiplier, as well as residual squares and sums. Integer implementation (on-box: `lib.rs` line 180).

For the new network, train with those quantisers from the start. Specify integer whole-frame area reduction, nearest-neighbour upsampling, coordinates, padding, dilation, timestep coefficients and output scale. Fold the timestep-150 embedding into channel biases. Keep the spatial conditioning path learned; do not introduce an analytic camera/projector warp.

For existing ARM-C, GroupNorm is input-dependent and **cannot be folded away like frozen inference BatchNorm**. Integer reciprocal-square-root, SiLU/GELU and attention softmax would need specified approximations and renewed validation. Replacing them changes the model. This is a substantial second reason to reject route (a).

Keep two separate tests: **integer reference versus Rust must be exact**; **float versus integer must preserve the relevant verdict and margin**. For ARM-C comparisons, the reference includes its actual BF16 conversions and autocast path, not an improvised FP32 rerun. Frozen numerical path (on-box: `armc_pubproto_eval.py` line 108).

Materialise the selected noise tensor once using the declared backend and row-order rule, then pin its canonical bytes. Prove its identity and integer forward-noising computation. Its correspondence to the original PyTorch RNG remains a separately checked provenance fact unless that RNG is also implemented in-circuit.

### Cheapest-first gates

**Recommended initial experiment:** one seeded **96×112, width-16 QAT feasibility run on the docked 5090**, capped at **60 GPU minutes after code and cached data are ready**. Test correct versus wrong conditioning and integer sign preservation. Do this before building the diffusion guest.

The cap is an experiment budget, not a promise of convergence. The 712 August raws alone occupy **17.4GB [derived]**; preprocessing and data availability can dominate the first evening. The inspected local audit directories contain source and score evidence, not an established ready-to-train corpus.

| Gate | Work and go/no-go test | Time and GPU cost **[estimate]** | Failure action |
|---|---|---|---|
| **G0: learning and integer feasibility** | One model, one seed. Preserve the d2/v10 training exclusions. Use t=150 and all five offsets on a fixed screen, for example one 40-row block per session. Proposed engineering thresholds: paired fraction and pooled AUROC each ≥0.95 per session; integer/float sign agreement ≥99%; chosen proof pair positive with quantisation error comfortably below its margin. | 0.5–1.5 engineering days; initial 60-minute GPU screen. **$0 on 5090**, or approximately **$1.99 for one authorised A100 hour**, excluding staging. | Stop proving work. Diagnose once; permit one 128×160 fallback. No success claim follows from a failed or incomplete screen. |
| **G1: exact guest execution** | Freeze model, arithmetic, row/offset, noise and statement. Run the complete guest on the development machine. Require byte-exact agreement with the independent integer oracle. Proposed launch gate: **≤200B instructions and ≤1 hour execution**. | 1–2 engineering days. Default candidate projects to 10–22 minutes execution at the paper rate; the development machine throughput remains unmeasured. **$0 GPU.** | Resolve parity failures from source. If over budget, reduce cost before launching a prover. |
| **G2: one real proof** | One **A100-SXM4-40GB**, matching the working configuration. Produce Groth16, verify independently, compare every public field with the oracle, and exercise tampered proof/public/key controls. Record actual peak memory and timings. | 0.5–1 engineering day; allow **3–12 instance-hours, $6–24**, for the preferred route including setup and uncertainty. Proposed hard attempt budget: **24 hours, $47.76**, with at most one bounded retry. | Stop on budget exhaustion, OOM, verification failure or unresolved output mismatch. Do not escalate automatically to eight GPUs. |
| **G3: audit and release** | Freeze source, integer blob/specification, program key, proof, public statement, evaluation evidence and manifests. Check raw/pattern/model commitment mutations and independent residuals. Stage publication and fetch-back verification. | 1–2 engineering days; **$0 GPU** normally. | Hold publication if the evidence or claimed relation does not match the artifact. |

The G0 thresholds are proposed engineering decisions, not inherited paper requirements or security guarantees. An 80-row screen must be reported as such; it does not reproduce the existing 1,700-row result. Reserve a small August development block from the **new** model’s training if the proved August row is to be called held out. Otherwise disclose that it was a training row. The 288 verification rows remain outside this work.

**Expected successful path [estimate]: 4–7 engineering days, roughly 5–9 elapsed days, and $25–150 GPU spend including contingency.** The lower end assumes staged data, available hardware and a passing first model. A resolution rescue or data-access delay can move the schedule beyond a week. The financial ceiling is much less restrictive than the learning and engineering uncertainty.


### Receipt, publication and claims

Stage the proof bundle in **`poliebotics/zeebeam`**, with the empirical companion in **`poliebotics/dark-lantern`**. Put larger reproducibility artifacts under a new immutable versioned prefix on the existing TruthBeam data layer. Include the model and preprocessing specifications, provenance and selected-row disclosure, oracle outputs, instruction/prover logs, final proof and publics, standalone verifier, checksums and fetch-back receipt. These are proposed locations, not completed uploads. Existing repository organisation (on-box: `README.md` line 54), data-layer publication practice (on-box: `README.md` line 145).

Suggested title: **“ZeeBeam: Diffusion in Zero Knowledge”**  
Subtitle: **“One Whole-Frame Conditional Denoising Verdict Bound to a Recorded Session Row.”**

The publishable claim, after a successful run, is:

> **For one recorded ZeeBeam row, a zero-knowledge proof binds whole-frame integer preprocessing and two executions of a pinned conditional diffusion denoiser to the committed frame and emitted-pattern records. The wrong-condition residual exceeds the correct-condition residual by the published integer difference. This establishes execution binding.**

It may report the separately measured conditioning discrimination with its actual model, split, sample count and selection procedure. It may not claim proof of physical capture, illumination causality, realness, liveness, adversarial resistance, unseen-take generalisation, or a complete diffusion sampling trajectory. The new model does not inherit the eight-seed AUROC. Those limitations follow the paper’s distinction between exact evaluation and physical meaning. Paper’s claim boundary (on-box: `zeebeam.md` line 567), audited diffusion limitations (repository root: `audits/diffusion_8seed_audit/CLAIM_DRAFT.md` line 42).

Do not count the existing `conditional_micro` artifact as completion: it uses real-development-derived 4×4 tensors, but does not prove the full-frame preprocessing and row binding, and its aggregate diffusion inequality conceals a failing directional comparison. Micro-proof’s own scope and results (repository root: `proofs/conditional_micro/README.md` line 10).

Avoid the detours: eight-seed retraining, a resolution/width sweep, a teacher-distillation campaign, full reverse diffusion, new custom cryptography, an SP1 precompile project, a new blockchain ceremony, hardware shopping, or proving all 259 rows. Preserve failed-attempt records and disclose any positive-example selection; neither requires turning this into another campaign.

**Audit note:** this review checked local source, archived measurements and arithmetic. No data inference or proof generation was performed. Alternative-stack throughput, cloud capacity, checkpoint/corpus accessibility and small-model separation remain unverified. One source discrepancy is explicit: the paper records a prior r32 one-look evaluation of the 288 rows on 6 September; this brief excludes those rows from diffusion work, and they were not inspected.

**VERDICT: A lean zero-crop diffusion execution-binding demo is plausibly achievable in about one engineering week and comfortably under $1,000 GPU spend [estimate], conditional on G0 passing. My working budget is 4–7 engineering days and $25–150 GPU. Full-resolution ARM-C through the current SP1 guest is outside those bounds.**

— BOSUN ⚓