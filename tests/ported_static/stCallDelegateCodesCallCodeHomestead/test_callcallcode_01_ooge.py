"""
CALLCODE -> DELEGATE -> CODE OOG.

Ported from:
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcode_01_OOGEFiller.json
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
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcode_01_OOGEFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcode_01_ooge(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALLCODE -> DELEGATE -> CODE OOG."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  (SSTORE 2 1) (KECCAK256 0x00 0x2fffff) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x2, value=0x1)
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {  [[ 1 ]] (DELEGATECALL 600000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) [[11]] 1 }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.DELEGATECALL(
                gas=0x927C0,
                address=addr_2,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0xB, value=0x1)
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {  [[ 0 ]] (CALLCODE 800000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0xC3500,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
    )

    post = {
        target: Account(storage={0: 1, 11: 1}),
        addr: Account(storage={}),
        addr_2: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
