"""
CALLCODE -> DELEGATE -> OOG DELEGATE -> CODE.

Ported from:
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_OOGMBeforeFiller.json
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
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_OOGMBeforeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcodecallcode_011_oogm_before(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALLCODE -> DELEGATE -> OOG DELEGATE -> CODE."""
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
    # {  [[ 0 ]] (CALLCODE 150000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x249F0,
                address=0xB5104F0F7758CE0CAAC73F593C6D63EB9A5EF905,
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
        address=Address(0xA74CA10B765DCDA3B60687F73F2881E2A56EDA64),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (DELEGATECALL 40080 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) [[11]] 1 }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.DELEGATECALL(
                gas=0x9C90,
                address=0xC176D297FF74C0F684B73D6CC8617E7F5FFE34FE,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0xB, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xB5104F0F7758CE0CAAC73F593C6D63EB9A5EF905),  # noqa: E501
    )
    # Source: lll
    # {  (KECCAK256 0x00 0x2fffff) [[ 2 ]] (DELEGATECALL 20020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(Op.SHA3(offset=0x0, size=0x2FFFFF))
        + Op.SSTORE(
            key=0x2,
            value=Op.DELEGATECALL(
                gas=0x4E34,
                address=0xB126C622075B1189FB6C45E851641CFADDF65B36,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xC176D297FF74C0F684B73D6CC8617E7F5FFE34FE),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0xB126C622075B1189FB6C45E851641CFADDF65B36),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=172000,
    )

    post = {
        target: Account(storage={0: 1, 11: 1}),
        addr: Account(storage={}),
        addr_2: Account(storage={}),
        addr_3: Account(storage={}),
        sender: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
