"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertOpcodeInCreateReturnsFiller.json
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
        "tests/static/state_tests/stRevertTest/RevertOpcodeInCreateReturnsFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_in_create_returns(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x834185262E53584684BF2B72C64E510013C235D0F45E462DB65900455DF45A35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=42949672960,
    )

    # Source: LLL
    # { (seq (CREATE 0 0 (lll (seq (mstore 0 0x112233) (revert 0 32)) 0)) (SSTORE 0 (RETURNDATASIZE)) (STOP) )}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0xD]
            + Op.CODECOPY(dest_offset=0x0, offset=0x15, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.CREATE)
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.STOP
            + Op.STOP
            + Op.INVALID
            + Op.MSTORE(offset=0x0, value=0x112233)
            + Op.REVERT(offset=0x0, size=0x20)
            + Op.STOP
        ),
        storage={0x0: 0x1},
        nonce=0,
        address=Address("0x910073ceed5c2372dc67ffd941b0f148dc4ebaf5"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 32},
                    code=bytes.fromhex(
                        "600d80601560003960006000f0503d6000550000fe6211223360005260206000fd00"  # noqa: E501
                    ),
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
