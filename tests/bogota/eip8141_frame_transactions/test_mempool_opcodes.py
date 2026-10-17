"""
Public mempool banned opcode tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Simulating the validation prefix must not reach environment-dependent
or state-changing opcodes, so a transaction whose prefix executes one
is rejected by the public mempool, while the same code after the
prefix is admitted. Filled, both land in a valid block: the bans are
mempool policy, not consensus.
"""

from enum import Enum, unique

import pytest
from execution_testing import (
    Alloc,
    Bytecode,
    Fork,
    MempoolTestFiller,
    MempoolTransaction,
    Op,
)

from .helpers import sender_frame
from .mempool_helpers import PrefixShape, prefix_transaction
from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


@unique
class ValidationAccount(Enum):
    """The account whose `VERIFY` frame runs the code under test."""

    SENDER = "sender"
    PAYMASTER = "paymaster"

    def __str__(self) -> str:
        """Return the account's name as the test id."""
        return self.value


def validation_transaction(
    pre: Alloc,
    fork: Fork,
    account: ValidationAccount,
    code: Bytecode,
    after_code: Bytecode | None = None,
) -> object:
    """
    Return a transaction whose sender or paymaster runs `code` before
    approving, followed by a frame running `after_code` as the sender.
    """
    after = []
    if after_code is not None:
        after = [sender_frame(target=pre.deploy_contract(code=after_code))]
    if account == ValidationAccount.SENDER:
        return prefix_transaction(
            pre, fork, PrefixShape.SELF_VERIFY, sender_code=code, after=after
        )
    return prefix_transaction(
        pre,
        fork,
        PrefixShape.ONLY_VERIFY_PAY,
        paymaster_code=code,
        after=after,
    )


@pytest.mark.parametrize("account", list(ValidationAccount), ids=str)
@pytest.mark.parametrize(
    "opcode",
    [
        pytest.param(Op.GASPRICE, id="GASPRICE"),
        pytest.param(Op.BLOCKHASH(0), id="BLOCKHASH"),
        pytest.param(Op.COINBASE, id="COINBASE"),
        pytest.param(Op.TIMESTAMP, id="TIMESTAMP"),
        pytest.param(Op.NUMBER, id="NUMBER"),
        pytest.param(Op.PREVRANDAO, id="PREVRANDAO"),
        pytest.param(Op.GASLIMIT, id="GASLIMIT"),
        pytest.param(Op.BASEFEE, id="BASEFEE"),
        pytest.param(Op.BLOBBASEFEE, id="BLOBBASEFEE"),
        pytest.param(Op.SLOTNUM, id="SLOTNUM"),
        pytest.param(Op.BALANCE(Op.ADDRESS), id="BALANCE"),
        pytest.param(Op.SELFBALANCE, id="SELFBALANCE"),
        pytest.param(Op.GAS, id="GAS"),
    ],
)
def test_banned_opcode_in_prefix(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    account: ValidationAccount,
    opcode: Bytecode,
) -> None:
    """
    Test that a banned opcode in a validation prefix frame is rejected,
    while the same opcode in a frame after the prefix is admitted.
    """
    code = opcode + Op.POP
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=validation_transaction(
                    pre, fork, account, Bytecode(), after_code=code
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=validation_transaction(pre, fork, account, code),
                accepted=False,
                reason="banned opcode in the validation prefix",
            ),
        ],
    )


@pytest.mark.parametrize("account", list(ValidationAccount), ids=str)
def test_gas_before_call(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    account: ValidationAccount,
) -> None:
    """
    Test that `GAS` immediately followed by a call, the standard way to
    forward gas, is admitted, while `GAS` read on its own is rejected.
    """
    stop = pre.deploy_contract(code=Op.STOP)
    forwarded = Op.POP(Op.CALL(gas=Op.GAS, address=stop))
    read = Op.POP(Op.GAS) + Op.POP(Op.CALL(gas=0, address=stop))
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=validation_transaction(pre, fork, account, forwarded),
                accepted=True,
            ),
            MempoolTransaction(
                tx=validation_transaction(pre, fork, account, read),
                accepted=False,
                reason="GAS not followed by a call",
            ),
        ],
    )


@pytest.mark.parametrize("account", list(ValidationAccount), ids=str)
@pytest.mark.parametrize(
    "callee_code",
    [
        pytest.param(Op.INVALID, id="INVALID"),
        pytest.param(Op.SELFDESTRUCT(Op.ADDRESS), id="SELFDESTRUCT"),
        pytest.param(Op.SSTORE(0, 1), id="SSTORE"),
        pytest.param(Op.CREATE(0, 0, 0), id="CREATE"),
        pytest.param(Op.CREATE2(0, 0, 0, 0), id="CREATE2"),
    ],
)
def test_banned_opcode_in_caught_call(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    account: ValidationAccount,
    callee_code: Bytecode,
) -> None:
    """
    Test that a banned opcode reached in a call the validation frame
    survives is rejected.

    The call halts on the opcode, which a static `VERIFY` frame cannot
    execute, so the frame still approves and the block stays valid.
    """
    stop = pre.deploy_contract(code=Op.STOP)
    callee = pre.deploy_contract(code=callee_code)
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=validation_transaction(
                    pre,
                    fork,
                    account,
                    Op.POP(Op.CALL(gas=Op.GAS, address=stop)),
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=validation_transaction(
                    pre,
                    fork,
                    account,
                    Op.POP(Op.CALL(gas=Op.GAS, address=callee)),
                ),
                accepted=False,
                reason="banned opcode in a call from the validation prefix",
            ),
        ],
    )
