# Contribution Guidelines

Help is always welcome. The Ethereum Execution Layer Specifications (EELS) are a community effort and we appreciate support in the following areas:

- Reporting issues.
- Fixing and responding to [issues](https://github.com/ethereum/execution-specs/issues), especially those tagged [E-easy](https://github.com/ethereum/execution-specs/labels/E-easy), which are intended as introductory issues for external contributors.
- Improving the documentation.

> [!IMPORTANT]
> Generally, we do not assign issues to external contributors. If you want to work on an issue, you are welcome to go ahead and make a pull request. We are happy to answer questions before you start implementing.

## Contributions we don't accept

Pull requests should have reasonable substance and context. In particular, we do not accept:

- Contributions that only fix spelling or grammatical errors in documentation, code, or elsewhere.
- Drive-by or vibe-coded contributions without proper engagement or context.

## Code of Conduct

All contributors are expected to be excellent to each other; other behavior is not tolerated. To report a concern, contact one of the [STEEL team members](https://steel.ethereum.foundation/team/).

## Principles

The specification aims to be:

1. **Correct.** Describe the *intended* behavior of the Ethereum blockchain. Any deviation from that is a bug.
2. **Complete.** Capture the entirety of *consensus-critical* parts of Ethereum.
3. **Accessible.** Prioritize readability, clarity, and plain language over performance and brevity.

## Getting set up

Environment setup (cloning the repository, installing `uv` and `just`, Python requirements) is documented in the [Installation guide](docs/getting_started/installation.md).

Before opening a PR, run the checks relevant to your change; see [Verifying Changes](docs/getting_started/verifying_changes.md).

## Changes that affect multiple forks

When creating pull requests that touch several forks under `src/ethereum/forks/`, we recommend a two-step workflow:

1. Apply the changes on a single fork, open a *draft* PR, and get feedback.
2. Apply the changes across the other forks, push them, and mark the PR as ready for review.

This saves you from applying code review feedback repeatedly for each fork.

See [Writing Specs](docs/specs/writing_specs.md) for the technical style rules (naming, comments, docstrings, constants, cross-fork discipline) and for the `ethereum_spec_tools` CLI utilities that help with these workflows.
