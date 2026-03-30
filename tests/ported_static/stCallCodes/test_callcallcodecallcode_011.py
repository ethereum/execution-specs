"""
Call -> callcode ->  callcode -> code, check params.

Ported from:
state_tests/stCallCodes/callcallcodecallcode_011Filler.json
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
    ["state_tests/stCallCodes/callcallcodecallcode_011Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcodecallcode_011(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Call -> callcode ->  callcode -> code, check params."""
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
    # {  [[ 0 ]] (CALL 350000 <contract:0x1000000000000000000000000000000000000001> 1 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x55730,
                address=0x4C0DE71B93DE6B7055A3686E4BF93ADD02B39ED8,
                value=0x1,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xEB09FF15547417853F6F4B240B8804769C37B0F1),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (CALLCODE 300000 <contract:0x1000000000000000000000000000000000000002> 2 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=0x493E0,
                address=0xFFFFAEB931552E5F094CA96A70BE612DA56B887,
                value=0x2,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x4C0DE71B93DE6B7055A3686E4BF93ADD02B39ED8),  # noqa: E501
    )
    # Source: lll
    # {  [[ 2 ]] (CALLCODE 250000 <contract:0x1000000000000000000000000000000000000003> 3 0 64 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.CALLCODE(
                gas=0x3D090,
                address=0x181B4ED322E192361633CC3C0A418F259AB0CF4B,
                value=0x3,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x0FFFFAEB931552E5F094CA96A70BE612DA56B887),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) (SSTORE 4 (CALLER)) (SSTORE 7 (CALLVALUE)) (SSTORE 330 (ADDRESS)) (SSTORE 332 (ORIGIN)) (SSTORE 336 (CALLDATASIZE)) (SSTORE 338 (CODESIZE)) (SSTORE 340 (GASPRICE))}  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x3, value=0x1)
        + Op.SSTORE(key=0x4, value=Op.CALLER)
        + Op.SSTORE(key=0x7, value=Op.CALLVALUE)
        + Op.SSTORE(key=0x14A, value=Op.ADDRESS)
        + Op.SSTORE(key=0x14C, value=Op.ORIGIN)
        + Op.SSTORE(key=0x150, value=Op.CALLDATASIZE)
        + Op.SSTORE(key=0x152, value=Op.CODESIZE)
        + Op.SSTORE(key=0x154, value=Op.GASPRICE)
        + Op.STOP,
        nonce=0,
        address=Address(0x181B4ED322E192361633CC3C0A418F259AB0CF4B),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {
        addr: Account(
            storage={
                1: 1,
                2: 1,
                3: 1,
                4: 0x4C0DE71B93DE6B7055A3686E4BF93ADD02B39ED8,
                7: 3,
                330: 0x4C0DE71B93DE6B7055A3686E4BF93ADD02B39ED8,
                332: 0xEBAF50DEBF10E08302FE4280C32DF010463CA297,
                336: 64,
                338: 39,
                340: 10,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
