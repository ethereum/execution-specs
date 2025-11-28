"""
Mainnet testing for osaka's [EIP-7939: Count leading zeros (CLZ)](https://eips.ethereum.org/EIPS/eip-7939).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Op,
    StateTestFiller,
    Transaction,
)
from execution_testing.test_types.block_types import Environment

from .spec import ref_spec_7939

REFERENCE_SPEC_GIT_PATH = ref_spec_7939.git_path
REFERENCE_SPEC_VERSION = ref_spec_7939.version

pytestmark = [pytest.mark.valid_at("Osaka"), pytest.mark.mainnet]


# ruff keeps making parameters unreadable by putting them in one line
# fmt: off
@pytest.mark.parametrize(
    "clz_input,clz_expected",
    [
        pytest.param(
            2**256 - 1,
            0,
            id="max-size-input-clz"
        ),
        pytest.param(
            0,
            256,
            id="min-size-input-clz"
        ),
        pytest.param(
            1231350950569847740520874169721133058840016695,
            106,
            id="some-other-input-clz"
        ),
    ],
)
# fmt: on
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
        to=contract_address,
        sender=sender,
        gas_limit=200_000,
    )
    post = {
        contract_address: Account(storage={"0x00": clz_expected}),
    }
    state_test(env=Environment(), pre=pre, post=post, tx=tx)
