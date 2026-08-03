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
    EOA,
    AccessList,
    Account,
    Address,
    Alloc,
    Environment,
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
@pytest.mark.pre_alloc_mutable
def test_manual_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[sender] = Account(balance=0x1000000000000000000, nonce=1)

    # EIP-8037 SSTORE-set spill into regular gas (empty reservoir).
    # Derive the warm and cold fresh-set deltas from the fork's own
    # gas model so each is exactly 0 pre-EIP-8037.
    def _sstore_delta(cancun_cost: int, **metadata: int) -> int:
        op = Op.SSTORE.with_metadata(**metadata)
        return op.gas_cost(fork) - cancun_cost

    warm_set_delta = _sstore_delta(
        20000, key_warm=True, current_value=0, new_value=2
    )
    cold_set_delta = _sstore_delta(
        22100, key_warm=False, current_value=0, new_value=2
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=1): Account(
                    storage={0: 20008 + warm_set_delta, 1: 106}
                ),
            },
        },
        {
            "indexes": {"data": [0, 1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=sender, nonce=1): Account(
                    storage={0: 22108 + cold_set_delta, 1: 106}
                ),
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
                address=Address(0x0000000000000000000000000000000000000100),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        1: [
            AccessList(
                address=Address(0xEC0E71AD0A90FFE1909D27DAC207F7680ABBA42D),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000001"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
        2: [
            AccessList(
                address=Address(0xEC0E71AD0A90FFE1909D27DAC207F7680ABBA42D),
                storage_keys=[
                    Hash(
                        "0x0000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    ),  # noqa: E501
                ],
            ),
        ],
    }

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        access_list=tx_access_lists.get(d),
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
