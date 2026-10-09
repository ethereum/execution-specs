"""Constants shared by the ported static tests."""

HIGH_GAS_LIMIT = 2**63 - 1
"""
Block gas limit for tests whose transactions exceed the default block gas
limit.

Every such test uses the same value so they share a genesis environment.
"""
