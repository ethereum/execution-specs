"""
Test_create_and_gas_inside_create_with_mem_expanding_calls.

Ported from:
state_tests/stMemExpandingEIP150Calls/CreateAndGasInsideCreateWithMemExpandingCallsFiller.json
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
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stMemExpandingEIP150Calls/CreateAndGasInsideCreateWithMemExpandingCallsFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_and_gas_inside_create_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_and_gas_inside_create_with_mem_expanding_calls."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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
    # Source: hex
    # 0x5a600a55635a60fd556000526004601c6000f0600b555a600955
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0xA, value=Op.GAS)
        + Op.MSTORE(offset=0x0, value=0x5A60FD55)
        + Op.SSTORE(key=0xB, value=Op.CREATE(value=0x0, offset=0x1C, size=0x4))
        + Op.SSTORE(key=0x9, value=Op.GAS),
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        sender: Account(nonce=1),
        contract_0: Account(
            storage={
                9: 0x75596,
                10: 0x8D5B6,
                11: 0xF1ECF98489FA9ED60A664FC4998DB699CFA39D40,
            },
            nonce=1,
        ),
        compute_create_address(address=contract_0, nonce=0): Account(
            storage={253: 0x7E23D}
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
