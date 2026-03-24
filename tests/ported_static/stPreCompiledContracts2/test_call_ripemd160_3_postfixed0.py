"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stPreCompiledContracts2
CallRipemd160_3_postfixed0Filler.json
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
        "tests/static/state_tests/stPreCompiledContracts2/CallRipemd160_3_postfixed0Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ripemd160_3_postfixed0(
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
        gas_limit=10000000,
    )

    # Source: LLL
    # { (MSTORE 0 0xf34578907f00) [[ 2 ]] (CALL 6000 3 0 0 37 0 32) [[ 0 ]] (MLOAD 0)}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0xF34578907F00)
            + Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=0x1770,
                    address=0x3,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x25,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0x1312D00,
        nonce=0,
        address=Address("0x0a7939b337794bf9784ca2edbaccf4c289d2bd69"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=365224,
        value=100000,
    )

    post = {
        contract: Account(
            storage={
                0: 0x7730B4642169B0F16752696DA8DA830A4B429C9D,
                2: 1,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
