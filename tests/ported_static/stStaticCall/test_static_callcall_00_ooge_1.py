"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_callcall_00_OOGE_1Filler.json
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
    "000000000000000000000000a2ca69f1cf9ffa7a761899e8dd2f941d40326fd6",
    "000000000000000000000000998a75f1a4457fb7b5872c51f34aa7256f732b1e",
]

TX_GAS = [380066]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcall_00_OOGE_1Filler.json",  # noqa: E501
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
def test_static_callcall_00_ooge_1(
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

    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x2, value=0x1)
            + Op.POP(
                Op.STATICCALL(
                    gas=0x186A0,
                    address=0x609E4DFE6190235B9A0362084C741D9EC330FB1E,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x20, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x1d401212ba6c32405b4fdc993079acab6c7aab6f"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1C,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.POP(Op.EXTCODESIZE(address=0x1))
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x0)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x609e4dfe6190235b9a0362084c741d9ec330fb1e"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x249F0,
                    address=0x1D401212BA6C32405B4FDC993079ACAB6C7AAB6F,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x998a75f1a4457fb7b5872c51f34aa7256f732b1e"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x2, value=0x1)
            + Op.POP(
                Op.STATICCALL(
                    gas=0x186A0,
                    address=0xA65F4B36F21EF107A26AB282B736F93D47BF83DE,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x20, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xa122fc55193a6573fa47c988f537ae631e411058"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x249F0,
                    address=0xA122FC55193A6573FA47C988F537AE631E411058,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xa2ca69f1cf9ffa7a761899e8dd2f941d40326fd6"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x2, value=0x1)
            + Op.SSTORE(key=0x5, value=Op.CALLVALUE)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xa65f4b36f21ef107a26ab282b736f93d47bf83de"),  # noqa: E501
    )
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
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600252604060006040600073609e4dfe6190235b9a0362084c741d9ec330fb1e620186a0fa50600160205200"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b00"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6040600060406000731d401212ba6c32405b4fdc993079acab6c7aab6f620249f0fa60005500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6001600252604060006040600073a65f4b36f21ef107a26ab282b736f93d47bf83de620186a0fa50600160205200"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "604060006040600073a122fc55193a6573fa47c988f537ae631e411058620249f0fa60005500"  # noqa: E501
                    ),
                ),
                callee_5: Account(code=bytes.fromhex("60016002553460055500")),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "6001600252604060006040600073609e4dfe6190235b9a0362084c741d9ec330fb1e620186a0fa50600160205200"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b00"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "6040600060406000731d401212ba6c32405b4fdc993079acab6c7aab6f620249f0fa60005500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex(
                        "6001600252604060006040600073a65f4b36f21ef107a26ab282b736f93d47bf83de620186a0fa50600160205200"  # noqa: E501
                    )
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "604060006040600073a122fc55193a6573fa47c988f537ae631e411058620249f0fa60005500"  # noqa: E501
                    )
                ),
                callee_5: Account(code=bytes.fromhex("60016002553460055500")),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000600060006000346000355af1600055600160015500"
                    ),
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
