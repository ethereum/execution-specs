# EIP-8037 Remaining Ported Static Test Failures

## Summary

- **Total remaining failures**: 399
- **Already fixed**: 234 tests across 144 files (gas limit bump)
- **Fork**: Amsterdam only

## Failure Categories

### storage_mismatch (370 failures)
**Reason**: Storage value mismatch — tx likely OOG due to state gas

**tests/ported_static/stSStoreTest** (112)
- `test_sstore_0to0.py`: 16f729f2, 226eb68e, 2fe12241, 6fe387c0, b9c1a9f0
- `test_sstore_0to0to0.py`: 336e39a2, 3c82d3b7, 8a3c969b, 8cd562b8, a622b494
- `test_sstore_0to0to_x.py`: 044fc66e, 54a91dba, 6c9928a6, ec6438b3, f1e5a712
- `test_sstore_0to_x.py`: 34509729, 9f186c81, bc93a6b3, e9b71917, f49ba552
- `test_sstore_0to_xto0.py`: 41a342c0, 6a03fd1b, a1524a6b, a2268ce6, c4d4ffd0
- `test_sstore_0to_xto0to_x.py`: 0af840a9, 57bd35ab, 99a4e620, ad777ea4, e0dc90fa
- `test_sstore_0to_xto_x.py`: 0504675a, 5fea7b2e, adf1bdc5, ae8e4b20, d7fea5d2
- `test_sstore_0to_xto_y.py`: 063b765a, 5da1f038, a3959e37, b2dd41c6, ef89f9a2
- `test_sstore_gas.py`: 9c5d4cd4
- `test_sstore_gas_left.py`: 465de9b5
- `test_sstore_xto0.py`: 1747fb60, 75a870a1, 9891dc8a, abff3515, fea793b4
- `test_sstore_xto0to0.py`: 0226bb1c, 20f63659, 59b28db4, 933aebbe, adfe4044
- `test_sstore_xto0to_x.py`: 11c83514, 3b62582c, 8b07f517, bf4761c8, dd1b2151
- `test_sstore_xto0to_xto0.py`: 46f6a34d, 71291325, 830c70dc, cdef1718, d829d999
- `test_sstore_xto0to_y.py`: 2703e860, 455fddc1, 7dccd537, 9f6061fc, f999854a
- `test_sstore_xto_x.py`: 378268bc, 46917f15, 58a786e4, 9fcfd37c, e9b7b6ee
- `test_sstore_xto_xto0.py`: 6da4e364, 93aa9a3f, 95070c20, cf916c60, dc90915a
- `test_sstore_xto_xto_x.py`: 02cd04d1, 22bcd3b8, 7648b006, 962e3a37, fdb8a607
- `test_sstore_xto_xto_y.py`: 614797fa, 658b12c6, 7afa70e8, a5759e8f, dc8836cd
- `test_sstore_xto_y.py`: 30f3e384, 541c93d6, 8be3d461, ce69d902, df934aef
- `test_sstore_xto_yto0.py`: 4c2d4720, b19716cf, d8451218, e14f3b6b, f0514656
- `test_sstore_xto_yto_x.py`: 72255d4f, 9a3d0021, befe2c41, c3f3a3d7, e50d3c95
- `test_sstore_xto_yto_y.py`: 49a49610, 5cd2cce1, 7903fbe6, 9d5459db, edb78bc8
- `test_sstore_xto_yto_z.py`: 422c6766, 5bba7dc2, 70adb3dc, be18761d, c6b8ce32

**tests/ported_static/stEIP2930** (67)
- `test_manual_create.py`: 170c939d, 7a044da7, ebb870a2
- `test_storage_costs.py`: 36 cases
- `test_varied_context.py`: 28 cases

**tests/ported_static/stPreCompiledContracts** (29)
- `test_precomps_eip2929_cancun.py`: 29 cases

