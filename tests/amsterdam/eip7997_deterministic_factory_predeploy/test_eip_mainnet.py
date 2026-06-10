"""
abstract: Crafted tests for mainnet of
[EIP-7997: Deterministic Factory Predeploy](https://eips.ethereum.org/EIPS/eip-7997).
"""  # noqa: E501

import pytest
from execution_testing import (
    Account,
    Alloc,
    Hash,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    compute_create2_address,
)

from .spec import Spec, ref_spec_7997

REFERENCE_SPEC_GIT_PATH = ref_spec_7997.git_path
REFERENCE_SPEC_VERSION = ref_spec_7997.version

pytestmark = [pytest.mark.valid_at("Amsterdam"), pytest.mark.mainnet]


def test_eip_7997(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Deploy a contract via the deterministic factory by sending
    `salt || initcode` from an EOA directly to the factory address.
    """
    salt = 0x42
    runtime = Op.PUSH1(0x01) + Op.PUSH1(0x00) + Op.RETURN
    initcode = Initcode(deploy_code=runtime)
    expected_address = compute_create2_address(
        Spec.FACTORY_ADDRESS, salt, initcode
    )

    state_test(
        pre=pre,
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=Spec.FACTORY_ADDRESS,
            data=Hash(salt) + bytes(initcode),
            gas_limit=200_000,
        ),
        post={
            expected_address: Account(nonce=1, code=bytes(runtime)),
        },
    )
