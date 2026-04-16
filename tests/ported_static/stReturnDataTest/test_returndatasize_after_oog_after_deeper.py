"""
Transaction calls A (CALL B(CALL C(RETURN) OOG) 'check buffers').

Ported from:
state_tests/stReturnDataTest/returndatasize_after_oog_after_deeperFiller.json
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
        "state_tests/stReturnDataTest/returndatasize_after_oog_after_deeperFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatasize_after_oog_after_deeper(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Transaction calls A (CALL B(CALL C(RETURN) OOG) 'check buffers')."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0x100000000000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    addr = pre.fund_eoa(amount=0x1000000000)  # noqa: F841
    # Source: lll
    # { (seq (MSTORE 0 255) (RETURN 0 32) )}
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xFF)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (seq (CALL 100000 <contract:0xbb00000000000000000000000000000000000000> 0 0 0 0 0) (while 1 (SSTORE 0 1)) )}  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x186A0,
                address=addr_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x34, condition=Op.ISZERO(0x1))
        + Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x25)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0x6400000000,
        nonce=0,
    )
    # Source: lll
    # { (seq (SSTORE 2 (CALL 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0 32)) (SSTORE 0 (RETURNDATASIZE))) (SSTORE 1 (MLOAD 0))}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x186A0,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={0: 0xFFFFFFFF, 1: 0xFFFFFFFF, 2: 0xFFFFFFFF},
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=200000,
    )

    post = {target: Account(storage={0: 0, 1: 0, 2: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
