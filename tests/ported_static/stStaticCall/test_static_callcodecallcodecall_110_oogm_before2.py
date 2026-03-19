"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcodecallcodecall_110_OOGMBefore2Filler.json
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
    "",
    "",
]

TX_GAS = [172000]

TX_VALUE = [0, 1, 2]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMBefore2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 1, id="case1"),
        pytest.param(2, 0, 2, id="case2"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcodecallcodecall_110_oogm_before2(
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
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALLCODE 150000 <contract:0x1000000000000000000000000000000000000001> (CALLVALUE) 0 64 0 64 ) [[ 1 ]] 1}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0x249F0,
                    address=0x861E86C681836FF531A2F84C5CDDE43E28E1D234,
                    value=Op.CALLVALUE,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x45f35e7e68477a74b163dd6e4eb2833fb1979873"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0x9C90,
                address=0xF32619344056AD22A07F10433F70165CE82D9273,
                value=Op.SUB(Op.CALLVALUE, 0x1),
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x861e86c681836ff531a2f84c5cdde43e28e1d234"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    callee_2 = pre.deploy_contract(
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
            + Op.STATICCALL(
                gas=0x4E34,
                address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xf32619344056ad22a07f10433f70165ce82d9273"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160035200")),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "60406000604060003473861e86c681836ff531a2f84c5cdde43e28e1d234620249f0f2600055600160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60406000604060006001340373f32619344056ad22a07f10433f70165ce82d9273619c90f200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b604060006040600073335c5531b84765a7626e6e76688f18b81be5259c614e34fa00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 1},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160035200")),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "60406000604060003473861e86c681836ff531a2f84c5cdde43e28e1d234620249f0f2600055600160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60406000604060006001340373f32619344056ad22a07f10433f70165ce82d9273619c90f200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b604060006040600073335c5531b84765a7626e6e76688f18b81be5259c614e34fa00"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 2},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160035200")),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "60406000604060003473861e86c681836ff531a2f84c5cdde43e28e1d234620249f0f2600055600160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60406000604060006001340373f32619344056ad22a07f10433f70165ce82d9273619c90f200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "5b61c3506080511015601c5760013b506001608051016080526000565b604060006040600073335c5531b84765a7626e6e76688f18b81be5259c614e34fa00"  # noqa: E501
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
