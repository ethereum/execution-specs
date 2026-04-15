# Adding a New EIP

This page outlines the process of specifying and testing EIPs for the Ethereum execution layer. It is intended for EIP authors, researchers, and implementers.

An EIP will typically go through the following stages:

| Stage              | Activities  | Outputs |
| ------------------ | ----------- | ------- |
| *Pre-Draft*        | Prospective EIP author conceives of an idea for an improvement to Ethereum, and discusses with the community. | <ul><li>Vague Consensus on [Ethereum Magicians][0]</li></ul> |
| **Draft**          | <p>EIP author writes a technical human-language document describing the improvement, initially in broad strokes and becoming more specific over time.</p><p>Concurrently, they develop a Python reference implementation to make the EIP executable and identify any immediate/obvious implementation issues. For example, the EIP may not be compatible with some detail of the current Ethereum Virtual Machine.</p><p>Finally for this stage, the author begins to write test schemes for the EIP. Having the reference implementation should help identify the various logical flows to test and thus feed into more robust testing. Once the test schemes are written, the reference implementation can then be used to fill the tests and generate the test vectors.</p> | <ul><li>Complete (but not final) document in [EIPs Repository][1]</li><li>Reference implementation in EELS (this repository)</li><li>Initial tests under `./tests/` (this repository)</li></ul> |
| **Review**         | <p>The broader Ethereum community discusses and provides input on the proposal.</p><p>Although the feedback from the community can be sought at all lifecycle stages, having a reference implementation and tests act as a good bridge between research and client implementation. It also helps core developers (who have limited time and resources) to understand the EIP better and provide more informed feedback.</p> | <ul><li>Complete &amp; final document in the [EIPs Repository][1]</li><li>Comprehensive tests under `./tests/`</li></ul> |
| **Last&nbsp;Call** | Usually after being nominated for inclusion in a fork, the EIP author signals that the proposal is effectively done and begins the last period for comments/discussion. | <ul><li>Complete reference implementation in EELS</li><li>Complete tests under `./tests/`</li><li>Immutable proposal in [EIPs Repository][1]</li></ul> |
| **Final**          | The proposal is now immutable (cannot be changed) and exists for reference. | <ul><li>Mainnet client implementations</li></ul> |

[0]: https://ethereum-magicians.org/
[1]: https://github.com/ethereum/EIPs/

The rest of this page focuses on the **Draft** and **Review** stages, where EIP authors interact most directly with EELS and the test suite.

## Executable specifications

This repository contains the executable specifications for the Ethereum execution layer under `src/ethereum/`.

### Forks live on mainnet

The folder `src/ethereum/forks/` contains the specifications for the different execution layer forks. Each fork has its own folder. For example, `src/ethereum/forks/frontier/` contains the specifications for the Frontier hardfork. The `state_transition` function in `src/ethereum/forks/<FORK_NAME>/fork.py` is the transition function for each fork.

### Fork under development

At any given time, there is a single fork under development. Any new EIP is implemented in the folder for that fork (`src/ethereum/forks/<FORK_NAME>/`).

For example, if Amsterdam is under development and Prague is live on mainnet, the `src/ethereum/forks/amsterdam/` folder starts as a copy of Prague with values updated to reflect Amsterdam and its under-development status. This folder serves as the baseline for further development and all new EIPs are implemented in it.

## Branch structure

### Forks live on mainnet

The final stable specification for all forks that are currently live on mainnet are on the `mainnet` branch.

### Fork under development

At any given time there is exactly one fork under active development. The branch structure for the fork under development is:

- `forks/<FORK_NAME>`: The main branch for the fork under development. For example, `forks/amsterdam` is the branch for the Amsterdam fork. This branch will be merged into `mainnet` after the fork has gone live.
- `eips/<FORK_NAME>/<EIP_NUMBER>`: Branches for each EIP within the fork under development. For example, `eips/amsterdam/eip-7928` is the branch for EIP-7928 for the Amsterdam fork. This branch will be merged into `forks/amsterdam` after the EIP has been confirmed for release in the fork.

## Writing a new EIP

Implementing a new EIP in this repository involves the following steps:

1. **Create a new branch.** Create a branch for the EIP under the appropriate fork. For example, if you are implementing an EIP for the Amsterdam fork, create a branch `eips/amsterdam/eip-<EIP_NUMBER>`.
2. **Implement the EIP.** Implement the EIP in the `src/ethereum/forks/<FORK_NAME>/` folder. See [Writing Specs](writing_specs.md) for style rules and the `ethereum_spec_tools` CLI utilities (the *New Fork Tool* in particular).
3. **Basic sanity checks.** Run `just static` to run formatting, linting, and spec-specific lints.
4. **Raise a PR.** Raise a PR against the appropriate fork branch. For example, if you are implementing an EIP for Amsterdam, raise a PR against `forks/amsterdam`.

An EIP can only be CFI'd (Considered For Inclusion) if it has a reference EELS implementation. The EIP author is responsible for keeping their EIP up to date with the latest changes. For example, if an author had written their EIP for Prague under `eips/prague/eip-x`, but for some reason it didn't make it into Prague, they would need to rebase their EIP to reflect the changes in Amsterdam under `eips/amsterdam/eip-x`.

A sample tutorial that walks through adding a new opcode to the specification is available on YouTube: [EELS tutorial](https://www.youtube.com/watch?v=QIcw_DGSy3s).

## Writing tests for an EIP

In addition to a reference implementation, it is very useful for the community and for core development if the EIP author conceives and writes test vectors for the EIP. Tests live in this repository under `./tests/` and use a user-friendly Python test-writing framework. See [Writing Tests](../writing_tests/index.md) for a guide.
