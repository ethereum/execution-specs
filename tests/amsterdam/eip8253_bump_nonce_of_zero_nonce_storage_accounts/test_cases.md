# EIP-8253 Bump Nonce of Zero-Nonce Storage Accounts Test Cases

All tests are fork-transition tests: the bump happens once, at the Amsterdam fork block. The targeted accounts are placed in the pre-state as on Mainnet (empty code, zero nonce, non-empty storage). `[0,1]` denotes the nonce change at block access index zero with post-nonce one.

| Function Name | Goal | Setup | Expectation | Status |
|---------------|------|-------|-------------|--------|
| `test_nonce_bump_at_fork_block` | Bump every targeted account exactly once, at the fork block | All 28 targets in the pre-state with distinct balances and their Mainnet storage; a transfer to one target before the fork; plain transfers in the fork block and the block after | Fork block BAL: each target once with only `[0,1]` (no balance, code, storage change, or storage read). Block after: targets absent. Post-state: nonce one, balance, storage, and empty code preserved, pre-fork transfer kept. | ✅ Completed |
| `test_targeted_accounts_absent_from_pre_state` | Bump is unconditional | No target in the pre-state | Each target created with nonce one, zero balance, no code; BAL `[0,1]`. | ✅ Completed |
| `test_non_targeted_accounts_unaffected` | Bump follows the fixed list, not the account shape | Same-shape look-alikes (one untouched, one read via `BALANCE`), a contract with storage, a used EOA, a fresh EOA | Untouched accounts absent from the BAL; the read look-alike present with empty changes; every nonce unchanged. | ✅ Completed |
| `test_create_collision_at_fork_block` | `CREATE` collision after the bump | Parametrized over all 28 targets: the Mainnet creator is deployed at its original creation nonce and repeats the `CREATE` as the first transaction of the fork block | `CREATE` returns zero, target keeps storage and empty code, creator nonce increments. Target BAL: only `[0,1]`, `storage_reads=[]` (collision from the nonce, not from a storage check). | ✅ Completed |
| `test_create_collision_after_fork_block` | Bump is not replayed | Same replay one block after the fork block | Target appears only as an accessed account with empty changes; `CREATE` still collides. | ✅ Completed |
| `test_create_early_failure_at_fork_block` | `CREATE` failing before the target is accessed | Parametrized: insufficient balance, static context, out of gas one below the opcode's own charge | Target: only `[0,1]`. Creator: no nonce change. | ✅ Completed |
| `test_call_to_bumped_account` | Calls to a target behave the same before and at the fork block | `CALL` with value plus `EXTCODEHASH`, `EXTCODESIZE`, `BALANCE` in the pre-fork block and in the fork block | Both succeed; fork block BAL pairs `[0,1]` with the balance change at index one. | ✅ Completed |
| `test_bal_bump_and_read_only_access` | Read-only access adds nothing | Parametrized: `BALANCE`, `EXTCODEHASH`, `EXTCODESIZE`, `CALL`, `STATICCALL`, `DELEGATECALL` against the target | One account entry with only `[0,1]`. | ✅ Completed |
| `test_bal_bump_and_transaction_to_targeted_account` | Zero-value and value transfers | Transaction to the target with value 0 or 5 | Value 0: only `[0,1]`. Value 5: `[0,1]` plus `balance_changes=[[1, post_balance]]`. | ✅ Completed |
| `test_bal_bump_and_reverted_transfer` | Bump survives a reverted transfer | `CALL` with value, or `SELFDESTRUCT` to the target, inside a frame that reverts | Target: only `[0,1]`; no balance change; reverting contracts present with empty changes. | ✅ Completed |
| `test_bal_bump_and_oog_before_target_access` | Target present although the access never happens | `CALL` to the target that runs out of gas before the target is accessed | Target: only `[0,1]`; caller present with empty changes. | ✅ Completed |
| `test_bal_bump_and_access_list_entry` | EIP-2930 listing is not an access | Type-1 transaction listing the target and its storage keys, sent elsewhere | Target: only `[0,1]`, `storage_reads=[]`. | ✅ Completed |
| `test_bal_bump_and_selfdestruct_beneficiary` | `SELFDESTRUCT` to the target | Pre-deployed victim with zero or positive balance self-destructs to the target | Zero: only `[0,1]`. Positive: `[0,1]` plus balance change at index one. | ✅ Completed |
| `test_bal_bump_of_fee_recipient` | Target as fee recipient | Parametrized: empty block, transaction with zero tip, transaction with positive tip | Empty block and zero tip: target present with only `[0,1]` (an untouched fee recipient is otherwise absent). Positive tip: plus balance change at index one. | ✅ Completed |
| `test_bal_bump_of_recipient_and_fee_recipient_in_one_transaction` | Same-index coalescing | Target is both transaction recipient and fee recipient | `[0,1]` plus exactly one balance change at index one with the combined balance. | ✅ Completed |
| `test_bal_bump_and_withdrawals` | Withdrawals to the target | Parametrized: one withdrawal, zero-amount withdrawal, three withdrawals, transfer then withdrawal | Zero amount: only `[0,1]`. Otherwise one balance change at the post-transaction index with the summed amount; the transfer variant also has one at index one. | ✅ Completed |
| `test_bal_bump_size_limit_counts_targeted_address_once` | Bumped address counts once toward the BAL budget | Empty fork block at the exact budget with a withdrawal to the target, or to another account | Target recipient: accepted. Other recipient: `BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED`. | ✅ Completed |
| `test_bal_access_to_bumped_account_after_fork_block` | No repeated bump | `BALANCE` of the target in the fork block and the block after | Fork block: `[0,1]`. Next block: empty changes. | ✅ Completed |
| `test_bal_invalid_missing_bumped_account` | Reject omitted target | Remove the untouched target's entry | `INVALID_BLOCK_ACCESS_LIST` | ✅ Completed |
| `test_bal_invalid_missing_bump_on_touched_account` | Reject missing `[0,1]` on a present account | Target receives value; drop only the nonce change | `INVALID_BLOCK_ACCESS_LIST` | ✅ Completed |
| `test_bal_invalid_bump_nonce_value` | Reject wrong post-nonce | Replace `[0,1]` with `[0,0]` or `[0,2]` | `INVALID_BLOCK_ACCESS_LIST` | ✅ Completed |
| `test_bal_invalid_bump_index` | Reject wrong index | Replace `[0,1]` with `[1,1]` or `[2,1]` (post-transaction index) | `INVALID_BLOCK_ACCESS_LIST` | ✅ Completed |
| `test_bal_invalid_duplicate_bump` | Reject duplicate nonce change | Two `[0,1]` entries | `INVALID_BLOCK_ACCESS_LIST` | ✅ Completed |
| `test_bal_invalid_split_target_account` | Reject fork and transaction changes in separate entries | Target receives value; split its entry into a nonce-only and a balance-only entry | `INCORRECT_BLOCK_FORMAT` | ✅ Completed |
| `test_bal_invalid_spurious_bump_field` | Reject anything but `[0,1]` at index zero | Add a balance change (true value), code change, storage write, or storage read to the untouched target | `INVALID_BLOCK_ACCESS_LIST` | ✅ Completed |
| `test_bal_invalid_missing_later_target_change` | Fork entry cannot mask later changes | Correct `[0,1]`; remove the balance change of a transfer or of a withdrawal | `INVALID_BLOCK_ACCESS_LIST` | ✅ Completed |
| `test_bal_invalid_target_ordering` | Targets sort with all accounts | Move the target's entry to the other end of the BAL | `INCORRECT_BLOCK_FORMAT` | ✅ Completed |
| `test_bal_invalid_bump_index_zero_encoding` | Canonical RLP of index zero | Engine only: encode the nonce change's index zero as `0x00` instead of the empty string, header committing to canonical or payload RLP | `INVALID_BLOCK_ACCESS_LIST` | ✅ Completed |

## Covered elsewhere

| Proposed case | Where |
|---------------|-------|
| BAL size budget of the fork block (28 extra items, no storage items) | `tests/amsterdam/eip7928_block_level_access_lists/test_fork_transition.py::test_fork_transition_bal_size_constraint` |
| State root reconstruction from the BAL | Every fixture carries the pre-state, the BAL, and the post-state root; consumers reconstruct from them. Not a separate test. |
| `CREATE2` collision at a target | Not possible: no salt and init code pair deriving a target address is known. `CREATE` collisions cover all 28 targets. |
