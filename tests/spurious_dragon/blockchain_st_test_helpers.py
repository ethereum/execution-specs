from functools import partial

from ..helpers.load import Load, run_blockchain_st_test

run_spurious_dragon_blockchain_st_tests = partial(
    run_blockchain_st_test, load=Load("EIP158", "spurious_dragon")
)
