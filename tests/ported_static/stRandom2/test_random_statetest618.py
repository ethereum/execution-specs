"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom2/randomStatetest618Filler.json
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
    ["tests/static/state_tests/stRandom2/randomStatetest618Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest618(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x9,
                condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLDATALOAD(offset=0x20),
            )
        ),
        balance=46,
        nonce=0,
        address=coinbase,  # noqa: E501
    )
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.SGT(
                Op.CALL(
                    gas=Op.EXTCODESIZE(
                        address=Op.PUSH32[
                            0x10000000000000000000000000000000000000000
                        ],
                    ),
                    address=Op.NUMBER,
                    value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    args_offset=Op.PUSH32[0xC350],
                    args_size=Op.TIMESTAMP,
                    ret_offset=Op.PUSH32[0x0],
                    ret_size=Op.PUSH32[0xC350],
                ),
                Op.PUSH32[0x4F3F701464972E74606D6EA82D4D3080599A0E79],
            )
            + Op.GAS
            + Op.GASPRICE
            + Op.PC
        ),
        nonce=0,
        address=Address("0xce2de07f0af237ed58f6f7e008c3a9d82eb1769a"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                coinbase: Account(
                    code=bytes.fromhex("6000355415600957005b60203560003555")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "7f0000000000000000000000004f3f701464972e74606d6ea82d4d3080599a0e797f000000000000000000000000000000000000000000000000000000000000c3507f0000000000000000000000000000000000000000000000000000000000000000427f000000000000000000000000000000000000000000000000000000000000c3507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff437f00000000000000000000000100000000000000000000000000000000000000003bf1135a3a58"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "7f0000000000000000000000004f3f701464972e74606d6ea82d4d3080599a0e797f0000"  # noqa: E501
            "00000000000000000000000000000000000000000000000000000000c3507f0000000000"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000427f00000000000000"  # noqa: E501
            "0000000000000000000000000000000000000000000000c3507fffffffffffffffffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffffffffffff437f000000000000000000000001"  # noqa: E501
            "00000000000000000000000000000000000000003bf1135a3a58"
        ),
        gas_limit=1024268380,
        value=1398079665,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
