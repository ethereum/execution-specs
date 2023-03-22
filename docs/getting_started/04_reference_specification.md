# Referencing Specification Documents

## Referencing an EIP in a test file

An Ethereum Improvement Proposal can be directly referenced within a python test file.

This is accomplished by adding two key variables anywhere in the file:

- REFERENCE_SPEC_GIT_PATH: Path within the https://github.com/ethereum/EIPs/ repository to the EIP markdown file.
    E.g. `"EIPS/eip-1234.md"`
- REFERENCE_SPEC_VERSION: `SHA` digest of the current version of the file

The `SHA` digest can be obtained using the github api by using the following endpoint:

```
https://api.github.com/repos/ethereum/EIPs/contents/EIPS/eip-<EIP Number>.md
```

By adding this reference in the python test file, the `tf` command will automatically detect and warn when there have been changes to the referenced EIP markdown file.
