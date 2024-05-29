"""
EOFCREATE, RETURNCONTRACT, and container tests

evmone tests not ported

create_tx_with_eof_initcode - This calls it invalid, it is now the way to add EOF contacts to state
eofcreate_extcall_returncontract - per the new initcode mode tests you cannot have RETURNCONTRACT
    in a deployed contract
eofcreate_dataloadn_referring_to_auxdata - covered by
    tests.prague.eip7480_data_section.test_data_opcodes.test_data_section_succeed
eofcreate_initcontainer_return - RETURN is banned in initcode containers
eofcreate_initcontainer_stop - STOP is banned in initcode containers
All TXCREATE tests - TXCREATE has been removed from Prague
"""
