# KZG Point Evaluation Test Vectors

This directory contains test vectors for the KZG point evaluation algorithm that are loaded and used throughout different tests.

Each file must contain a JSON list of objects, each with the following fields:

- `name`: a string describing the test case
- `input`: object containing `commitment`, `proof`, `z` and `y`
- `output`: expected output of the evaluation, true, false or null.

## Generating The Test Vectors (used in v1.0.6 and on)

From execution-spec-tests release v1.0.6 and on, the point evaluation test vectors were generated using commit [63aa303c](https://github.com/ethereum/consensus-specs/tree/63aa303c5a2cf46ea98edbf3f82286079651bb78) from the [official-kzg](https://github.com/ethereum/consensus-specs/commits/official-kzg) [consensus-specs](https://github.com/ethereum/consensus-specs) branch.

The test vectors were generated as following:

1. In the consensus-specs repo:

    ```console
    cd tests/generators/kzg_4844/
    rm -rf /tmp/kzg_4844_output
    mkdir /tmp/kzg_4844_output
    python -m main --output /tmp/kzg_4844_output
    ```

2. In the execution-spec-tests repo:

    ```console
    cd tests/cancun/4844_blobs/point_evaluation_vectors/
    pip install -r requirements.txt
    python concat_kzg_vectors_to_json.py \
        --input /tmp/kzg_4844_output/general/deneb/kzg/verify_kzg_proof/kzg-mainnet/
        --output go_kzg_4844_verify_kzg_proof.json
    ```

## Previous Versions of the Test Vectors (used up to v1.0.5)

The test vectors up and including execution-spec-tests [release v1.0.5](https://github.com/ethereum/execution-spec-tests/releases/tag/v1.0.5) were:
- `go_kzg_4844_verify_kzg_proof.json`: test vectors from the [go-kzg-4844](https://github.com/crate-crypto/go-kzg-4844) repository.