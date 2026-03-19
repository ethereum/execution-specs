"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callToDelCallOpCodeCheckFiller.json
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
        "tests/static/state_tests/stStaticCall/static_callToDelCallOpCodeCheckFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call_to_del_call_op_code_check(
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
        gas_limit=10000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xEBAF50DEBF10E08302FE4280C32DF010463CA297,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0x7EF8271E6CDB0A23220B73BF3E9697E173F9D015,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0x692BDB71BF492107772D8FB07345FAA13B37937B,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x114ca039127835ca3472ef43e00d15e2d8623286"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=Op.DELEGATECALL(
                    gas=0x186A0,
                    address=0x114CA039127835CA3472EF43E00D15E2D8623286,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPI(pc=0x36, condition=Op.EQ(0x1, Op.MLOAD(offset=0x0)))
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.JUMP(pc=0x3C)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x692bdb71bf492107772d8fb07345faa13b37937b"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (STATICCALL 100000 (CALLDATALOAD 0) 0 0 0 0)  }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x186A0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x7ef8271e6cdb0a23220b73bf3e9697e173f9d015"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "3273ebaf50debf10e08302fe4280c32df010463ca2971460225760026001556028565b60016001525b33737ef8271e6cdb0a23220b73bf3e9697e173f9d01514604b5760026001556051565b60016001525b3073692bdb71bf492107772d8fb07345faa13b37937b146074576002600155607a565b60016001525b34600014608a5760026001556090565b60016001525b00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "600060006000600073114ca039127835ca3472ef43e00d15e2d8623286620186a0f46000526000516001146036576001600155603c565b60016001525b00"  # noqa: E501
                    )
                ),
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "6000600060006000600035620186a0fa60005500"
                    ),
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "000000000000000000000000692bdb71bf492107772d8fb07345faa13b37937b"
        ),
        gas_limit=1000000,
        value=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
