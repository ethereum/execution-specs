# EIP-8037 Ported Static Test Failures

## Summary

- **Total failures**: 623
- **Affected suites**: 41
- **Fork**: Amsterdam only (passes at Osaka)
- **Root cause**: EIP-8037 adds state gas costs (SSTORE, CREATE, code deposit, new account)
  that increase total gas consumption. Ported static tests have hardcoded gas limits
  that were sufficient pre-EIP-8037 but now cause OOG.

## Error Categories

- **Storage mismatch (likely OOG from state gas)**: 543
- **Transaction exception mismatch**: 41
- **Other**: 39

## Failures by Suite

### tests/ported_static/stSStoreTest (131 failures)

**test_sstore_0to0.py**
- `test_sstore_0to0[case0`
- `test_sstore_0to0[case2`
- `test_sstore_0to0[case4`
- `test_sstore_0to0[case6`
- `test_sstore_0to0[case8`

**test_sstore_0to0to0.py**
- `test_sstore_0to0to0[case0`
- `test_sstore_0to0to0[case2`
- `test_sstore_0to0to0[case4`
- `test_sstore_0to0to0[case6`
- `test_sstore_0to0to0[case8`

**test_sstore_0to0to_x.py**
- `test_sstore_0to0to_x[case0`
- `test_sstore_0to0to_x[case2`
- `test_sstore_0to0to_x[case4`
- `test_sstore_0to0to_x[case6`
- `test_sstore_0to0to_x[case8`

**test_sstore_0to_x.py**
- `test_sstore_0to_x[case0`
- `test_sstore_0to_x[case2`
- `test_sstore_0to_x[case4`
- `test_sstore_0to_x[case6`
- `test_sstore_0to_x[case8`

**test_sstore_0to_xto0.py**
- `test_sstore_0to_xto0[case0`
- `test_sstore_0to_xto0[case2`
- `test_sstore_0to_xto0[case4`
- `test_sstore_0to_xto0[case6`
- `test_sstore_0to_xto0[case8`

**test_sstore_0to_xto0to_x.py**
- `test_sstore_0to_xto0to_x[case0`
- `test_sstore_0to_xto0to_x[case2`
- `test_sstore_0to_xto0to_x[case4`
- `test_sstore_0to_xto0to_x[case6`
- `test_sstore_0to_xto0to_x[case8`
- `test_sstore_0to_xto0to_x[case9`

**test_sstore_0to_xto_x.py**
- `test_sstore_0to_xto_x[case0`
- `test_sstore_0to_xto_x[case2`
- `test_sstore_0to_xto_x[case4`
- `test_sstore_0to_xto_x[case6`
- `test_sstore_0to_xto_x[case8`

**test_sstore_0to_xto_y.py**
- `test_sstore_0to_xto_y[case0`
- `test_sstore_0to_xto_y[case2`
- `test_sstore_0to_xto_y[case4`
- `test_sstore_0to_xto_y[case6`
- `test_sstore_0to_xto_y[case8`

**test_sstore_change_from_external_call_in_init_code.py**
- `test_sstore_change_from_external_call_in_init_code[case0`
- `test_sstore_change_from_external_call_in_init_code[case10`
- `test_sstore_change_from_external_call_in_init_code[case11`
- `test_sstore_change_from_external_call_in_init_code[case13`
- `test_sstore_change_from_external_call_in_init_code[case14`
- `test_sstore_change_from_external_call_in_init_code[case15`
- `test_sstore_change_from_external_call_in_init_code[case2`
- `test_sstore_change_from_external_call_in_init_code[case7`
- `test_sstore_change_from_external_call_in_init_code[case9`

**test_sstore_gas.py**
- `test_sstore_gas[fork_Amsterdam-blockchain_test_from_state_test`

**test_sstore_gas_left.py**
- `test_sstore_gas_left[case2`
- `test_sstore_gas_left[case3`
- `test_sstore_gas_left[case4`
- `test_sstore_gas_left[case5`
- `test_sstore_gas_left[case6`
- `test_sstore_gas_left[case7`
- `test_sstore_gas_left[case8`

**test_sstore_xto0.py**
- `test_sstore_xto0[case0`
- `test_sstore_xto0[case2`
- `test_sstore_xto0[case4`
- `test_sstore_xto0[case6`
- `test_sstore_xto0[case8`

**test_sstore_xto0to0.py**
- `test_sstore_xto0to0[case0`
- `test_sstore_xto0to0[case2`
- `test_sstore_xto0to0[case4`
- `test_sstore_xto0to0[case6`
- `test_sstore_xto0to0[case8`

**test_sstore_xto0to_x.py**
- `test_sstore_xto0to_x[case0`
- `test_sstore_xto0to_x[case2`
- `test_sstore_xto0to_x[case4`
- `test_sstore_xto0to_x[case6`
- `test_sstore_xto0to_x[case8`
- `test_sstore_xto0to_x[case9`

**test_sstore_xto0to_xto0.py**
- `test_sstore_xto0to_xto0[case0`
- `test_sstore_xto0to_xto0[case2`
- `test_sstore_xto0to_xto0[case4`
- `test_sstore_xto0to_xto0[case6`
- `test_sstore_xto0to_xto0[case8`
- `test_sstore_xto0to_xto0[case9`

**test_sstore_xto0to_y.py**
- `test_sstore_xto0to_y[case0`
- `test_sstore_xto0to_y[case2`
- `test_sstore_xto0to_y[case4`
- `test_sstore_xto0to_y[case6`
- `test_sstore_xto0to_y[case8`
- `test_sstore_xto0to_y[case9`

**test_sstore_xto_x.py**
- `test_sstore_xto_x[case0`
- `test_sstore_xto_x[case2`
- `test_sstore_xto_x[case4`
- `test_sstore_xto_x[case6`
- `test_sstore_xto_x[case8`

