"""
Test the gas of SELFDESTRUCT to a cold or pre-warmed beneficiary.

Ported from:
state_tests/stEIP150singleCodeGasPrices/eip2929-ffFiller.yml

@manually-enhanced: Do not overwrite. The first expect-entry (the
`simple`/NOP case) measures a `CALL` into a contract that
`SELFDESTRUCT`s with an as-yet-untouched (cold) beneficiary. EIP-8038
raises `COLD_ACCOUNT_ACCESS`, so that cost shifts by the fork's
`COLD_ACCOUNT_ACCESS` less Cancun's, exactly 0 pre-EIP-8038. The other
entry pre-warms the beneficiary, so its cost is unchanged. Do not
hardcode the Amsterdam number.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Cancun, Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def if_then(
    start: int, condition: Bytecode, body: Bytecode, has_value: bool
) -> Bytecode:
    """
    Build the LLL `(if condition body NOP)` layout at code offset `start`.

    Jump destinations are derived from the code length, so the layout
    holds for any address push width.
    """
    skip = Op.PUSH1[0] if has_value else Op.POP(0)
    head = (
        len(Op.JUMPI(pc=Op.PUSH2[0], condition=condition))
        + len(skip)
        + len(Op.JUMP(pc=Op.PUSH2[0]))
    )
    then = start + head
    end = then + len(Op.JUMPDEST) + len(body)
    code = (
        Op.JUMPI(pc=Op.PUSH2[then], condition=condition)
        + skip
        + Op.JUMP(pc=Op.PUSH2[end])
        + Op.JUMPDEST
        + body
        + Op.JUMPDEST
    )
    return code + Op.POP if has_value else code


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/eip2929-ffFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="simple",
        ),
        pytest.param(
            1,
            0,
            0,
            id="balance",
        ),
        pytest.param(
            2,
            0,
            0,
            id="extcodesize",
        ),
        pytest.param(
            3,
            0,
            0,
            id="extcodecopy",
        ),
        pytest.param(
            4,
            0,
            0,
            id="extcodehash",
        ),
        pytest.param(
            5,
            0,
            0,
            id="call",
        ),
        pytest.param(
            6,
            0,
            0,
            id="callcode",
        ),
        pytest.param(
            7,
            0,
            0,
            id="delegatecall",
        ),
        pytest.param(
            8,
            0,
            0,
            id="staticcall",
        ),
    ],
)
def test_eip2929_minus_ff(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Store the gas of a CALL into a SELFDESTRUCT after a warm-up."""
    # EIP-8038 raises COLD_ACCOUNT_ACCESS, 0 on earlier forks.
    cold_account_delta = (
        fork.gas_costs().COLD_ACCOUNT_ACCESS
        - Cancun.gas_costs().COLD_ACCOUNT_ACCESS
    )
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE)

    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.STOP,
    )
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=contract_0) + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )
    warm_ups = [
        (0x31, Op.BALANCE(address=contract_0), True),
        (0x3B, Op.EXTCODESIZE(address=contract_0), True),
        (
            0x3C,
            Op.EXTCODECOPY(
                address=contract_0, dest_offset=0, offset=0, size=1
            ),
            False,
        ),
        (0x3F, Op.EXTCODEHASH(address=contract_0), True),
        (0xF1, Op.CALL(gas=0x10000, address=contract_0), True),
        (0xF2, Op.CALLCODE(gas=0x10000, address=contract_0), True),
        (0xF4, Op.DELEGATECALL(gas=0x10000, address=contract_0), True),
        (0xFA, Op.STATICCALL(gas=0x10000, address=contract_0), True),
    ]
    measurement = (
        Op.MSTORE(offset=0x100, value=0xFF)
        + Op.MSTORE(offset=0x120, value=0xFF)
        + Op.POP(Op.BALANCE(address=contract_1))
    )
    for operation, body, has_value in warm_ups:
        condition = Op.EQ(Op.CALLDATALOAD(offset=0x4), operation)
        measurement += if_then(len(measurement), condition, body, has_value)
    contract_2 = pre.deploy_contract(
        code=measurement
        + Op.MSTORE(offset=0x100, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x1000000,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x120, value=Op.GAS)
        + Op.SSTORE(
            key=0x0,
            value=Op.SUB(
                Op.SUB(Op.MLOAD(offset=0x100), Op.MLOAD(offset=0x120)), 0x8
            ),
        )
        + Op.MSTORE(offset=0x100, value=Op.GAS)
        + Op.POP(Op.BALANCE(address=contract_0))
        + Op.MSTORE(offset=0x120, value=Op.GAS)
        + Op.SSTORE(
            key=0x1,
            value=Op.SUB(
                Op.SUB(Op.MLOAD(offset=0x100), Op.MLOAD(offset=0x120)), 0x8
            ),
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_2: Account(
                    storage={0: 7726 + cold_account_delta, 1: 105}
                )
            },
        },
        {
            "indexes": {
                "data": [1, 2, 3, 4, 5, 6, 7, 8],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_2: Account(storage={0: 5126, 1: 105})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x31),
        Bytes("693c6139") + Hash(0x3B),
        Bytes("693c6139") + Hash(0x3C),
        Bytes("693c6139") + Hash(0x3F),
        Bytes("693c6139") + Hash(0xF1),
        Bytes("693c6139") + Hash(0xF2),
        Bytes("693c6139") + Hash(0xF4),
        Bytes("693c6139") + Hash(0xFA),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_2,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
