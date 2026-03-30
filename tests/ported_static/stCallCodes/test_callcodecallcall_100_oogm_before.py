"""
Callcode -> call -> oog call -> code.

Ported from:
state_tests/stCallCodes/callcodecallcall_100_OOGMBeforeFiller.json
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
    ["state_tests/stCallCodes/callcodecallcall_100_OOGMBeforeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcall_100_oogm_before(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Callcode -> call -> oog call -> code ."""
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
    # {  [[ 0 ]] (CALLCODE 800000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0xC3500,
                address=0x471072D55A5A95044C2326F0E94A6D8DF5B8089E,
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
        address=Address(0x9E57433AFAFF8A546FBC43CF0330AFB6561DC550),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (CALL 600000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) [[11]] 1 }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0x927C0,
                address=0x4A780315E172DB6C0A08FE70FF4362B0E061B668,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0xB, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x471072D55A5A95044C2326F0E94A6D8DF5B8089E),  # noqa: E501
    )
    # Source: lll
    # {  (KECCAK256 0x00 0x2fffff) [[ 2 ]] (CALL 400000 <contract:0x1000000000000000000000000000000000000003> 0 0 64 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(Op.SHA3(offset=0x0, size=0x2FFFFF))
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x61A80,
                address=0xB126C622075B1189FB6C45E851641CFADDF65B36,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x4A780315E172DB6C0A08FE70FF4362B0E061B668),  # noqa: E501
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
        gas_limit=1000000,
    )

    post = {
        target: Account(storage={0: 1, 11: 1}),
        addr: Account(storage={}),
        addr_2: Account(storage={}),
        addr_3: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
