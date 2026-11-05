"""
Verify the Deterministic Factory Contract on mainnet.

<https://eips.ethereum.org/EIPS/eip-7997>
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from .spec import Spec, ref_spec_7997

REFERENCE_SPEC_GIT_PATH = ref_spec_7997.git_path
REFERENCE_SPEC_VERSION = ref_spec_7997.version

pytestmark = [pytest.mark.valid_at("EIP7997"), pytest.mark.mainnet]

FACTORY = Spec.FACTORY_ADDRESS


def test_eip_7997(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Verify canonical factory code without assuming a nonce or balance."""
    storage = Storage()
    extcodesize_slot = storage.store_next(
        len(Spec.FACTORY_BYTECODE), "extcodesize"
    )
    extcodehash_slot = storage.store_next(
        Spec.FACTORY_BYTECODE.keccak256(), "extcodehash"
    )
    extcodecopy_hash_slot = storage.store_next(
        Spec.FACTORY_BYTECODE.keccak256(), "extcodecopy_hash"
    )
    code = (
        Op.SSTORE(extcodesize_slot, Op.EXTCODESIZE(FACTORY))
        + Op.SSTORE(extcodehash_slot, Op.EXTCODEHASH(FACTORY))
        + Op.EXTCODECOPY(FACTORY, 0, 0, Op.EXTCODESIZE(FACTORY))
        + Op.SSTORE(extcodecopy_hash_slot, Op.SHA3(0, Op.EXTCODESIZE(FACTORY)))
        + Op.STOP
    )
    caller = pre.deploy_contract(code)
    gas_limit = fork.transaction_intrinsic_cost_calculator()() + code.gas_cost(
        fork
    )
    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
            gas_limit=gas_limit,
        ),
        post={
            FACTORY: Account(code=Spec.FACTORY_BYTECODE),
            caller: Account(storage=storage),
        },
    )
