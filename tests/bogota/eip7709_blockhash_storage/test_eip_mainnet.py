"""
Mainnet marked execute checklist tests for
[EIP-7709: Read BLOCKHASH from storage and update cost](https://eips.ethereum.org/EIPS/eip-7709).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    CodeGasMeasure,
    Fork,
    Op,
    Transaction,
)

from .spec import ref_spec_7709

REFERENCE_SPEC_GIT_PATH = ref_spec_7709.git_path
REFERENCE_SPEC_VERSION = ref_spec_7709.version

pytestmark = [pytest.mark.valid_at("EIP7709"), pytest.mark.mainnet]


def test_blockhash_storage_mainnet(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Mainnet smoke test for EIP-7709: executes a cold and warm in-bounds
    ``BLOCKHASH(0)`` alongside an out-of-bounds ``BLOCKHASH(NUMBER)`` and
    asserts their exact gas costs and non-zero parent hash resolution.
    """
    cold_gas = Op.BLOCKHASH(key_warm=False, in_bounds=True).gas_cost(fork)
    warm_gas = Op.BLOCKHASH(key_warm=True, in_bounds=True).gas_cost(fork)
    oob_gas = Op.BLOCKHASH(in_bounds=False).gas_cost(fork)

    measured_in_bounds = Op.BLOCKHASH(0)
    in_bounds_overhead = measured_in_bounds.gas_cost(fork) - cold_gas

    measured_oob = Op.BLOCKHASH(Op.NUMBER)
    oob_overhead = Op.NUMBER.gas_cost(fork)

    code = (
        CodeGasMeasure(
            code=measured_in_bounds,
            overhead_cost=in_bounds_overhead,
            extra_stack_items=1,
            sstore_key=0,
        )
        + CodeGasMeasure(
            code=measured_in_bounds,
            overhead_cost=in_bounds_overhead,
            extra_stack_items=1,
            sstore_key=1,
        )
        + CodeGasMeasure(
            code=measured_oob,
            overhead_cost=oob_overhead,
            extra_stack_items=1,
            sstore_key=2,
        )
        + Op.SSTORE(3, Op.ISZERO(Op.BLOCKHASH(0)))
    )
    contract = pre.deploy_contract(code=code, storage={3: 0xDEAD})
    tx = Transaction(
        ty=0x02,
        sender=pre.fund_eoa(),
        to=contract,
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={
            contract: Account(
                storage={
                    0: cold_gas,
                    1: warm_gas,
                    2: oob_gas,
                    3: 0,
                }
            )
        },
    )
