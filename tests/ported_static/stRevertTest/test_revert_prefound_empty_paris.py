"""
Test_revert_prefound_empty_paris.

Ported from:
state_tests/stRevertTest/RevertPrefoundEmpty_ParisFiller.json
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
    ["state_tests/stRevertTest/RevertPrefoundEmpty_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_prefound_empty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_revert_prefound_empty_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x7DB299E0885C85039F56FA504A13DD8CE8A56AA7)
    contract_1 = Address(0xA000000000000000000000000000000000000000)
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
    pre[contract_0] = Account(balance=10)
    # Source: lll
    # { [[0]] (CREATE 0 0 32) [[1]]12 }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0, value=Op.CREATE(value=0x0, offset=0x0, size=0x20)
        )
        + Op.SSTORE(key=0x1, value=0xC)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0xA000000000000000000000000000000000000000),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=Bytes(""),
        gas_limit=940000,
    )

    post = {contract_0: Account(storage={}, code=b"", balance=10, nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
