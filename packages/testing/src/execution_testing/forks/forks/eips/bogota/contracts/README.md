# EIP-8483 contracts and proofs

## Bytecode

Bogota pre-allocates the runtime bytecode of three contracts. The two
registration predeploys come from sys-asm#60 at `49891c0`, and they call the
verifier at `0x8483…ffff` to check a proof of possession:

| File | Contract | Source |
| --- | --- | --- |
| `pq_validator_registrations.bin` | Validator registrations | sys-asm `bytecode/pq_validator_registrations/main.hex` |
| `pq_builder_registrations.bin` | Builder registrations | sys-asm `bytecode/pq_builder_registrations/main.hex` |
| `pq_proof_of_possession.bin` | `PQProofOfPossession` | leanxmss-evm-verifier at `c91df85`, as sys-asm copies it to `test/vectors/pq_proof_of_possession/main.hex` |

## Proofs of possession

The EIP-8483 registration contracts only queue a request with a proof of
possession of its leanXMSS key. A proof signs the chain ID, so the tests need
proofs for chain 1, the chain `fill` uses. These files come from
[leanxmss-evm-verifier](https://github.com/ethereum/leanxmss-evm-verifier),
which has the verifier and the generator that signs the proofs.

`leanxmss_pop_chain_1.json` has 17 valid proofs for chain ID 1, each with
its own XMSS and BLS key, and two that the verifier rejects: `wrongLeaf` is
signed at leaf 1, and `noDomain` signs the message without the domain. The
generator wrote it at `d130696`, run from its `xmss/` directory:

```sh
cargo run --release -- --chain-id 1 --proofs 17 \
    --out <this directory>/leanxmss_pop_chain_1.json
```

`leanxmss_pop_chain_31337.json` is `contracts/test/vectors/leanxmss_pop.json`
at `c91df85`, the vectors of the verifier's forge tests. On chain 1 its
proofs are valid proofs for another chain, which the verifier rejects.
