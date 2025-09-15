## 🗒️ Description
<!-- Brief description of the changes introduced by this PR -->
<!-- Don't submit this PR if it could expose a mainnet bug, see SECURITY.md in the repo root for details -->

## 🔗 Related Issues or PRs
<!-- Reference any related issues using the GitHub issue number (e.g., Fixes #123). Default is N/A. -->
N/A.

## ✅ Checklist
<!-- Please check off all required items. For those that don't apply remove them accordingly. -->

- [ ] All: Ran fast `tox` checks to avoid unnecessary CI fails, see also [Code Standards](https://eest.ethereum.org/main/getting_started/code_standards/) and [Enabling Pre-commit Checks](https://eest.ethereum.org/main/dev/precommit/):
    ```console
    uvx --with=tox-uv tox -e lint,typecheck,spellcheck,markdownlint
    ```
- [ ] All: PR title adheres to the [repo standard](https://eest.ethereum.org/main/getting_started/contributing/?h=contri#commit-messages-issue-and-pr-titles) - it will be used as the squash commit message and should start `type(scope):`.
- [ ] All: Considered adding an entry to [CHANGELOG.md](/ethereum/execution-spec-tests/blob/main/docs/CHANGELOG.md).
- [ ] All: Considered updating the online docs in the [./docs/](/ethereum/execution-spec-tests/blob/main/docs/) directory.
- [ ] All: Set appropriate labels for the changes (only maintainers can apply labels).
- [ ] Tests: Ran `mkdocs serve` locally and verified the auto-generated docs for new tests in the [Test Case Reference](https://eest.ethereum.org/main/tests/) are correctly formatted.
- [ ] Tests: For PRs implementing a missed test case, update the [post-mortem document](/ethereum/execution-spec-tests/blob/main/docs/writing_tests/post_mortems.md) to add an entry the list.
- [ ] Ported Tests: All converted JSON/YML tests from [ethereum/tests](/ethereum/tests) or [tests/static](/ethereum/execution-spec-tests/blob/main/tests/static) have been assigned `@ported_from` marker.

#### Cute Animal Picture

![Put a link to a cute animal picture inside the parenthesis-->]()
