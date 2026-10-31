"""
Measurement instrument: how much EXECUTION gas a transaction can be granted.

EIP-7825 caps a transaction at 2**24. EIP-8037 reinterprets the same constant:
it stops being a validity bound and becomes an allocation bound, with the
excess routed into the state-gas reservoir. This probe measures the top
frame's execution grant as a function of `tx.gas` on each fork.

FAILURES ARE THE MEASUREMENT.
"""

import pytest
from execution_testing import Account, Alloc, Op, StateTestFiller, Transaction

CAP = 2**24  # 16,777,216

CANDIDATES = [
    16_756_214,  # CAP - 21_000 - 2        (pre-2780 intrinsic, at the cap)
    16_762_214,  # CAP - 15_000 - 2        (Amsterdam intrinsic, at the cap)
    17_756_214,  # CAP + 1e6 - 21_000 - 2  (no cap, pre-2780)
    17_762_214,  # CAP + 1e6 - 15_000 - 2  (no cap, Amsterdam intrinsic)
]


@pytest.mark.parametrize("expected", CANDIDATES)
@pytest.mark.parametrize(
    "tx_gas", [CAP, CAP + 1_000_000], ids=["at_cap", "above_cap"]
)
@pytest.mark.valid_from("Prague")
def test_grant(
    state_test: StateTestFiller, pre: Alloc, tx_gas: int, expected: int
) -> None:
    """Probe."""
    c = pre.deploy_contract(Op.SSTORE(0, Op.GAS) + Op.STOP)
    tx = Transaction(
        to=c, gas_limit=tx_gas, sender=pre.fund_eoa(amount=10**18)
    )
    state_test(pre=pre, post={c: Account(storage={0: expected})}, tx=tx)
