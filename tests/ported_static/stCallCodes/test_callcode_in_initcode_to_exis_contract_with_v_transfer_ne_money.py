"""
callcode inside create/create2 contract init to existing contract. callcode with value transfer but not enough balance

Ported from:
state_tests/stCallCodes/callcodeInInitcodeToExisContractWithVTransferNEMoneyFiller.json
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
    "0000000000000000000000001000000000000000000000000000000000000000",
    "0000000000000000000000002000000000000000000000000000000000000000",
]
TX_GAS = [1000000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCallCodes/callcodeInInitcodeToExisContractWithVTransferNEMoneyFiller.json"],
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
def test_callcode_in_initcode_to_exis_contract_with_v_transfer_ne_money(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """callcode inside create/create2 contract init to existing contract."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x1100000000000000000000000000000000000000")
    contract_1 = Address("0x1000000000000000000000000000000000000000")
    contract_2 = Address("0x2000000000000000000000000000000000000000")
    contract_3 = Address("0x1000000000000000000000000000000000000001")
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
        gas_limit=1000000,
    )

    # Source: lll
    # { (CALL 300000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_0 = pre.deploy_contract(
        code=Op.CALL(gas=0x493e0, address=Op.CALLDATALOAD(offset=0x0), value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0x1100000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # {(seq (CREATE 0 0 (lll (seq  [[1]] (CALLCODE 500000 0x1000000000000000000000000000000000000001 1 0 0 0 0)) 0)   )           )}
    contract_1 = pre.deploy_contract(
        code=Op.PUSH1[0x28] + Op.CODECOPY(dest_offset=0x0, offset=0xf, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.CREATE + Op.STOP + Op.INVALID
        + Op.SSTORE(key=0x1, value=Op.CALLCODE(gas=0x7a120, address=0x1000000000000000000000000000000000000001, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # {(seq (CREATE2 0 0 (lll (seq  [[1]] (CALLCODE 500000 0x1000000000000000000000000000000000000001 1 0 0 0 0)) 0)   0)           )}
    contract_2 = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.PUSH1[0x28]
        + Op.CODECOPY(dest_offset=0x0, offset=0x11, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.CREATE2 + Op.STOP + Op.INVALID
        + Op.SSTORE(key=0x1, value=Op.CALLCODE(gas=0x7a120, address=0x1000000000000000000000000000000000000001, value=0x1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address("0x2000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 2 1) }
    contract_3 = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000001"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2386f26fc10000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0x13136008b64ff592819b2fa6d43f2835c452020e"): Account(storage={1: 0, 2: 0}, balance=0, nonce=1),  # noqa: E501
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0xb0de090b1e01bd09ac6b1d9224229302ed48fd47"): Account(storage={1: 0, 2: 0}, balance=0, nonce=1),  # noqa: E501
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
