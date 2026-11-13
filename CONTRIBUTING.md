# Contribution Guidelines

Help is always welcome. The Ethereum Execution Layer Specifications (EELS) are a community effort and we appreciate support in the following areas:

- Reporting issues.
- Fixing and responding to [issues](https://github.com/ethereum/execution-specs/issues), especially those tagged [E-easy](https://github.com/ethereum/execution-specs/labels/E-easy), which are intended as introductory issues for external contributors.
- Improving the documentation.

## Before you open a pull request

Our review resources are constrained, so we review pull requests that have a concrete reason behind them, for example:

- Something in this repository is broken for a project you maintain (link it).
- Your client is missing test coverage that a change here would add (name the client and link the gap).
- A fix for an open issue that a maintainer has assigned to you.

New EIP features stay on your own fork until the EIP is Proposed or Considered for Inclusion (PFI or CFI) in a fork. Open an issue that links your branch and a maintainer will ask for a pull request when the time comes.

### What we won't review

We close the following without review:

- Pull requests from outside contributors that don't link an issue assigned to them. These are closed automatically.
- New EIP features for EIPs that are not yet PFI or CFI.
- Changes without a concrete reason, such as refactors, renames or style changes nobody asked for.
- Changes that only fix spelling, grammar or formatting.
- Drive-by or vibe-coded contributions, including generated code or text the author hasn't reviewed and can't explain.
- Work on an issue assigned to someone else, or a duplicate of an open pull request.

### Outside contributors

This applies to everyone without write access who isn't a member of the Ethereum GitHub organization or on the bypass list. For every pull request:

1. Comment on an existing issue, or open a new one, saying in your own words what you want to change and why.
2. Wait for a maintainer to assign the issue to you.
3. Open a pull request that links the issue with a [closing keyword](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue#linking-a-pull-request-to-an-issue-using-a-keyword), for example `Closes #123`.

Pull requests without a linked issue assigned to their author are closed automatically. A closed pull request can't be reopened by its author, so open a new one once you are assigned. Your branch is not affected.

### Limits

- Contributors without write access can have at most 2 open pull requests, drafts included.

If you are an EIP author or part of an EL client or tooling team, message us in `#el-testing` on the [Ethereum R&D Discord](https://discord.com/invite/qGpsxSA) to get added to the bypass list.

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

Maintainers apply the matching labels when triaging the PR.

Keep the description short, lowercase and in the imperative mood ("add", not "added" or "adds"), with code names in backticks and no trailing period.
