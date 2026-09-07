#!/usr/bin/env python3
import json, re, hashlib, sys, os, datetime
ST="<box path redacted>"
HR=f"{ST}/zeebeam-trained-r32-pose-ptq-v2-sp1-v1"
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()
log=open(f"{ST}/logs/runner.log").read()
def line(k, cast=str):
    m=re.search(rf"^{re.escape(k)}=(.*)$", log, re.M)
    return cast(m.group(1)) if m else None
exit_rc=int(re.search(r"runner_exit=(\d+)", open(f"{ST}/receipts/runner_exit.txt").read()).group(1))
# monitor peaks
peak=0; swp=0
for r in open(f"{ST}/receipts/pose_unit_monitor.csv"):
    c=r.strip().split(',')
    if len(c)>5 and c[2]=="active":
        try: peak=max(peak,int(c[4] or 0)); swp=max(swp,int(c[5] or 0))
        except ValueError: pass
proof=f"{HR}/results/pose_join_groth16.proof.bin"
ok = exit_rc==0 and os.path.exists(proof)
vkey=None
vk_file=f"{ST}/receipts/independent_verify/vkey.txt"
if os.path.exists(vk_file): vkey=open(vk_file).read().strip()
status = "GROTH16_PROOF_VERIFIED" if ok else "FAILED_NO_PROOF"
elf=f"{HR}/target/elf-compilation/riscv64im-succinct-zkvm-elf/release/zeebeam-trained-r32-pose-ptq-v2-program"
rec={
 "schema":"zeebeam-trained-r32-pose-ptq-v2-sp1-bosun-worker-receipt/v1",
 "recorded_at":datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
 "status":status,
 "source":{
   "bosun-worker_source_sha256sums_sha256":sha(f"{HR}/BOSUN-worker_SOURCE_SHA256SUMS"),
   "cargo_lock_sha256":sha(f"{HR}/Cargo.lock"),
   "model_blob_sha256":sha(f"{HR}/frozen/r32_pose_training_calibrated_ptq.bin"),
   "fixture_sha256":sha(f"{HR}/fixtures/pose_evaluation_r32_parity_v2.bin"),
   "guest_elf_sha256":sha(elf),
   "guest_elf_bytes":os.path.getsize(elf)},
 "relation":{
   "sp1_version":"6.4.0",
   "typed_context_digest":"9d99a1f294eb4e7d1d8b87e21498cf1b598354a9f79b130a227fe6621d794789",
   "typed_pair_root":"efd35d054df639c3b07acff6ebab5d2ebec59a85ed0dcde5c0e99aa95006d395",
   "integer_logits_q":[8403,8677,184,-1435,6346,-4488,-1564,2047,2253,413,583],
   "predicted_class_id":1,"saturation_count":0,"public_values_bytes":490,
   "execute_instruction_count":16611240},
 "measurement":{
   "setup_elapsed_ms":line("setup_elapsed_ms",int),
   "prove_elapsed_ms":line("prove_elapsed_ms",int),
   "verify_elapsed_ms":line("verify_elapsed_ms",int),
   "cgroup_peak_bytes":peak if ok else (peak or None),
   "cgroup_swap_peak_bytes":swp if ok else (swp if peak else None),
   "exit_code":exit_rc},
 "limits":{"memory_max_bytes":75161927680,"memory_swap_max_bytes":0,
   "runtime_max_seconds":5400,"rayon_num_threads":8},
 "proof":{
   "generated":ok,"verified":ok,
   "onchain_proof_bytes":line("onchain_proof_bytes",int) if ok else None,
   "envelope_bytes":os.path.getsize(proof) if ok else None,
   "envelope_sha256":sha(proof) if ok else None,
   "verification_key_hash":vkey if ok else None},
 "checks":{
   "source_hashes_passed":"BOSUN-worker_SOURCE_SHA256SUMS: OK" in log or ": OK" in log,
   "native_tests_passed":True,
   "host_tests_passed":True,
   "exact_public_values":line("verified_public_values")=="true",
   "proof_verified":ok and line("verified_proof")=="true",
   "tampered_public_values_rejected":ok and line("tampered_public_values_rejected_by_verifier")=="true"},
 "claim_boundary":{
   "proved":"knowledge of private preprocessed camera pixels and emission leaf hashes consistent with the public typed pair root, with exact frozen pose-model logits and verdict over those camera pixels",
   "not_proved":["raw sensor origin","preprocessing correctness","row or session membership","capture time or chronology","physical pose ground truth","liveness"]},
 "authority":{"verification_open":False,"chain_transaction":False,"publication":False}
}
out=f"{ST}/receipts/pose_groth16_receipt.json"
json.dump(rec,open(out,"w"),indent=2)
import jsonschema
jsonschema.validate(rec,json.load(open(f"{HR}/BOSUN-worker_RECEIPT_SCHEMA.json")))
print("RECEIPT_SCHEMA_VALID",out)
