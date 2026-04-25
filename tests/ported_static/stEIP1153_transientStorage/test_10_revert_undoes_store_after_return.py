"""
Revert undoes the transient storage writes after a successful call.

Ported from:
state_tests/Cancun/stEIP1153_transientStorage/10_revertUndoesStoreAfterReturnFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/Cancun/stEIP1153_transientStorage/10_revertUndoesStoreAfterReturnFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_10_revert_undoes_store_after_return(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Revert undoes the transient storage writes after a successful call."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x3635C9ADC5DEA00000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4503599627370496,
    )

    # Source: yul
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
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SHR(0xE0, Op.CALLDATALOAD(offset=Op.PUSH0))
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
        + Op.JUMP,
        storage={1: 65535},
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("70ac643e"),
        gas_limit=400000,
        max_fee_per_gas=2000,
        max_priority_fee_per_gas=0,
        access_list=[],
    )

    post = {target: Account(storage={0: 5, 1: 0, 2: 1, 3: 5})}

    state_test(env=env, pre=pre, post=post, tx=tx)
