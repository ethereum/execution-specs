"""
Test_extcodesize_to_non_existent.

Ported from:
state_tests/stEIP158Specific/EXTCODESIZE_toNonExistentFiller.json

@manually-enhanced: Do not overwrite. The measured slot captures the
regular gas of an EXTCODESIZE on a cold, non-existent address plus the
SSTORE that stores its (zero) result. EIP-8038 reprices the cold
account access and adds a second WARM_ACCESS for the code read
(EXTCODESIZE delta), and reprices the cold value-unchanged SSTORE.
Both deltas are derived from the fork's own opcode gas model, so each
is exactly 0 before EIP-8038.
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
from execution_testing.forks import Cancun, Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP158Specific/EXTCODESIZE_toNonExistentFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_extcodesize_to_non_existent(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_extcodesize_to_non_existent."""
    # EIP-8038 deltas, each 0 before EIP-8038. EXTCODESIZE gains the
    # cold account reprice plus a second WARM_ACCESS for the code read;
    # the cold value-unchanged SSTORE gains its own reprice.
    cold_extcodesize = Op.EXTCODESIZE.with_metadata(address_warm=False)
    cancun_extcodesize_cost = cold_extcodesize.gas_cost(Cancun)
    extcodesize_delta = (
        cold_extcodesize.gas_cost(fork) - cancun_extcodesize_cost
    )
    cold_noop_sstore = Op.SSTORE.with_metadata(
        key_warm=False, original_value=0, current_value=0, new_value=0
    )
    cancun_noop_sstore_cost = cold_noop_sstore.gas_cost(Cancun)
    cold_noop_sstore_delta = (
        cold_noop_sstore.gas_cost(fork) - cancun_noop_sstore_cost
    )
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
    # Source: lll
    # { [0](GAS) [[1]] (EXTCODESIZE 0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b) [[100]] (SUB @0 (GAS)) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(
            key=0x1,
            value=Op.EXTCODESIZE(
                address=0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B
            ),
        )
        + Op.SSTORE(key=0x64, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
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
        Address(
            0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B
        ): Account.NONEXISTENT,
        contract_0: Account(
            storage={100: 4817 + extcodesize_delta + cold_noop_sstore_delta}
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
