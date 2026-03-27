"""
A test for (add 1 1) opcode result.

Ported from:
state_tests/stExample/add11_ymlFiller.yml
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
    ["state_tests/stExample/add11_ymlFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_add11_yml(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """A test for (add 1 1) opcode result."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    # Source: lll
    # {
    #    ; Can also add lll style comments here
    #    [[0]] (ADD 1 1)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, 0x1)) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        gas_limit=400000,
        value=0x186A0,
        gas_price=10,
    )

    post = {
        contract_0: Account(
            storage={0: 2},
            code=bytes.fromhex("600160010160005500"),
        ),
        coinbase: Account(nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
        Address(
            "0xe94f5374fce5edbc8e2a8697c15331677e6ebf0b"
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
