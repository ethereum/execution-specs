"""Tests for EIP-8368 (CPSB recalibration for new gas limit)."""

# TODO: Tests marked `valid_before("EIP8368")` (grepping the marker
#  enumerates the worklist) pin gas budgets or capacities derived at
#  the original cost per state byte. Re-derive each budget through
#  the fork APIs, or park the scenario permanently, once the EIP's
#  final value lands.
