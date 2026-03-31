"""
Test_create_name_registrator_per_txs_before.

Ported from:
state_tests/stTransitionTest/createNameRegistratorPerTxsBeforeFiller.json
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
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stTransitionTest/createNameRegistratorPerTxsBeforeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_name_registrator_per_txs_before(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_name_registrator_per_txs_before."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.SSTORE(key=0x1, value=0x1)
        + Op.PUSH1[0x10]
        + Op.CODECOPY(dest_offset=0x0, offset=0xC, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP
        + Op.JUMPI(
            pc=0x9,
            condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(
            key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)
        ),
        gas_limit=200000,
        value=0x186A0,
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account(
            storage={1: 1},
            code=bytes.fromhex("396000f3006000355415600957005b60"),
            balance=0x186A0,
            nonce=1,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
