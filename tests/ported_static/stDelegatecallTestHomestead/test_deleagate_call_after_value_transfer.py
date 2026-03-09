"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stDelegatecallTestHomestead
deleagateCallAfterValueTransferFiller.json
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
        "tests/static/state_tests/stDelegatecallTestHomestead/deleagateCallAfterValueTransferFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_deleagate_call_after_value_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x3722FAAB4D25B944622D559EA4BCF38B4BCF3CAF07A6D2C6FD99321C1A66C974
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.CALLVALUE)
            + Op.SSTORE(key=0x1, value=Op.CALLER)
            + Op.SSTORE(key=0x2, value=Op.CALLDATALOAD(offset=0x0))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x0346aa231cb52f55ddf201dc19ca469cc73e6495"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2386F26FC10000)
    # Source: LLL
    # { (MSTORE 0 0x01) (DELEGATECALL 100000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x1)
            + Op.DELEGATECALL(
                gas=0x186A0,
                address=0x346AA231CB52F55DDF201DC19CA469CC73E6495,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0x10C8E0,
        nonce=0,
        address=Address("0xdd657898b318b3d967472eaa82bb75c4141b6735"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=453081,
    )

    post = {
        contract: Account(
            storage={
                1: 0x6FDA566D1950D7E0A4DAC1DE87109B2CA7D12DA4,
                2: 1,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
