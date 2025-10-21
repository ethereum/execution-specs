"""
Benchmark code generator classes for creating
optimized bytecode patterns.
"""

from dataclasses import dataclass

from ethereum_test_base_types import Address
from ethereum_test_forks import Fork
from ethereum_test_specs.benchmark import BenchmarkCodeGenerator
from ethereum_test_types import Alloc
from ethereum_test_vm.opcodes import Opcodes as Op


@dataclass(kw_only=True)
class JumpLoopGenerator(BenchmarkCodeGenerator):
    """Generates bytecode that loops execution using JUMP operations."""

    def deploy_contracts(self, *, pre: Alloc, fork: Fork) -> Address:
        """Deploy the looping contract."""
        # Benchmark Test Structure:
        # setup + JUMPDEST +
        # attack + attack + ... + attack +
        # cleanup + JUMP(setup_length)
        code = self.generate_repeated_code(
            repeated_code=self.attack_block,
            setup=self.setup,
            cleanup=self.cleanup,
            fork=fork,
        )
        self._contract_address = pre.deploy_contract(code=code)
        return self._contract_address


@dataclass(kw_only=True)
class ExtCallGenerator(BenchmarkCodeGenerator):
    """
    Generates bytecode that fills the contract to
    maximum allowed code size.
    """

    contract_balance: int = 0

    def deploy_contracts(self, *, pre: Alloc, fork: Fork) -> Address:
        """Deploy both target and caller contracts."""
        # Benchmark Test Structure:
        # There are two contracts:
        # 1. The target contract that executes certain operation
        #    but not loop (e.g. PUSH)
        # 2. The loop contract that calls the target contract in a loop

        pushed_stack_items = self.attack_block.pushed_stack_items
        popped_stack_items = self.attack_block.popped_stack_items
        stack_delta = pushed_stack_items - popped_stack_items

        max_iterations = fork.max_code_size() // len(self.attack_block)

        if stack_delta > 0:
            max_iterations = min(
                fork.max_stack_height() // stack_delta, max_iterations
            )

        # Deploy target contract that contains the actual attack block
        self._target_contract_address = pre.deploy_contract(
            code=self.setup + self.attack_block * max_iterations,
            balance=self.contract_balance,
        )

        # Create caller contract that repeatedly calls the target contract
        # attack = POP(
        #             STATICCALL(GAS, target_contract_address, 0, 0, 0, 0)
        #          )
        #
        # setup + JUMPDEST + attack + attack + ... + attack +
        # JUMP(setup_length)
        code_sequence = Op.POP(
            Op.STATICCALL(Op.GAS, self._target_contract_address, 0, 0, 0, 0)
        )

        caller_code = self.generate_repeated_code(
            repeated_code=code_sequence, cleanup=self.cleanup, fork=fork
        )
        self._contract_address = pre.deploy_contract(code=caller_code)
        return self._contract_address
