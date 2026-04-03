"""Vector file for pytest fill command example coverage."""

from typing import Any

from execution_testing import Transaction


def test_function(state_test: Any, pre: Any) -> None:
    """Generate a minimal signed state test transaction."""
    tx = Transaction(
        to=0, gas_limit=21_000, sender=pre.fund_eoa()
    ).with_signature_and_sender()
    state_test(pre=pre, post={}, tx=tx)
