"""
Test_zero_value_suicide_to_non_zero_balance_oog_revert.

Ported from:
state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToNonZeroBalance_OOGRevertFiller.json
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
        "state_tests/stZeroCallsRevert/ZeroValue_SUICIDE_ToNonZeroBalance_OOGRevertFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_zero_value_suicide_to_non_zero_balance_oog_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_zero_value_suicide_to_non_zero_balance_oog_revert."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    addr_2 = Address(0x9089DA66E8BBC08846842A301905501BC8525DC4)
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { (CALL 50000 <contract:0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]]12 [[3]]12 [[4]]12 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0xC350,
                address=0x888748026558F849C1B2433EA5E1DAF1444DFC60,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x2, value=0xC)
        + Op.SSTORE(key=0x3, value=0xC)
        + Op.SSTORE(key=0x4, value=0xC)
        + Op.STOP,
        nonce=0,
        address=Address(0xA2E25F47A24C66CFEF22D3304777A22D6DD7AD4A),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0x9089DA66E8BBC08846842A301905501BC8525DC4
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x888748026558F849C1B2433EA5E1DAF1444DFC60),  # noqa: E501
    )
    pre[addr_2] = Account(balance=100)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=75000,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={}),
        addr_2: Account(balance=100),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
