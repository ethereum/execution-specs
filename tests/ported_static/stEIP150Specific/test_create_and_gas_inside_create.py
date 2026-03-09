"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stEIP150Specific/CreateAndGasInsideCreateFiller.json
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
    [
        "tests/static/state_tests/stEIP150Specific/CreateAndGasInsideCreateFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_and_gas_inside_create(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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
    # Source: LLL
    # { [100] (GAS) (MSTORE 0 0x5a60fd55) (SSTORE 11 (CREATE 0 28 4)) (SSTORE 9 (SUB @100 (GAS))) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x64, value=Op.GAS)
            + Op.MSTORE(offset=0x0, value=0x5A60FD55)
            + Op.SSTORE(
                key=0xB, value=Op.CREATE(value=0x0, offset=0x1C, size=0x4)
            )
            + Op.SSTORE(key=0x9, value=Op.SUB(Op.MLOAD(offset=0x64), Op.GAS))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=600000,
    )

    post = {
        contract: Account(
            storage={
                9: 0x129DB,
                11: 0xF1ECF98489FA9ED60A664FC4998DB699CFA39D40,
            },
        ),
        Address("0xf1ecf98489fa9ed60a664fc4998db699cfa39d40"): Account(
            storage={253: 0x83729},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
