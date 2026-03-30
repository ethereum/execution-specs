"""
Test_delegate_call_on_eip.

Ported from:
state_tests/stEIP150Specific/DelegateCallOnEIPFiller.json
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
    ["state_tests/stEIP150Specific/DelegateCallOnEIPFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegate_call_on_eip(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_delegate_call_on_eip."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
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
    # { [8] (GAS) (SSTORE 9 (DELEGATECALL 600000 <contract:0x1000000000000000000000000000000000000105> 0 0 0 0)) [[8]] (SUB @8 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x8, value=Op.GAS)
        + Op.SSTORE(
            key=0x9,
            value=Op.DELEGATECALL(
                gas=0x927C0,
                address=0xFD59ABAE521384B5731AC657616680219FBC423D,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x8, value=Op.SUB(Op.MLOAD(offset=0x8), Op.GAS))
        + Op.STOP,
        nonce=0,
        address=Address(0x90BC108216940A7DDAF3BA6624F2FDBE4C5E83DC),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x12) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x12) + Op.STOP,
        nonce=0,
        address=Address(0xFD59ABAE521384B5731AC657616680219FBC423D),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {target: Account(storage={0: 18, 8: 46841, 9: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
