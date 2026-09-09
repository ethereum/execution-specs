# EIP-8253 test cases

| Test | Description | Status |
| --- | --- | --- |
| `test_nonce_bump_and_bal` | Bump all 28 fixed accounts at the Amsterdam boundary, preserve balance/code/storage, leave a non-target storage account unchanged, emit index-zero BAL nonce changes, and do not reapply the transition. | Implemented |
| `test_create_collision_in_first_fork_transaction` | Recreate a known historical target via its original creator and nonce in the first Amsterdam transaction; EIP-684 rejects it after the transition bump. | Implemented |
| CALL behavior | Check that calling a targeted account remains successful and does not charge new-account gas. | Not yet implemented |
| BAL replay | Reapply the activation BAL to the pre-fork root and compare the post-fork root. | Covered indirectly by fixture state-root validation; an explicit replay test is not yet implemented |
| Invalid activation payload and reorgs | Ensure an invalid first payload does not consume the transition and each branch crossing the boundary applies it. | Not yet implemented |
