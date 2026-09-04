"""
TODO revertOpcodeInInit followed by OOG.

Ported from:
state_tests/stRevertTest/RevertOpcodeInInitFiller.json

@manually-enhanced: Do not overwrite. tx gas budget bumped
for EIP-8037 NEW_ACCOUNT state-gas headroom on Amsterdam (post-state
expectations are unchanged on all forks). EIP-7928 block access list
expectations added for the reverted creation.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    BlockAccessListExpectation,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertOpcodeInInitFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="-v1",
        ),
    ],
)
def test_revert_opcode_in_init(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """TODO revertOpcodeInInit followed by OOG."""
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

    tx_data = [
        Op.SSTORE(key=0x0, value=0x1)
        + Op.REVERT(offset=0x0, size=0x1)
        + Op.SSTORE(key=0x1, value=0x11),
    ]
    # EIP-8037 NEW_ACCOUNT + init-code state-gas spill on Amsterdam;
    # pre-EIP-8037 keeps the original 160 000 budget.
    outer_tx_gas = 160_000
    if fork.is_eip_enabled(8037):
        outer_tx_gas = 800_000
    tx_gas = [outer_tx_gas]
    tx_value = [0, 10]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    created = compute_create_address(address=sender, nonce=0)
    post = {
        created: Account.NONEXISTENT,
        sender: Account(nonce=1),
    }

    expected_block_access_list = None
    if fork.is_eip_enabled(7928):
        # The creation address is accessed during transaction setup, so
        # it stays in the block access list after the init code reverts;
        # the reverted SSTORE survives only as a read of its slot.
        expected_block_access_list = BlockAccessListExpectation(
            account_expectations={
                sender: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                created: BalAccountExpectation(
                    storage_reads=[0],
                    storage_changes=[],
                    balance_changes=[],
                    nonce_changes=[],
                    code_changes=[],
                ),
            }
        )

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=expected_block_access_list,
    )
