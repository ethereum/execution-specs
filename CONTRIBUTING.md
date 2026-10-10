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

## Commit messages and PR titles

Pull requests are squash merged, and the PR title becomes the commit message. PR titles follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```text
<type>(<area>): <description>
```

`<type>` comes from a [`C-<type>`](https://github.com/ethereum/execution-specs/labels?q=C-) label:

| `<type>`   | Label        | Use for                                                     |
| ---------- | ------------ | ----------------------------------------------------------- |
| `feat`     | `C-feat`     | An improvement or new feature, including new test cases.    |
| `fix`      | `C-bug`      | A bug fix. Issues use the `bug` label; PR titles use `fix`. |
| `refactor` | `C-refactor` | Code changes that neither fix a bug nor add a feature.      |
| `perf`     | `C-perf`     | A performance optimization.                                 |
| `docs`     | `C-docs`     | Documentation-only changes.                                 |
| `test`     | `C-test`     | Changes to unit tests only.                                 |
| `chore`    | `C-chore`    | Routine maintenance, such as cleanups and dependency bumps. |

The remaining `C-` labels (for example `C-eip`, `C-question` and `C-tracker`) categorize issues and are not used as title types.

`<area>` comes from an [`A-<area>`](https://github.com/ethereum/execution-specs/labels?q=A-) label, for example `spec-specs` for the specification, `tests` for consensus tests, `test-fill` for the `fill` command, `doc` for documentation, or `ci`. Separate multiple areas with a comma, for example `feat(spec-specs,tests): ...`.

Keep the description short, lowercase and in the imperative mood ("add", not "added" or "adds"), with code names in backticks and no trailing period.
