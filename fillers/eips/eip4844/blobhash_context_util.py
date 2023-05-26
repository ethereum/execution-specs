"""
Utility Module: BLOBHASH Opcode Contexts
Test: fillers/eips/eip4844/blobhash_opcode_contexts.py
"""

from ethereum_test_tools import (
    TestAddress,
    Yul,
    compute_create2_address,
    compute_create_address,
    to_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op


class BlobhashContext:
    """
    A utility class for mapping common EVM opcodes in different contexts
    to specific bytecode (with BLOBHASH), addresses and contracts.
    """

    @staticmethod
    def _get_blobhash_verbatim():
        """
        Returns the BLOBHASH verbatim as a formatted string.
        """
        return "verbatim_{}i_{}o".format(
            Op.BLOBHASH.popped_stack_items,
            Op.BLOBHASH.pushed_stack_items,
        )

    @classmethod
    def address(cls, context_name):
        """
        Maps an opcode context to a specific address.
        """
        addresses = {
            "blobhash_sstore": to_address(0x100),
            "blobhash_return": to_address(0x600),
            "call": to_address(0x200),
            "delegatecall": to_address(0x300),
            "callcode": to_address(0x800),
            "staticcall": to_address(0x700),
            "create": to_address(0x400),
            "create2": to_address(0x500),
        }
        return addresses.get(context_name)

    @classmethod
    def code(cls, context_name):
        """
        Maps an opcode context to bytecode that utilizes the BLOBHASH opcode.
        """
        blobhash_verbatim = cls._get_blobhash_verbatim()

        code = {
            "blobhash_sstore": Yul(
                f"""
                {{
                   let pos := calldataload(0)
                   let end := calldataload(32)
                   for {{}} lt(pos, end) {{ pos := add(pos, 1) }}
                   {{
                    let blobhash := {blobhash_verbatim}
                        (hex"{Op.BLOBHASH.hex()}", pos)
                    sstore(pos, blobhash)
                   }}
                   let blobhash := {blobhash_verbatim}
                        (hex"{Op.BLOBHASH.hex()}", end)
                   sstore(end, blobhash)
                   return(0, 0)
                }}
                """
            ),
            "blobhash_return": Yul(
                f"""
                {{
                   let pos := calldataload(0)
                   let blobhash := {blobhash_verbatim}
                        (hex"{Op.BLOBHASH.hex()}", pos)
                   mstore(0, blobhash)
                   return(0, 32)
                }}
                """
            ),
            "call": Yul(
                """
                {
                    calldatacopy(0, 0, calldatasize())
                    pop(call(gas(), 0x100, 0, 0, calldatasize(), 0, 0))
                }
                """
            ),
            "delegatecall": Yul(
                """
                {
                    calldatacopy(0, 0, calldatasize())
                    pop(delegatecall(gas(), 0x100, 0, calldatasize(), 0, 0))
                }
                """
            ),
            "callcode": Yul(
                f"""
                {{
                    let pos := calldataload(0)
                    let end := calldataload(32)
                    for {{ }} lt(pos, end) {{ pos := add(pos, 1) }}
                    {{
                    mstore(0, pos)
                    pop(callcode(gas(),
                        {cls.address("blobhash_return")}, 0, 0, 32, 0, 32))
                    let blobhash := mload(0)
                    sstore(pos, blobhash)
                    }}

                    mstore(0, end)
                    pop(callcode(gas(),
                        {cls.address("blobhash_return")}, 0, 0, 32, 0, 32))
                    let blobhash := mload(0)
                    sstore(end, blobhash)
                    return(0, 0)
                }}
                """
            ),
            "staticcall": Yul(
                f"""
                {{
                    let pos := calldataload(0)
                    let end := calldataload(32)
                    for {{ }} lt(pos, end) {{ pos := add(pos, 1) }}
                    {{
                    mstore(0, pos)
                    pop(staticcall(gas(),
                        {cls.address("blobhash_return")}, 0, 32, 0, 32))
                    let blobhash := mload(0)
                    sstore(pos, blobhash)
                    }}

                    mstore(0, end)
                    pop(staticcall(gas(),
                        {cls.address("blobhash_return")}, 0, 32, 0, 32))
                    let blobhash := mload(0)
                    sstore(end, blobhash)
                    return(0, 0)
                }}
                """
            ),
            "create": Yul(
                """
                {
                    calldatacopy(0, 0, calldatasize())
                    pop(create(0, 0, calldatasize()))
                }
                """
            ),
            "create2": Yul(
                """
                {
                    calldatacopy(0, 0, calldatasize())
                    pop(create2(0, 0, calldatasize(), 0))
                }
                """
            ),
            "initcode": Yul(
                f"""
                {{
                   for {{ let pos := 0 }} lt(pos, 10) {{ pos := add(pos, 1) }}
                   {{
                    let blobhash := {blobhash_verbatim}
                        (hex"{Op.BLOBHASH.hex()}", pos)
                    sstore(pos, blobhash)
                   }}
                   return(0, 0)
                }}
                """
            ),
        }
        return code.get(context_name)

    @classmethod
    def created_contract(cls, context_name):
        """
        Maps contract creation to a specific context to a specific address.
        """
        contract = {
            "tx_created_contract": compute_create_address(TestAddress, 0),
            "create": compute_create_address(
                BlobhashContext.address("create"),
                0,
            ),
            "create2": compute_create2_address(
                BlobhashContext.address("create2"),
                0,
                BlobhashContext.code("initcode").assemble(),
            ),
        }
        return contract.get(context_name)
