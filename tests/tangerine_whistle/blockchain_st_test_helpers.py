from functools import partial

from ..helpers.load import Load, run_blockchain_st_test

run_tangerine_whistle_blockchain_st_tests = partial(
    run_blockchain_st_test, load=Load("EIP150", "tangerine_whistle")
)
