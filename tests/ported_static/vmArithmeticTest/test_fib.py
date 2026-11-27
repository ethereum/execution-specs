"""
Test a Fibonacci sequence computed in storage.

The original tests were written by Ori Pomerantz.

Ported from:
state_tests/VMTests/vmArithmeticTest/fibFiller.yml

@manually-enhanced: Do not overwrite. Built from a loop over the index.

The contract starts with the first two Fibonacci numbers in slots 0 and
1, and stores each later one as the sum of the two slots before it, so
every step reads back what the previous steps stored. The expected
storage is the sequence computed in Python.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

pytestmark = [
    pytest.mark.ported_from(
        ["state_tests/VMTests/vmArithmeticTest/fibFiller.yml"],
    ),
    pytest.mark.valid_from("Frontier"),
]

FIRST_FIBONACCI_NUMBERS = [0, 1]
LAST_INDEX = 10


def test_fib(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Store each Fibonacci number as the sum of the two before it."""
    fibonacci = list(FIRST_FIBONACCI_NUMBERS)
    code = Bytecode()
    for n in range(len(fibonacci), LAST_INDEX + 1):
        code += Op.SSTORE(n, Op.ADD(Op.SLOAD(n - 1), Op.SLOAD(n - 2)))
        fibonacci.append(fibonacci[n - 1] + fibonacci[n - 2])
    code += Op.STOP

    contract = pre.deploy_contract(
        code=code, storage=dict(enumerate(FIRST_FIBONACCI_NUMBERS))
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        protected=fork.supports_protected_txs(),
    )
    post = {contract: Account(storage=dict(enumerate(fibonacci)))}
    state_test(pre=pre, post=post, tx=tx)
