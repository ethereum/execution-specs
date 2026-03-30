"""
DELEGATE -> CALLCODE -> CALLCODE -> CODE OOG.

Ported from:
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_OOGEFiller.json
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
    [
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_OOGEFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcallcode_101_ooge(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """DELEGATE -> CALLCODE -> CALLCODE -> CODE OOG."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
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

    # Source: lll
    # {  [[ 0 ]] (DELEGATECALL 800000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0xC3500,
                address=0x913CF7A18F61BAB7BCCF5607DFA9B730C5976000,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x0E7163A4A90126C4A13E52F48E84C74600E844DA),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (CALLCODE 600000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=0x927C0,
                address=0xFCF790146E167FB47D128896C5BA30B0265B1780,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x913CF7A18F61BAB7BCCF5607DFA9B730C5976000),  # noqa: E501
    )
    # Source: lll
    # {  [[ 2 ]] (DELEGATECALL 400000 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 )  [[11]] 1 }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.DELEGATECALL(
                gas=0x61A80,
                address=0x1DD747F92062BB53BB8E867EC2902792435F1748,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0xB, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xFCF790146E167FB47D128896C5BA30B0265B1780),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) (KECCAK256 0x00 0x2fffff) }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x3, value=0x1)
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.STOP,
        nonce=0,
        address=Address(0x1DD747F92062BB53BB8E867EC2902792435F1748),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
    )

    post = {
        target: Account(storage={0: 1, 1: 1, 11: 1}),
        addr: Account(storage={}),
        addr_2: Account(storage={}),
        addr_3: Account(storage={}),
        sender: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
