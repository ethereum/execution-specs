"""
check output memory after callcode.

Ported from:
tests/static/state_tests/stCallCreateCallCodeTest
callcodeOutput3partialFiller.json
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
        "tests/static/state_tests/stCallCreateCallCodeTest/callcodeOutput3partialFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_output3partial(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Check output memory after callcode."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # { (MSTORE 0 0x5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6) (CALLCODE 150000 <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0 10) [[ 0 ]] (MLOAD 0)}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x5E20A0453CECD065EA59C37AC63E079EE08998B6045136A8CE6635C7912EC0B6,  # noqa: E501
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=0x249F0,
                    address=0xBCC1197CCD23A97607F2F96D031F3432E0D16A02,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0xA,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x8e33b4f8eb53a43a1e8ef9b4b46a65fb94fef790"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xbcc1197ccd23a97607f2f96d031f3432e0d16a02"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1000000,
        value=100000,
    )

    post = {
        contract: Account(
            storage={
                0: 0x5E20A0453CECD065EA59C37AC63E079EE08998B6045136A8CE6635C7912EC0B6,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
