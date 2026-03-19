"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_Call1024BalanceTooLow2Filler.json
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
    "000000000000000000000000d395a2cb1cb7ef1b90e2edb71fc0a390ecc84fe8",
    "000000000000000000000000e8f28ee50521b0388cf0a623b1a89e43d022c039",
]

TX_GAS = [17592186099592]

TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_Call1024BalanceTooLow2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call1024_balance_too_low2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )
    callee_1 = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: LLL
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=Op.CALLVALUE,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=0xFFFFFFFFFFF,
                    address=0xD395A2CB1CB7EF1B90E2EDB71FC0A390ECC84FE8,
                    args_offset=Op.SLOAD(key=0x0),
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=1024,
        nonce=0,
        address=Address("0xd395a2cb1cb7ef1b90e2edb71fc0a390ecc84fe8"),  # noqa: E501
    )
    pre[callee_1] = Account(balance=7000, nonce=0)
    callee_2 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
            + Op.MSTORE(
                offset=0x20,
                value=Op.STATICCALL(
                    gas=0xFFFFFFFFFFF,
                    address=0xE8F28EE50521B0388CF0A623B1A89E43D022C039,
                    args_offset=Op.MLOAD(offset=0x0),
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=1024,
        nonce=0,
        address=Address("0xe8f28ee50521b0388cf0a623b1a89e43d022c039"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
                callee: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "60016000540160005560006000600060005473d395a2cb1cb7ef1b90e2edb71fc0a390ecc84fe8650ffffffffffffa60015500"  # noqa: E501
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60016000510160005260006000600060005173e8f28ee50521b0388cf0a623b1a89e43d022c039650ffffffffffffa60205200"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "60016000540160005560006000600060005473d395a2cb1cb7ef1b90e2edb71fc0a390ecc84fe8650ffffffffffffa60015500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60016000510160005260006000600060005173e8f28ee50521b0388cf0a623b1a89e43d022c039650ffffffffffffa60205200"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