**test_sstore_xto_xto0.py**
- `test_sstore_xto_xto0[case0`
- `test_sstore_xto_xto0[case2`
- `test_sstore_xto_xto0[case4`
- `test_sstore_xto_xto0[case6`
- `test_sstore_xto_xto0[case8`

**test_sstore_xto_xto_x.py**
- `test_sstore_xto_xto_x[case0`
- `test_sstore_xto_xto_x[case2`
- `test_sstore_xto_xto_x[case4`
- `test_sstore_xto_xto_x[case6`
- `test_sstore_xto_xto_x[case8`

**test_sstore_xto_xto_y.py**
- `test_sstore_xto_xto_y[case0`
- `test_sstore_xto_xto_y[case2`
- `test_sstore_xto_xto_y[case4`
- `test_sstore_xto_xto_y[case6`
- `test_sstore_xto_xto_y[case8`

**test_sstore_xto_y.py**
- `test_sstore_xto_y[case0`
- `test_sstore_xto_y[case2`
- `test_sstore_xto_y[case4`
- `test_sstore_xto_y[case6`
- `test_sstore_xto_y[case8`

**test_sstore_xto_yto0.py**
- `test_sstore_xto_yto0[case0`
- `test_sstore_xto_yto0[case2`
- `test_sstore_xto_yto0[case4`
- `test_sstore_xto_yto0[case6`
- `test_sstore_xto_yto0[case8`

**test_sstore_xto_yto_x.py**
- `test_sstore_xto_yto_x[case0`
- `test_sstore_xto_yto_x[case2`
- `test_sstore_xto_yto_x[case4`
- `test_sstore_xto_yto_x[case6`
- `test_sstore_xto_yto_x[case8`

**test_sstore_xto_yto_y.py**
- `test_sstore_xto_yto_y[case0`
- `test_sstore_xto_yto_y[case2`
- `test_sstore_xto_yto_y[case4`
- `test_sstore_xto_yto_y[case6`
- `test_sstore_xto_yto_y[case8`

**test_sstore_xto_yto_z.py**
- `test_sstore_xto_yto_z[case0`
- `test_sstore_xto_yto_z[case2`
- `test_sstore_xto_yto_z[case4`
- `test_sstore_xto_yto_z[case6`
- `test_sstore_xto_yto_z[case8`

### tests/ported_static/stEIP2930 (67 failures)

**test_manual_create.py**
- `test_manual_create[case0`
- `test_manual_create[case1`
- `test_manual_create[case2`

**test_storage_costs.py**
- `test_storage_costs[case0`
- `test_storage_costs[case10`
- `test_storage_costs[case11`
- `test_storage_costs[case12`
- `test_storage_costs[case13`
- `test_storage_costs[case14`
- `test_storage_costs[case15`
- `test_storage_costs[case16`
- `test_storage_costs[case17`
- `test_storage_costs[case18`
- `test_storage_costs[case19`
- `test_storage_costs[case1`
- `test_storage_costs[case20`
- `test_storage_costs[case21`
- `test_storage_costs[case22`
- `test_storage_costs[case23`
- `test_storage_costs[case24`
- `test_storage_costs[case25`
- `test_storage_costs[case26`
- `test_storage_costs[case27`
- `test_storage_costs[case28`
- `test_storage_costs[case29`
- `test_storage_costs[case2`
- `test_storage_costs[case30`
- `test_storage_costs[case31`
- `test_storage_costs[case32`
- `test_storage_costs[case33`
- `test_storage_costs[case34`
- `test_storage_costs[case35`
- `test_storage_costs[case3`
- `test_storage_costs[case4`
- `test_storage_costs[case5`
- `test_storage_costs[case6`
- `test_storage_costs[case7`
- `test_storage_costs[case8`
- `test_storage_costs[case9`

**test_varied_context.py**
- `test_varied_context[case0`
- `test_varied_context[case10`
- `test_varied_context[case11`
- `test_varied_context[case12`
- `test_varied_context[case13`
- `test_varied_context[case14`
- `test_varied_context[case15`
- `test_varied_context[case16`
- `test_varied_context[case17`
- `test_varied_context[case18`
- `test_varied_context[case19`
- `test_varied_context[case1`
- `test_varied_context[case20`
- `test_varied_context[case21`
- `test_varied_context[case22`
- `test_varied_context[case23`
- `test_varied_context[case24`
- `test_varied_context[case25`
- `test_varied_context[case28`
- `test_varied_context[case29`
- `test_varied_context[case2`
- `test_varied_context[case3`
- `test_varied_context[case4`
- `test_varied_context[case5`
- `test_varied_context[case6`
- `test_varied_context[case7`
- `test_varied_context[case8`
- `test_varied_context[case9`

### tests/ported_static/stCreateTest (44 failures)

