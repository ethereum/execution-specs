## Introduction

This document outlines the process of specifying and testing EIPs for the Ethereum execution layer. It is intended for EIP authors, researchers and implementers. An EIP will typically go through the following stages:

1. **Research**: The EIP author concieves and refines an idea for an improvement to Ethereum.
2. **Plain English Specification**: The EIP author writes a document describing the EIP. This is done in the eips repository. [EIPS](https://github.com/ethereum/EIPs/tree/master/EIPS)
3. **Executable Specifications**: The EIP is implemented in the `execution-specs`. This is intended to make the EIP executable, identify any immediate and obvious implementation issues with the EIP (For example, the eip may not be compatible with some minor detail of the current Ethereum Virtual Machine).
4. **Writing Tests**: The EIP author writes test schemes for the EIP in the `execution-spec-tests` repository. Having the reference implementation should help identify the various logical flows to test and thus, feed into more robust testing. Once the test schemes are written, the reference implementation can then be used to fill the tests and generate the test vectors.
5. **Community Discussion**: The EIP is now ready for discussion with the broader Ethereum community. Although the feedback from the community can be sought at all stages of the EIP lifecycle, we feel that having a reference implementation and tests act as a good bridge between research and client implemtation. It also helps core developers (who have limited time and resources) to understand the EIP better and provide more informed feedback.
6. **Inclusion in a Fork**: Contigent on the community agreeing to the merits of the EIP, it can be included for implementation in a future fork. The test vectors can then be generated using the reference implementation and made available to the client teams.
7. **Client Implementation**: The EIP is implemented by the various client teams with the test vectors as the guide.
8. **Mainnet Deployment**: The EIP is deployed on the Ethereum mainnet.

This document will focus on stages 3 and 4 of the above lifecycle.


### Executable Specifications

This repository contains the executable specifications for the Ethereum execution layer.

## Folder Structure

# Forks live on mainnet

The folder `src/ethereum` contains the specifications for the different execution layer forks. Each fork has its own folder. For example, the folder `src/ethereum/frontier` contains the specifications for the Frontier hardfork. The `state_transition` function which is available in the `src/ethereum/<FORK NAME>/fork.py` is the transition function for each fork.

# Forks under development

At the time of writing, the Prague Fork is still under development and the previous fork is Cancun, which is live on Mainnet.

So the prague folder under `src/ethereum` is essentially just the Cancun fork with the values of variables updated to reflect Prague and its under-development status. This folder (`src/ethereum/prague`) serves as the baseline for further Prague development and all the EIPs for Prague are to be implemented in this folder.

## Branch Structure

# Forks live on mainnet

The final stable specification for all forks that are currently live on mainnet are in the `master` branch.

# Forks under development

At any given time, there can only be one fork under active development. The branch structure for the fork under development is as follows:

- `forks/<FORK_NAME>`: The main branch for the fork under development. For example, `forks/prague` is the branch for the Prague fork. This branch will  be merged into `master` after the fork has gone live on mainnet. 
- `eips/<FORK_NAME>/<EIP_NUMBER>`: Branches for each EIP within the fork under development. For example, `eips/prague/eip-7702` is the branch for EIP-7702 for the Prague fork. This branch will be merged into `forks/prague` after the EIP has been confirmed for release in the fork.

## Writing New EIPS

Implementing a new EIP in the `execution-specs` repository involves the following steps:

1. **Create a new branch**: Create a new branch for the EIP under the appropriate fork. For example, if you are implementing an EIP for the Prague fork, create a new branch under `eips/<FORK_NAME>/eip-<EIP_NUMBER>`.
2. **Implement the EIP**: Implement the EIP in the `src/ethereum/<FORK_NAME>` folder.
3. **Basic sanity checks**: Run `tox -e static` to run basic formatting and linting checks.
4. **Raise a PR**: Raise a PR against the appropriate branch. For example, if you are implementing an EIP for the Prague fork, raise a PR against the `forks/prague` branch.

An EIP can only be CFI'd (Considered For Inclusion) if it has a reference `execution-specs` implementation. The EIP author is responsible for maintaining their EIP up-to-date with the latest changes. For example, if an author had written their EIP for Cancun under `eips/cancun/eip-x`, but for some reason it didn't make it into Cancun, they would need to rebase their EIP to reflect the changes in Prague under `eips/prague/eip-x`.

Please refer the following tutorial for writing new EIP. It takes you through a sample EIP for adding a new opcode to the specs.
[Tutorial](https://www.youtube.com/watch?v=QIcw_DGSy3s&t)

## Writing Tests with `execution-spec-tests`

In addition to having a reference implementation, it is also very useful for the community and core development if the EIP author concieves and writes test vectors for the EIP. There is a very user friendly framework for writing ethereum tests in the `execution-spec-tests` repository. Please refer to the following guide for writing tests to your EIP.

[Writing Tests with `execution-spec-tests`](https://ethereum.github.io/execution-spec-tests/main/getting_started/quick_start/)