"""Loop-construction helpers for benchmark attack contracts."""

from execution_testing import Op

# Standard While-loop decrement-and-test condition.
#
# Expects the iteration counter on top of the stack:
#   [counter] → SUB(counter, 1) → continue if nonzero
DECREMENT_COUNTER_CONDITION = (
    Op.PUSH1(1) + Op.SWAP1 + Op.SUB + Op.DUP1 + Op.ISZERO + Op.ISZERO
)
