"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcodecallcallcode_101Filler.json
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


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcodecallcallcode_101Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcodecallcallcode_101(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
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
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x2a142c79a9b097c111ce945214226126b75e332c"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (DELEGATECALL 350000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 1 ]] 1 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.DELEGATECALL(
                    gas=0x55730,
                    address=0xF553D6B8627C39028BD1E05A4F55E2A4B3042A1D,
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
        address=Address("0x4eef7e2b5ae9be0fc5b43dc4fe39195a1ae10fc4"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x1)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0x3D090,
                    address=0x2A142C79A9B097C111CE945214226126B75E332C,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x1F, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x999e3c988e5fdf24adf774e3502f0095e6530b72"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    callee_2 = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x1)
            + Op.POP(
                Op.STATICCALL(
                    gas=0x493E0,
                    address=0x999E3C988E5FDF24ADF774E3502F0095E6530B72,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x1F, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xf553d6b8627c39028bd1e05a4f55e2a4b3042a1d"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160015200")),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "604060006040600073f553d6b8627c39028bd1e05a4f55e2a4b3042a1d62055730f4600055600160015500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60016001526040600060406000732a142c79a9b097c111ce945214226126b75e332c6203d090f4506001601f5200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6001600152604060006040600073999e3c988e5fdf24adf774e3502f0095e6530b72620493e0fa506001601f5200"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=3000000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
