"""Helpers shared by the reorg tests."""

from typing import List, Tuple

from execution_testing import Address, Alloc, Hash, Transaction
from execution_testing.fixtures.reorg import (
    ForkchoiceUpdatedStep,
    NewPayloadStep,
    Outcome,
    PayloadAttributes,
    Step,
)
from execution_testing.specs import ReorgBlock


def applied(head: str, payload_id: bool = False) -> List[Outcome]:
    """Single legal outcome: applied, with a payload id if requested."""
    return [
        Outcome(
            id="applied",
            status="VALID",
            latest_valid_hash=head,
            payload_id="nonNull" if payload_id else None,
        )
    ]


def build_attrs(prev_randao: int, timestamp: int = 0) -> PayloadAttributes:
    """
    Payload attributes; withdrawals, beacon root and, if 0, the timestamp
    are filled at fill.
    """
    return PayloadAttributes(
        timestamp=timestamp,
        prev_randao=Hash(prev_randao),
        suggested_fee_recipient=0x1234,
    )


def chain(
    pre: Alloc,
    prefix: str,
    length: int,
    parent: str = "genesis",
    start: int = 1,
    value: int = 1,
    recipient: Address | None = None,
    with_fcu: bool = True,
) -> Tuple[List[ReorgBlock], List[Step]]:
    """
    ``length`` blocks ``{prefix}{start}..`` on ``parent``, each with one value
    transfer from a fresh sender (nonces independent per chain) to
    ``recipient`` (a fresh empty account if unset), plus the newPayload steps
    and, ``with_fcu``, the forkchoiceUpdated steps that make the last block
    the head.
    """
    sender = pre.fund_eoa()
    if recipient is None:
        recipient = pre.fund_eoa(amount=0)
    blocks: List[ReorgBlock] = []
    steps: List[Step] = []
    for i in range(length):
        label = f"{prefix}{start + i}"
        blocks.append(
            ReorgBlock(
                label=label,
                parent=parent if i == 0 else None,
                txs=[
                    Transaction(
                        sender=sender, nonce=i, to=recipient, value=value
                    )
                ],
            )
        )
        steps.append(NewPayloadStep(block=label))
        if with_fcu:
            steps.append(ForkchoiceUpdatedStep(head=label))
    return blocks, steps
