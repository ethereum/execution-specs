# KZG Point Evaluation Test Vectors

This directory contains test vectors for the KZG point evaluation algorithm, compiled from different sources.

Each file must contain a JSON list of objects, each with the following fields:
- `name`: a string describing the test case
- `input`: object containing `commitment`, `proof`, `z` and `y`
- `output`: expected output of the evaluation, true, false or null.

The files are loaded and used throughout different test fillers.

Current files and their sources:
- `go_kzg_4844_verify_kzg_proof.json`: test vectors from the [go-kzg-4844](https://github.com/crate-crypto/go-kzg-4844) repository.