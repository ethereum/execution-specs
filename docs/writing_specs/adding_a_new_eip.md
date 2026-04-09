# Adding a New EIP

This guide walks through implementing a new EIP in the execution-specs repository.

## EIP Lifecycle

An EIP typically progresses through these stages:

| Stage | Activities | Outputs |
|---|---|---|
| _Pre-Draft_ | Conceive of an improvement, discuss with the community. | Vague consensus on [Ethereum Magicians](https://ethereum-magicians.org/). |
| **Draft** | Write the EIP document. Develop a Python reference implementation. Begin writing test schemes. | EIP document in the [EIPs Repository](https://github.com/ethereum/EIPs/). Reference implementation and initial tests in [execution-specs](https://github.com/ethereum/execution-specs). |
| **Review** | Community discusses and provides input. Having a reference implementation and tests bridges research and client implementation. | Comprehensive tests alongside the spec. |
| **Last Call** | EIP is nominated for a fork. Final period for comments. | Complete reference implementation and tests. Immutable proposal. |
| **Final** | Immutable. Exists for reference. | Mainnet client implementations. |

## Steps

### 1. Create a branch

Create a branch for your EIP under the appropriate fork:

```text
eips/<fork_name>/eip-<number>
```

For example, `eips/amsterdam/eip-1234`.

### 2. Implement the EIP

Implement the changes in the `src/ethereum/<fork_name>/` directory. The fork folder is a complete copy of the previous fork, so you modify it in place.

### 3. Run checks

```console
just static
```

This runs formatting, linting and type checks.

### 4. Raise a PR

Open a PR against the fork's main branch (e.g., `forks/amsterdam`).

!!! note "CFI requirement"
    An EIP can only be Considered For Inclusion (CFI) if it has a reference implementation in this repository. The EIP author is responsible for keeping their implementation up to date. If an EIP misses its target fork, rebase the branch onto the next fork.

## Writing Tests

Tests for an EIP live alongside the specs in this same repository, under `tests/<fork_name>/`. See [Writing Tests](../writing_tests/index.md) for a guide to the test framework.

## Tutorial

For a video walkthrough of implementing a sample EIP (adding a new opcode), see [this tutorial](https://www.youtube.com/watch?v=QIcw_DGSy3s&t).
