## 🗒️ Description
<!-- Brief description of the changes introduced by this PR -->
<!-- Don't submit this PR if it could expose a mainnet bug, see SECURITY.md in the repo root for details -->

## 🔗 Related Issues or PRs
<!-- Reference any related issues using the GitHub issue number (e.g., Fixes #123). Default is N/A. -->
N/A.

## ✅ Checklist
<!-- Please check off all required items. For those that don't apply remove them accordingly. -->

- [ ] All: Ran fast static checks to avoid unnecessary CI fails, see also [Code Standards](https://steel.ethereum.foundation/docs/execution-specs/getting_started/code_standards/) and [Verifying Changes](https://steel.ethereum.foundation/docs/execution-specs/getting_started/verifying_changes/):
    ```console
    just static
    ```
- [ ] All: PR title have the form `<type>(<area>):`, where `<type>` and `<area>` come from an approrpriate `C-<type>`, respectively `A-<area>`, label. The title should match the a target squash commit message.
- [ ] All: Considered updating the online docs in the [./docs/](/ethereum/execution-specs/blob/HEAD/docs/) directory.
- [ ] All: Set appropriate labels for the changes (only maintainers can apply labels).
- [ ] Tests: For PRs implementing a missed test case, update the [post-mortem document](/ethereum/execution-specs/blob/HEAD/docs/writing_tests/post_mortems.md) to add an entry the list.
- [ ] Ported Tests: Add the following docstring to manually enhanced tests from `./tests/ported_static/`:
    ```text
	@manually-enhanced: Do not overwrite. Post-state expectations corrected
	manually (see PR #2784).
	````

#### Cute Animal Picture

![Put a link to a cute animal picture inside the parenthesis-->]()
