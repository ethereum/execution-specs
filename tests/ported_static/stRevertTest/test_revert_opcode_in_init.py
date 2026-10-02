"""
Verify REVERT in create-tx initcode discards the account (unreachable
ops after REVERT do not run).

Ported from:
state_tests/stRevertTest/RevertOpcodeInInitFiller.json

@manually-enhanced: Do not overwrite. Dropped the tight gas_limit and
port boilerplate so the create-tx runs to REVERT on every fork from
Byzantium; EIP-7928 block access list expectations cover the reverted
creation path.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BalNonceChange,
    BlockAccessListExpectation,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Unreachable after REVERT — kept so a client that continues past REVERT fails.
INITCODE = (
    Op.SSTORE(key=0x0, value=0x1)
    + Op.REVERT(offset=0x0, size=0x1)
    + Op.SSTORE(key=0x1, value=0x11)
)


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertOpcodeInInitFiller.json"],
)
@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize("tx_value", [0, 10], ids=["v0", "v1"])
def test_revert_opcode_in_init(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tx_value: int,
) -> None:
    """REVERT in initcode leaves no created account; sender nonce advances."""
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=None,
        data=INITCODE,
        value=tx_value,
        protected=fork.supports_protected_txs(),
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
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=expected_block_access_list,
    )
