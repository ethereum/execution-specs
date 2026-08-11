"""
Compare the spec's `eth_simulateV1` against a real client, case by case.

The claim this package exists to keep honest is that a `blockStateCall`
is an ordinary block, so the specification can answer the method exactly
rather than approximately — down to the state root and the block hash,
which no amount of coincidence produces. That claim is only worth
anything if it is measured, and the measurement is only worth anything
if it can be repeated, so the genesis, the vectors, the client harness
and the comparison all live here rather than in a scratch directory.

The pieces:

- [`genesis`] is one description of a chain, rendered two ways: the JSON
  go-ethereum initializes from, and the [`State`] the spec executes
  against. Both sides therefore start from a state that is known
  exactly, and the harness asserts that the two agree on the genesis
  header before it compares anything else.
- [`cases`] holds the request vectors, each with a note saying what it
  is for.
- [`client`] runs go-ethereum out of the hive image and talks JSON-RPC
  to it.
- [`compare`] walks the client's answer against ours, field by field.

Everything is skipped without Docker and the hive client image, so an
ordinary test run never touches it. `--simulate-client` opts in.

[`State`]: ref:ethereum.state_mpt.State
[`cases`]: ref:tests.evm_tools.simulate_conformance.cases
[`client`]: ref:tests.evm_tools.simulate_conformance.client
[`compare`]: ref:tests.evm_tools.simulate_conformance.compare
[`genesis`]: ref:tests.evm_tools.simulate_conformance.genesis
"""
