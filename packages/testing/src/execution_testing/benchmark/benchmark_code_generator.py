"""
Benchmark code generator classes for creating
optimized bytecode patterns.
"""

from dataclasses import dataclass

from execution_testing.base_types import Address
from execution_testing.forks import Fork
from execution_testing.specs.benchmark import BenchmarkCodeGenerator
from execution_testing.test_types import Alloc
from execution_testing.vm import Op


@dataclass(kw_only=True)
class JumpLoopGenerator(BenchmarkCodeGenerator):
    """Generates bytecode that loops execution using JUMP operations."""

    contract_balance: int = 0

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
        self._contract_address = pre.deploy_contract(
            code=code, balance=self.contract_balance
        )
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

        attack_block_stack_delta = (
            self.attack_block.pushed_stack_items
            - self.attack_block.popped_stack_items
        )
        assert attack_block_stack_delta >= 0, (
            "attack block stack delta must be non-negative"
        )

        setup_stack_delta = (
            self.setup.pushed_stack_items - self.setup.popped_stack_items
        )
        assert setup_stack_delta >= 0, "setup stack delta must be non-negative"

        max_iterations = fork.max_code_size() // len(self.attack_block)
        max_stack_height = fork.max_stack_height() - setup_stack_delta

        if attack_block_stack_delta > 0:
            max_iterations = min(
                max_stack_height // attack_block_stack_delta, max_iterations
            )

        code = self.setup + self.attack_block * max_iterations
        # Pad the code to the maximum code size.
        if self.code_padding_opcode is not None:
            code += self.code_padding_opcode * (
                fork.max_code_size() - len(code)
            )

        self._validate_code_size(code, fork)

        # Deploy target contract that contains the actual attack block
        self._target_contract_address = pre.deploy_contract(
            code=code,
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
            Op.STATICCALL(
                Op.GAS,
                self._target_contract_address,
                Op.PUSH0,
                Op.CALLDATASIZE,
                Op.PUSH0,
                Op.PUSH0,
            )
        )

        caller_code = self.generate_repeated_code(
            setup=Op.CALLDATACOPY(Op.PUSH0, Op.PUSH0, Op.CALLDATASIZE),
            repeated_code=code_sequence,
            cleanup=self.cleanup,
            fork=fork,
        )

        self._contract_address = pre.deploy_contract(code=caller_code)
        return self._contract_address
