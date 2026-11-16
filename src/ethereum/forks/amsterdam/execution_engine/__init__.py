"""
The execution engine is the interface defined by the consensus layer in the
consensus-specs for calling the execution layer.

This package has the part of that interface that validates a new payload: the
types of the request that the consensus layer sends, and the functions that
check it and execute its block. They correspond to the `ExecutionEngine`
abstraction in the consensus-specs and can change over forks.
"""
