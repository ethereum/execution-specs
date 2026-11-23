# EIP-8288 proof vectors

The proofs here are genuine dependency proofs of the recursive guest of
`Nethermind.Crypto.Lean` 0.24.0 (NethermindEth/lean-bindings at `8dbfc66e`,
upstream leanVM `f7ba4999`, leanSPHINCS over Keccak-256), whose key is
`AGGREGATED_VK = 645bc491d3d0728b8a0f556be143f845e2ff80aa59da060d750f32cfb05b800c`.

Each proof file is named by its `block_deps_hash`: Keccak-256 of the sorted,
deduplicated claims, each in its canonical 96-byte encoding (scheme word,
data hash, verification key hash). The proof bytes are the native backend's
serialization, as an execution payload's `dependencyProof` carries them.

`keys.bin` holds sixteen test leanSPHINCS public keys (`PK.seed || PK.root`),
from seeds `[i, 42, 42, ..., 42]` for `i = 0..15`. `leanstark-key.bin` is the
verification key hash of the accept-all leanSTARK test program. These are test
keys only.

## Regenerating

Build the native library and the two signing helpers from lean-bindings:

```sh
cd src/ffi
cargo build --release --lib --example fixtures --example eels_sign
```

`eels_sign` is not part of lean-bindings; add it as
`src/ffi/examples/eels_sign.rs` first:

```rust
// Local helper for EELS EIP-8288 fixture generation (not committed).
// eels_sign key <seed-byte>           -> prints the 32-byte leanSPHINCS key (hex)
// eels_sign sign <seed-byte> <msghex> -> prints key || signature (hex)
use lean_sphincs::{key_gen, sign};
use nethermind_lean::verification_key;
fn main() {
    let a: Vec<String> = std::env::args().collect();
    let mut sk = [42u8; 32];
    sk[0] = a[2].parse().unwrap();
    let pk = key_gen(&sk);
    let hex = |b: &[u8]| b.iter().map(|x| format!("{x:02x}")).collect::<String>();
    match a[1].as_str() {
        "key" => println!("{}", hex(&verification_key(&pk))),
        "sign" => {
            let m = &a[3];
            let mut msg = [0u8; 32];
            for i in 0..32 { msg[i] = u8::from_str_radix(&m[i*2..i*2+2], 16).unwrap(); }
            let s = sign(&sk, &msg);
            println!("{}{}", hex(&verification_key(&pk)), hex(&s.to_bytes()));
        }
        _ => panic!("usage"),
    }
}
```

Then fill with the build directory in `EIP8288_PROVER`; missing proofs are
proved through `nlean_prove_recursive` and written here:

```sh
EIP8288_PROVER=<lean-bindings>/src/ffi/target/release \
ETHEREUM_LEAN_LIBRARY=<lean-bindings>/src/ffi/target/release/libnethermind_lean.dylib \
  uv run fill tests/bogota/eip8288_proof_aggregation --fork Bogota
```

`ETHEREUM_LEAN_LIBRARY` is also what the specification's
`ethereum.crypto.leanvm` loads to verify proofs when it consumes fixtures.

| File | SHA-256 |
| --- | --- |
| `0626b5195994357b039bfdaf3744e86a2106acd576b64afab0e74d4c45a4da98.bin` | `1b3f9815cc04999da58fdd28e47b2cc642d8d0aa294e2ccaf8021d2614fbd4d5` |
| `112b6e1e5663647deda5d410690db3b9bf11b77e10a0c5667ca86d86d856a28c.bin` | `cb86ed4943ec1adce828fb31a18f350ee570ddb4fe47d7e80da72d168b1c7c73` |
| `1c4fb731f4b09b72f97726d2b4bd47647bf14910254ad5e691aa76d289eb560f.bin` | `1ead987619080a44f4a5bfa8576ece5a43a3eb8ee1f1695e806040bb6967cf63` |
| `3f8670a180cc65df0178d8142c18d64077899a8ca45637638653fbc5612ed67d.bin` | `46ce0afa5e53c11c94b218f249b670cd5ad03392a6aa769eb2f7a2adfaa66ae8` |
| `4bf41199019ed5f3d506aaf404f3e6f1010d14ce3dbb13eaa9fc0dd8ecb4c40e.bin` | `0d9a36c07a027914bc0d2bb1e9e292a67e8ae9a6918afe0d79fea72c7f533435` |
| `617488ee5cf2ea58957891e1d70690cbba4cb02049500584e0e57f02a00ab257.bin` | `8e4557f83ca6a7d8835b7e1a0fc24c3d321dec70f1fbba9aab8f83dbd31b24cf` |
| `7c2c01aa9d733d8d4d3309d02e97a371f8acb2c69a7b24c9a653de034ceaad26.bin` | `c932b61868dad6b4b76630d49370f9d70db49c285d48774a4ca22dc3754083a7` |
| `87cb79c24181a591303010a1f2ce1c9f8ab76501f31cbed1da1142f447e0894a.bin` | `1797e4e9a3959efd9cf9d040be0891dcecddc5620e32317d7e341efc9f3c3fcb` |
| `95b6d00a3b487c4e49f6e54f45f40868efa413c5e102519e1ef6537c40fdc412.bin` | `a3be32ec3785a0c6b20e54392377d76a16b46d0083b89541b8b5790792e46e6a` |
| `c6dc6f8e67105f37426525594602a52b1c65159aef9d19eee14d954d54b730c6.bin` | `459c887d3410293238c848666cde402dc4d32e181804cfc178ed1ddb7523e995` |
| `d19cf97511937f90756acbaf4b78de3031525eb6dfccc4f6a2a71b512c193c0e.bin` | `ca78ab9efdb6e3fa4275ca263c72530473076644565b116a96b5c2fcf981f643` |
| `f3ef5c19075a1cdd4520204939c0ee4f81bda0f433cf25c2a80cc2cb40aaa57f.bin` | `6532ae77ffe2f910d804fe3fa44989611784939da57769f529bcf3faf6742454` |
| `f9fbac023f4b152e011df0fb4a6cb9c6e394da507514219c1a90f0975f9c62dd.bin` | `723286a051a3fddf0cb1132665a65276ce82b059ba703d775dcdf14551bdbd5e` |
| `ff6d7d3e27029ee3c60abd688c0093f5bbbf4e62b3ac3ca0b4cfed696df0bdb3.bin` | `90bc29323fefe0b1df6c7041952c38866a66c38d1ef2c61c72533e0782aa6233` |
| `keys.bin` | `4bf170c11bf8c4c073c3659a81e634374d9c6d210fb38b056faff1bc713dbfaa` |
| `leanstark-key.bin` | `fd753cd040d903cb2b2fd891ecd1a732669a5827f11283ad55cf949dbca93c30` |
