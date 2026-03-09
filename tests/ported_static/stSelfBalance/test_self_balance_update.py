"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSelfBalance/selfBalanceUpdateFiller.json
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
    ["tests/static/state_tests/stSelfBalance/selfBalanceUpdateFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_self_balance_update(
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

    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)
    # Source: asm
    # (asm SELFBALANCE DUP1 1 SSTORE 0 0 0 0 1 0 0 CALL POP SELFBALANCE DUP1 2 SSTORE SWAP1 SUB 3 SSTORE)  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SELFBALANCE
            + Op.SSTORE(key=0x1, value=Op.DUP1)
            + Op.POP(
                Op.CALL(
                    gas=0x0,
                    address=0x0,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SELFBALANCE
            + Op.SSTORE(key=0x2, value=Op.DUP1)
            + Op.SWAP1
            + Op.SSTORE(key=0x3, value=Op.SUB)
            + Op.STOP
        ),
        balance=500,
        nonce=0,
        address=Address("0xff44472f5ffdd079c61153f097871f57c1f689ca"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=200000,
    )

    post = {
        contract: Account(storage={1: 500, 2: 499, 3: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
