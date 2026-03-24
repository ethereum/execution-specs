"""
Revert undoes the transient storage writes after a successful call.

Ported from:
tests/static/state_tests/Cancun/stEIP1153_transientStorage
10_revertUndoesStoreAfterReturnFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/Cancun/stEIP1153_transientStorage/10_revertUndoesStoreAfterReturnFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_10_revert_undoes_store_after_return(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Revert undoes the transient storage writes after a successful call."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xBE0E7D5FEA1604BF57E004B0B414DF8DE04816DBB1C8F8719B725D0D6619B531
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4503599627370496,
    )

    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)
    # Source: Yul
    # {
    #   switch selector()
    #
    #   case 0x70ac643e { // doFirstCall()
    #     doFirstCall()
    #   }
    #
    #   case 0x76b85d23 { // doCallThenRevert()
    #     doCallThenRevert()
    #   }
    #
    #   case 0x4ccca553 { // doSuccessfulStore()
    #     doSuccessfulStore()
    #   }
    #
    #   function doFirstCall() {
    #     verbatim_2i_0o(hex"5D", 0, 5)
    #
    #     let v := verbatim_1i_1o(hex"5C", 0)
    #     sstore(0, v)
    #
    #     mstore(0, hex"76b85d23") // calls doCallThenRevert()
    #     let fail := call(gas(), address(), 0, 0, 32, 0, 32)
    #
    #     sstore(1, fail) // should be 0 (revert)
    #     sstore(2, mload(0)) // load 1 (successful call)
    #
    #     let val := verbatim_1i_1o(hex"5C", 0)
    #     sstore(3, val)
    #   }
    # ... (23 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.SHR(0xE0, Op.CALLDATALOAD(offset=Op.PUSH0))
            + Op.JUMPI(pc=0x2F, condition=Op.EQ(0x70AC643E, Op.DUP1))
            + Op.JUMPI(pc=0x2B, condition=Op.EQ(0x76B85D23, Op.DUP1))
            + Op.PUSH4[0x4CCCA553]
            + Op.JUMPI(pc=0x23, condition=Op.EQ)
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x29]
            + Op.JUMP(pc=0x76)
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.JUMP(pc=0x5C)
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH1[0x29]
            + Op.TSTORE(key=Op.PUSH0, value=0x5)
            + Op.SSTORE(key=Op.PUSH0, value=Op.TLOAD(key=Op.PUSH0))
            + Op.MSTORE(offset=Op.PUSH0, value=Op.SHL(0xE0, 0x76B85D23))
            + Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.ADDRESS,
                    value=Op.DUP1,
                    args_offset=Op.DUP2,
                    args_size=Op.DUP2,
                    ret_offset=Op.PUSH0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=Op.PUSH0))
            + Op.SSTORE(key=0x3, value=Op.TLOAD(key=Op.PUSH0))
            + Op.JUMP
            + Op.JUMPDEST
            + Op.MSTORE(offset=Op.PUSH0, value=Op.SHL(0xE0, 0x4CCCA553))
            + Op.MSTORE(
                offset=Op.PUSH0,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.ADDRESS,
                    value=Op.DUP1,
                    args_offset=Op.DUP2,
                    args_size=0x20,
                    ret_offset=Op.DUP1,
                    ret_size=Op.PUSH0,
                ),
            )
            + Op.REVERT(offset=Op.PUSH0, size=0x20)
            + Op.JUMPDEST
            + Op.TSTORE(key=Op.PUSH0, value=0x6)
            + Op.JUMP
        ),
        storage={0x1: 0xFFFF},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xe42b9e92d5348b0fc6353d40e3d220c316d3c685"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("70ac643e"),
        gas_limit=400000,
        max_fee_per_gas=2000,
    )

    post = {
        contract: Account(storage={0: 5, 2: 1, 3: 5}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
