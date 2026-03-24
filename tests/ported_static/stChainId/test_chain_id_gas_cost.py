"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stChainId/chainIdGasCostFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stChainId/chainIdGasCostFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_chain_id_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    # Source: asm
    # (asm GAS CHAINID GAS SWAP1 POP SWAP1 SUB 2 SWAP1 SUB 0x01 SSTORE)
    contract = pre.deploy_contract(
        code=(
            Op.GAS
            + Op.CHAINID
            + Op.GAS
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.SUB
            + Op.PUSH1[0x2]
            + Op.SWAP1
            + Op.SSTORE(key=0x1, value=Op.SUB)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x53f64910db5c1bbb54ccb272c0e28bd47249ba9b"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
    )

    post = {
        contract: Account(storage={1: 2}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
