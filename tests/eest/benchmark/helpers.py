"""Helper functions for the EVM benchmark worst-case tests."""

from ethereum_test_forks import Fork
from ethereum_test_tools import Bytecode
from ethereum_test_tools.vm.opcode import Opcodes as Op


def code_loop_precompile_call(calldata: Bytecode, attack_block: Bytecode, fork: Fork):
    """Create a code loop that calls a precompile with the given calldata."""
    max_code_size = fork.max_code_size()

    # The attack contract is: CALLDATA_PREP + #JUMPDEST + [attack_block]* + JUMP(#)
    jumpdest = Op.JUMPDEST
    jump_back = Op.JUMP(len(calldata))
    max_iters_loop = (max_code_size - len(calldata) - len(jumpdest) - len(jump_back)) // len(
        attack_block
    )
    code = calldata + jumpdest + sum([attack_block] * max_iters_loop) + jump_back
    if len(code) > max_code_size:
        # Must never happen, but keep it as a sanity check.
        raise ValueError(f"Code size {len(code)} exceeds maximum code size {max_code_size}")

    return code