**tests/ported_static/stEIP150singleCodeGasPrices** (28)
- `test_gas_cost.py`: c90b375a
- `test_gas_cost_berlin.py`: 1d09d788
- `test_raw_call_code_gas.py`: eceb96d5
- `test_raw_call_code_gas_ask.py`: 30dde1ed
- `test_raw_call_code_gas_memory.py`: c5038321
- `test_raw_call_code_gas_memory_ask.py`: 002445ef
- `test_raw_call_code_gas_value_transfer.py`: 09184f51
- `test_raw_call_code_gas_value_transfer_ask.py`: df04edf0
- `test_raw_call_code_gas_value_transfer_memory.py`: a5ef6bd6
- `test_raw_call_code_gas_value_transfer_memory_ask.py`: bec8e5a1
- `test_raw_call_gas.py`: 8a25cd0b
- `test_raw_call_gas_ask.py`: 497ed502
- `test_raw_call_gas_value_transfer.py`: 11e1b9ee
- `test_raw_call_gas_value_transfer_ask.py`: 352ebf2a
- `test_raw_call_gas_value_transfer_memory.py`: c557c746
- `test_raw_call_gas_value_transfer_memory_ask.py`: 7f57953e
- `test_raw_call_memory_gas.py`: dc09daf9
- `test_raw_call_memory_gas_ask.py`: b2e6c6ed
- `test_raw_create_fail_gas_value_transfer.py`: 43716741
- `test_raw_create_fail_gas_value_transfer2.py`: 91815fd3
- `test_raw_create_gas.py`: 4e5c6260
- `test_raw_create_gas_memory.py`: aece01cc
- `test_raw_create_gas_value_transfer.py`: d69bb321
- `test_raw_create_gas_value_transfer_memory.py`: 107d69ae
- `test_raw_delegate_call_gas.py`: d976b326
- `test_raw_delegate_call_gas_ask.py`: c1fb0f0d
- `test_raw_delegate_call_gas_memory.py`: 2c8c2c0b
- `test_raw_delegate_call_gas_memory_ask.py`: cfe8d89f

**tests/ported_static/stCreateTest** (27)
- `test_create_address_warm_after_fail.py`: 16 cases
- `test_create_collision_to_empty2.py`: 1913d83b, 7bb1711e
- `test_create_e_contract_then_call_to_non_existent_acc.py`: bfca199f
- `test_create_empty_contract.py`: 22d4e92a
- `test_create_empty_contract_and_call_it_0wei.py`: c9dae64e
- `test_create_empty_contract_and_call_it_1wei.py`: d00d38b6
- `test_create_empty_contract_with_balance.py`: b1b1ceed
- `test_create_empty_contract_with_storage.py`: 007456c7
- `test_create_empty_contract_with_storage_and_call_it_0wei.py`: 49aed756
- `test_create_empty_contract_with_storage_and_call_it_1wei.py`: 2d7e9310
- `test_create_oo_gafter_init_code_revert2.py`: fa16c416

**tests/ported_static/stCallCodes** (17)
- `test_callcall_00.py`: 1122a53c
- `test_callcallcall_000.py`: 31fecf10
- `test_callcallcallcode_001.py`: f8ef548f
- `test_callcallcode_01.py`: 545f7573
- `test_callcallcodecall_010.py`: a2fa3120
- `test_callcallcodecallcode_011.py`: a202ce87
- `test_callcode_dynamic_code.py`: 11b286b2, 4aed2e32, c05bc371, ed6b4ae8
- `test_callcode_dynamic_code2_self_call.py`: 0801f0f5
- `test_callcodecall_10.py`: 24a10341
- `test_callcodecallcall_100.py`: 79a23bcb
- `test_callcodecallcallcode_101.py`: 2457c69e
- `test_callcodecallcode_11.py`: f1b609ce
- `test_callcodecallcodecall_110.py`: 5c62d8ad
- `test_callcodecallcodecallcode_111.py`: 9ad44c97

**tests/ported_static/stCreate2** (12)
- `test_create2_contract_suicide_during_init_then_store_then_return.py`: 1acee5e8
- `test_create2_first_byte_loop.py`: e200af59
- `test_create2_oo_gafter_init_code_returndata2.py`: 1e40bb21
- `test_create2_oo_gafter_init_code_revert2.py`: 3662c27b
- `test_revert_depth_create2_oog.py`: 0ca6c6f1, 5d942957
- `test_revert_depth_create2_oog_berlin.py`: 873e680d, a6af381e
- `test_revert_depth_create_address_collision.py`: 4b19d06d, 4b573bf3
- `test_revert_depth_create_address_collision_berlin.py`: 262af7ad, a18ca95d

