"""
Test_extcodesize_to_epmty_paris.

Ported from:
state_tests/stEIP158Specific/EXTCODESIZE_toEpmtyParisFiller.json

@manually-enhanced: Do not overwrite. The measured slot captures the
regular gas of an EXTCODESIZE on a cold (empty, code-less) EOA plus
the SSTORE that clears a populated slot to its (zero) result.
EIP-8038 reprices the cold account access and adds a second
WARM_ACCESS for the code read (EXTCODESIZE delta), and spills the
cold SSTORE-clear's state-gas into regular gas (the reservoir is
empty). Both deltas are derived from the fork's own opcode gas model,
so each is exactly 0 before EIP-8038.
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
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP158Specific/EXTCODESIZE_toEpmtyParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_extcodesize_to_epmty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_extcodesize_to_epmty_paris."""
    # EIP-8038 deltas, each 0 before EIP-8038. EXTCODESIZE gains the
    # cold account reprice plus a second WARM_ACCESS for the code read;
    # the cold SSTORE-clear (nonzero -> 0) spills its state-gas back
    # into regular gas.
    extcodesize_delta = (
        Op.EXTCODESIZE.with_metadata(address_warm=False).gas_cost(fork) - 2600
    )
    cold_clear_sstore_delta = (
        Op.SSTORE.with_metadata(
            key_warm=False, original_value=1, current_value=1, new_value=0
        ).gas_cost(fork)
        - 5000
    )
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    addr = pre.fund_eoa(amount=10)  # noqa: F841
    # Source: lll
    # { [0](GAS) [[1]] (EXTCODESIZE <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>) [[100]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x1, value=Op.EXTCODESIZE(address=addr))
        + Op.SSTORE(key=0x64, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        storage={1: 1536},
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        addr: Account(storage={}, code=b"", balance=10, nonce=0),
        target: Account(
            storage={100: 7617 + extcodesize_delta + cold_clear_sstore_delta}
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
