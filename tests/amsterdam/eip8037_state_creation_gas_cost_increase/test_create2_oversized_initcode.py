"""
Test CREATE2 with oversized initcode and state gas spillover.

When a CREATE transaction's constructor executes an internal CREATE2
whose initcode exceeds the EIP-7954 max_initcode_size, the CREATE2
charges GAS_CREATE state gas (112 * cpsb) as a pre-state cost BEFORE
the initcode size validation. If the state gas reservoir is empty
(tx.gas_limit <= TX_MAX_GAS_LIMIT), this state gas spills into
gas_left.

The size check then fails with a hard error, aborting the constructor.
The key invariant: state gas charged from gas_left (spillover) must
still count in the state dimension for block-level 2D accounting.
Per EIP-8037 line 117, the cost TYPE determines the accounting
dimension, not the SOURCE of the gas.

Regression tests for geth divergence at bal-devnet-3 block 1031
(2026-04-08), where geth misclassified spilled CREATE2 state gas
after a hard error, producing block gas_used that was 112 * cpsb
= 131,488 too low.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Fork,
    Header,
    Op,
    Transaction,
    compute_create_address,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


def _constructor_with_create2(initcode_size: int) -> bytes:
    """
    Build constructor bytecode that does:
      CALLDATACOPY(0, 0, initcode_size)
      CREATE2(value=0, offset=0, size=initcode_size, salt=0)
      STOP

    The CREATE2 initcode is `initcode_size` bytes of zeros from memory.
    """
    return bytes(
        Op.CALLDATACOPY(0, 0, initcode_size)
        + Op.CREATE2(0, 0, initcode_size, 0)
        + Op.STOP
    )


@pytest.mark.parametrize(
    "initcode_size_delta",
    [
        pytest.param(0, id="at_max_initcode_size"),
        pytest.param(1, id="one_over_max_initcode_size"),
        pytest.param(0x10000, id="double_max_initcode_size"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_create2_initcode_size_boundary_spillover(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode_size_delta: int,
) -> None:
    """
    Test GAS_CREATE state gas at the EIP-7954 initcode size boundary.

    A CREATE tx (gas_limit <= TX_MAX_GAS_LIMIT, so reservoir=0)
    deploys a constructor that attempts CREATE2 with initcode at or
    above max_initcode_size. The CREATE2 charges GAS_CREATE state gas
    as a pre-state cost that spills into gas_left.

    At the boundary: CREATE2 proceeds normally (initcode executes).
    Over the boundary: hard error aborts the constructor. The spilled
    GAS_CREATE state gas must still count in the state dimension.

    This is the core scenario from bal-devnet-3 block 1031.
    """
    max_initcode = fork.max_initcode_size()
    initcode_size = max_initcode + initcode_size_delta
    constructor = _constructor_with_create2(initcode_size)
    exceeds_limit = initcode_size_delta > 0

    sender = pre.fund_eoa(10**21)
    created = compute_create_address(address=sender, nonce=0)

    tx = Transaction(
        to=None,
        data=constructor,
        value=0,
        gas_limit=3_000_000,  # Below TX_MAX_GAS_LIMIT → reservoir=0
        sender=sender,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    if exceeds_limit:
        # Hard error aborts constructor → no contract
        post = {created: Account.NONEXISTENT}
    else:
        # CREATE2 initcode (zeros) halts immediately → empty
        # deployed contract from CREATE2, outer constructor deploys
        post = {created: Account(nonce=2)}

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post=post,
    )


@pytest.mark.valid_from("Amsterdam")
def test_create2_oversized_initcode_mixed_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block gas_used with mixed CREATE txs including one whose
    constructor has an internal CREATE2 exceeding max_initcode_size.

    Reproduces the bal-devnet-3 block 1031 pattern:
      TX[0]: Successful CREATE (simple constructor)
      TX[1]: CREATE whose constructor does CREATE2 with oversized
             initcode → hard error → constructor fails
      TX[2]: Successful CREATE (simple constructor)

    TX[1]'s internal CREATE2 charges GAS_CREATE state gas (112*cpsb)
    that spills into gas_left (reservoir=0). After the hard error,
    this must still count as state gas in block_state_gas_used.

    If the spilled state gas is misclassified, block gas_used =
    max(block_regular, block_state) differs by exactly 112 * cpsb.
    """
    max_initcode = fork.max_initcode_size()
    oversized = max_initcode * 2

    # TX[0]: Simple successful CREATE
    sender_0 = pre.fund_eoa(10**21)
    tx0 = Transaction(
        to=None,
        data=bytes(Op.MSTORE8(0, 0x60) + Op.RETURN(0, 1)),
        value=0,
        gas_limit=3_000_000,
        sender=sender_0,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    # TX[1]: Constructor with internal CREATE2 that hard-errors
    sender_1 = pre.fund_eoa(10**21)
    tx1 = Transaction(
        to=None,
        data=_constructor_with_create2(oversized),
        value=0,
        gas_limit=3_000_000,
        sender=sender_1,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    # TX[2]: Another simple successful CREATE
    sender_2 = pre.fund_eoa(10**21)
    tx2 = Transaction(
        to=None,
        data=bytes(Op.MSTORE8(0, 0x00) + Op.RETURN(0, 1)),
        value=0,
        gas_limit=3_000_000,
        sender=sender_2,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    created_0 = compute_create_address(address=sender_0, nonce=0)
    created_1 = compute_create_address(address=sender_1, nonce=0)
    created_2 = compute_create_address(address=sender_2, nonce=0)

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx0, tx1, tx2])],
        post={
            created_0: Account(nonce=1),
            created_1: Account.NONEXISTENT,
            created_2: Account(nonce=1),
        },
    )


@pytest.mark.valid_from("Amsterdam")
def test_create2_oversized_initcode_with_reservoir(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Contrast: CREATE2 oversized initcode with reservoir available.

    Same scenario as spillover test but tx.gas_limit > TX_MAX_GAS_LIMIT,
    so state gas is drawn from the reservoir instead of gas_left.
    Verifies the accounting is correct regardless of gas source.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    max_initcode = fork.max_initcode_size()
    create_state_gas = fork.create_state_gas(code_size=0)
    oversized = max_initcode * 2

    sender = pre.fund_eoa(10**21)
    created = compute_create_address(address=sender, nonce=0)

    # Gas above cap → reservoir has state gas for the outer CREATE
    # The inner CREATE2's GAS_CREATE also draws from reservoir
    tx = Transaction(
        to=None,
        data=_constructor_with_create2(oversized),
        value=0,
        gas_limit=gas_limit_cap + create_state_gas * 2,
        sender=sender,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    # Hard error still aborts constructor
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={created: Account.NONEXISTENT},
    )
