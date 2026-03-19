"""
Check that create2 does not fill returndata buffer with its return opcode.

Ported from:
tests/static/state_tests/stCreate2/returndatacopy_following_createFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "0000000000000000000000000f572e5295c57f15886f9b263e2f6d2d6c7b5ec6",
    "0000000000000000000000001f572e5295c57f15886f9b263e2f6d2d6c7b5ec6",
]

TX_GAS = [100000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCreate2/returndatacopy_following_createFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_returndatacopy_following_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Check that create2 does not fill returndata buffer with its..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=47244640256,
    )

    # Source: LLL
    # { (CREATE2 0 0 (lll (seq (MSTORE 0 0x0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff) (RETURN 0 32)) 0) 0) (RETURNDATACOPY 0 0 32) (SSTORE 0 (MLOAD 0)) }  # noqa: E501
    callee = pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0x28]
            + Op.CODECOPY(dest_offset=0x0, offset=0x1F, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.CREATE2)
            + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.STOP
            + Op.INVALID
            + Op.MSTORE(
                offset=0x0,
                value=0x111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF,  # noqa: E501
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.STOP
        ),
        storage={0x0: 0x1},
        nonce=0,
        address=Address("0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"),  # noqa: E501
    )
    # Source: LLL
    # { (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1aabbccdd5c57f15886f9b263e2f6d2d6c7b5ec6"),  # noqa: E501
    )
    # Source: LLL
    # { (seq (create2 0 0 (lll (STOP) 0) 0) (RETURNDATACOPY 0 0 32) (SSTORE 0 (MLOAD 0)) )}  # noqa: E501
    callee_1 = pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0x2]
            + Op.CODECOPY(dest_offset=0x0, offset=0x1F, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.CREATE2)
            + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.STOP
            + Op.INVALID
            + Op.STOP
            + Op.STOP
        ),
        storage={0x0: 0x1},
        nonce=0,
        address=Address("0x1f572e5295c57f15886f9b263e2f6d2d6c7b5ec6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {callee: Account(storage={0: 1})},
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {callee_1: Account(storage={0: 1})},
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
