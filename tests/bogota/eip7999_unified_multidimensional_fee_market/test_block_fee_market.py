"""
Tests for the EIP-7999 block-level fee market: the header's gas vectors,
per-resource capacity, and the excess gas updates that price each
resource.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Fork,
    Hash,
    Header,
    Op,
    RecipientType,
    Storage,
    Transaction,
    TransactionException,
    add_kzg_version,
)
from execution_testing.test_types.block_types import DEFAULT_BASE_FEE

from ...cancun.eip4844_blobs.spec import Spec as Spec4844
from .conftest import transfer_gas
from .spec import Spec, ref_spec_7999

REFERENCE_SPEC_GIT_PATH = ref_spec_7999.git_path
REFERENCE_SPEC_VERSION = ref_spec_7999.version

pytestmark = pytest.mark.valid_from("EIP7999")

SMALL_GAS_LIMIT = 1_000_000
"""Block EVM gas limit that keeps resource targets within one transaction."""


def transfer_intrinsic_gas(fork: Fork, calldata: bytes) -> int:
    """Return the gas limit a transfer with `calldata` needs."""
    return fork.transaction_intrinsic_cost_calculator()(
        calldata=calldata,
        sends_value=True,
        recipient_type=RecipientType.EOA,
    )


def test_header_gas_used_vector(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    sender: Address,
    recipient: Address,
) -> None:
    """
    The header's gas used vector sums EVM gas, blob gas and calldata gas
    over transactions of every type, with the scalar fields mirroring the
    EVM and blob entries.
    """
    fee_market_calldata = bytes(100)
    multidim_calldata = bytes(50)
    txs = [
        Transaction(
            ty=2,
            sender=sender,
            to=recipient,
            value=1,
            data=fee_market_calldata,
            gas_limit=transfer_intrinsic_gas(fork, fee_market_calldata),
            max_fee_per_gas=10,
            max_priority_fee_per_gas=0,
        ),
        Transaction(
            ty=3,
            sender=sender,
            to=recipient,
            value=1,
            gas_limit=transfer_gas(fork),
            max_fee_per_gas=10,
            max_priority_fee_per_gas=0,
            max_fee_per_blob_gas=10,
            blob_versioned_hashes=add_kzg_version(
                [Hash(1)], Spec4844.BLOB_COMMITMENT_VERSION_KZG
            ),
        ),
        Transaction(
            ty=Spec.MULTIDIM_TX_TYPE,
            sender=sender,
            to=recipient,
            value=1,
            data=multidim_calldata,
            gas_limit=transfer_gas(fork, multidim_calldata),
            max_priority_fees_per_gas=[0],
        ),
    ]
    evm_gas_used = (
        transfer_gas(fork, fee_market_calldata)
        + transfer_gas(fork)
        + transfer_gas(fork, multidim_calldata)
    )
    blob_gas_used = fork.blob_gas_per_blob()
    calldata_gas_used = fork.calldata_gas_calculator()(
        data=fee_market_calldata
    ) + fork.calldata_gas_calculator()(data=multidim_calldata)
    blockchain_test(
        pre=pre,
        post={recipient: Account(balance=1 + len(txs))},
        blocks=[
            Block(
                txs=txs,
                header_verify=Header(
                    gas_used_vector=[
                        evm_gas_used,
                        blob_gas_used,
                        calldata_gas_used,
                    ],
                    gas_used=evm_gas_used,
                    blob_gas_used=blob_gas_used,
                ),
            )
        ],
    )


@pytest.mark.parametrize(
    "overflow",
    [
        pytest.param(False, id="at_limit"),
        pytest.param(True, id="over", marks=pytest.mark.exception_test),
    ],
)
def test_calldata_capacity(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    sender: Address,
    recipient: Address,
    overflow: bool,
) -> None:
    """
    A block's calldata gas is capped at its own limit, a quarter of the
    EVM gas limit, independently of the EVM gas left.
    """
    gas_limit = 400_000
    gas_limits = fork.block_gas_limits_calculator()(gas_limit=gas_limit)
    calldata_gas_limit = gas_limits[Spec.CALLDATA_GAS]
    # Zero bytes cost the fewest gas per byte, so this fills the limit.
    full_calldata = bytes(
        calldata_gas_limit // fork.calldata_gas_calculator()(data=b"\x00")
    )
    assert (
        fork.calldata_gas_calculator()(data=full_calldata)
        == calldata_gas_limit
    ), "test correctness: calldata must fill the limit exactly"
    txs = [
        Transaction(
            ty=2,
            sender=sender,
            to=recipient,
            value=1,
            data=full_calldata,
            gas_limit=transfer_intrinsic_gas(fork, full_calldata),
            max_fee_per_gas=10,
            max_priority_fee_per_gas=0,
        )
    ]
    exception = None
    if overflow:
        exception = TransactionException.CALLDATA_GAS_LIMIT_EXCEEDED
        txs.append(
            Transaction(
                ty=2,
                sender=sender,
                to=recipient,
                value=1,
                data=b"\x00",
                gas_limit=transfer_intrinsic_gas(fork, b"\x00"),
                max_fee_per_gas=10,
                max_priority_fee_per_gas=0,
                error=exception,
            )
        )
    blockchain_test(
        genesis_environment=Environment(gas_limit=gas_limit),
        pre=pre,
        post={} if overflow else {recipient: Account(balance=2)},
        blocks=[
            Block(
                txs=txs,
                exception=exception,
                header_verify=(
                    None
                    if overflow
                    else Header(
                        gas_limits=gas_limits,
                        gas_used_vector=[
                            transfer_gas(fork, full_calldata),
                            0,
                            calldata_gas_limit,
                        ],
                    )
                ),
            )
        ],
    )


def test_evm_base_fee_update(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    sender: Address,
) -> None:
    """
    The EVM base fee moves exponentially with the excess gas: a full
    block raises it by the maximum step and an empty block lowers it back,
    with BASEFEE reporting the price.
    """
    genesis_base_fee = 1000
    gas_limits = fork.block_gas_limits_calculator()(gas_limit=SMALL_GAS_LIMIT)
    excess_gas_calculator = fork.excess_gas_calculator()
    base_fees_calculator = fork.base_fees_calculator()

    genesis_excess_gas = fork.initial_excess_gas_calculator()(
        base_fee_per_gas=genesis_base_fee, excess_blob_gas=0
    )
    block_1_excess_gas = excess_gas_calculator(
        parent_excess_gas=genesis_excess_gas,
        parent_gas_used=[0, 0, 0],
        parent_gas_limits=gas_limits,
    )
    # Block 1 burns its whole EVM limit.
    block_2_excess_gas = excess_gas_calculator(
        parent_excess_gas=block_1_excess_gas,
        parent_gas_used=[SMALL_GAS_LIMIT, 0, 0],
        parent_gas_limits=gas_limits,
    )
    # Block 2 is empty.
    block_3_excess_gas = excess_gas_calculator(
        parent_excess_gas=block_2_excess_gas,
        parent_gas_used=[0, 0, 0],
        parent_gas_limits=gas_limits,
    )
    base_fees = [
        base_fees_calculator(excess_gas=excess)[Spec.EVM_GAS]
        for excess in (
            block_1_excess_gas,
            block_2_excess_gas,
            block_3_excess_gas,
        )
    ]
    assert base_fees[1] > base_fees[0] and base_fees[2] < base_fees[1], (
        "test correctness: the base fee must rise then fall"
    )

    burner = pre.deploy_contract(Op.JUMPDEST + Op.JUMP(0))
    storage = Storage()
    probe = pre.deploy_contract(
        Op.SSTORE(storage.store_next(base_fees[2]), Op.BASEFEE) + Op.STOP
    )
    blockchain_test(
        genesis_environment=Environment(
            gas_limit=SMALL_GAS_LIMIT, base_fee_per_gas=genesis_base_fee
        ),
        pre=pre,
        post={probe: Account(storage=storage)},
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=burner,
                        gas_limit=SMALL_GAS_LIMIT,
                        max_fee_per_gas=2 * genesis_base_fee,
                        max_priority_fee_per_gas=0,
                    )
                ],
                header_verify=Header(
                    excess_gas=block_1_excess_gas,
                    base_fee_per_gas=base_fees[0],
                    gas_used_vector=[SMALL_GAS_LIMIT, 0, 0],
                ),
            ),
            Block(
                txs=[],
                header_verify=Header(
                    excess_gas=block_2_excess_gas,
                    base_fee_per_gas=base_fees[1],
                ),
            ),
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=probe,
                        gas_limit=200_000,
                        max_fee_per_gas=2 * genesis_base_fee,
                        max_priority_fee_per_gas=0,
                    )
                ],
                header_verify=Header(
                    excess_gas=block_3_excess_gas,
                    base_fee_per_gas=base_fees[2],
                ),
            ),
        ],
    )


@pytest.mark.parametrize(
    "blob_base_fee,reserve_path",
    [
        pytest.param(1, False, id="regular_path"),
        pytest.param(100, True, id="reserve_path"),
    ],
)
def test_calldata_reserve_price(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    sender: Address,
    recipient: Address,
    blob_base_fee: int,
    reserve_path: bool,
) -> None:
    """
    Calldata anchors on blob gas: once its base fee times the reserve
    factor falls below the blob base fee, calldata usage below target
    still raises its excess gas instead of lowering it.
    """
    gas_limits = fork.block_gas_limits_calculator()(gas_limit=SMALL_GAS_LIMIT)
    excess_gas_calculator = fork.excess_gas_calculator()
    initial_excess_gas = fork.initial_excess_gas_calculator()
    # Every resource shares the pricing exponential, so the EVM inversion
    # also finds the blob excess that prices at `blob_base_fee`.
    genesis_excess_gas = [
        initial_excess_gas(
            base_fee_per_gas=DEFAULT_BASE_FEE, excess_blob_gas=0
        )[Spec.EVM_GAS],
        initial_excess_gas(base_fee_per_gas=blob_base_fee, excess_blob_gas=0)[
            Spec.EVM_GAS
        ],
        0,
    ]
    block_1_excess_gas = excess_gas_calculator(
        parent_excess_gas=genesis_excess_gas,
        parent_gas_used=[0, 0, 0],
        parent_gas_limits=gas_limits,
    )
    calldata = bytes(2500)
    calldata_gas = fork.calldata_gas_calculator()(data=calldata)
    assert calldata_gas < gas_limits[Spec.CALLDATA_GAS] // (
        Spec.CALLDATA_LIMIT_TARGET_RATIO
    ), "test correctness: calldata usage must stay below target"
    block_1_gas_used = [transfer_gas(fork, calldata), 0, calldata_gas]
    block_2_excess_gas = excess_gas_calculator(
        parent_excess_gas=block_1_excess_gas,
        parent_gas_used=block_1_gas_used,
        parent_gas_limits=gas_limits,
    )
    assert (block_2_excess_gas[Spec.CALLDATA_GAS] > 0) == reserve_path, (
        "test correctness: the reserve path must decide the calldata excess"
    )
    blockchain_test(
        genesis_environment=Environment(
            gas_limit=SMALL_GAS_LIMIT, excess_gas=genesis_excess_gas
        ),
        pre=pre,
        post={recipient: Account(balance=2)},
        blocks=[
            Block(
                txs=[
                    Transaction(
                        ty=2,
                        sender=sender,
                        to=recipient,
                        value=1,
                        data=calldata,
                        gas_limit=transfer_intrinsic_gas(fork, calldata),
                        max_fee_per_gas=10,
                        max_priority_fee_per_gas=0,
                    )
                ],
                header_verify=Header(
                    excess_gas=block_1_excess_gas,
                    gas_used_vector=block_1_gas_used,
                ),
            ),
            Block(txs=[], header_verify=Header(excess_gas=block_2_excess_gas)),
        ],
    )
