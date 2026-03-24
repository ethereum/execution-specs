"""
transaction calls A (CALL B(CALL C(RETURN) OOG) 'check buffers').

Ported from:
tests/static/state_tests/stReturnDataTest
returndatasize_after_oog_after_deeperFiller.json
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
        "tests/static/state_tests/stReturnDataTest/returndatasize_after_oog_after_deeperFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_returndatasize_after_oog_after_deeper(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Transaction calls A (CALL B(CALL C(RETURN) OOG) 'check buffers')."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x987C63506890B18862BD2304513F21B726A7E35961C9214954326694141FDB46
    )
    callee_1 = Address("0xbda572e15071b6ab42cfec01423f1fbb1de68703")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    # Source: LLL
    # { (seq (SSTORE 2 (CALL 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0 32)) (SSTORE 0 (RETURNDATASIZE))) (SSTORE 1 (MLOAD 0))}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=0x186A0,
                    address=0xCB33B9A773995316746A40201081D054635D02DA,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={
            0x0: 0xFFFFFFFF,
            0x1: 0xFFFFFFFF,
            0x2: 0xFFFFFFFF,
        },
        nonce=0,
        address=Address("0x58eaa3041ad52c24e38e485222953f1cc19c7484"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0xFF)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x8e0c75135225713d8c9acbb889abba5a5f598920"),  # noqa: E501
    )
    pre[callee_1] = Account(balance=0x1000000000, nonce=0)
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x186A0,
                    address=0x8E0C75135225713D8C9ACBB889ABBA5A5F598920,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x34, condition=Op.ISZERO(0x1))
            + Op.SSTORE(key=0x0, value=0x1)
            + Op.JUMP(pc=0x25)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0x6400000000,
        nonce=0,
        address=Address("0xcb33b9a773995316746a40201081d054635d02da"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=200000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
