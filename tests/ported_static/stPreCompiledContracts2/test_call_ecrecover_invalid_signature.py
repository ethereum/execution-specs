"""
CALL to ECREC precompile with input which is a completely invalid signature...

Ported from:
tests/static/state_tests/stPreCompiledContracts2
CallEcrecoverInvalidSignatureFiller.json
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
        "tests/static/state_tests/stPreCompiledContracts2/CallEcrecoverInvalidSignatureFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ecrecover_invalid_signature(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALL to ECREC precompile with input which is a completely invalid..."""
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
    # { (MSTORE 128 0x1122334455667788991011121314151617181920212223242526272829303132) (CALL 300000 1 0 0 128 128 32) [[ 0 ]] (MLOAD 128) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x80,
                value=0x1122334455667788991011121314151617181920212223242526272829303132,  # noqa: E501
            )
            + Op.POP(
                Op.CALL(
                    gas=0x493E0,
                    address=0x1,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x80,
                    ret_offset=0x80,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x80))
            + Op.STOP
        ),
        balance=0x1312D00,
        nonce=0,
        address=Address("0x2b8fd4adb0602fe9ee5823b0576f619daefbd369"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=3652240,
        value=100000,
    )

    post = {
        contract: Account(
            storage={
                0: 0x1122334455667788991011121314151617181920212223242526272829303132,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
