"""
Mainnet marked execute checklist tests for
[EIP-7843: SLOTNUM](https://eips.ethereum.org/EIPS/eip-7843).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import ref_spec_7843

REFERENCE_SPEC_GIT_PATH = ref_spec_7843.git_path
REFERENCE_SPEC_VERSION = ref_spec_7843.version

pytestmark = [pytest.mark.valid_at("EIP7843"), pytest.mark.mainnet]


def test_slotnum_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that SLOTNUM is callable and returns a non-zero slot number.

    Asserts on ``POP(SLOTNUM)`` rather than the slot value itself
    so the test remains valid when ``execute``-ed against a live network,
    where the slot number is whatever the consensus layer transmits and
    cannot be controlled by the test.
    """
    contract = pre.deploy_contract(
        code=Op.POP(Op.SLOTNUM) + Op.SSTORE(0, 1),
        storage={"0x00": "0xdeadbeef"},
    )
    tx = Transaction(
        ty=0x02,
        to=contract,
        sender=pre.fund_eoa(),
        gas_limit=200_000,
    )
    post = {contract: Account(storage={"0x00": 1})}

    state_test(
        env=Environment(),
        pre=pre,
        tx=tx,
        post=post,
    )
