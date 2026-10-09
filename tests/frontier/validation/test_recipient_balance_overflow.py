"""
Recipient balance overflow on value transfer.

when the tx value plus the recipient's current balance would
exceed ``2**256 - 1`` (maximum representable balance),
besu crashes.

- besu  : ``java.lang.ArithmeticException: UInt256 overflow`` is raised
          inside ``MessageCallProcessor.transferValue`` (an internal
          client error / stack trace, not a clean consensus rule). The
          tx and block are rejected.

- geth / nethermind / erigon / reth : silently wrap the recipient's
          balance modulo ``2**256``. The bytecode executes normally and
          the transaction settles with the wrapped balance.

- EELS  : behavior adjusted to match geth / nethermind / erigon / reth in this
          commit.

On mainnet the case is unreachable (total ETH supply <  2**256) so it is
more of a theoretical case
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op


@pytest.mark.eels_base_coverage
def test_recipient_balance_overflow(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Value transfer where ``recipient.balance + tx.value`` exactly equals
    ``2**256`` — one wei past the UINT256 ceiling.

    The recipient is a normal contract whose code is a single ``STOP``,
    so the only operation that touches the recipient's balance is the
    transaction's value transfer. The recipient's balance must wrap to
    zero.
    """
    sender = pre.fund_eoa()
    recipient = pre.deploy_contract(
        code=Op.STOP,
        balance=2**256 - 2,
    )

    tx = Transaction(
        sender=sender,
        to=recipient,
        value=2,
        gas_limit=21_000,
        protected=False,
    )

    post = {
        recipient: Account(balance=0),
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)
