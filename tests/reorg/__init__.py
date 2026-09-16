"""
Engine API reorganization tests.

Cross-client, deterministic reorg conformance tests expressed as a block DAG
plus a step script (``ReorgTest``), consumed via ``consume reorg`` in hive.

Forkchoice behaviour itself does not change between forks, so these tests
carry no fork-specific expectations; they are filled for every fork from
Cancun on because the Engine API method versions, the payload fields and the
``getPayload`` response shape do change, and a fixture that exercises the
wrong version is the failure mode this catches. Two tests are marked
``valid_at_transition_to`` instead, and cover a reorg whose branches straddle
a fork boundary.
"""
