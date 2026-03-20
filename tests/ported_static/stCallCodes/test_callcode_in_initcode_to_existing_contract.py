"""
callcode inside create/create2 contract init to existing contract.

Ported from:
tests/static/state_tests/stCallCodes
callcodeInInitcodeToExistingContractFiller.json
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
    "0000000000000000000000001000000000000000000000000000000000000000",
    "0000000000000000000000002000000000000000000000000000000000000000",
]

TX_GAS = [1000000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCallCodes/callcodeInInitcodeToExistingContractFiller.json",  # noqa: E501
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
def test_callcode_in_initcode_to_existing_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Callcode inside create/create2 contract init to existing contract."""
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
        gas_limit=1000000,
    )

    # Source: LLL
    # {(seq (CREATE 1 0 (lll (seq  [[1]] (CALLCODE 50000 0x1000000000000000000000000000000000000001 1 0 0 0 0)) 0)   )           )}  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x27]
            + Op.CODECOPY(dest_offset=0x0, offset=0xF, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x1]
            + Op.CREATE
            + Op.STOP
            + Op.INVALID
            + Op.SSTORE(
                key=0x1,
                value=Op.CALLCODE(
                    gas=0xC350,
                    address=0x1000000000000000000000000000000000000001,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0x2710,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (SSTORE 2 1) }
    pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # { (CALL 300000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0x493E0,
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
        address=Address("0x1100000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # {(seq (CREATE2 1 0 (lll (seq  [[1]] (CALLCODE 50000 0x1000000000000000000000000000000000000001 1 0 0 0 0)) 0)   0)           )}  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0x27]
            + Op.CODECOPY(dest_offset=0x0, offset=0x11, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x1]
            + Op.CREATE2
            + Op.STOP
            + Op.INVALID
            + Op.SSTORE(
                key=0x1,
                value=Op.CALLCODE(
                    gas=0xC350,
                    address=0x1000000000000000000000000000000000000001,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0x2710,
        nonce=0,
        address=Address("0x2000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2386F26FC10000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x13136008b64ff592819b2fa6d43f2835c452020e"): Account(
                    storage={1: 1, 2: 1}, balance=1
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address("0x11b62573be8f72b4085bafe5b675b3e7f08ed522"): Account(
                    storage={1: 1, 2: 1}, balance=1
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