**test_create2_call_data.py**
- `test_create2_call_data[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_address_warm_after_fail.py**
- `test_create_address_warm_after_fail[case11`
- `test_create_address_warm_after_fail[case13`
- `test_create_address_warm_after_fail[case15`
- `test_create_address_warm_after_fail[case17`
- `test_create_address_warm_after_fail[case19`
- `test_create_address_warm_after_fail[case1`
- `test_create_address_warm_after_fail[case21`
- `test_create_address_warm_after_fail[case23`
- `test_create_address_warm_after_fail[case25`
- `test_create_address_warm_after_fail[case27`
- `test_create_address_warm_after_fail[case29`
- `test_create_address_warm_after_fail[case3`
- `test_create_address_warm_after_fail[case5`
- `test_create_address_warm_after_fail[case6`
- `test_create_address_warm_after_fail[case7`
- `test_create_address_warm_after_fail[case9`

**test_create_collision_to_empty2.py**
- `test_create_collision_to_empty2[case0`
- `test_create_collision_to_empty2[case1`

**test_create_contract_sstore_during_init.py**
- `test_create_contract_sstore_during_init[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_e_contract_create_ne_contract_in_init_oog_tr.py**
- `test_create_e_contract_create_ne_contract_in_init_oog_tr[case0`
- `test_create_e_contract_create_ne_contract_in_init_oog_tr[case1`

**test_create_e_contract_then_call_to_non_existent_acc.py**
- `test_create_e_contract_then_call_to_non_existent_acc[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_empty_contract.py**
- `test_create_empty_contract[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_empty_contract_and_call_it_0wei.py**
- `test_create_empty_contract_and_call_it_0wei[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_empty_contract_and_call_it_1wei.py**
- `test_create_empty_contract_and_call_it_1wei[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_empty_contract_with_balance.py**
- `test_create_empty_contract_with_balance[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_empty_contract_with_storage.py**
- `test_create_empty_contract_with_storage[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_empty_contract_with_storage_and_call_it_0wei.py**
- `test_create_empty_contract_with_storage_and_call_it_0wei[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_empty_contract_with_storage_and_call_it_1wei.py**
- `test_create_empty_contract_with_storage_and_call_it_1wei[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_oo_gafter_init_code_returndata2.py**
- `test_create_oo_gafter_init_code_returndata2[case1`

**test_create_oo_gafter_init_code_revert2.py**
- `test_create_oo_gafter_init_code_revert2[case0`

**test_create_transaction_call_data.py**
- `test_create_transaction_call_data[case0`
- `test_create_transaction_call_data[case1`
- `test_create_transaction_call_data[case2`

**test_create_transaction_high_nonce.py**
- `test_create_transaction_high_nonce[case0`
- `test_create_transaction_high_nonce[case1`

**test_create_transaction_refund_ef.py**
- `test_create_transaction_refund_ef[fork_Amsterdam-blockchain_test_from_state_test`

**test_transaction_collision_to_empty2.py**
- `test_transaction_collision_to_empty2[case2`
- `test_transaction_collision_to_empty2[case3`

**test_transaction_collision_to_empty_but_code.py**
- `test_transaction_collision_to_empty_but_code[case2`
- `test_transaction_collision_to_empty_but_code[case3`

**test_transaction_collision_to_empty_but_nonce.py**
- `test_transaction_collision_to_empty_but_nonce[case2`
- `test_transaction_collision_to_empty_but_nonce[case3`

### tests/ported_static/stZeroKnowledge (36 failures)

**test_point_add.py**
- `test_point_add[case13`
- `test_point_add[case14`
- `test_point_add[case17`
- `test_point_add[case18`
- `test_point_add[case1`
- `test_point_add[case29`
- `test_point_add[case30`
- `test_point_add[case33`
- `test_point_add[case34`
- `test_point_add[case37`
- `test_point_add[case38`

**test_point_add_trunc.py**
- `test_point_add_trunc[case13`
- `test_point_add_trunc[case1`
- `test_point_add_trunc[case29`
- `test_point_add_trunc[case33`
- `test_point_add_trunc[case37`
- `test_point_add_trunc[case9`

**test_point_mul_add.py**
- `test_point_mul_add[case11`
- `test_point_mul_add[case31`
- `test_point_mul_add[case35`

**test_point_mul_add2.py**
- `test_point_mul_add2[case115`
- `test_point_mul_add2[case131`
- `test_point_mul_add2[case135`
- `test_point_mul_add2[case139`
- `test_point_mul_add2[case143`
- `test_point_mul_add2[case147`
- `test_point_mul_add2[case151`
- `test_point_mul_add2[case19`
- `test_point_mul_add2[case39`
- `test_point_mul_add2[case3`
- `test_point_mul_add2[case51`
- `test_point_mul_add2[case59`
- `test_point_mul_add2[case79`
- `test_point_mul_add2[case7`
- `test_point_mul_add2[case95`
- `test_point_mul_add2[case99`

### tests/ported_static/stPreCompiledContracts (29 failures)

**test_precomps_eip2929_cancun.py**
- `test_precomps_eip2929_cancun_from_osaka[case0`
- `test_precomps_eip2929_cancun_from_osaka[case1`
- `test_precomps_eip2929_cancun_from_osaka[case27`
- `test_precomps_eip2929_cancun_from_osaka[case28`
- `test_precomps_eip2929_cancun_from_osaka[case29`
- `test_precomps_eip2929_cancun_from_osaka[case2`
- `test_precomps_eip2929_cancun_from_osaka[case30`
- `test_precomps_eip2929_cancun_from_osaka[case31`
- `test_precomps_eip2929_cancun_from_osaka[case32`
- `test_precomps_eip2929_cancun_from_osaka[case33`
- `test_precomps_eip2929_cancun_from_osaka[case34`
- `test_precomps_eip2929_cancun_from_osaka[case35`
- `test_precomps_eip2929_cancun_from_osaka[case36`
- `test_precomps_eip2929_cancun_from_osaka[case37`
- `test_precomps_eip2929_cancun_from_osaka[case38`
- `test_precomps_eip2929_cancun_from_osaka[case39`
- `test_precomps_eip2929_cancun_from_osaka[case3`
- `test_precomps_eip2929_cancun_from_osaka[case40`
- `test_precomps_eip2929_cancun_from_osaka[case41`
- `test_precomps_eip2929_cancun_from_osaka[case42`
- `test_precomps_eip2929_cancun_from_osaka[case43`
- `test_precomps_eip2929_cancun_from_osaka[case44`
- `test_precomps_eip2929_cancun_from_osaka[case45`
- `test_precomps_eip2929_cancun_from_osaka[case46`
- `test_precomps_eip2929_cancun_from_osaka[case47`
- `test_precomps_eip2929_cancun_from_osaka[case48`
- `test_precomps_eip2929_cancun_from_osaka[case49`
- `test_precomps_eip2929_cancun_from_osaka[case4`
- `test_precomps_eip2929_cancun_from_osaka[case5`

### tests/ported_static/stEIP150singleCodeGasPrices (28 failures)

**test_gas_cost.py**
- `test_gas_cost[case44`

**test_gas_cost_berlin.py**
- `test_gas_cost_berlin[case44`

**test_raw_call_code_gas.py**
- `test_raw_call_code_gas[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_code_gas_ask.py**
- `test_raw_call_code_gas_ask[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_code_gas_memory.py**
- `test_raw_call_code_gas_memory[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_code_gas_memory_ask.py**
- `test_raw_call_code_gas_memory_ask[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_code_gas_value_transfer.py**
- `test_raw_call_code_gas_value_transfer[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_code_gas_value_transfer_ask.py**
- `test_raw_call_code_gas_value_transfer_ask[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_code_gas_value_transfer_memory.py**
- `test_raw_call_code_gas_value_transfer_memory[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_code_gas_value_transfer_memory_ask.py**
- `test_raw_call_code_gas_value_transfer_memory_ask[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_gas.py**
- `test_raw_call_gas[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_gas_ask.py**
- `test_raw_call_gas_ask[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_gas_value_transfer.py**
- `test_raw_call_gas_value_transfer[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_gas_value_transfer_ask.py**
- `test_raw_call_gas_value_transfer_ask[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_gas_value_transfer_memory.py**
- `test_raw_call_gas_value_transfer_memory[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_gas_value_transfer_memory_ask.py**
- `test_raw_call_gas_value_transfer_memory_ask[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_memory_gas.py**
- `test_raw_call_memory_gas[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_call_memory_gas_ask.py**
- `test_raw_call_memory_gas_ask[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_create_fail_gas_value_transfer.py**
- `test_raw_create_fail_gas_value_transfer[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_create_fail_gas_value_transfer2.py**
- `test_raw_create_fail_gas_value_transfer2[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_create_gas.py**
- `test_raw_create_gas[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_create_gas_memory.py**
- `test_raw_create_gas_memory[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_create_gas_value_transfer.py**
- `test_raw_create_gas_value_transfer[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_create_gas_value_transfer_memory.py**
- `test_raw_create_gas_value_transfer_memory[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_delegate_call_gas.py**
- `test_raw_delegate_call_gas[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_delegate_call_gas_ask.py**
- `test_raw_delegate_call_gas_ask[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_delegate_call_gas_memory.py**
- `test_raw_delegate_call_gas_memory[fork_Amsterdam-blockchain_test_from_state_test`

**test_raw_delegate_call_gas_memory_ask.py**
- `test_raw_delegate_call_gas_memory_ask[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stCallCodes (25 failures)

**test_callcall_00.py**
- `test_callcall_00[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcall_000.py**
- `test_callcallcall_000[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcall_abcb_recursive.py**
- `test_callcallcall_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcallcode_001.py**
- `test_callcallcallcode_001[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcallcode_abcb_recursive.py**
- `test_callcallcallcode_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcode_01.py**
- `test_callcallcode_01[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcodecall_010.py**
- `test_callcallcodecall_010[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcodecall_abcb_recursive.py**
- `test_callcallcodecall_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcodecallcode_011.py**
- `test_callcallcodecallcode_011[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcodecallcode_abcb_recursive.py**
- `test_callcallcodecallcode_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcode_dynamic_code.py**
- `test_callcode_dynamic_code[case0`
- `test_callcode_dynamic_code[case1`
- `test_callcode_dynamic_code[case2`
- `test_callcode_dynamic_code[case3`

**test_callcode_dynamic_code2_self_call.py**
- `test_callcode_dynamic_code2_self_call[case1`

**test_callcodecall_10.py**
- `test_callcodecall_10[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcall_100.py**
- `test_callcodecallcall_100[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcall_abcb_recursive.py**
- `test_callcodecallcall_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcallcode_101.py**
- `test_callcodecallcallcode_101[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcallcode_abcb_recursive.py**
- `test_callcodecallcallcode_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcode_11.py**
- `test_callcodecallcode_11[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcodecall_110.py**
- `test_callcodecallcodecall_110[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcodecall_abcb_recursive.py**
- `test_callcodecallcodecall_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcodecallcode_111.py**
- `test_callcodecallcodecallcode_111[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcodecallcode_abcb_recursive.py**
- `test_callcodecallcodecallcode_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/Cancun (23 failures)

**test_mcopy_copy_cost.py**
- `test_mcopy_copy_cost[case11`
- `test_mcopy_copy_cost[case13`
- `test_mcopy_copy_cost[case15`
- `test_mcopy_copy_cost[case17`
- `test_mcopy_copy_cost[case19`
- `test_mcopy_copy_cost[case1`
- `test_mcopy_copy_cost[case21`
- `test_mcopy_copy_cost[case23`
- `test_mcopy_copy_cost[case25`
- `test_mcopy_copy_cost[case33`
- `test_mcopy_copy_cost[case35`
- `test_mcopy_copy_cost[case37`
- `test_mcopy_copy_cost[case39`
- `test_mcopy_copy_cost[case3`
- `test_mcopy_copy_cost[case41`
- `test_mcopy_copy_cost[case49`
- `test_mcopy_copy_cost[case51`
- `test_mcopy_copy_cost[case53`
- `test_mcopy_copy_cost[case55`
- `test_mcopy_copy_cost[case57`
- `test_mcopy_copy_cost[case5`
- `test_mcopy_copy_cost[case7`
- `test_mcopy_copy_cost[case9`

### tests/ported_static/stCreate2 (22 failures)

**test_create2_contract_suicide_during_init_then_store_then_return.py**
- `test_create2_contract_suicide_during_init_then_store_then_return[fork_Amsterdam-blockchain_test_from_state_test`

**test_create2_first_byte_loop.py**
- `test_create2_first_byte_loop[case0`

**test_create2_oo_gafter_init_code_returndata2.py**
- `test_create2_oo_gafter_init_code_returndata2[case1`

**test_create2_oo_gafter_init_code_revert.py**
- `test_create2_oo_gafter_init_code_revert[fork_Amsterdam-blockchain_test_from_state_test`

**test_create2_oo_gafter_init_code_revert2.py**
- `test_create2_oo_gafter_init_code_revert2[fork_Amsterdam-blockchain_test_from_state_test`

**test_create2_smart_init_code.py**
- `test_create2_smart_init_code[case0`
- `test_create2_smart_init_code[case1`

**test_create_message_reverted.py**
- `test_create_message_reverted[case1`

**test_create_message_reverted_oog_in_init2.py**
- `test_create_message_reverted_oog_in_init2[case0`
- `test_create_message_reverted_oog_in_init2[case1`

**test_returndatacopy_0_0_following_successful_create.py**
- `test_returndatacopy_0_0_following_successful_create[fork_Amsterdam-blockchain_test_from_state_test`

**test_returndatacopy_after_failing_create.py**
- `test_returndatacopy_after_failing_create[fork_Amsterdam-blockchain_test_from_state_test`

**test_returndatacopy_following_revert_in_create.py**
- `test_returndatacopy_following_revert_in_create[fork_Amsterdam-blockchain_test_from_state_test`

**test_revert_depth_create2_oog.py**
- `test_revert_depth_create2_oog[case6`
- `test_revert_depth_create2_oog[case7`

**test_revert_depth_create2_oog_berlin.py**
- `test_revert_depth_create2_oog_berlin[case6`
- `test_revert_depth_create2_oog_berlin[case7`

**test_revert_depth_create_address_collision.py**
- `test_revert_depth_create_address_collision[case6`
- `test_revert_depth_create_address_collision[case7`

**test_revert_depth_create_address_collision_berlin.py**
- `test_revert_depth_create_address_collision_berlin[case6`
- `test_revert_depth_create_address_collision_berlin[case7`

**test_revert_opcode_in_create_returns_create2.py**
- `test_revert_opcode_in_create_returns_create2[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stMemoryTest (20 failures)

**test_mem32kb.py**
- `test_mem32kb[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem32kb_minus_1.py**
- `test_mem32kb_minus_1[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem32kb_minus_31.py**
- `test_mem32kb_minus_31[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem32kb_minus_32.py**
- `test_mem32kb_minus_32[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem32kb_minus_33.py**
- `test_mem32kb_minus_33[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem32kb_plus_1.py**
- `test_mem32kb_plus_1[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem32kb_plus_31.py**
- `test_mem32kb_plus_31[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem32kb_plus_32.py**
- `test_mem32kb_plus_32[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem32kb_plus_33.py**
- `test_mem32kb_plus_33[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem64kb.py**
- `test_mem64kb[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem64kb_minus_1.py**
- `test_mem64kb_minus_1[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem64kb_minus_31.py**
- `test_mem64kb_minus_31[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem64kb_minus_32.py**
- `test_mem64kb_minus_32[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem64kb_minus_33.py**
- `test_mem64kb_minus_33[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem64kb_plus_1.py**
- `test_mem64kb_plus_1[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem64kb_plus_31.py**
- `test_mem64kb_plus_31[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem64kb_plus_32.py**
- `test_mem64kb_plus_32[fork_Amsterdam-blockchain_test_from_state_test`

**test_mem64kb_plus_33.py**
- `test_mem64kb_plus_33[fork_Amsterdam-blockchain_test_from_state_test`

**test_oog.py**
- `test_oog[case26`
- `test_oog[case27`

### tests/ported_static/stCallDelegateCodesCallCodeHomestead (18 failures)

**test_callcallcallcode_001.py**
- `test_callcallcallcode_001[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcallcode_abcb_recursive.py**
- `test_callcallcallcode_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcode_01.py**
- `test_callcallcode_01[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcodecall_010.py**
- `test_callcallcodecall_010[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcodecall_abcb_recursive.py**
- `test_callcallcodecall_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcodecallcode_011.py**
- `test_callcallcodecallcode_011[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcodecallcode_abcb_recursive.py**
- `test_callcallcodecallcode_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecall_10.py**
- `test_callcodecall_10[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcall_100.py**
- `test_callcodecallcall_100[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcall_abcb_recursive.py**
- `test_callcodecallcall_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcallcode_101.py**
- `test_callcodecallcallcode_101[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcallcode_abcb_recursive.py**
- `test_callcodecallcallcode_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcode_11.py**
- `test_callcodecallcode_11[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcodecall_110.py**
- `test_callcodecallcodecall_110[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcodecall_abcb_recursive.py**
- `test_callcodecallcodecall_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcodecallcode_111.py**
- `test_callcodecallcodecallcode_111[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcodecallcode_111_suicide_end.py**
- `test_callcodecallcodecallcode_111_suicide_end[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcodecallcode_abcb_recursive.py**
- `test_callcodecallcodecallcode_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stRandom (18 failures)

**test_random_statetest164.py**
- `test_random_statetest164[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest17.py**
- `test_random_statetest17[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest236.py**
- `test_random_statetest236[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest237.py**
- `test_random_statetest237[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest245.py**
- `test_random_statetest245[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest270.py**
- `test_random_statetest270[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest291.py**
- `test_random_statetest291[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest293.py**
- `test_random_statetest293[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest31.py**
- `test_random_statetest31[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest337.py**
- `test_random_statetest337[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest338.py**
- `test_random_statetest338[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest343.py**
- `test_random_statetest343[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest349.py**
- `test_random_statetest349[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest371.py**
- `test_random_statetest371[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest39.py**
- `test_random_statetest39[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest43.py**
- `test_random_statetest43[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest64.py**
- `test_random_statetest64[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest98.py**
- `test_random_statetest98[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stCallDelegateCodesHomestead (17 failures)

**test_callcallcallcode_001.py**
- `test_callcallcallcode_001[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcallcode_abcb_recursive.py**
- `test_callcallcallcode_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcode_01.py**
- `test_callcallcode_01[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcodecall_010.py**
- `test_callcallcodecall_010[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcodecall_abcb_recursive.py**
- `test_callcallcodecall_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcodecallcode_011.py**
- `test_callcallcodecallcode_011[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcallcodecallcode_abcb_recursive.py**
- `test_callcallcodecallcode_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecall_10.py**
- `test_callcodecall_10[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcall_100.py**
- `test_callcodecallcall_100[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcall_abcb_recursive.py**
- `test_callcodecallcall_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcallcode_101.py**
- `test_callcodecallcallcode_101[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcallcode_abcb_recursive.py**
- `test_callcodecallcallcode_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcode_11.py**
- `test_callcodecallcode_11[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcodecall_110.py**
- `test_callcodecallcodecall_110[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcodecall_abcb_recursive.py**
- `test_callcodecallcodecall_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcodecallcode_111.py**
- `test_callcodecallcodecallcode_111[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcodecallcodecallcode_abcb_recursive.py**
- `test_callcodecallcodecallcode_abcb_recursive[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stInitCodeTest (17 failures)

**test_call_contract_to_create_contract_and_call_it_oog.py**
- `test_call_contract_to_create_contract_and_call_it_oog[fork_Amsterdam-blockchain_test_from_state_test`

**test_call_contract_to_create_contract_oog_bonus_gas.py**
- `test_call_contract_to_create_contract_oog_bonus_gas[fork_Amsterdam-blockchain_test_from_state_test`

**test_call_contract_to_create_contract_which_would_create_contract_if_called.py**
- `test_call_contract_to_create_contract_which_would_create_contract_if_called[fork_Amsterdam-blockchain_test_from_state_test`

**test_call_contract_to_create_contract_which_would_create_contract_in_init_code.py**
- `test_call_contract_to_create_contract_which_would_create_contract_in_init_code[fork_Amsterdam-blockchain_test_from_state_test`

**test_call_recursive_contract.py**
- `test_call_recursive_contract[fork_Amsterdam-blockchain_test_from_state_test`

**test_out_of_gas_contract_creation.py**
- `test_out_of_gas_contract_creation[case0`
- `test_out_of_gas_contract_creation[case1`
- `test_out_of_gas_contract_creation[case2`
- `test_out_of_gas_contract_creation[case3`

**test_out_of_gas_prefunded_contract_creation.py**
- `test_out_of_gas_prefunded_contract_creation[case0`
- `test_out_of_gas_prefunded_contract_creation[case1`
- `test_out_of_gas_prefunded_contract_creation[case2`

**test_stack_under_flow_contract_creation.py**
- `test_stack_under_flow_contract_creation[fork_Amsterdam-blockchain_test_from_state_test`

**test_transaction_create_auto_suicide_contract.py**
- `test_transaction_create_auto_suicide_contract[fork_Amsterdam-blockchain_test_from_state_test`

**test_transaction_create_random_init_code.py**
- `test_transaction_create_random_init_code[fork_Amsterdam-blockchain_test_from_state_test`

**test_transaction_create_stop_in_initcode.py**
- `test_transaction_create_stop_in_initcode[fork_Amsterdam-blockchain_test_from_state_test`

**test_transaction_create_suicide_in_initcode.py**
- `test_transaction_create_suicide_in_initcode[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stCallCreateCallCodeTest (14 failures)

**test_call1024_oog.py**
- `test_call1024_oog[case0`
- `test_call1024_oog[case1`
- `test_call1024_oog[case2`
- `test_call1024_oog[case3`

**test_call_lose_gas_oog.py**
- `test_call_lose_gas_oog[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcode1024_oog.py**
- `test_callcode1024_oog[case0`
- `test_callcode1024_oog[case1`

**test_callcode_lose_gas_oog.py**
- `test_callcode_lose_gas_oog[case2`

**test_contract_creation_make_call_that_ask_more_gas_then_transaction_provided.py**
- `test_contract_creation_make_call_that_ask_more_gas_then_transaction_provided[case0`
- `test_contract_creation_make_call_that_ask_more_gas_then_transaction_provided[case1`

**test_create_js_example_contract.py**
- `test_create_js_example_contract[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_js_no_collision.py**
- `test_create_js_no_collision[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_name_registrator_per_txs_not_enough_gas.py**
- `test_create_name_registrator_per_txs_not_enough_gas[case0`
- `test_create_name_registrator_per_txs_not_enough_gas[case1`

### tests/ported_static/stRandom2 (11 failures)

**test_random_statetest406.py**
- `test_random_statetest406[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest435.py**
- `test_random_statetest435[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest437.py**
- `test_random_statetest437[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest442.py**
- `test_random_statetest442[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest493.py**
- `test_random_statetest493[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest501.py**
- `test_random_statetest501[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest517.py**
- `test_random_statetest517[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest521.py**
- `test_random_statetest521[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest542.py**
- `test_random_statetest542[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest584.py**
- `test_random_statetest584[fork_Amsterdam-blockchain_test_from_state_test`

**test_random_statetest612.py**
- `test_random_statetest612[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stRevertTest (11 failures)

**test_revert_depth_create_oog.py**
- `test_revert_depth_create_oog[case6`
- `test_revert_depth_create_oog[case7`

**test_revert_in_call_code.py**
- `test_revert_in_call_code[fork_Amsterdam-blockchain_test_from_state_test`

**test_revert_in_create_in_init_paris.py**
- `test_revert_in_create_in_init_paris[fork_Amsterdam-blockchain_test_from_state_test`

**test_revert_in_delegate_call.py**
- `test_revert_in_delegate_call[fork_Amsterdam-blockchain_test_from_state_test`

**test_revert_opcode_in_create_returns.py**
- `test_revert_opcode_in_create_returns[fork_Amsterdam-blockchain_test_from_state_test`

**test_revert_opcode_in_init.py**
- `test_revert_opcode_in_init[case0`
- `test_revert_opcode_in_init[case1`

**test_revert_prefound_call.py**
- `test_revert_prefound_call[fork_Amsterdam-blockchain_test_from_state_test`

**test_revert_prefound_empty_call_paris.py**
- `test_revert_prefound_empty_call_paris[fork_Amsterdam-blockchain_test_from_state_test`

**test_touch_to_empty_account_revert3_paris.py**
- `test_touch_to_empty_account_revert3_paris[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stNonZeroCallsTest (10 failures)

**test_non_zero_value_call.py**
- `test_non_zero_value_call[fork_Amsterdam-blockchain_test_from_state_test`

**test_non_zero_value_call_to_empty_paris.py**
- `test_non_zero_value_call_to_empty_paris[fork_Amsterdam-blockchain_test_from_state_test`

**test_non_zero_value_call_to_one_storage_key_paris.py**
- `test_non_zero_value_call_to_one_storage_key_paris[fork_Amsterdam-blockchain_test_from_state_test`

**test_non_zero_value_callcode.py**
- `test_non_zero_value_callcode[fork_Amsterdam-blockchain_test_from_state_test`

**test_non_zero_value_callcode_to_empty_paris.py**
- `test_non_zero_value_callcode_to_empty_paris[fork_Amsterdam-blockchain_test_from_state_test`

**test_non_zero_value_callcode_to_one_storage_key_paris.py**
- `test_non_zero_value_callcode_to_one_storage_key_paris[fork_Amsterdam-blockchain_test_from_state_test`

**test_non_zero_value_delegatecall.py**
- `test_non_zero_value_delegatecall[fork_Amsterdam-blockchain_test_from_state_test`

**test_non_zero_value_delegatecall_to_empty_paris.py**
- `test_non_zero_value_delegatecall_to_empty_paris[fork_Amsterdam-blockchain_test_from_state_test`

**test_non_zero_value_delegatecall_to_non_non_zero_balance.py**
- `test_non_zero_value_delegatecall_to_non_non_zero_balance[fork_Amsterdam-blockchain_test_from_state_test`

**test_non_zero_value_delegatecall_to_one_storage_key_paris.py**
- `test_non_zero_value_delegatecall_to_one_storage_key_paris[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stEIP150Specific (8 failures)

**test_call_ask_more_gas_on_depth2_then_transaction_has.py**
- `test_call_ask_more_gas_on_depth2_then_transaction_has[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_and_gas_inside_create.py**
- `test_create_and_gas_inside_create[fork_Amsterdam-blockchain_test_from_state_test`

**test_delegate_call_on_eip.py**
- `test_delegate_call_on_eip[fork_Amsterdam-blockchain_test_from_state_test`

**test_execute_call_that_ask_fore_gas_then_trabsaction_has.py**
- `test_execute_call_that_ask_fore_gas_then_trabsaction_has[fork_Amsterdam-blockchain_test_from_state_test`

**test_new_gas_price_for_codes.py**
- `test_new_gas_price_for_codes[fork_Amsterdam-blockchain_test_from_state_test`

**test_transaction64_rule_d64e0.py**
- `test_transaction64_rule_d64e0[fork_Amsterdam-blockchain_test_from_state_test`

**test_transaction64_rule_d64m1.py**
- `test_transaction64_rule_d64m1[fork_Amsterdam-blockchain_test_from_state_test`

**test_transaction64_rule_d64p1.py**
- `test_transaction64_rule_d64p1[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stWalletTest (8 failures)

**test_day_limit_construction.py**
- `test_day_limit_construction[case0`
- `test_day_limit_construction[case1`

**test_day_limit_construction_partial.py**
- `test_day_limit_construction_partial[fork_Amsterdam-blockchain_test_from_state_test`

**test_multi_owned_construction_not_enough_gas_partial.py**
- `test_multi_owned_construction_not_enough_gas_partial[case1`

**test_wallet_construction.py**
- `test_wallet_construction[case0`
- `test_wallet_construction[case1`

**test_wallet_construction_oog.py**
- `test_wallet_construction_oog[case1`

**test_wallet_construction_partial.py**
- `test_wallet_construction_partial[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stPreCompiledContracts2 (7 failures)

**test_call_ecrecover_overflow.py**
- `test_call_ecrecover_overflow[case5`
- `test_call_ecrecover_overflow[case6`
- `test_call_ecrecover_overflow[case7`

**test_ecrecover_short_buff.py**
- `test_ecrecover_short_buff[fork_Amsterdam-blockchain_test_from_state_test`

**test_modexp_0_0_0_22000.py**
- `test_modexp_0_0_0_22000_from_osaka[case0`

**test_modexp_0_0_0_25000.py**
- `test_modexp_0_0_0_25000_from_osaka[case0`

**test_modexp_0_0_0_35000.py**
- `test_modexp_0_0_0_35000_from_osaka[case0`

### tests/ported_static/stTransactionTest (6 failures)

**test_create_message_success.py**
- `test_create_message_success[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_transaction_success.py**
- `test_create_transaction_success[fork_Amsterdam-blockchain_test_from_state_test`

**test_empty_transaction3.py**
- `test_empty_transaction3[fork_Amsterdam-blockchain_test_from_state_test`

**test_internal_call_hitting_gas_limit_success.py**
- `test_internal_call_hitting_gas_limit_success[fork_Amsterdam-blockchain_test_from_state_test`

**test_store_gas_on_create.py**
- `test_store_gas_on_create[fork_Amsterdam-blockchain_test_from_state_test`

**test_transaction_sending_to_empty.py**
- `test_transaction_sending_to_empty[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stDelegatecallTestHomestead (5 failures)

**test_call1024_oog.py**
- `test_call1024_oog[case0`
- `test_call1024_oog[case1`

**test_call_lose_gas_oog.py**
- `test_call_lose_gas_oog[fork_Amsterdam-blockchain_test_from_state_test`

**test_delegatecall1024_oog.py**
- `test_delegatecall1024_oog[fork_Amsterdam-blockchain_test_from_state_test`

**test_delegatecall_in_initcode_to_existing_contract_oog.py**
- `test_delegatecall_in_initcode_to_existing_contract_oog[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/Shanghai (4 failures)

**test_create2_init_code_size_limit.py**
- `test_create2_init_code_size_limit[case1`

**test_create_init_code_size_limit.py**
- `test_create_init_code_size_limit[case1`

**test_push0.py**
- `test_push0[case4`

**test_push0_gas.py**
- `test_push0_gas[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stBadOpcode (4 failures)

**test_measure_gas.py**
- `test_measure_gas[case2`
- `test_measure_gas[case3`

**test_operation_diff_gas.py**
- `test_operation_diff_gas[case2`
- `test_operation_diff_gas[case3`

### tests/ported_static/stEIP1559 (4 failures)

**test_sender_balance.py**
- `test_sender_balance[fork_Amsterdam-blockchain_test_from_state_test`

**test_val_causes_oof.py**
- `test_val_causes_oof[case6`
- `test_val_causes_oof[case8`
- `test_val_causes_oof[case9`

### tests/ported_static/stMemExpandingEIP150Calls (4 failures)

**test_call_ask_more_gas_on_depth2_then_transaction_has_with_mem_expanding_calls.py**
- `test_call_ask_more_gas_on_depth2_then_transaction_has_with_mem_expanding_calls[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_and_gas_inside_create_with_mem_expanding_calls.py**
- `test_create_and_gas_inside_create_with_mem_expanding_calls[fork_Amsterdam-blockchain_test_from_state_test`

**test_execute_call_that_ask_more_gas_then_transaction_has_with_mem_expanding_calls.py**
- `test_execute_call_that_ask_more_gas_then_transaction_has_with_mem_expanding_calls[fork_Amsterdam-blockchain_test_from_state_test`

**test_new_gas_price_for_codes_with_mem_expanding_calls.py**
- `test_new_gas_price_for_codes_with_mem_expanding_calls[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stRefundTest (4 failures)

**test_refund50_2.py**
- `test_refund50_2[fork_Amsterdam-blockchain_test_from_state_test`

**test_refund50percent_cap.py**
- `test_refund50percent_cap[fork_Amsterdam-blockchain_test_from_state_test`

**test_refund_suicide50procent_cap.py**
- `test_refund_suicide50procent_cap[case0`
- `test_refund_suicide50procent_cap[case1`

### tests/ported_static/stReturnDataTest (4 failures)

**test_create_callprecompile_returndatasize.py**
- `test_create_callprecompile_returndatasize[fork_Amsterdam-blockchain_test_from_state_test`

**test_returndatacopy_0_0_following_successful_create.py**
- `test_returndatacopy_0_0_following_successful_create[fork_Amsterdam-blockchain_test_from_state_test`

**test_returndatacopy_after_failing_create.py**
- `test_returndatacopy_after_failing_create[fork_Amsterdam-blockchain_test_from_state_test`

**test_returndatacopy_following_revert_in_create.py**
- `test_returndatacopy_following_revert_in_create[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stHomesteadSpecific (3 failures)

**test_contract_creation_oo_gdont_leave_empty_contract.py**
- `test_contract_creation_oo_gdont_leave_empty_contract[fork_Amsterdam-blockchain_test_from_state_test`

**test_contract_creation_oo_gdont_leave_empty_contract_via_transaction.py**
- `test_contract_creation_oo_gdont_leave_empty_contract_via_transaction[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_contract_via_transaction_cost53000.py**
- `test_create_contract_via_transaction_cost53000[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stStaticFlagEnabled (3 failures)

**test_callcode_to_precompile_from_called_contract.py**
- `test_callcode_to_precompile_from_called_contract_from_osaka[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcode_to_precompile_from_contract_initialization.py**
- `test_callcode_to_precompile_from_contract_initialization_from_osaka[fork_Amsterdam-blockchain_test_from_state_test`

**test_callcode_to_precompile_from_transaction.py**
- `test_callcode_to_precompile_from_transaction_from_osaka[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stSystemOperationsTest (3 failures)

**test_ab_acalls3.py**
- `test_ab_acalls3[fork_Amsterdam-blockchain_test_from_state_test`

**test_call_recursive_bomb3.py**
- `test_call_recursive_bomb3[fork_Amsterdam-blockchain_test_from_state_test`

**test_test_random_test.py**
- `test_test_random_test[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stTransitionTest (3 failures)

**test_create_name_registrator_per_txs_after.py**
- `test_create_name_registrator_per_txs_after[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_name_registrator_per_txs_at.py**
- `test_create_name_registrator_per_txs_at[fork_Amsterdam-blockchain_test_from_state_test`

**test_create_name_registrator_per_txs_before.py**
- `test_create_name_registrator_per_txs_before[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stCodeSizeLimit (2 failures)

**test_create2_code_size_limit.py**
- `test_create2_code_size_limit[case1`

**test_create_code_size_limit.py**
- `test_create_code_size_limit[case1`

### tests/ported_static/stExtCodeHash (2 failures)

**test_ext_code_hash_created_and_deleted_account_recheck_in_outer_call.py**
- `test_ext_code_hash_created_and_deleted_account_recheck_in_outer_call[fork_Amsterdam-blockchain_test_from_state_test`

**test_ext_code_hash_subcall_suicide_cancun.py**
- `test_ext_code_hash_subcall_suicide_cancun[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stSolidityTest (2 failures)

**test_call_low_level_creates_solidity.py**
- `test_call_low_level_creates_solidity[fork_Amsterdam-blockchain_test_from_state_test`

**test_recursive_create_contracts_create4_contracts.py**
- `test_recursive_create_contracts_create4_contracts[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stSpecialTest (2 failures)

**test_deployment_error.py**
- `test_deployment_error[fork_Amsterdam-blockchain_test_from_state_test`

**test_failed_create_reverts_deletion_paris.py**
- `test_failed_create_reverts_deletion_paris[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/VMTests (1 failures)

**test_two_ops.py**
- `test_two_ops[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stEIP158Specific (1 failures)

**test_exp_empty.py**
- `test_exp_empty[fork_Amsterdam-blockchain_test_from_state_test`

### tests/ported_static/stMemoryStressTest (1 failures)

**test_return_bounds.py**
- `test_return_bounds[case1`

### tests/ported_static/stSelfBalance (1 failures)

**test_self_balance_update.py**
- `test_self_balance_update[fork_Amsterdam-blockchain_test_from_state_test`
