# Publication subset of the SP1 v6.1.0 Groth16 runtime cache

Retained: `Groth16Verifier.sol` (the generated on-chain verifier for the circuit, MIT, Succinct Labs; template by Remco
Bloemen) and `groth16_vk.bin` (the verifying key). Absent: `constraints.json`, `groth16_circuit.bin`, `groth16_pk.bin`
(large circuit and proving-key material), the upstream `SP1VerifierGroth16.sol` excerpt (it imports an interface that is
not shipped) and `groth16_witness.json` (an upstream circuit-build template, unused by the release path). `.complete` was
deleted because this publication is not a complete installed cache. This is not an installed or runnable proving cache.
Licence texts: `licenses/` at the repository root.
