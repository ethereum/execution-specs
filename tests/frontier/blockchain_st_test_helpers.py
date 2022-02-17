from functools import partial

from ..helpers.load import Load, run_blockchain_st_test

run_frontier_blockchain_st_tests = partial(
    run_blockchain_st_test, load=Load("Frontier", "frontier")
)
