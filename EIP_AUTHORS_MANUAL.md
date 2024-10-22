# Introduction

This document outlines the process of specifying and testing EIPs for the Ethereum execution layer. It is intended for EIP authors, researchers and implementers. An EIP will typically go through the following stages:

| Stage              | Activities  | Outputs |
| ------------------ | ----------- | ------- |
| _Pre‑Draft_        | Prospective EIP author conceives of an idea for an improvement to Ethereum, and discusses with the community. | <ul><li>Vague Consensus on [Ethereum Magicians][0]</li></ul> |
| **Draft**          | <p>EIP author writes a technical human-language document describing the improvement, initially in broad strokes and becoming more specific over time.</p><p>Concurrently, they develop a Python reference implementation to make the EIP executable and identify any immediate/obvious implementation issues. For example, the EIP may not be compatible with some detail of the current Ethereum Virtual Machine.</p><p>Finally for this stage, the author begins to write test schemes for the EIP. Having the reference implementation should help identify the various logical flows to test and thus feed into more robust testing. Once the test schemes are written, the reference implementation can then be used to fill the tests and generate the test vectors.</p> | <ul><li>Complete (but not final) document in [EIPs Repository][1]</li><li>Reference Implementation in [EELS][2]</li><li>Initial Tests in [EEST][3]</li></ul> |
| **Review**         | <p>The broader Ethereum community discusses and provides input on the proposal.</p><p>Although the feedback from the community can be sought at all lifecycle stages, having a reference implementation and tests act as a good bridge between research and client implemtation. It also helps core developers (who have limited time and resources) to understand the EIP better and provide more informed feedback.</p> | <ul><li>Complete &amp; final document in the [EIPs Repository][1]</li><li>Comprehensive tests in [EEST][3]</li></ul>
| **Last&nbsp;Call** | Usually after being nominated for inclusion in a fork, the EIP author signals that the proposal is effectively done and begins the last period for comments/discussion. | <ul><li>Complete reference implementation in [EELS][2]</li><li>Complete tests in [EEST][3]</li><li>Immutable proposal in [EIPs Repository][1]</li></ul> |
| **Final**          | The proposal is now immutable (cannot be changed) and exists for reference. | <ul><li>Mainnet client implementations</li></ul> |

[0]: https://ethereum-magicians.org/
[1]: https://github.com/ethereum/EIPs/
[2]: https://github.com/ethereum/execution-specs
[3]: https://github.com/ethereum/execution-spec-tests

This document will focus on stages 3 and 4 of the above lifecycle.


# Executable Specifications

This repository contains the executable specifications for the Ethereum execution layer.

## Folder Structure

### Forks live on mainnet

The folder `src/ethereum` contains the specifications for the different execution layer forks. Each fork has its own folder. For example, the folder `src/ethereum/frontier` contains the specifications for the Frontier hardfork. The `state_transition` function which is available in the `src/ethereum/<FORK NAME>/fork.py` is the transition function for each fork.

### Fork under development

At any given time, there is a single fork under development. Any new EIP has to be implemented in the folder that is meant for that fork (`src/ethereum/<FORK_NAME>` folder). 

For example, at the time of writing, the Prague Fork is still under development and the previous fork is Cancun, which is live on Mainnet. So the prague folder under `src/ethereum` is essentially just the Cancun fork with the values of variables updated to reflect Prague and its under-development status. This folder (`src/ethereum/prague`) serves as the baseline for further development and all new EIPs are to be implemented in this folder.

## Branch Structure

### Forks live on mainnet

The final stable specification for all forks that are currently live on mainnet are in the `master` branch.

### Fork under development

At any given time, there can only be one fork under active development. The branch structure for the fork under development is as follows:

- `forks/<FORK_NAME>`: The main branch for the fork under development. For example, `forks/prague` is the branch for the Prague fork. This branch will  be merged into `master` after the fork has gone live on mainnet. 
- `eips/<FORK_NAME>/<EIP_NUMBER>`: Branches for each EIP within the fork under development. For example, `eips/prague/eip-7702` is the branch for EIP-7702 for the Prague fork. This branch will be merged into `forks/prague` after the EIP has been confirmed for release in the fork.

# Writing New EIPS

Implementing a new EIP in the `execution-specs` repository involves the following steps:

1. **Create a new branch**: Create a new branch for the EIP under the appropriate fork. For example, if you are implementing an EIP for the Prague fork, create a new branch under `eips/<FORK_NAME>/eip-<EIP_NUMBER>`.
2. **Implement the EIP**: Implement the EIP in the `src/ethereum/<FORK_NAME>` folder.
3. **Basic sanity checks**: Run `tox -e static` to run basic formatting and linting checks.
4. **Raise a PR**: Raise a PR against the appropriate branch. For example, if you are implementing an EIP for the Prague fork, raise a PR against the `forks/prague` branch.

An EIP can only be CFI'd (Considered For Inclusion) if it has a reference `execution-specs` implementation. The EIP author is responsible for maintaining their EIP up-to-date with the latest changes. For example, if an author had written their EIP for Cancun under `eips/cancun/eip-x`, but for some reason it didn't make it into Cancun, they would need to rebase their EIP to reflect the changes in Prague under `eips/prague/eip-x`.

Please refer the following tutorial for writing new EIP. It takes you through a sample EIP for adding a new opcode to the specs.
[Tutorial](https://www.youtube.com/watch?v=QIcw_DGSy3s&t)

# Writing Tests with `execution-spec-tests`

In addition to having a reference implementation, it is also very useful for the community and core development if the EIP author concieves and writes test vectors for the EIP. There is a very user friendly framework for writing ethereum tests in the `execution-spec-tests` repository. Please refer to the following guide for writing tests to your EIP.

[Writing Tests with `execution-spec-tests`](https://ethereum.github.io/execution-spec-tests/main/getting_started/quick_start/)