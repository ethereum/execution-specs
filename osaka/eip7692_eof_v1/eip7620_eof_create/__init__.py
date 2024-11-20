"""
abstract: Test cases for [EIP-7620: EOF Contract Creation](https://eips.ethereum.org/EIPS/eip-7620)
    EIP-7620 replaces `CREATE` and `CREATE2` with `EOFCREATE` for deploying contracts in the EOF format.
    Opcodes introduced: `EOFCREATE` (`0xEC`), `RETURNCONTRACT` (`0xEE`).


EOFCREATE, RETURNCONTRACT, and container tests

evmone tests not ported

- create_tx_with_eof_initcode - This calls it invalid, it is now the way to add EOF contacts to state
- eofcreate_extcall_returncontract - per the new initcode mode tests you cannot have RETURNCONTRACT
    in a deployed contract
- eofcreate_dataloadn_referring_to_auxdata - covered by
    tests.osaka.eip7480_data_section.test_data_opcodes.test_data_section_succeed
- eofcreate_initcontainer_return - RETURN is banned in initcode containers
- eofcreate_initcontainer_stop - STOP is banned in initcode containers
- All TXCREATE tests.
"""  # noqa: E501
