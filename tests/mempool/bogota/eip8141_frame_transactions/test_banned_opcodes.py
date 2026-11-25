"""
Banned opcode tests for the public mempool rules of
[EIP-8141: Frame Transaction](https://eips.ethereum.org/EIPS/eip-8141).

Before the payer is set, the validation prefix must not execute an opcode
whose result depends on the block or on balances, since one block could
then invalidate many pooled transactions at once. Each such opcode is
valid on chain in a `VERIFY` frame, so the transaction stays includable
and only the mempool refuses it.
"""

from typing import Callable

import pytest
from execution_testing import (
    Address,
    Alloc,
    Bytecode,
    Environment,
    Fork,
    Frame,
    MempoolTestFiller,
    Op,
    Transaction,
)

from tests.bogota.eip8141_frame_transactions.helpers import (
    APPROVE_ALL,
)

from .spec import MempoolRule, ref_spec_8141

REFERENCE_SPEC_GIT_PATH = ref_spec_8141.git_path
REFERENCE_SPEC_VERSION = ref_spec_8141.version

pytestmark = pytest.mark.valid_from("Bogota")

Operation = Callable[[Address], Bytecode]
"""Bytecode reading one value, given an existing account to read from."""

BANNED_READS = [
    pytest.param(lambda _: Op.GASPRICE, id="GASPRICE"),
    # The block being built has no hash yet, so this reads zero without
    # a lookup and without the banned `NUMBER`.
    pytest.param(lambda _: Op.BLOCKHASH(Environment().number), id="BLOCKHASH"),
    pytest.param(lambda _: Op.COINBASE, id="COINBASE"),
    pytest.param(lambda _: Op.TIMESTAMP, id="TIMESTAMP"),
    pytest.param(lambda _: Op.NUMBER, id="NUMBER"),
    pytest.param(lambda _: Op.PREVRANDAO, id="PREVRANDAO"),
    pytest.param(lambda _: Op.GASLIMIT, id="GASLIMIT"),
    pytest.param(lambda _: Op.BASEFEE, id="BASEFEE"),
    pytest.param(lambda _: Op.BLOBBASEFEE, id="BLOBBASEFEE"),
    pytest.param(lambda _: Op.SLOTNUM, id="SLOTNUM"),
    pytest.param(lambda account: Op.BALANCE(account), id="BALANCE"),
    pytest.param(lambda _: Op.SELFBALANCE, id="SELFBALANCE"),
    # `GAS` is allowed only directly before a `*CALL`.
    pytest.param(lambda _: Op.GAS, id="GAS"),
]
"""
Banned opcodes that a `STATICCALL` allows, so they leave the transaction
valid on chain. The banned opcodes a `STATICCALL` forbids (`CREATE`,
`CREATE2`, `SSTORE`, `SELFDESTRUCT`) make the transaction invalid instead.
"""


@pytest.mark.parametrize("operation", BANNED_READS)
@pytest.mark.parametrize("nested", [False, True], ids=["direct", "nested"])
def test_banned_opcode_in_validation_prefix(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    operation: Operation,
    nested: bool,
) -> None:
    """
    Refuse a frame transaction whose self-verifying `VERIFY` frame runs a
    banned opcode, directly or in a contract it calls, before approving.
    """
    readable = pre.deploy_contract(code=Op.STOP, balance=1)
    read = Op.POP(operation(readable))
    if nested:
        callee = pre.deploy_contract(code=read + Op.STOP)
        sender_code = Op.POP(Op.CALL(gas=Op.GAS, address=callee)) + APPROVE_ALL
    else:
        sender_code = read + APPROVE_ALL
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[Frame.verify()],
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=False,
        rules=[MempoolRule.BANNED_OPCODE],
    )


@pytest.mark.parametrize(
    "gas_before_call", [False, True], ids=["no_read", "gas_before_call"]
)
def test_allowed_validation_prefix(
    mempool_test: MempoolTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_before_call: bool,
) -> None:
    """
    Admit a frame transaction whose self-verifying `VERIFY` frame runs no
    banned opcode, or runs `GAS` only as the gas argument of a `CALL`.

    This is the positive twin of the banned opcode tests: the same
    transaction without the banned read is broadcast.
    """
    if gas_before_call:
        callee = pre.deploy_contract(code=Op.STOP)
        sender_code = Op.POP(Op.CALL(gas=Op.GAS, address=callee)) + APPROVE_ALL
    else:
        sender_code = APPROVE_ALL
    sender = pre.deploy_contract(code=sender_code, balance=10**18)

    tx = Transaction(
        sender=sender,
        nonce=1,
        frames=[Frame.verify()],
    )

    mempool_test(
        pre=pre,
        tx=tx,
        broadcast=True,
        rules=[MempoolRule.BANNED_OPCODE],
    )