**tests/ported_static/stCallDelegateCodesCallCodeHomestead** (11)
- `test_callcallcallcode_001.py`: 91e98b4d
- `test_callcallcode_01.py`: 1937d7e4
- `test_callcallcodecall_010.py`: f0577458
- `test_callcallcodecallcode_011.py`: d47c3061
- `test_callcodecall_10.py`: a786ae81
- `test_callcodecallcall_100.py`: 2c3bd191
- `test_callcodecallcallcode_101.py`: 95135564
- `test_callcodecallcode_11.py`: 8b011c9a
- `test_callcodecallcodecall_110.py`: ae0d7a3e
- `test_callcodecallcodecallcode_111.py`: 91480d7c
- `test_callcodecallcodecallcode_111_suicide_end.py`: 1429fedd

**tests/ported_static/stCallDelegateCodesHomestead** (10)
- `test_callcallcallcode_001.py`: 3973adb5
- `test_callcallcode_01.py`: 64225621
- `test_callcallcodecall_010.py`: 27491e51
- `test_callcallcodecallcode_011.py`: bc3c3b63
- `test_callcodecall_10.py`: 149b4fc5
- `test_callcodecallcall_100.py`: 4e03be74
- `test_callcodecallcallcode_101.py`: 253ba3cd
- `test_callcodecallcode_11.py`: 97cfc275
- `test_callcodecallcodecall_110.py`: 7b486908
- `test_callcodecallcodecallcode_111.py`: 6edbc658

**tests/ported_static/stNonZeroCallsTest** (10)
- `test_non_zero_value_call.py`: 980e895c
- `test_non_zero_value_call_to_empty_paris.py`: a3dc7607
- `test_non_zero_value_call_to_one_storage_key_paris.py`: 7e870f5f
- `test_non_zero_value_callcode.py`: 260a823b
- `test_non_zero_value_callcode_to_empty_paris.py`: 689f09b6
- `test_non_zero_value_callcode_to_one_storage_key_paris.py`: 893d4ada
- `test_non_zero_value_delegatecall.py`: a6513ec7
- `test_non_zero_value_delegatecall_to_empty_paris.py`: 5259eeaf
- `test_non_zero_value_delegatecall_to_non_non_zero_balance.py`: 131e241b
- `test_non_zero_value_delegatecall_to_one_storage_key_paris.py`: 8be9f26f

**tests/ported_static/stEIP150Specific** (7)
- `test_call_ask_more_gas_on_depth2_then_transaction_has.py`: 06e32dab
- `test_create_and_gas_inside_create.py`: 99fd6cbe
- `test_delegate_call_on_eip.py`: 9dbacd77
- `test_new_gas_price_for_codes.py`: 87319bd8
- `test_transaction64_rule_d64e0.py`: bd9f404b
- `test_transaction64_rule_d64m1.py`: f99420c8
- `test_transaction64_rule_d64p1.py`: e6a65889

**tests/ported_static/stCallCreateCallCodeTest** (6)
- `test_call1024_oog.py`: 053e0685, 62477118, 624940e3, c0b57c1f
- `test_callcode1024_oog.py`: 0d05b21e, 41a7ea43

**tests/ported_static/Shanghai** (4)
- `test_create2_init_code_size_limit.py`: c03cd68f
- `test_create_init_code_size_limit.py`: cf48697f
- `test_push0.py`: 1bd801d9
- `test_push0_gas.py`: feb40869

**tests/ported_static/stBadOpcode** (4)
- `test_measure_gas.py`: dd2cf580, eeb4d196
- `test_operation_diff_gas.py`: 4f2491de, 9c351c5f

**tests/ported_static/stEIP1559** (4)
- `test_sender_balance.py`: 0faa3f60
- `test_val_causes_oof.py`: 5558b1f8, 87fe7935, e5eaee72

