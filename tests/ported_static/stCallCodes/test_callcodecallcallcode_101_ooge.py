"""
callcode -> call -> callcode -> code oog.

Ported from:
tests/static/state_tests/stCallCodes/callcodecallcallcode_101_OOGEFiller.json
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
        "tests/static/state_tests/stCallCodes/callcodecallcallcode_101_OOGEFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcallcode_101_ooge(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Callcode -> call -> callcode -> code oog."""
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

    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x3, value=0x1)
            + Op.SHA3(offset=0x0, size=0x2FFFFF)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1dd747f92062bb53bb8e867ec2902792435f1748"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.CALLCODE(
                    gas=0x61A80,
                    address=0x1DD747F92062BB53BB8E867EC2902792435F1748,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0xB, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x3568ec0dda63b253e338fbc4990869fd168ab515"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALLCODE 800000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0xC3500,
                    address=0xBBDCE54B3C571B853032CB3A637E8F5B81DBAF0D,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x9e57433afaff8a546fbc43cf0330afb6561dc550"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=0x927C0,
                    address=0x3568EC0DDA63B253E338FBC4990869FD168AB515,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xbbdce54b3c571b853032cb3a637e8f5b81dbaf0d"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1000000,
    )

    post = {
        callee_1: Account(storage={11: 1}),
        contract: Account(storage={0: 1, 1: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
