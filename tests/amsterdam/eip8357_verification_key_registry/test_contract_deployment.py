"""Deployment tests for the EIP-8357 verification-key registry."""

import json
from pathlib import Path
from typing import Any

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    EIPChecklist,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create2_address,
)

from .spec import Spec, ref_spec_8357

REFERENCE_SPEC_GIT_PATH = ref_spec_8357.git_path
REFERENCE_SPEC_VERSION = ref_spec_8357.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _deployment_vector() -> dict[str, Any]:
    """Load the canonical factory deployment vector."""
    path = Path(__file__).with_name("registry_factory_deploy.json")
    return json.loads(path.read_text())


@EIPChecklist.SystemContract.Test.Deployment.Address()
def test_registry_factory_deployment(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    The EIP-7997 factory deploys the registry's exact runtime at the
    EIP-8357 address from the specified salt and initcode.
    """
    vector = _deployment_vector()
    factory = Address(vector["factory"])
    salt = Hash(vector["salt"])
    initcode = Bytes(vector["initcode"])
    registry = compute_create2_address(factory, salt, initcode)

    assert factory == Spec.FACTORY_ADDRESS
    assert salt == Hash(Spec.REGISTRY_DEPLOYMENT_SALT)
    assert initcode == Spec.REGISTRY_INITCODE
    assert registry == Spec.EVM_VK_REGISTRY_ADDRESS

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=factory,
            data=salt + initcode,
        ),
        post={
            registry: Account(
                nonce=1,
                balance=0,
                code=Spec.REGISTRY_RUNTIME_CODE,
                storage={},
            ),
        },
    )
