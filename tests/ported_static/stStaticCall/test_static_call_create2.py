"""
Test_static_call_create2.

Ported from:
state_tests/stStaticCall/static_callCreate2Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callCreate2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
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
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
    ],
)
def test_static_call_create2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call_create2."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # {  (CALL 600000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_0 = pre.deploy_contract(
        code=Op.CALL(
            gas=0x927C0,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {  [[ 0 ]] (CREATE 1 0 0) [[ 1 ]] (STATICCALL 300000 (SLOAD 0) 0 0 0 0) }
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(
            key=0x0, value=Op.CREATE(value=0x1, offset=0x0, size=0x0)
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x493E0,
                address=Op.SLOAD(key=0x0),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {  (MSTORE 0 0x6460016001556000526005601bf3 ) [[ 0 ]] (CREATE 1 18 14) [[ 1 ]] (STATICCALL 300000 (SLOAD 0) 0 0 0 0) }  # noqa: E501
    contract_2 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x6460016001556000526005601BF3)
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x1, offset=0x12, size=0xE))
        + Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x493E0,
                address=Op.SLOAD(key=0x0),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    # Source: lll
    # {  (MSTORE 0 0x6460016001556000526005601bf3 ) [[ 0 ]] (CREATE 1 18 14) [[ 1 ]] (STATICCALL 300000 (SLOAD 0) 0 0 0 0) (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }  # noqa: E501
    contract_3 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x6460016001556000526005601BF3)
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x1, offset=0x12, size=0xE))
        + Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x493E0,
                address=Op.SLOAD(key=0x0),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x4B, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x2F)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_1: Account(
                    storage={
                        0: compute_create_address(address=contract_1, nonce=1),
                        1: 1,
                    },
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_2: Account(
                    storage={
                        0: compute_create_address(address=contract_2, nonce=1),
                        1: 0,
                    },
                ),
                compute_create_address(address=contract_2, nonce=1): Account(
                    storage={}, code=bytes.fromhex("6001600155")
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_2: Account(storage={0: 0, 1: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(contract_1, left_padding=True),
        Hash(contract_2, left_padding=True),
        Hash(contract_3, left_padding=True),
    ]
    tx_gas = [1000000]
    tx_value = [100000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