**tests/ported_static/stRefundTest** (4)
- `test_refund50_2.py`: 714e3f64
- `test_refund50percent_cap.py`: d59d5864
- `test_refund_suicide50procent_cap.py`: 0244fbc3, 4507ffd9

**tests/ported_static/stDelegatecallTestHomestead** (3)
- `test_call1024_oog.py`: 2f7d41b8, 512c0be9
- `test_delegatecall1024_oog.py`: 9632f3a4

**tests/ported_static/stMemExpandingEIP150Calls** (3)
- `test_call_ask_more_gas_on_depth2_then_transaction_has_with_mem_expanding_calls.py`: 9d82e0c4
- `test_create_and_gas_inside_create_with_mem_expanding_calls.py`: 8bd930f3
- `test_new_gas_price_for_codes_with_mem_expanding_calls.py`: 8aae89a0

**tests/ported_static/stCodeSizeLimit** (2)
- `test_create2_code_size_limit.py`: 3e24101b
- `test_create_code_size_limit.py`: 0ea991f4

**tests/ported_static/stRevertTest** (2)
- `test_revert_depth_create_oog.py`: 19554ddf, 728b9381

**tests/ported_static/stSystemOperationsTest** (2)
- `test_ab_acalls3.py`: 2838dee8
- `test_call_recursive_bomb3.py`: 876df445

**tests/ported_static/VMTests** (1)
- `test_two_ops.py`: 32b0e7e0

**tests/ported_static/stEIP158Specific** (1)
- `test_exp_empty.py`: bdec7470

**tests/ported_static/stExtCodeHash** (1)
- `test_ext_code_hash_created_and_deleted_account_recheck_in_outer_call.py`: a9ea5f1b

**tests/ported_static/stHomesteadSpecific** (1)
- `test_contract_creation_oo_gdont_leave_empty_contract.py`: 20ba0c5c

**tests/ported_static/stPreCompiledContracts2** (1)
- `test_ecrecover_short_buff.py`: 7e06c8c9

**tests/ported_static/stTransactionTest** (1)
- `test_internal_call_hitting_gas_limit_success.py`: 0177cba0

### other (21 failures)
**Reason**: Unknown error

**tests/ported_static/stSStoreTest** (10)
- `test_sstore_0to_xto0to_x.py`: cb258b9a
- `test_sstore_gas_left.py`: 6 cases
- `test_sstore_xto0to_x.py`: 87a0a25d
- `test_sstore_xto0to_xto0.py`: a9b96083
- `test_sstore_xto0to_y.py`: a70473dd

**tests/ported_static/stWalletTest** (8)
- `test_day_limit_construction.py`: 609cebc5, cdb3a533
- `test_day_limit_construction_partial.py`: 714a6277
- `test_multi_owned_construction_not_enough_gas_partial.py`: a43ade0e
- `test_wallet_construction.py`: 3339c79d, 38673f4a
- `test_wallet_construction_oog.py`: 463ef689
- `test_wallet_construction_partial.py`: 6f1a4df8

**tests/ported_static/stCreate2** (1)
- `test_create_message_reverted.py`: 4125712b

**tests/ported_static/stInitCodeTest** (1)
- `test_call_recursive_contract.py`: 0ebf8806

**tests/ported_static/stTransactionTest** (1)
- `test_store_gas_on_create.py`: fb2730e4

### unexpected_tx_fail (8 failures)
**Reason**: Transaction unexpectedly failed

**tests/ported_static/stCallCreateCallCodeTest** (2)
- `test_contract_creation_make_call_that_ask_more_gas_then_transaction_provided.py`: 32a0c035, e3935f95

**tests/ported_static/stCreate2** (2)
- `test_create_message_reverted_oog_in_init2.py`: 0a58953b, d5f7f2a7

**tests/ported_static/stHomesteadSpecific** (2)
- `test_contract_creation_oo_gdont_leave_empty_contract_via_transaction.py`: 88fe9bb6
- `test_create_contract_via_transaction_cost53000.py`: df5c8b47

**tests/ported_static/stInitCodeTest** (2)
- `test_transaction_create_auto_suicide_contract.py`: 48183752
- `test_transaction_create_stop_in_initcode.py`: f60e36a2
