"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_callcode_checkPCFiller.json
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcode_checkPCFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcode_check_pc(
    state_test: StateTestFiller,
    pre: Alloc,
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
        gas_limit=3000000000,
    )

    pre.deploy_contract(
        code=bytes.fromhex("00"),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x0fa032348694ad238cccc23b44fe450999cdc0fe"),  # noqa: E501
    )
    # Source: LLL
    # { (STATICCALL 1000000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[3]] (PC)}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0xF4240,
                    address=0xFA032348694AD238CCCC23B44FE450999CDC0FE,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x3, value=Op.PC)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x6a1bc409e9c1914f80d4a72653f9d1c4a53c0343"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1100000,
    )

    post = {
        contract: Account(storage={3: 35}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
