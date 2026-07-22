"""
Crafted tests for mainnet of
[EIP-7997: Deterministic Factory Predeploy](https://eips.ethereum.org/EIPS/eip-7997).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
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
) -> None:
    """
    The factory bytecode is present at the canonical Arachnid factory
    address with nonce 1. Verifies EVM-observable views of
    the predeploy via `EXTCODESIZE`, `EXTCODEHASH` and `EXTCODECOPY`.
    """
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
    caller = pre.deploy_contract(
        Op.SSTORE(extcodesize_slot, Op.EXTCODESIZE(FACTORY))
        + Op.SSTORE(extcodehash_slot, Op.EXTCODEHASH(FACTORY))
        + Op.EXTCODECOPY(FACTORY, 0, 0, Op.EXTCODESIZE(FACTORY))
        + Op.SSTORE(extcodecopy_hash_slot, Op.SHA3(0, Op.EXTCODESIZE(FACTORY)))
        + Op.STOP,
    )
    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=caller,
        ),
        post={
            FACTORY: Account(code=Spec.FACTORY_BYTECODE),
            caller: Account(storage=storage),
        },
    )
