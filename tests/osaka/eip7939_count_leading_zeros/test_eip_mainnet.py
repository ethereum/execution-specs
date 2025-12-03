"""
Mainnet marked execute checklist tests for
[EIP-7939: Count leading zeros (CLZ)](https://eips.ethereum.org/EIPS/eip-7939).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)

from .spec import ref_spec_7939

REFERENCE_SPEC_GIT_PATH = ref_spec_7939.git_path
REFERENCE_SPEC_VERSION = ref_spec_7939.version

pytestmark = [pytest.mark.valid_at("Osaka"), pytest.mark.mainnet]


@pytest.mark.parametrize(
    "clz_input,clz_expected",
    [
        pytest.param(
            0x00FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            8,
            id="clz-8-leading-zeros",
        ),
        pytest.param(0, 256, id="clz-all-zeros"),
    ],
)
def test_clz_mainnet(
    state_test: StateTestFiller,
    pre: Alloc,
    clz_input: int,
    clz_expected: int,
) -> None:
    """
    Test CLZ opcode on mainnet.
    """
    sender = pre.fund_eoa()
    contract_address = pre.deploy_contract(
        code=Op.SSTORE(0, Op.CLZ(clz_input)),
        storage={"0x00": "0xdeadbeef"},
    )
    tx = Transaction(
        ty=0x02,
        to=contract_address,
        sender=sender,
        gas_limit=200_000,
    )
    post = {
        contract_address: Account(storage={"0x00": clz_expected}),
    }
    state_test(pre=pre, post=post, tx=tx)
