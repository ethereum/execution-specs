"""
DELEGATECALL -> DELEGATECALL2 -> CALL -> DELEGATECALL2 -> ...

Ported from:
state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_ABCB_RECURSIVEFiller.json
"""

import pytest
from execution_testing import (
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
    [
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_ABCB_RECURSIVEFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcodecall_abcb_recursive(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """DELEGATECALL -> DELEGATECALL2 -> CALL -> DELEGATECALL2 -> ."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    # Source: lll
    # {  [[ 0 ]] (DELEGATECALL 25000000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0x17D7840,
                address=0xE0B280638526CECD3EC29969B517AEB3FCBB31FA,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x15600A91A7AF84B8C85782714B3391ED5D73F9A0),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (DELEGATECALL 1000000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.DELEGATECALL(
                gas=0xF4240,
                address=0x91A8703C1BEF34C1E76E152C1F7FB8C336C3BE24,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0xE0B280638526CECD3EC29969B517AEB3FCBB31FA),  # noqa: E501
    )
    # Source: lll
    # {  [[ 2 ]] (CALL 500000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x7A120,
                address=0xE0B280638526CECD3EC29969B517AEB3FCBB31FA,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x91A8703C1BEF34C1E76E152C1F7FB8C336C3BE24),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        target: Account(storage={0: 1, 1: 1}),
        addr: Account(storage={1: 0, 2: 0}),
        addr_2: Account(storage={1: 0, 2: 0}),
        sender: Account(storage={1: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
