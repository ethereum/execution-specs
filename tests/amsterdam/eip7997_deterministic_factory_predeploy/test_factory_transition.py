"""
Fork-transition tests for [EIP-7997: Deterministic Factory Predeploy](https://eips.ethereum.org/EIPS/eip-7997).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Hash,
    Initcode,
    Op,
    Storage,
    Transaction,
    compute_create2_address,
)

from .spec import Spec, ref_spec_7997

REFERENCE_SPEC_GIT_PATH = ref_spec_7997.git_path
REFERENCE_SPEC_VERSION = ref_spec_7997.version

FACTORY = Spec.FACTORY_ADDRESS


@pytest.mark.valid_at_transition_to("EIP7997")
@pytest.mark.pre_alloc_mutable
def test_factory_absent_pre_fork(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Verify pre-Amsterdam blocks observe no contract at the factory address
    (calls to `0x12` look like calls to an empty EOA).

    The test framework auto-allocates the factory at genesis when the
    destination fork is Amsterdam; this test uses `pre_alloc_mutable` to
    clear that allocation so the pre-fork block sees the address as it
    actually was before EIP-7997.

    Note: this test does not assert that the factory APPEARS at the
    Amsterdam-side block because the t8n tool does not invoke apply_fork
    at transition time. With the genesis allocation cleared, the Amsterdam
    block would also observe a missing factory — verifying that case would
    contradict the EIP's intent. Post-fork factory behavior is covered by
    the regular tests in test_factory.py (which rely on the auto-allocated
    predeploy).
    """
    pre[FACTORY] = Account(code=b"", nonce=0, balance=0)

    salt = 0x42
    runtime = Op.STOP
    initcode = Initcode(deploy_code=runtime)
    expected_address = compute_create2_address(FACTORY, salt, initcode)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(1, "call_to_empty_eoa_succeeds"),
            Op.CALL(
                gas=Op.GAS,
                address=FACTORY,
                value=0,
                args_offset=0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x100,
                ret_size=32,
            ),
        )
        + Op.SSTORE(
            storage.store_next(0, "no_returndata"),
            Op.RETURNDATASIZE,
        )
        + Op.STOP,
    )

    pre_block = Block(
        timestamp=14_999,
        txs=[
            Transaction(
                sender=pre.fund_eoa(),
                to=caller,
                data=Hash(salt) + bytes(initcode),
                gas_limit=500_000,
            )
        ],
    )

    blockchain_test(
        pre=pre,
        blocks=[pre_block],
        post={
            caller: Account(storage=storage),
            expected_address: Account.NONEXISTENT,
            FACTORY: Account.NONEXISTENT,
        },
    )
