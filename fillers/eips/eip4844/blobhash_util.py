"""
Utility Module: BLOBHASH Opcode
Tests: fillers/eips/eip4844/
    > blobhash_opcode_contexts.py
    > blobhash_opcode.py
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
        address = cls.addresses.get(context_name)
        if address is None:
            raise ValueError(f"Invalid context: {context_name}")
        return address

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
        code = code.get(context_name)
        if code is None:
            raise ValueError(f"Invalid context: {context_name}")
        return code

    @classmethod
    def created_contract(cls, context_name):
        """
        Maps contract creation to a specific context to a specific address.
        """
        contract = {
            "tx_created_contract": compute_create_address(TestAddress, 0),
            "create": compute_create_address(
                cls.address("create"),
                0,
            ),
            "create2": compute_create2_address(
                cls.address("create2"),
                0,
                cls.code("initcode").assemble(),
            ),
        }
        contract = contract.get(context_name)
        if contract is None:
            raise ValueError(f"Invalid contract: {context_name}")
        return contract


class BlobhashScenario:
    """
    A utility class for generating blobhash calls.
    """

    MAX_BLOB_PER_BLOCK = 4

    @staticmethod
    def blobhash_sstore(index: int):
        """
        Returns an BLOBHASH sstore to the given index.
        """
        return Op.SSTORE(index, Op.BLOBHASH(index))

    @classmethod
    def generate_blobhash_calls(cls, scenario_name: str) -> bytes:
        """
        Returns BLOBHASH bytecode calls for the given scenario.
        """
        scenarios = {
            "single_valid": lambda: b"".join(
                cls.blobhash_sstore(i) for i in range(cls.MAX_BLOB_PER_BLOCK)
            ),
            "repeated_valid": lambda: b"".join(
                b"".join(cls.blobhash_sstore(i) for _ in range(10))
                for i in range(cls.MAX_BLOB_PER_BLOCK)
            ),
            "valid_invalid": lambda: b"".join(
                cls.blobhash_sstore(i)
                + cls.blobhash_sstore(cls.MAX_BLOB_PER_BLOCK)
                + cls.blobhash_sstore(i)
                for i in range(cls.MAX_BLOB_PER_BLOCK)
            ),
            "varied_valid": lambda: b"".join(
                cls.blobhash_sstore(i)
                + cls.blobhash_sstore(i + 1)
                + cls.blobhash_sstore(i)
                for i in range(cls.MAX_BLOB_PER_BLOCK - 1)
            ),
            "invalid_calls": lambda: b"".join(
                cls.blobhash_sstore(i)
                for i in range(-5, cls.MAX_BLOB_PER_BLOCK + 5)
            ),
        }
        scenario = scenarios.get(scenario_name)
        if scenario is None:
            raise ValueError(f"Invalid scenario: {scenario_name}")
        return scenario()
