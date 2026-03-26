"""
test_static_call_contract_to_create_contract_and_call_it_oog

Ported from:
state_tests/stStaticCall/static_CallContractToCreateContractAndCallItOOGFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "00",
    "01",
]
TX_GAS = [2000000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_CallContractToCreateContractAndCallItOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0",
        ),
        pytest.param(
            1, 0, 0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_contract_to_create_contract_and_call_it_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_static_call_contract_to_create_contract_and_call_it_oog"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
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
    # {(MSTORE 0 0x600c60005566602060406000f060205260076039f3)[[0]](CREATE 1 11 21) (STATICCALL 1000 (SLOAD 0) 0 0 0 0) (IF (EQ (CALLDATALOAD 0) 0) (KECCAK256 0x00 0x2fffff) (GAS) )  }
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x600c60005566602060406000f060205260076039f3)
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x1, offset=0xb, size=0x15))
        + Op.POP(Op.STATICCALL(gas=0x3e8, address=Op.SLOAD(key=0x0), args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.JUMPI(pc=0x40, condition=Op.EQ(Op.CALLDATALOAD(offset=0x0), 0x0))
        + Op.GAS + Op.JUMP(pc=0x48) + Op.JUMPDEST
        + Op.SHA3(offset=0x0, size=0x2fffff) + Op.JUMPDEST + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5f5e100)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(
                storage={0: 0xd2571607e241ecf590ed94b12d87c94babe36db6},
                nonce=1,
            ),
        sender: Account(nonce=1),
        Address("0xd2571607e241ecf590ed94b12d87c94babe36db6"): Account(storage={0: 12}, balance=1, nonce=1),  # noqa: E501
    },
        },
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(storage={0: 0, 2: 0}, nonce=0),
        sender: Account(nonce=1),
        Address("0xd2571607e241ecf590ed94b12d87c94babe36db6"): Account.NONEXISTENT,  # noqa: E501
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
