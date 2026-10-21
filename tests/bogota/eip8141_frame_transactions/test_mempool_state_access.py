"""
Public mempool state access tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Simulating the validation prefix may read the sender's storage only,
and may call or inspect only existing contracts and precompiles that
carry no EIP-7702 delegation, so that no third party's state change can
invalidate pending transactions. Each test sends a sender whose
validation code performs one access, admitted or rejected per the rule,
next to a sender whose code performs none. Filled, all land in a valid
block: the rules are mempool policy, not consensus.
"""

from typing import Callable

import pytest
from execution_testing import (
    Address,
    Alloc,
    Bytecode,
    Fork,
    MempoolTestFiller,
    MempoolTransaction,
    Op,
)

from .mempool_helpers import PrefixShape, prefix_transaction
from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

IDENTITY_PRECOMPILE = Address(0x04)


def storage_reader(pre: Alloc) -> Address:
    """Deploy a contract reading slot zero of the running account."""
    return pre.deploy_contract(code=Op.POP(Op.SLOAD(0)), storage={0: 1})


@pytest.mark.parametrize(
    "sender_code,accepted",
    [
        pytest.param(
            lambda _pre: Op.POP(Op.SLOAD(0)), True, id="sender_storage"
        ),
        pytest.param(
            lambda pre: Op.POP(
                Op.DELEGATECALL(gas=Op.GAS, address=storage_reader(pre))
            ),
            True,
            id="sender_storage_via_delegatecall",
        ),
        pytest.param(
            lambda pre: Op.POP(
                Op.CALL(gas=Op.GAS, address=storage_reader(pre))
            ),
            False,
            id="callee_storage",
        ),
        pytest.param(
            lambda pre: Op.POP(
                Op.STATICCALL(gas=Op.GAS, address=storage_reader(pre))
            ),
            False,
            id="callee_storage_via_staticcall",
        ),
    ],
)
def test_sender_validation_storage_read(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    sender_code: Callable[[Alloc], Bytecode],
    accepted: bool,
) -> None:
    """
    Test that a sender's validation code may read its own storage,
    directly or through `DELEGATECALL`, but not a callee's storage.
    """
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=prefix_transaction(
                    pre, fork, PrefixShape.SELF_VERIFY, sender_code=Bytecode()
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=prefix_transaction(
                    pre,
                    fork,
                    PrefixShape.SELF_VERIFY,
                    sender_code=sender_code(pre),
                ),
                accepted=accepted,
                reason=None if accepted else "storage read outside sender",
            ),
        ],
    )


def test_paymaster_validation_storage_read(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a non-canonical paymaster's validation code may not read
    its own storage, which is not the sender's.
    """
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=prefix_transaction(
                    pre,
                    fork,
                    PrefixShape.ONLY_VERIFY_PAY,
                    paymaster_code=Bytecode(),
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=prefix_transaction(
                    pre,
                    fork,
                    PrefixShape.ONLY_VERIFY_PAY,
                    paymaster_code=Op.POP(Op.SLOAD(0)),
                ),
                accepted=False,
                reason="storage read outside sender",
            ),
        ],
    )


@pytest.mark.parametrize(
    "target,accepted",
    [
        pytest.param(
            lambda pre: pre.deploy_contract(code=Op.STOP),
            True,
            id="contract",
        ),
        pytest.param(lambda _pre: IDENTITY_PRECOMPILE, True, id="precompile"),
        pytest.param(lambda pre: pre.fund_eoa(), False, id="eoa"),
        pytest.param(
            lambda pre: pre.nonexistent_account(), False, id="nonexistent"
        ),
        pytest.param(
            lambda pre: pre.fund_eoa(
                delegation=pre.deploy_contract(code=Op.STOP)
            ),
            False,
            id="delegated",
        ),
    ],
)
@pytest.mark.parametrize(
    "access",
    [
        pytest.param(
            lambda target: Op.POP(Op.CALL(gas=Op.GAS, address=target)),
            id="CALL",
        ),
        pytest.param(
            lambda target: Op.POP(Op.EXTCODESIZE(target)), id="EXTCODESIZE"
        ),
        pytest.param(
            lambda target: Op.POP(Op.EXTCODEHASH(target)), id="EXTCODEHASH"
        ),
    ],
)
def test_validation_account_access(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    target: Callable[[Alloc], Address],
    accepted: bool,
    access: Callable[[Address], Bytecode],
) -> None:
    """
    Test that validation code may call or inspect an existing contract
    or a precompile, but not an account without code or one carrying an
    EIP-7702 delegation.
    """
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=prefix_transaction(
                    pre, fork, PrefixShape.SELF_VERIFY, sender_code=Bytecode()
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=prefix_transaction(
                    pre,
                    fork,
                    PrefixShape.SELF_VERIFY,
                    sender_code=access(target(pre)),
                ),
                accepted=accepted,
                reason=None
                if accepted
                else "validation accesses a disallowed account",
            ),
        ],
    )
