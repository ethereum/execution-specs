"""
Check that create2 does not fill returndata buffer with its return opcode.

Ported from:
state_tests/stCreate2/returndatacopy_following_createFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreate2/returndatacopy_following_createFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
    ],
)
def test_returndatacopy_following_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Check that create2 does not fill returndata buffer with its return..."""
    sender = pre.fund_eoa(amount=0x6400000000)

    # Source: lll
    # { (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_0 = pre.deploy_contract(
        code=Op.CALL(
            gas=Op.GAS,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
    )
    # Source: lll
    # { (CREATE2 0 0 (lll (seq (MSTORE 0 0x0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff) (RETURN 0 32)) 0) 0) (RETURNDATACOPY 0 0 32) (SSTORE 0 (MLOAD 0)) }  # noqa: E501
    contract_1 = pre.deploy_contract(
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0x28]
        + Op.CODECOPY(dest_offset=0x0, offset=0x1F, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
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
        + Op.STOP,
        storage={0: 1},
    )
    # Source: lll
    # { (seq (create2 0 0 (lll (STOP) 0) 0) (RETURNDATACOPY 0 0 32) (SSTORE 0 (MLOAD 0)) )}  # noqa: E501
    contract_2 = pre.deploy_contract(
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0x2]
        + Op.CODECOPY(dest_offset=0x0, offset=0x1F, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE2)
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP
        + Op.INVALID
        + Op.STOP * 2,
        storage={0: 1},
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_1: Account(storage={0: 1})},
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_2: Account(storage={0: 1})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(contract_1, left_padding=True),
        Hash(contract_2, left_padding=True),
    ]
    tx_gas = [100000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
