"""
Gas analysis showed this test's gas can go as low as 101174, and still...

Ported from:
state_tests/stStaticCall/static_CallContractToCreateContractOOGBonusGasFiller.json
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
    "",
]
TX_GAS = [20000000, 80000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_CallContractToCreateContractOOGBonusGasFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
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
@pytest.mark.pre_alloc_mutable
def test_static_call_contract_to_create_contract_oog_bonus_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Gas analysis showed this test's gas can go as low as 101174, and..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # { (MSTORE 0 0x600c60005566602060406000f060205260076039f3) [[0]](CREATE 1 11 21) [[ 1 ]] (STATICCALL 0 (SLOAD 0) 0 0 0 0)}  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0, value=0x600C60005566602060406000F060205260076039F3
        )
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x1, offset=0xB, size=0x15))
        + Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x0,
                address=Op.SLOAD(key=0x0),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=112,
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2540BE400)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_0: Account(
                    storage={0: 0xD2571607E241ECF590ED94B12D87C94BABE36DB6},
                    nonce=1,
                ),
                sender: Account(nonce=1),
                Address("0xd2571607e241ecf590ed94b12d87c94babe36db6"): Account(
                    storage={0: 12, 1: 0}, balance=1, nonce=1
                ),
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_0: Account(storage={0: 0}, nonce=0),
                sender: Account(nonce=1),
                Address(
                    "0xd2571607e241ecf590ed94b12d87c94babe36db6"
                ): Account.NONEXISTENT,
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
