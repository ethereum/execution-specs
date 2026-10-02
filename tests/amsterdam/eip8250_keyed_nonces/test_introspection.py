"""
Transaction introspection tests for
[EIP-8250: Keyed Nonces for Frame Transactions](https://eips.ethereum.org/EIPS/eip-8250).

`TXPARAM(0x01)` returns `nonce_seq`. Four new parameters expose the
sender's legacy account nonce as observed before any frame executes,
the number of selected keys, a commitment to the key set, and its first
key.
"""

from typing import List

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Conditional,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)

from ..eip8141_frame_transactions.helpers import (
    default_frame,
    sender_frame,
    verify_frame,
)
from ..eip8141_frame_transactions.spec import Spec as Spec8141
from .helpers import (
    FULL_WIDTH_KEY,
    KEY_A,
    NULLIFIER_KEY,
    nonce_keys_hash,
    set_keyed_nonces,
)
from .spec import Spec, ref_spec_8250

REFERENCE_SPEC_GIT_PATH = ref_spec_8250.git_path
REFERENCE_SPEC_VERSION = ref_spec_8250.version

pytestmark = pytest.mark.valid_from("Bogota")

PROBE_FRAME_GAS = 200_000
"""Execution gas budget of the frame running the probe."""

NONCE_PARAMS = [
    Spec.TXPARAM_NONCE_SEQ,
    Spec.TXPARAM_LEGACY_NONCE,
    Spec.TXPARAM_NONCE_KEY_COUNT,
    Spec.TXPARAM_NONCE_KEYS_HASH,
    Spec.TXPARAM_NONCE_KEY_0,
]
"""
The nonce parameters the probe records, each into the storage slot
numbered after the parameter itself.
"""


def record_params() -> Bytecode:
    """
    Return code storing one plus every nonce parameter, so a zero value
    reads back distinct from a slot never written.
    """
    code = Bytecode()
    for param in NONCE_PARAMS:
        code += Op.SSTORE(param, Op.ADD(1, Op.TXPARAM(param)))
    return code


@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize(
    "nonce_keys,nonce_seq",
    [
        pytest.param([0], 7, id="legacy_keys"),
        pytest.param([KEY_A], 0, id="one_key"),
        pytest.param([KEY_A], 4, id="one_used_key"),
        pytest.param(
            [KEY_A, NULLIFIER_KEY, FULL_WIDTH_KEY], 0, id="three_keys"
        ),
    ],
)
def test_nonce_txparams(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    nonce_keys: List[int],
    nonce_seq: int,
) -> None:
    """
    Read every nonce parameter from a frame after payment approval.

    The sender's account nonce is 7 before the transaction. Approval
    moves it to 8 for the legacy key set, yet `TXPARAM(0x0D)` still
    returns 7. For keyed sets it stays 7 and differs from `nonce_seq`.
    """
    sender = pre.fund_eoa(nonce=7)
    if nonce_seq and nonce_keys != [0]:
        set_keyed_nonces(pre, [(sender, dict.fromkeys(nonce_keys, nonce_seq))])
    probe_code = record_params() + Op.STOP
    probe = pre.deploy_contract(code=probe_code)

    tx = Transaction(
        sender=sender,
        nonce=nonce_seq,
        nonce_keys=nonce_keys,
        frames=[
            verify_frame(),
            default_frame(
                target=probe,
                gas_limit=PROBE_FRAME_GAS,
                state_gas_limit=probe_code.state_cost(fork),
            ),
        ],
    )

    expected = {
        Spec.TXPARAM_NONCE_SEQ: nonce_seq,
        Spec.TXPARAM_LEGACY_NONCE: 7,
        Spec.TXPARAM_NONCE_KEY_COUNT: len(nonce_keys),
        Spec.TXPARAM_NONCE_KEYS_HASH: nonce_keys_hash(nonce_keys),
        Spec.TXPARAM_NONCE_KEY_0: nonce_keys[0],
    }
    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=8 if nonce_keys == [0] else 7),
            probe: Account(
                storage={
                    param: (value + 1) % 2**256
                    for param, value in expected.items()
                }
            ),
        },
    )


@pytest.mark.pre_alloc_mutable
def test_legacy_nonce_param_ignores_create(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Keep `TXPARAM(0x0D)` at the pre-state nonce after `CREATE` moves the
    sender's account nonce within the transaction.

    The sender contract approves in its first frame. Its `SENDER` frame
    runs `CREATE`, raising its nonce from 3 to 4, and then records the
    parameter.
    """
    sender_code = Conditional(
        condition=Op.TXPARAM(Spec8141.TXPARAM_FRAME_INDEX),
        if_true=Op.POP(Op.CREATE(0, 0, 0))
        + Op.SSTORE(
            Spec.TXPARAM_LEGACY_NONCE,
            Op.TXPARAM(Spec.TXPARAM_LEGACY_NONCE),
        )
        + Op.STOP,
        if_false=Op.APPROVE(0, 0, Spec8141.APPROVE_EXECUTION_AND_PAYMENT),
    )
    sender = pre.deploy_contract(code=sender_code, balance=10**18, nonce=3)

    tx = Transaction(
        sender=sender,
        nonce=0,
        nonce_keys=[KEY_A],
        frames=[
            verify_frame(target=sender),
            sender_frame(target=sender, gas_limit=PROBE_FRAME_GAS),
        ],
    )

    state_test(
        pre=pre,
        tx=tx,
        post={
            sender: Account(nonce=4, storage={Spec.TXPARAM_LEGACY_NONCE: 3}),
        },
    )
