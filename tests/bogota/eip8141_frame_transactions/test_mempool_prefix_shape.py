"""
Public mempool validation prefix shape tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

The public mempool recognizes four validation prefixes, `[self_verify]`,
`[deploy, self_verify]`, `[only_verify, pay]` and
`[deploy, only_verify, pay]`, optionally opened by an expiry verifier
frame, and admits no `VERIFY` frame after the prefix. Each test sends a
recognized transaction, which must be admitted, and a variant breaking
one structural rule, which must be rejected. Filled, both land in a
valid block: the rules are mempool policy, not consensus.
"""

import pytest
from execution_testing import (
    Alloc,
    Bytecode,
    Fork,
    MempoolTestFiller,
    MempoolTransaction,
    Op,
)

from .helpers import default_frame, sender_frame, verify_frame
from .mempool_helpers import (
    PrefixShape,
    budgeted_transaction,
    frame_gas,
    prefix,
    priced_expiry_frame,
)
from .spec import Spec, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


@pytest.mark.parametrize(
    "shape",
    [
        PrefixShape.DEPLOY_SELF_VERIFY,
        PrefixShape.ONLY_VERIFY_PAY,
        PrefixShape.DEPLOY_ONLY_VERIFY_PAY,
    ],
    ids=str,
)
def test_extra_default_frame_in_prefix(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    shape: PrefixShape,
) -> None:
    """
    Test that a `DEFAULT` frame inside the validation prefix, after its
    first frame, makes the prefix unrecognized.
    """
    noop = pre.deploy_contract(code=Op.STOP)
    rejected = prefix(pre, fork, shape)
    rejected.insert(
        1,
        default_frame(
            target=noop,
            gas_limit=frame_gas(fork, Op.STOP, target_warm=False),
            state_gas_limit=0,
        ),
    )
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=budgeted_transaction(fork, prefix(pre, fork, shape)),
                accepted=True,
            ),
            MempoolTransaction(
                tx=budgeted_transaction(fork, rejected),
                accepted=False,
                reason="DEFAULT frame inside the validation prefix",
            ),
        ],
    )


@pytest.mark.parametrize("shape", list(PrefixShape), ids=str)
def test_expiry_frame_not_first(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    shape: PrefixShape,
) -> None:
    """
    Test that an expiry verifier frame is recognized only as the first
    frame.
    """
    rejected = prefix(pre, fork, shape)
    rejected.insert(1, priced_expiry_frame(fork))
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=budgeted_transaction(
                    fork, prefix(pre, fork, shape, expiry=True)
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=budgeted_transaction(fork, rejected),
                accepted=False,
                reason="expiry verifier frame is not the first frame",
            ),
        ],
    )


@pytest.mark.parametrize(
    "shape",
    [PrefixShape.DEPLOY_SELF_VERIFY, PrefixShape.DEPLOY_ONLY_VERIFY_PAY],
    ids=str,
)
def test_atomic_batch_in_prefix(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    shape: PrefixShape,
) -> None:
    """
    Test that a `deploy` frame batched with a following frame is not
    admitted, as no validation prefix frame may set `ATOMIC_BATCH_FLAG`.
    """
    noop = pre.deploy_contract(code=Op.STOP)
    rejected = prefix(pre, fork, shape)
    deploy = rejected.frames[0]
    rejected.frames[0] = deploy.model_copy(
        update={"flags": Spec.ATOMIC_BATCH_FLAG}
    )
    rejected.insert(
        1,
        default_frame(
            target=noop,
            gas_limit=frame_gas(fork, Op.STOP, target_warm=False),
            state_gas_limit=0,
        ),
    )
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=budgeted_transaction(fork, prefix(pre, fork, shape)),
                accepted=True,
            ),
            MempoolTransaction(
                tx=budgeted_transaction(fork, rejected),
                accepted=False,
                reason="ATOMIC_BATCH_FLAG inside the validation prefix",
            ),
        ],
    )


@pytest.mark.parametrize("shape", list(PrefixShape), ids=str)
def test_verify_frame_after_prefix(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    shape: PrefixShape,
) -> None:
    """
    Test that a `VERIFY` frame after the validation prefix is not
    admitted, even one that succeeds without approving, as simulation
    stops at the prefix and could not foresee it reverting.
    """
    stop = pre.deploy_contract(code=Op.STOP)
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=budgeted_transaction(
                    fork,
                    prefix(pre, fork, shape),
                    after=[sender_frame(target=stop)],
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=budgeted_transaction(
                    fork,
                    prefix(pre, fork, shape),
                    after=[
                        verify_frame(
                            target=stop,
                            flags=Spec.APPROVE_NONE,
                            gas_limit=frame_gas(
                                fork, Op.STOP, target_warm=False
                            ),
                            state_gas_limit=0,
                        )
                    ],
                ),
                accepted=False,
                reason="VERIFY frame after the validation prefix",
            ),
        ],
    )


def test_approve_scope_must_match_flags(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a `VERIFY` frame whose flags allow execution and payment
    but which approves execution only is not recognized as
    `only_verify`, though the following `pay` frame makes it valid.
    """
    rejected = prefix(
        pre, fork, PrefixShape.ONLY_VERIFY_PAY, sender_code=Bytecode()
    )
    only_verify = rejected.frames[0]
    rejected.frames[0] = only_verify.model_copy(
        update={"flags": Spec.APPROVE_EXECUTION_AND_PAYMENT}
    )
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=budgeted_transaction(
                    fork,
                    prefix(
                        pre,
                        fork,
                        PrefixShape.ONLY_VERIFY_PAY,
                        sender_code=Bytecode(),
                    ),
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=budgeted_transaction(fork, rejected),
                accepted=False,
                reason="APPROVE scope narrower than the frame flags",
            ),
        ],
    )


def test_explicit_sender_target(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that a `self_verify` frame naming the sender as its target is
    recognized like one with a null target.
    """
    built = prefix(pre, fork, PrefixShape.SELF_VERIFY)
    built.frames[0] = built.frames[0].model_copy(
        update={"target": built.sender}
    )
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=budgeted_transaction(fork, built), accepted=True
            ),
        ],
    )
