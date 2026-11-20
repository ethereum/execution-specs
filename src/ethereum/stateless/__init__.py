"""
Parts of stateless validation that don't depend on a fork.

Stateless validation executes a block against an _execution witness_ instead
of a full copy of the state. [`ExecutionWitness`] is the witness itself, and
[`build_execution_witness`][builder] builds one from what a block read and
wrote while it executed. The parts that name a fork's header, payload or
requests live in each fork's `stateless` module.

[`ExecutionWitness`]: ref:ethereum.stateless.types.ExecutionWitness
[builder]: ref:ethereum.stateless.witness_builder.build_execution_witness
"""
