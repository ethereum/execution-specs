"""
CreateMessageReverted for CREATE2.

Ported from:
state_tests/stCreate2/CreateMessageRevertedFiller.json
@manually-enhanced: Do not overwrite. tx_gas[1] bumped on Amsterdam to
cover EIP-8037 state-gas spill (CREATE2 new account + 2 fresh
SSTOREs in init code); pre-EIP-8037 unchanged. g0 (OoG case) is
intentionally left alone.

"""

import pytest
from execution_testing import (
    Account,
    Alloc,
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
    ["state_tests/stCreate2/CreateMessageRevertedFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
def test_create_message_reverted(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """CreateMessageReverted for CREATE2."""
    sender = pre.fund_eoa()
    initcode = Op.SSTORE(key=0, value=0xC) + Op.SSTORE(key=1, value=0xD)
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0, value=int.from_bytes(bytes(initcode), "big")
        )
        + Op.CREATE2(
            value=0x0,
            offset=32 - len(initcode),
            size=len(initcode),
            salt=0x0,
        )
        + Op.STOP,
    )

    created = compute_create_address(
        address=contract_0, salt=0, initcode=initcode, opcode=Op.CREATE2
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                created: Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                created: Account(storage={0: 12, 1: 13}, balance=0, nonce=1),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_gas = [80000, 150000]
    if fork.is_eip_enabled(8037):
        tx_gas = [80000, 500_000]
    tx_value = [100]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
