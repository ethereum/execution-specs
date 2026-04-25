"""
Test_callcodecallcode_11.

Ported from:
state_tests/stCallDelegateCodesHomestead/callcodecallcode_11Filler.json
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
        "state_tests/stCallDelegateCodesHomestead/callcodecallcode_11Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcode_11(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_callcodecallcode_11."""
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
    # {  (SSTORE 2 1) (SSTORE 4 (CALLER))  (SSTORE 7 (CALLVALUE)) (SSTORE 230 (ADDRESS)) (SSTORE 232 (ORIGIN)) (SSTORE 236 (CALLDATASIZE)) (SSTORE 238 (CODESIZE)) (SSTORE 240 (GASPRICE)) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x2, value=0x1)
        + Op.SSTORE(key=0x4, value=Op.CALLER)
        + Op.SSTORE(key=0x7, value=Op.CALLVALUE)
        + Op.SSTORE(key=0xE6, value=Op.ADDRESS)
        + Op.SSTORE(key=0xE8, value=Op.ORIGIN)
        + Op.SSTORE(key=0xEC, value=Op.CALLDATASIZE)
        + Op.SSTORE(key=0xEE, value=Op.CODESIZE)
        + Op.SSTORE(key=0xF0, value=Op.GASPRICE)
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {  [[ 1 ]] (DELEGATECALL 250000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.DELEGATECALL(
                gas=0x3D090,
                address=addr_2,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {  [[ 0 ]] (DELEGATECALL 350000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0x55730,
                address=addr,
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
        gas_limit=3000000,
    )

    post = {
        target: Account(
            storage={
                0: 1,
                1: 1,
                2: 1,
                4: sender,
                230: target,
                232: sender,
                236: 64,
                238: 34,
                240: 10,
            },
        ),
        addr: Account(storage={1: 0, 2: 0, 4: 0}),
        addr_2: Account(storage={2: 0}),
        sender: Account(storage={1: 0, 2: 0, 4: 0}, nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
