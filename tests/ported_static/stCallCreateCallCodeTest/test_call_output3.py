"""
Check the output memory after call.

Ported from:
state_tests/stCallCreateCallCodeTest/callOutput3Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCallCreateCallCodeTest/callOutput3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_output3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Check the output memory after call."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
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

    # Source: lll
    # { (MSTORE 0 0x5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6) (CALL 150000 <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0 32) [[ 0 ]] (MLOAD 0)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x5E20A0453CECD065EA59C37AC63E079EE08998B6045136A8CE6635C7912EC0B6,  # noqa: E501
        )
        + Op.POP(
            Op.CALL(
                gas=0x249F0,
                address=0xBCC1197CCD23A97607F2F96D031F3432E0D16A02,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xD4E4BFA87DC8F20706BF63F45861945315BE24F0),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw
    # 0x6001600101600055
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xBCC1197CCD23A97607F2F96D031F3432E0D16A02),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
        value=0x186A0,
    )

    post = {
        target: Account(
            storage={
                0: 0x5E20A0453CECD065EA59C37AC63E079EE08998B6045136A8CE6635C7912EC0B6,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
