"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_RevertDepth2Filler.json
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
    ["tests/static/state_tests/stStaticCall/static_RevertDepth2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_revert_depth2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    callee = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x15b1327fe926a2172adfd10efdef1505c8e15461"),  # noqa: E501
    )
    # Source: LLL
    # { [[0]] (ADD 1 (SLOAD 0)) [[1]] (STATICCALL 150000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0) [[2]] (STATICCALL 150000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0)}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
            + Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=0x249F0,
                    address=0x5DD18F4768E54DE1443F70EC11AD95D5DB424293,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x2,
                value=Op.STATICCALL(
                    gas=0x249F0,
                    address=0xA61140A1C2699A13C619940208A513D42F654E98,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x57c111943c5e6f1817ee85fd1212409b7d1f7f26"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0xC350,
                    address=0x15B1327FE926A2172ADFD10EFDEF1505C8E15461,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x5dd18f4768e54de1443f70ec11ad95d5db424293"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0xC350,
                    address=0x15B1327FE926A2172ADFD10EFDEF1505C8E15461,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SHA3(offset=0x0, size=0x2FFFFF)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xa61140a1c2699a13c619940208a513d42f654e98"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(code=bytes.fromhex("600160015200")),
                contract: Account(
                    storage={0: 1, 1: 1},
                    code=bytes.fromhex(
                        "6000546001016000556000600060006000735dd18f4768e54de1443f70ec11ad95d5db424293620249f0fa600155600060006000600073a61140a1c2699a13c619940208a513d42f654e98620249f0fa60025500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60006000600060007315b1327fe926a2172adfd10efdef1505c8e1546161c350fa50600160015200"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "60006000600060007315b1327fe926a2172adfd10efdef1505c8e1546161c350fa50622fffff60002000"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1706850,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
