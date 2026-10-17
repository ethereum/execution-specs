"""
Public mempool `deploy` frame tests for
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

A validation prefix may open with a `deploy` frame, which must install
code at the sender and may write state only by creating that code and
storing to the sender's storage. Each test sends a sender deployed by
the deterministic factory, which must be admitted, next to a variant
breaking one rule, admitted or rejected per the rule. Filled, all land
in a valid block: the rules are mempool policy, not consensus.
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

from .helpers import default_frame
from .mempool_helpers import (
    PrefixShape,
    budgeted_transaction,
    deploy_frame,
    frame_gas,
    prefix,
    prefix_transaction,
)
from .spec import ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")


def factory_code(extra: Bytecode) -> Bytecode:
    """
    Return a factory sharing the deterministic factory's calldata
    layout, `salt || initcode`, that runs `extra` after deploying.
    """
    initcode_size = Op.SUB(Op.CALLDATASIZE, 32)
    return (
        Op.CALLDATACOPY(0, 32, initcode_size)
        + Op.POP(
            Op.CREATE2(
                value=0, offset=0, size=initcode_size, salt=Op.CALLDATALOAD(0)
            )
        )
        + extra
    )


@pytest.mark.parametrize("foreign", [False, True], ids=["noop", "foreign"])
def test_deploy_must_install_sender_code(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    foreign: bool,
) -> None:
    """
    Test that a `DEFAULT` first frame leaving the sender without code,
    whether doing nothing or deploying another account, is rejected.
    """
    rejected = prefix(pre, fork, PrefixShape.SELF_VERIFY)
    if foreign:
        deploy, _ = deploy_frame(pre, fork, Op.STOP)
        rejected.insert(0, deploy)
        rejected.work_frame = 0
    else:
        rejected.insert(
            0,
            default_frame(
                target=pre.deploy_contract(code=Op.STOP),
                gas_limit=frame_gas(fork, Op.STOP, target_warm=False),
                state_gas_limit=0,
            ),
        )
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=prefix_transaction(
                    pre, fork, PrefixShape.DEPLOY_SELF_VERIFY
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=budgeted_transaction(fork, rejected),
                accepted=False,
                reason="deploy frame installs no code at the sender",
            ),
        ],
    )


@pytest.mark.parametrize(
    "factory_extra,initcode_prefix,accepted",
    [
        pytest.param(None, Op.SSTORE(0, 1), True, id="sender_storage"),
        pytest.param(Bytecode(), None, True, id="custom_factory"),
        pytest.param(Op.SSTORE(0, 1), None, False, id="factory_storage"),
        pytest.param(Op.POP(Op.CREATE(0, 0, 0)), None, False, id="create"),
    ],
)
def test_deploy_frame_state_writes(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    factory_extra: Bytecode | None,
    initcode_prefix: Bytecode | None,
    accepted: bool,
) -> None:
    """
    Test that a `deploy` frame may store to the sender's storage while
    creating its code, but may not write any other state.
    """
    factory = None
    if factory_extra is not None:
        factory = pre.deploy_contract(code=factory_code(factory_extra))
    mempool_test(
        pre=pre,
        txs=[
            MempoolTransaction(
                tx=prefix_transaction(
                    pre, fork, PrefixShape.DEPLOY_SELF_VERIFY
                ),
                accepted=True,
            ),
            MempoolTransaction(
                tx=budgeted_transaction(
                    fork,
                    prefix(
                        pre,
                        fork,
                        PrefixShape.DEPLOY_SELF_VERIFY,
                        factory=factory,
                        initcode_prefix=initcode_prefix,
                    ),
                ),
                accepted=accepted,
                reason=None
                if accepted
                else "deploy frame writes state outside the sender",
            ),
        ],
    )
