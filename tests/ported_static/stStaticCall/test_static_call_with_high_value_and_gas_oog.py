"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callWithHighValueAndGasOOGFiller.json
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
    "000000000000000000000000a5b789cb3b73deb59cef5b261568362db2f967dd",
    "000000000000000000000000be9c847927d7e832ff5655392c160933d99cb4e8",
]

TX_GAS = [3000000]

TX_VALUE = [100000]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callWithHighValueAndGasOOGFiller.json",  # noqa: E501
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
@pytest.mark.slow
def test_static_call_with_high_value_and_gas_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: LLL
    # { (CALL 500000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0x7A120,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x46fcfdfd17a5789b6ab6d7e23f33f4eadecfb5ad"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xAAFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAA,  # noqa: E501
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0xFFFFFFFFFFFFFFFFFFFFFFFF,
                    address=0xD5D9E9E0158920B17B6DF82FAC474B3E2691EE99,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x2,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xa5b789cb3b73deb59cef5b261568362db2f967dd"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xAAFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAA,  # noqa: E501
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0xFFFFFFFFFFFFFFFFFFFFFFFF,
                    address=0xD2B07D10E28B46411527B841F0E0382A8E3BCB80,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x2,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x0: 0x1, 0x1: 0x1},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xbe9c847927d7e832ff5655392c160933d99cb4e8"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=Op.SHA3(offset=0x0, size=0x2FFFFF) + Op.STOP,
        balance=23,
        nonce=0,
        address=Address("0xd2b07d10e28b46411527b841f0e0382a8e3bcb80"),  # noqa: E501
    )
    # Source: raw bytecode
    callee_3 = pre.deploy_contract(
        code=(
            Op.MSTORE8(offset=0x0, value=0x37)
            + Op.RETURN(offset=0x0, size=0x2)
        ),
        balance=23,
        nonce=0,
        address=Address("0xd5d9e9e0158920b17b6df82fac474b3e2691ee99"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006000356207a120f100"
                    )
                ),
                callee: Account(
                    storage={
                        0: 1,
                        1: 0x3700FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    },
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6000527faaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa602052600260006040600073d5d9e9e0158920b17b6df82fac474b3e2691ee996bfffffffffffffffffffffffffa60005560005160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6000527faaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa602052600260006040600073d2b07d10e28b46411527b841f0e0382a8e3bcb806bfffffffffffffffffffffffffa60005560005160015500"  # noqa: E501
                    ),
                ),
                callee_2: Account(code=bytes.fromhex("622fffff60002000")),
                callee_3: Account(code=bytes.fromhex("603760005360026000f3")),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006000356207a120f100"
                    )
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6000527faaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa602052600260006040600073d5d9e9e0158920b17b6df82fac474b3e2691ee996bfffffffffffffffffffffffffa60005560005160015500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6000527faaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa602052600260006040600073d2b07d10e28b46411527b841f0e0382a8e3bcb806bfffffffffffffffffffffffffa60005560005160015500"  # noqa: E501
                    ),
                ),
                callee_2: Account(code=bytes.fromhex("622fffff60002000")),
                callee_3: Account(code=bytes.fromhex("603760005360026000f3")),
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
