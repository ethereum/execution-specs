# Engine API reorg tests

These tests fill `blockchain_test_engine_reorg` fixtures: a labeled block DAG
plus an ordered list of Engine API and JSON-RPC steps, run against one fresh
client by `consume reorg`. See [the format documentation](https://steel.ethereum.foundation/docs/execution-specs/running_tests/test_formats/blockchain_test_engine_reorg/).

This README maps the current tests to commit-pinned sources. Its notes record
adaptations and omissions; a related source does not establish equivalent
coverage. Function docstrings describe the scenarios in more detail.

| Kind | Meaning |
|---|---|
| port | The source scenario, calls and observations are reproduced. |
| adapted port | The source scenario is reshaped, with changed mechanisms, shape or expectations stated in the notes. |
| partial port | Only the stated checks or variants of the source are reproduced. |
| inspiration | Related shape or context, not a port; listed only in the related column. |

Labels in brackets are pytest case-ID components, not complete node IDs: fork
and fixture-format components are omitted. For example,
`[canonical-field_state_root]` identifies a chain/field combination.

## `test_depth_matrix.py`

Side-chain replacements and canonical-ancestor rewinds at default and requested
higher depth limits. Depths up to 8 must be applied; deeper default-limit
reorgs may return `-38006`. Every side payload is delivered by `newPayload`:
these are not peer-sync or backfill tests.

| Test | Source relationship and limitations | Related upstream tests |
|---|---|---|
| `test_side_chain_reorg_depth_default`: Replace a branch and return to the original tip. | Authored depth matrix: `[depth_1]`, `[depth_8]`, `[depth_31]`, `[depth_32]`, `[depth_64]`, `[depth_128]`; no direct depth-policy port. | Inspiration: Erigon [`TestReorgsWithInsertChain`][erigon-insert] switches shallow branches (at most 10 blocks unwound), not a deep-limit test. Erigon [`TestNewPayloadShouldReturnValidWhenSideChainGoingBackIsLtMaxReorgDepth`][erigon-lower-side] imports one low side block, not a replacement branch. geth [`testReorgLong`][geth-reorg-long] selects by total difficulty, not FCU. |
| `test_canonical_ancestor_reorg_depth_default`: Rewind to a1 and clear higher canonical mappings. | Authored default-limit matrix, with the same six depth components as the side-chain row. Rewinds within 8 blocks must move the head; deeper ones may return `-38006`. | Related: geth [`TestForkchoiceUpdatedReorgDepthLimit`][geth-depth] tests canonical-ancestor rewinds with explicit limited/unlimited configurations, not this default-limit matrix. |
| `test_side_chain_reorg_depth_tuned`: Request a higher depth limit before replacing a branch. | Adapted port of geth [`TestLargeReorgTrieGC`][geth-trie-gc]: execution across a state-retention horizon, via Engine API rather than internal inserts; no trie-GC/cache assertions. `[depth_64]` requires application; `[depth_129]` also allows disputed SYNCING for missing state. The fixture requests `HIVE_ENGINE_MAX_REORG_DEPTH`; wrapper support is not an assertion that tuning works on every client. | Inspiration: reth [`test_long_reorg`][reth-long-reorg] and [`test_reorg_through_backfill`][reth-backfill] use two-node sync; Besu [`BackwardSyncContextTest`][besu-backward-sync] uses mocked sync machinery. ethrex [`deep_reorg_beyond_legacy_128_cap_succeeds`][ethrex-depth] tests cap policy with mostly fake stored headers, not full EVM execution. |

## `test_fork_boundary_reorg.py`

Valid payloads and FCUs across timestamp 15000, for transitions from
Paris → Shanghai onwards. Both tests check withdrawals credited on the winning
branch and reverted on the losing branch. They do not send wrong-version
payloads or request builds.

| Test | Source relationship and limitations | Related upstream tests |
|---|---|---|
| `test_reorg_across_fork_boundary`: Switch between branches activating the fork at different heights. | Partial port of Hive [`WithdrawalsReorgSpec`][hive-withdrawals]: reduced branch lengths and withdrawal counts, NewPayload delivery only. `[side_activates_later]` and `[side_activates_earlier]` cover both activation orders; the latter mirrors the [canonical block 8 / side block 7 registration][hive-withdrawals-earlier]. Generalized to later transitions. | Related: geth [`TestEngineAPIAcrossForks`][geth-forks] checks FCU(attrs) → getPayload → newPayload → FCU across activation, but does not reorg. |
| `test_sibling_first_fork_blocks`: Switch between first post-fork siblings, then extend the loser. | Partial port of Hive [`WithdrawalsReorgSpec`][hive-withdrawals], reducing the [same-height fork registration][hive-withdrawals-same] to two siblings and a child; no sync-delivery variants. | No additional source. |

## `test_forkchoice_behaviour.py`

Post-merge forkchoice: head selection, canonical mappings, labels and payload
knowledge. Short rewinds above finalized, or with no finalized block, must
actually be applied rather than acknowledged as VALID no-ops.

| Test | Source relationship and limitations | Related upstream tests |
|---|---|---|
| `test_head_follows_fcu_regardless_of_length`: FCU selects shorter, equal and longer branches. | Partial port of geth [`TestReorgToShorterRemovesCanonMapping`][geth-shorter-mapping] for `[shorter]` and `[from_genesis_shorter]`: canonical-number cleanup only; FCU replaces difficulty selection, and by-hash retention is not checked. `[equal]`, `[longer]`, `[near_tip_longer]` extend the FCU-length-independence scenario. | Inspiration: Nethermind [`Can_reorganize_to_shorter_path`][nm-shorter], [`Can_reorganize_to_same_length`][nm-equal] and [`Can_reorganize_to_longer_path`][nm-longer] select by total difficulty, not requested head hash. |
| `test_forks_going_back_and_forward_in_height`: Interleave three genesis forks of heights 2, 1 and 2. | Adapted port of Erigon [`TestValidateChainAndUpdateForkChoiceWithSideForksThatGoBackAndForwardInHeight`][erigon-heights]: preserve the per-block import/forkchoice order through public Engine API calls and explicitly check that higher canonical mappings disappear. | No additional source. |
| `test_reorg_back_and_forth_between_branches`: Ping-pong between two branches. | Adapted port of reth [`test_tree_state_on_new_head_deep_fork`][reth-branch-bounce]: six-block branches instead of ten, public FCU/canonical queries instead of internal old/new-chain assertions. | Inspiration: Nethermind [`Can_reorganize_there_and_back`][nm-bounce] is difficulty-driven; Erigon [`TestReorgsWithInsertChain`][erigon-insert] is a shallow internal-insert scenario. |
| `test_reorg_to_older_canonical_ancestor_and_forward`: Rewind to a5 after each extension, then return to the tip. | Partial port of Hive [`ReOrgBackToCanonicalTest`][hive-back-canonical]: repeated depths 1–5; omit its optional side-payload execution. Adapted port of Erigon [`TestFcuAllowsReorgBackOnCanonicalChainWhenAfterFinalisedHash`][erigon-rewind]: repeat its one-block rewind at multiple depths, without its contract setup. | Historical contrast: Besu [`shouldIgnoreUpdateToOldHeadAndNotPreparePayload`][besu-old-build-skip] returned VALID without preparing a payload; [`forkchoiceUpdateShouldIgnoreAncestorOfChainHead`][besu-old-rewind-skip] never rewound. Neither establishes the required applied-rewind behavior here. |
| `test_fcu_to_unknown_block_is_syncing`: Recover canonical progress after unknown-head FCUs. | Partial ports of Hive [`ForkchoiceUpdatedUnknownBlockHashTest`][hive-unknown] (without payload-attribute variants) and [`ReOrgBackFromSyncingTest`][hive-back-syncing]. FCU to never-delivered s14 and NP/FCU to leaf s15 are SYNCING only; recover a5, then apply the next canonical a6. Unlike Hive's older leaf expectation, unknown ancestors do not allow ACCEPTED here. | Related: Besu [`shouldReturnInvalidForkchoiceStateIfFinalizedBlockIsUnknown`][besu-unknown-finalized] and [`shouldReturnInvalidForkchoiceStateIfSafeBlockIsUnknown`][besu-unknown-safe] check the unknown-label rejections with mocks. |
| `test_inconsistent_forkchoice_state`: Reject a head, safe or finalized hash on the other branch. | Adapted port of Hive [`InconsistentForkchoiceTest`][hive-inconsistent]: `[field_head]`, `[field_safe]`, `[field_finalized]`. The safe case finalizes genesis to isolate the off-chain safe hash; all cases recover with a valid canonical FCU. | Related: Nethermind [`inconsistent_sibling_hash_is_rejected`][nm-inconsistent] has named cases `inconsistent_finalized_hash` and `inconsistent_safe_hash`; Besu [`shouldReturnInvalidForkchoiceStateIfFinalizedBlockIsNotAnAncestorOfNewHead`][besu-offchain-finalized] and [`shouldReturnInvalidForkchoiceStateIfSafeBlockIsNotAnAncestorOfNewHead`][besu-offchain-safe] are mocked checks. |
| `test_safe_finalized_labels_follow_fcu`: Track latest, safe and finalized through branch switches. | Adapted port of Hive [`SafeReOrgToSideChainTest`][hive-safe-reorg]: fixed three-block chains, then extra zero-safe and all-equal updates. Zero safe with nonzero finalized also permits disputed `-38002`. | Related: Nethermind [`forkchoiceUpdatedV1_should_update_finalized_block_hash`][nm-finalized], [`forkchoiceUpdatedV1_should_update_safe_block_hash`][nm-safe] and [`forkchoiceUpdatedV1_should_change_head_when_all_parameters_are_the_newHeadHash`][nm-all-equal] check individual label updates. |
| `test_newpayload_does_not_move_head`: Payload delivery alone changes neither latest nor canonical mappings. | Adapted port of Hive [`NewPayloadWithMissingFcUTest`][hive-missing-fcu]: replay five prefilled payloads without its producer/secondary-node lifecycle; add canonical-number checks, then apply one FCU. | Related: Nethermind [`block_should_not_be_canonical_before_forkchoiceUpdatedV1`][nm-before-fcu] checks canonical membership. No attribution to reth's CreateFork framework smoke test for this invariant. |
| `test_reexecute_payloads`: Replay valid and invalid payloads without changing the head. | Partial port of Hive [`ReExecutePayloadTest`][hive-reexecute]: five canonical payloads instead of ten, without building them on a producer node. Add repeated invalid-payload rejection. | Related: Besu [`shouldReturnSuccessOnAlreadyPresent`][besu-already-present] and [`shouldReuseStoredLatestValidHashOnRepeatedInvalidPayload`][besu-repeat-invalid] cover valid replay and stored invalid LVH with mocks. |
| `test_many_siblings_same_parent`: Import 40 VALID siblings, then select the canonical block. | Partial port of Hive [`MultiplePayloadsExtendingCanonicalChainTest`][hive-siblings]: 40 siblings versus upstream 80, with both [registrations][hive-sibling-orders] covered by `[siblings_first]` and `[canonical_first]`; fixture payloads replace client-built payloads. | No additional source. |
| `test_out_of_order_payload_delivery`: Fill an unknown-parent gap, then select the child. | Partial port of Hive [`NewPayloadOnSyncingClientTest`][hive-syncing-payload] and adapted port of reth [`test_engine_tree_buffered_blocks_are_eventually_connected_e2e`][reth-buffered]: one client with prefilled payloads instead of two disconnected nodes. Initial NP and FCU are SYNCING only; resend the child after the parent arrives. | No additional source. |
| `test_alternating_canonical_and_depth1_forks`: Select a canonical block, its sibling and the canonical block again. | Adapted port of geth [`testBlockchainHeaderchainReorgConsistency`][geth-interleaved]: 16 rounds instead of 64; explicit FCUs replace difficulty-driven imports, and RPC head consistency replaces internal block/header equality. | No additional source. |
| `test_valid_and_invalid_forks_with_older_canonical_head`: Rewind, select two forks and reject an invalid extension. | Adapted port of reth [`test_engine_tree_valid_and_invalid_forks_with_older_canonical_head_e2e`][reth-older-head]: eight-block forks instead of ten and one invalid extension; require the initial rewind to move the head, unlike the source's acknowledged ancestor FCU without unwinding. | No additional source. |
| `test_reorg_to_fork_behind_finalized`: Reject a competing head whose chain excludes finalized a7. | Adapted port of the historical reth [`test_reorg_to_fork_behind_finalized`][reth-historical-finalized]: same a5 fork point, a7 finalized and a10 head shape; upstream expected VALID, while this test requires `-38002` per paris.md step 5. | Related: Besu [`shouldReturnInvalidForkchoiceStateIfFinalizedBlockIsNotAnAncestorOfNewHead`][besu-offchain-finalized] checks the rejection with mocks. |
| `test_forkchoice_state_unchanged_on_invalid_state`: Reject an inconsistent FCU atomically. | Partial port of Nethermind [`inconsistent_sibling_hash_is_rejected`][nm-inconsistent]: keep rejection/state-unchanged checks for a head on a sibling branch; do not reproduce every safe/finalized variant. | Related: Besu [`shouldReturnInvalidForkchoiceStateIfFinalizedBlockIsNotAnAncestorOfNewHead`][besu-offchain-finalized] checks the error, not this full RPC-state observation. |
| `test_fcu_rewind_with_no_finalized`: Apply a short rewind with zero finalized hash. | Authored no-finalized variant of the rewind scenario; no direct port. The head must move from a8 to a5 and higher canonical mappings must clear. | Related: Besu [`shouldNotSkipUpdateWhenFinalizedHashIsZero`][besu-no-finalized] verifies that its coordinator is called, not that RPC latest moved. Historical [`forkchoiceUpdateShouldIgnoreAncestorOfChainHead`][besu-old-rewind-skip] expected the opposite no-rewind behavior. |

## `test_forkchoice_reorg.py`

Sibling, invalid-side-chain and finalized-boundary forkchoice tests.

| Test | Source relationship and limitations | Related upstream tests |
|---|---|---|
| `test_sibling_reorg`: State and canonical mappings follow a2 → b2 → a2. | Authored public-API scenario; no direct port. | Related: Nethermind [`block_should_not_be_canonical_after_reorg`][nm-after-reorg] checks sibling canonical membership, without these recipient-balance checks. |
| `test_storage_across_multi_block_reorgs`: Restore storage across branch switches, continuation and rewind/redo. | Adapted port of Erigon [`TestReorgOverStateChange`][erigon-storage]: predeploy a storage writer, add a cleared slot and a read-dependent write, and switch repeatedly with FCU rather than selecting an internally inserted heavier chain. | No additional source. |
| `test_invalid_side_chain`: An execution-invalid branch must never become canonical. | Authored scenario; no direct port. `[invalid_index_1]`, `[invalid_index_3]`, `[invalid_index_5]`. Off-canonical invalid payloads may be ACCEPTED; descendants may remain SYNCING/ACCEPTED, but FCU cannot select the invalid branch. | Inspiration: Hive [`InvalidMissingAncestorReOrgTest`][hive-invalid-ancestor] provides the invalid-ancestor/recovery shape, not this exact delivery sequence. |
| `test_fcu_below_finalized_with_inconsistent_state`: Keep the head when an ancestor of finalized is requested. | Authored paris.md/#786 scenario, including calls without and with build attributes and then inconsistent labels. No direct port; `-38002`/`-38006` alternatives are disputed under execution-apis#891. | Related: Besu [`shouldSkipUpdateWhenHeadIsAncestorOfFinalized`][besu-below-finalized] checks the no-update shortcut; Nethermind [`forkchoiceUpdatedV1_processed_skips_reorg_only_when_head_is_ancestor_of_finalized`][nm-shortcut] checks the processed-ancestor distinction. |
| `test_fcu_finalized_regression`: Move finalized from a9 back to a1 without changing the head. | Authored paris.md/#786 scenario; no direct port. | Related: Nethermind [`forkchoiceUpdated_accepts_lower_finalized_than_previous_but_rejects_safe_before_finalized`][nm-finalized-regression] checks lower finality plus a separate safe-ordering rejection; this test keeps only the regression observation. |
| `test_fcu_rewind_to_canonical_ancestor_above_finalized`: Apply a three-block rewind, then restore the tip. | Authored paris.md/#786 scenario; no direct port. Rewind within 8 blocks must be applied, not refused or acknowledged as a no-op. | Related: Erigon [`TestFcuAllowsReorgBackOnCanonicalChainWhenAfterFinalisedHash`][erigon-rewind] checks an applied rewind; Besu [`shouldNotSkipUpdateWhenHeadIsNotAncestorOfFinalized`][besu-above-finalized] checks coordinator invocation, not RPC latest. geth [`TestForkchoiceUpdatedReorgDepthLimit`][geth-depth] checks rewinds with explicit limits. |

## `test_invalid_payloads_reorg.py`

Malformed payloads, invalid ancestry and `latestValidHash`. These tests start
at Shanghai: bad hashes require INVALID with null LVH; INVALID_BLOCK_HASH is
a newPayloadV1 response, not a permitted Shanghai+ result here.

| Test | Source relationship and limitations | Related upstream tests |
|---|---|---|
| `test_bad_block_hash_on_new_payload`: Reject the claimed hash without poisoning the real payload. | Partial port of Hive [`BadHashOnNewPayload`][hive-bad-hash], non-syncing `[canonical]` and `[sidechain]` shapes only. The sidechain setup uses a validated sibling parent rather than an older canonical parent. Omit Hive's child-of-bad-hash follow-up; instead deliver/select the correctly hashed payload. | No additional source. |
| `test_parent_hash_equals_block_hash`: Reject an unknown self-parent hash with null LVH. | Partial port of Hive [`ParentHashOnNewPayload`][hive-self-parent]: its unknown/self-parent (`Syncing=True`) shape only; this does not mean an initial syncing FCU is sent. The known-real-parent (`Syncing=False`) variant is not reproduced. | No additional source. |
| `test_invalid_payload_field`: Corrupt one header field and recover with a valid sibling. | Partial port of Hive [`InvalidPayloadTestCase`][hive-invalid-field]: non-syncing, nonempty canonical cases, e.g. `[canonical-field_state_root]`; omit other field/syncing/empty-transaction combinations. The `sidechain-field_*` cases are a local extension (e.g. `[sidechain-field_state_root]`) and may return ACCEPTED. INVALID requires parent LVH; `field_number` also permits disputed SYNCING. `[canonical-field_state_root]` additionally checks builder recovery. | Related: geth [`TestEmptyBlocks`][geth-empty] includes a rehashed gas-used-invalid payload, but expects zero LVH above a PoW ancestor; these tests use a known post-merge parent. |
| `test_invalid_missing_ancestor_reorg`: Deliver an invalid ten-block branch and return to a5. | Partial port of Hive [`InvalidMissingAncestorReOrgTest`][hive-invalid-ancestor]: state-root corruption at local positions 1, 3 or 5, nonempty payloads delivered via NP. FCU after each valid prefix block; omit upstream FCUs after invalid/descendant blocks except the final tip. Branch roots vary with `[from_genesis-invalid_index_3]` / `[from_canonical-invalid_index_3]` (also indices 1 and 5). ACCEPTED remains possible for an unvalidated off-canonical block. | Related: Besu [`shouldReturnInvalidWhenParentIsBadBlock`][besu-bad-parent] checks propagation of a seeded LVH with mocks. |
| `test_invalid_ancestor_descendants_delivered_first`: Deliver descendants before their invalid ancestor. | Authored composition of buffering and invalid-ancestor propagation; no direct port. Initially SYNCING only. After the ancestor is rejected, re-sent descendants may be INVALID with the last-valid parent LVH, or SYNCING/ACCEPTED if not validated. | Related: reth [`test_engine_tree_buffered_blocks_are_eventually_connected_e2e`][reth-buffered] delivers valid blocks in reverse order, without an invalid ancestor; Besu [`shouldReturnInvalidWhenParentIsBadBlock`][besu-bad-parent] and [`shouldReturnInvalidWithoutSyncingWhenHeadDescendsFromBadBlock`][besu-bad-head] use seeded invalid ancestry. |

## `test_payload_building_reorg.py`

Build on reorganized heads and observe client-built payloads through
`getPayload`.

| Test | Source relationship and limitations | Related upstream tests |
|---|---|---|
| `test_build_on_previously_validated_side_payload`: Build on a previously validated non-leaf side block. | Adapted port of Hive [`ReOrgPrevValidatedPayloadOnSideChainTest`][hive-build-side]: shorter prefilled branches replace the producer-node lifecycle. Add post-update `-38003` and applicable `-38005` build-attribute checks, verifying that the head update stands. | No additional source. |
| `test_two_built_payloads_same_parent`: Switch the PREVRANDAO value stored by the same transaction in competing builds. | Adapted port of Hive [`SidechainReOrgTest`][hive-build-siblings]: two builds on a1 both include the pending PREVRANDAO-store transaction; select p → q → p and check storage/canonical mappings. Shorter setup and deterministic attributes replace CLMock callbacks. | No additional source. |
| `test_pool_tx_reorged_out_of_built_payload`: Remove and restore the receipt of a transaction in a built payload. | Partial port of Hive [`TransactionReOrgTest` (`ReOrgOut`)][hive-tx-reorg]: one pool transaction and one build on a1; a prefilled b1 removes the receipt, and returning to existing p restores it. No sibling-head build and no `ReOrgBackIn` broadcast/build lifecycle. | No additional source. |

## `test_selfdestruct_reorg.py`

Account creation, destruction and recreation across reorgs. The original
later-block destruction shape runs only in Paris/Shanghai; Cancun+ cases adapt
it to EIP-6780's same-transaction deletion rule.

| Test | Source relationship and limitations | Related upstream tests |
|---|---|---|
| `test_reorg_over_same_tx_selfdestruct`: Switch between a destroyed account and a live sibling, then recreate it. | Adapted port of Erigon [`TestReorgOverSelfDestruct`][erigon-selfdestruct]: factory CREATE2 plus destruction in the creating transaction, instead of separate creation/change/destruction blocks; required by EIP-6780. | Related: Erigon [`TestRecreateAndRewind`][erigon-recreate] destroys/recreates across different blocks under Berlin rules. |
| `test_reorg_over_same_block_destroy_and_recreate`: Reorg a block that destroys and recreates one address. | Authored same-block/EIP-6780 scenario; no direct port of an executable upstream test. | Inspiration/context: Erigon's [`WithoutExperimentalBAL` comment][erigon-recreate-comment] names the intra-block SELFDESTRUCT/CREATE2 limitation. Related: [`TestRecreateAndRewind`][erigon-recreate] recreates in a later block; here deletion is in the creating transaction and recreation is in another transaction of the same block. |
| `test_reorg_over_selfdestruct_in_a_later_block`: Undo both destruction and an earlier storage change. | Adapted port of Erigon [`TestReorgOverSelfDestruct`][erigon-selfdestruct]: preserve creation → change → destruction and branch off creation, using public NP/FCU/state queries instead of internal insertion/database access. Paris and Shanghai only; no EIP-6780 rewrite. | No additional source. |

## `test_tx_receipts_logs_reorg.py`

Transactions, receipts and canonical log queries across reorgs. Transaction-pool
reinjection is observed as client policy, not required as conformance.

| Test | Source relationship and limitations | Related upstream tests |
|---|---|---|
| `test_tx_reorg_shared_dropped_postponed_added`: Receipts and transaction status follow the winning branch. | Adapted port of geth [`testChainTxReorgs`][geth-tx-reorg]: keep shared/dropped/postponed/added classes, with smaller branches, FCU selection and RPC observations instead of internal indexes; omit a separate swapped-transaction class. Dropped transactions may be pending or dropped. | No additional source. |
| `test_logs_follow_reorg`: Return only the canonical branch's logs before and after reorgs. | Adapted port of Erigon [`TestEthGetLogsDoNotGetAffectedAfterNewPayloadOnSideChain`][erigon-logs]: range queries and a smaller emitter replace its block-hash query/contract setup; add branch switches and receipt removal. | Inspiration: geth [`testLogReorgs`][geth-logs] asserts subscription removal events, not these RPC log queries; no event-stream or removed-log-flag coverage is claimed. |
| `test_txpool_reinjection_after_reorg`: Record whether an executable reorged-out transaction returns to the pool. | Policy observation, not a direct conformance port: allow pending or dropped after reorg; require the replacement transaction to be included and restore the original receipt on returning. | Related: reth [`maintain_txpool_reorg`][reth-pool] and Besu [`shouldReAddTransactionsFromThePreviousCanonicalHeadWhenAReorgOccurs`][besu-pool] require reinjection in their pool tests. geth [`LegacyPool.reset`][geth-pool] is implementation context, not an upstream test. |

## Not covered: delivery by peer sync

Every block in these tests reaches the client through `engine_newPayload`.
Reaching a head by syncing it from a peer, as Hive's
[`Withdrawals Fork on Block 1 - 8 Block Re-Org, Sync` registration][hive-withdrawals-sync]
does, is tracked in ethereum/execution-specs#3991.

[geth-depth]: https://github.com/ethereum/go-ethereum/blob/8801a261e0f47d087e80611355b1cfff48f54a67/eth/catalyst/api_test.go#L489
[geth-trie-gc]: https://github.com/ethereum/go-ethereum/blob/8801a261e0f47d087e80611355b1cfff48f54a67/core/blockchain_test.go#L1631
[geth-reorg-long]: https://github.com/ethereum/go-ethereum/blob/8801a261e0f47d087e80611355b1cfff48f54a67/core/blockchain_test.go#L542
[geth-shorter-mapping]: https://github.com/ethereum/go-ethereum/blob/8801a261e0f47d087e80611355b1cfff48f54a67/core/blockchain_test.go#L2299
[geth-forks]: https://github.com/ethereum/go-ethereum/blob/8801a261e0f47d087e80611355b1cfff48f54a67/eth/catalyst/api_forks_test.go#L135
[geth-interleaved]: https://github.com/ethereum/go-ethereum/blob/8801a261e0f47d087e80611355b1cfff48f54a67/core/blockchain_test.go#L1540
[geth-empty]: https://github.com/ethereum/go-ethereum/blob/8801a261e0f47d087e80611355b1cfff48f54a67/eth/catalyst/api_test.go#L793
[geth-tx-reorg]: https://github.com/ethereum/go-ethereum/blob/8801a261e0f47d087e80611355b1cfff48f54a67/core/blockchain_test.go#L926
[geth-logs]: https://github.com/ethereum/go-ethereum/blob/8801a261e0f47d087e80611355b1cfff48f54a67/core/blockchain_test.go#L1063
[geth-pool]: https://github.com/ethereum/go-ethereum/blob/8801a261e0f47d087e80611355b1cfff48f54a67/core/txpool/legacypool/legacypool.go#L1299
[erigon-insert]: https://github.com/erigontech/erigon/blob/d1a4a6b21be22aae5d5fae4caba6721ae97748e5/execution/execmodule/execmoduletester/exec_module_tester_test.go#L84
[erigon-lower-side]: https://github.com/erigontech/erigon/blob/d1a4a6b21be22aae5d5fae4caba6721ae97748e5/execution/engineapi/engine_api_reorg_test.go#L269
[erigon-heights]: https://github.com/erigontech/erigon/blob/d1a4a6b21be22aae5d5fae4caba6721ae97748e5/execution/execmodule/exec_module_test.go#L303
[erigon-rewind]: https://github.com/erigontech/erigon/blob/d1a4a6b21be22aae5d5fae4caba6721ae97748e5/execution/engineapi/engine_api_reorg_test.go#L338
[erigon-storage]: https://github.com/erigontech/erigon/blob/d1a4a6b21be22aae5d5fae4caba6721ae97748e5/execution/tests/state_database_test.go#L669
[erigon-selfdestruct]: https://github.com/erigontech/erigon/blob/d1a4a6b21be22aae5d5fae4caba6721ae97748e5/execution/tests/state_database_test.go#L503
[erigon-recreate]: https://github.com/erigontech/erigon/blob/d1a4a6b21be22aae5d5fae4caba6721ae97748e5/execution/tests/state_database_test.go#L1325
[erigon-recreate-comment]: https://github.com/erigontech/erigon/blob/d1a4a6b21be22aae5d5fae4caba6721ae97748e5/execution/execmodule/execmoduletester/exec_module_tester.go#L315
[erigon-logs]: https://github.com/erigontech/erigon/blob/d1a4a6b21be22aae5d5fae4caba6721ae97748e5/execution/engineapi/engine_api_reorg_test.go#L196
[hive-withdrawals]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/withdrawals/tests.go#L1500
[hive-withdrawals-earlier]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/withdrawals/tests.go#L424
[hive-withdrawals-same]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/withdrawals/tests.go#L328
[hive-withdrawals-sync]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/withdrawals/tests.go#L365
[hive-back-canonical]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/reorg.go#L404
[hive-back-syncing]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/reorg.go#L543
[hive-unknown]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/forkchoice.go#L87
[hive-inconsistent]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/forkchoice.go#L24
[hive-safe-reorg]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/reorg.go#L743
[hive-missing-fcu]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/payload_execution.go#L447
[hive-reexecute]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/payload_execution.go#L17
[hive-siblings]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/payload_execution.go#L202
[hive-sibling-orders]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/tests.go#L147
[hive-syncing-payload]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/payload_execution.go#L300
[hive-bad-hash]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/bad_hash.go#L41
[hive-self-parent]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/bad_hash.go#L139
[hive-invalid-field]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/invalid_payload.go#L23
[hive-invalid-ancestor]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/invalid_ancestor.go#L27
[hive-build-side]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/reorg.go#L629
[hive-build-siblings]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/reorg.go#L20
[hive-tx-reorg]: https://github.com/ethereum/hive/blob/ece8bcb0a1236aa530a4f145cf8aa0d28c568ae6/simulators/ethereum/engine/suites/engine/reorg.go#L124
[reth-long-reorg]: https://github.com/paradigmxyz/reth/blob/8458973f25fec5e2bc1a51992da041620c266e62/crates/ethereum/node/tests/e2e/p2p.rs#L213
[reth-backfill]: https://github.com/paradigmxyz/reth/blob/8458973f25fec5e2bc1a51992da041620c266e62/crates/ethereum/node/tests/e2e/p2p.rs#L295
[reth-branch-bounce]: https://github.com/paradigmxyz/reth/blob/8458973f25fec5e2bc1a51992da041620c266e62/crates/engine/tree/src/tree/tests.rs#L1470
[reth-buffered]: https://github.com/paradigmxyz/reth/blob/8458973f25fec5e2bc1a51992da041620c266e62/crates/engine/tree/tests/e2e-testsuite/main.rs#L500
[reth-older-head]: https://github.com/paradigmxyz/reth/blob/8458973f25fec5e2bc1a51992da041620c266e62/crates/engine/tree/tests/e2e-testsuite/main.rs#L409
[reth-historical-finalized]: https://github.com/paradigmxyz/reth/blob/b224494e257deb41b3b99e388c14580816a7552d/crates/engine/tree/tests/e2e-testsuite/fcu_finalized_blocks.rs#L44
[reth-pool]: https://github.com/paradigmxyz/reth/blob/8458973f25fec5e2bc1a51992da041620c266e62/crates/ethereum/node/tests/e2e/pool.rs#L115
[besu-backward-sync]: https://github.com/besu-eth/besu/blob/6fa699b3bd82d5041a8cd5d591c3eb52c2203233/ethereum/eth/src/test/java/org/hyperledger/besu/ethereum/eth/sync/backwardsync/BackwardSyncContextTest.java#L106
[besu-old-build-skip]: https://github.com/besu-eth/besu/blob/72361b3bb9b67ad07dc3cb933a53acc3c071dd19/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/AbstractEngineForkchoiceUpdatedTest.java#L434
[besu-old-rewind-skip]: https://github.com/besu-eth/besu/blob/72361b3bb9b67ad07dc3cb933a53acc3c071dd19/consensus/merge/src/test/java/org/hyperledger/besu/consensus/merge/blockcreation/MergeCoordinatorTest.java#L1061
[besu-unknown-finalized]: https://github.com/besu-eth/besu/blob/d0d649bb3de87ad150b7c05d1c3e7ad1c556cb96/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineForkchoiceUpdatedV1Test.java#L354
[besu-unknown-safe]: https://github.com/besu-eth/besu/blob/d0d649bb3de87ad150b7c05d1c3e7ad1c556cb96/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineForkchoiceUpdatedV1Test.java#L417
[besu-offchain-finalized]: https://github.com/besu-eth/besu/blob/d0d649bb3de87ad150b7c05d1c3e7ad1c556cb96/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineForkchoiceUpdatedV1Test.java#L373
[besu-offchain-safe]: https://github.com/besu-eth/besu/blob/d0d649bb3de87ad150b7c05d1c3e7ad1c556cb96/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineForkchoiceUpdatedV1Test.java#L469
[besu-already-present]: https://github.com/besu-eth/besu/blob/d0d649bb3de87ad150b7c05d1c3e7ad1c556cb96/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineNewPayloadV1Test.java#L246
[besu-repeat-invalid]: https://github.com/besu-eth/besu/blob/d0d649bb3de87ad150b7c05d1c3e7ad1c556cb96/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineNewPayloadV1Test.java#L222
[besu-no-finalized]: https://github.com/besu-eth/besu/blob/d0d649bb3de87ad150b7c05d1c3e7ad1c556cb96/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineForkchoiceUpdatedV1Test.java#L664
[besu-below-finalized]: https://github.com/besu-eth/besu/blob/d0d649bb3de87ad150b7c05d1c3e7ad1c556cb96/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineForkchoiceUpdatedV1Test.java#L600
[besu-above-finalized]: https://github.com/besu-eth/besu/blob/d0d649bb3de87ad150b7c05d1c3e7ad1c556cb96/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineForkchoiceUpdatedV1Test.java#L644
[besu-bad-parent]: https://github.com/besu-eth/besu/blob/d0d649bb3de87ad150b7c05d1c3e7ad1c556cb96/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineNewPayloadV1Test.java#L428
[besu-bad-head]: https://github.com/besu-eth/besu/blob/d0d649bb3de87ad150b7c05d1c3e7ad1c556cb96/ethereum/api/src/test/java/org/hyperledger/besu/ethereum/api/jsonrpc/internal/methods/engine/EngineForkchoiceUpdatedV1Test.java#L282
[besu-pool]: https://github.com/besu-eth/besu/blob/d0d649bb3de87ad150b7c05d1c3e7ad1c556cb96/ethereum/eth/src/test/java/org/hyperledger/besu/ethereum/eth/transactions/AbstractTransactionPoolTest.java#L202
[nm-shorter]: https://github.com/NethermindEth/nethermind/blob/e735e6edfeed57de898c898f0b517fbd627f3a21/src/Nethermind/Nethermind.Blockchain.Test/BlockchainProcessorTests.cs#L1186
[nm-equal]: https://github.com/NethermindEth/nethermind/blob/e735e6edfeed57de898c898f0b517fbd627f3a21/src/Nethermind/Nethermind.Blockchain.Test/BlockchainProcessorTests.cs#L1177
[nm-longer]: https://github.com/NethermindEth/nethermind/blob/e735e6edfeed57de898c898f0b517fbd627f3a21/src/Nethermind/Nethermind.Blockchain.Test/BlockchainProcessorTests.cs#L1166
[nm-bounce]: https://github.com/NethermindEth/nethermind/blob/e735e6edfeed57de898c898f0b517fbd627f3a21/src/Nethermind/Nethermind.Blockchain.Test/BlockchainProcessorTests.cs#L1155
[nm-inconsistent]: https://github.com/NethermindEth/nethermind/blob/e735e6edfeed57de898c898f0b517fbd627f3a21/src/Nethermind/Nethermind.Merge.Plugin.Test/EngineModuleTests.V1.cs#L2488
[nm-finalized]: https://github.com/NethermindEth/nethermind/blob/e735e6edfeed57de898c898f0b517fbd627f3a21/src/Nethermind/Nethermind.Merge.Plugin.Test/EngineModuleTests.V1.cs#L642
[nm-safe]: https://github.com/NethermindEth/nethermind/blob/e735e6edfeed57de898c898f0b517fbd627f3a21/src/Nethermind/Nethermind.Merge.Plugin.Test/EngineModuleTests.V1.cs#L766
[nm-all-equal]: https://github.com/NethermindEth/nethermind/blob/e735e6edfeed57de898c898f0b517fbd627f3a21/src/Nethermind/Nethermind.Merge.Plugin.Test/EngineModuleTests.V1.cs#L1317
[nm-before-fcu]: https://github.com/NethermindEth/nethermind/blob/e735e6edfeed57de898c898f0b517fbd627f3a21/src/Nethermind/Nethermind.Merge.Plugin.Test/EngineModuleTests.V1.cs#L274
[nm-after-reorg]: https://github.com/NethermindEth/nethermind/blob/e735e6edfeed57de898c898f0b517fbd627f3a21/src/Nethermind/Nethermind.Merge.Plugin.Test/EngineModuleTests.V1.cs#L292
[nm-shortcut]: https://github.com/NethermindEth/nethermind/blob/e735e6edfeed57de898c898f0b517fbd627f3a21/src/Nethermind/Nethermind.Merge.Plugin.Test/EngineModuleTests.V1.cs#L2742
[nm-finalized-regression]: https://github.com/NethermindEth/nethermind/blob/e735e6edfeed57de898c898f0b517fbd627f3a21/src/Nethermind/Nethermind.Merge.Plugin.Test/EngineModuleTests.V1.cs#L2921
[ethrex-depth]: https://github.com/lambdaclass/ethrex/blob/fea1cd20f23dbf1016eec4602b9345fd904c9643/test/tests/blockchain/smoke_tests.rs#L463
