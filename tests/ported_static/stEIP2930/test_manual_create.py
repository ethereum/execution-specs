"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP2930/manualCreateFiller.yml

@manually-enhanced: Do not overwrite. The three parametrizations of
this test measure regular gas around a fresh SSTORE-set inside a
CREATE-deployed contract. EIP-8037 moves the bulk of the SSTORE-set
cost into a per-storage state-gas charge; with an empty reservoir it
spills back into regular gas, which `Op.GAS` observes. Derive the
warm and cold fresh-set deltas from the fork's own gas model so each
is exactly 0 pre-EIP-8037 and tracks parameter changes; bake the
warm delta into the declared-key entry and the cold delta into the
undeclared-key entries.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Cancun, Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP2930/manualCreateFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="allBad",
        ),
        pytest.param(
            1,
            0,
            0,
            id="addrGoodCellBad",
        ),
        pytest.param(
            2,
            0,
            0,
            id="allGood",
        ),
    ],
)
def test_manual_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    sender = pre.fund_eoa(amount=0x1000000000000000000)
    created = compute_create_address(address=sender, nonce=0)

    # EIP-8037 SSTORE-set spill into regular gas (empty reservoir).
    # Derive the warm and cold fresh-set deltas from the fork's own
    # gas model so each is exactly 0 pre-EIP-8037.
    def _sstore_delta(**metadata: int) -> int:
        op = Op.SSTORE.with_metadata(**metadata)
        return op.gas_cost(fork) - op.gas_cost(Cancun)

    warm_set_delta = _sstore_delta(key_warm=True, current_value=0, new_value=2)
    cold_set_delta = _sstore_delta(
        key_warm=False, current_value=0, new_value=2
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created: Account(storage={0: 20008 + warm_set_delta, 1: 106}),
            },
        },
        {
            "indexes": {"data": [0, 1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                created: Account(storage={0: 22108 + cold_set_delta, 1: 106}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Op.GAS
        + Op.POP(Op.BALANCE(address=Op.ADDRESS))
        + Op.GAS
        + Op.SWAP1
        + Op.SSTORE(key=0x1, value=Op.SUB)
        + Op.GAS
        + Op.SSTORE(key=0x0, value=0xFF)
        + Op.GAS
        + Op.SWAP1
        + Op.SSTORE(key=0x0, value=Op.SUB)
        + Op.STOP,
        Op.GAS
        + Op.POP(Op.BALANCE(address=Op.ADDRESS))
        + Op.GAS
        + Op.SWAP1
        + Op.SSTORE(key=0x1, value=Op.SUB)
        + Op.GAS
        + Op.SSTORE(key=0x0, value=0xFF)
        + Op.GAS
        + Op.SWAP1
        + Op.SSTORE(key=0x0, value=Op.SUB)
        + Op.STOP,
        Op.GAS
        + Op.POP(Op.BALANCE(address=Op.ADDRESS))
        + Op.GAS
        + Op.SWAP1
        + Op.SSTORE(key=0x1, value=Op.SUB)
        + Op.GAS
        + Op.SSTORE(key=0x0, value=0xFF)
        + Op.GAS
        + Op.SWAP1
        + Op.SSTORE(key=0x0, value=Op.SUB)
        + Op.STOP,
    ]
    # EIP-8037 NEW_ACCOUNT state-gas spill into regular gas on
    # Amsterdam exceeds the original 400 000 budget. Pre-EIP-8037
    # keeps the original value.
    outer_tx_gas = 400_000
    if fork.is_eip_enabled(8037):
        outer_tx_gas = 1_000_000
    tx_gas = [outer_tx_gas]
    tx_access_lists: dict[int, list] = {
        0: [
            AccessList(
                address=Address(0x100),
                storage_keys=[Hash(0)],
            ),
        ],
        1: [
            AccessList(
                address=created,
                storage_keys=[Hash(1)],
            ),
        ],
        2: [
            AccessList(
                address=created,
                storage_keys=[Hash(0)],
            ),
        ],
    }

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        access_list=tx_access_lists.get(d),
        error=_exc,
    )

    state_test(pre=pre, post=post, tx=tx)
