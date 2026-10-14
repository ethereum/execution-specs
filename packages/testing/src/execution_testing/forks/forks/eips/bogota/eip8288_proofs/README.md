# EIP-8288 proof vectors

These proofs and the sixteen test public keys come from [`export_eip8288_test_proofs`](https://github.com/spencer-tb/leanVM/blob/46cb599c0e40b605b21d91dd78d6adb2a93f6bd7/crates/rec_aggregation/src/eip8288_mixed.rs), built on the `eip8288-spec-align` guest. The pinned guest key is `6deed6ff48d7e4af71132fb8cdc5224d16574d0358a94d274af5caee648c80ad`.

Each proof filename is the BLAKE2s digest of its sorted, deduplicated `data_hash || verification_key_hash` entries. The payload is the fixed-integer bincode encoding of the deferred bytecode point, two deferred matrix points, and the CPU proof. `keys.bin` contains sixteen consecutive 32-byte public keys, generated from seeds `[i + 1; 32]` for `i = 0..15`. These are test keys.

To regenerate at the pinned leanVM revision, first set `EIP8288_PROOF_REQUESTS` to an existing directory and fill the EIP-8288 suite with the proof files absent. The fill writes the missing canonical dependency sets there. Then run:

```sh
EXPORT_DIR=<proof-directory> EXPORT_REQUESTS=<request-directory> \
  cargo test --release --features eip8288-mixed \
  export_eip8288_test_proofs -- --ignored
```

The exporter verifies each proof with Rust before writing it. Filling retrieves proofs by digest. EELS blockchain replay checks them through the pinned `leanvm-verifier` package.

This guest has a 256-distinct-claim root capacity and an 8 MiB payload limit. These are prototype profile limits, not additional limits specified by the pinned EIP. Adopting another guest or verifier protocol requires a new key and new vectors.

| File | SHA-256 |
| --- | --- |
| `018886cc6c8396b49ccac16f5e577766953a2d369a1f8923ac76dd48808daa03.bin` | `5a06e3ab13657cbea0d8a43255067fbe1c3c76a60f585f6f47a19804bfff7f6f` |
| `2113dc437806ce845a00b0a80c3110c727ba1bae5b035c60c578603f5d2e537f.bin` | `5f93d046808e55a11079059905c6931223b77927f0ec21d49e704bcc3f874367` |
| `44a58ded6710703387be45a51940575f3956e0564c586a559d8eba7a5ed1dfe4.bin` | `68bb1db05257da9830b214f8804e3c4f794e6db70d9e93f25834f1f43e2bf19c` |
| `62188a2c2888630968acc1a40efd5ab4682697e3973198dc0b421bc00782e044.bin` | `3a058398b5a3e29c0461ec98f104c322c0698ce94a1f28a0d8d78861c1b102ba` |
| `69b66c60ef170946844ec4426426b61785d6c460681ef0b889c6c2002e34e96c.bin` | `f787ab75fde3266511f3fafcf478ee0017f2a3de0b45b09881562d7c6723d579` |
| `85a47cde2d970c60c6fe4ce348f3f9191ea4bc3c444a0e4f95a5e7516d61a090.bin` | `42f74aa80a34baf018c3b13402ae7e383509f1aa4e6add38478d675ffe994927` |
| `9dd89d6a8fef38ab98628069153a98b198569c75c6f3550c0083e831c2b1cf6a.bin` | `bffe8e601e7ec5badb903912a7f333f6c7d40bf34d364b630876a76af3aff7af` |
| `b4c9b73a4dc3f366ab0eb5b10e47fc9eee05b6fdfe888b0a14f01ac744965eff.bin` | `87828558c7831ede65bbc287de51f00c1ee5bd144346546d4208f1197011c032` |
| `fe29cfbae16d419494baf2800df856f0236e2b5457eaf3027764d5b4f63562d4.bin` | `b604e615308d2b8a8d7a5703c60adf89dae1c4f882bf17468ec30d161dcac003` |
| `keys.bin` | `d7822e1a8e39679fef4b6ea46e0a5afcd5b41a38a30548aa3ba8571144187768` |
