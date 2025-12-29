"""
Benchmark code generator classes for creating
optimized bytecode patterns.
"""

from dataclasses import dataclass, field

from execution_testing.base_types import Address
from execution_testing.forks import Fork
from execution_testing.specs.benchmark import BenchmarkCodeGenerator
from execution_testing.test_types import Alloc
from execution_testing.vm import Bytecode, Op


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

        # Account for setup code length when calculating max iterations
        available_space = fork.max_code_size() - len(self.setup)
        max_iterations = (
            available_space // len(self.attack_block)
            if len(self.attack_block) > 0
            else 0
        )
        max_stack_height = fork.max_stack_height() - setup_stack_delta

        if attack_block_stack_delta > 0:
            max_iterations = min(
                max_stack_height // attack_block_stack_delta, max_iterations
            )

        code = self.setup + self.attack_block * max_iterations
        # Pad the code to the maximum code size.
        if self.code_padding_opcode is not None:
            padding_size = fork.max_code_size() - len(code)
            if padding_size > 0:
                code += self.code_padding_opcode * padding_size

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


@dataclass(kw_only=True)
class XCallGenerator(BenchmarkCodeGenerator):
    """Generator for CALL, STATICCALL, DELEGATECALL, and CALLCODE benchmarks."""

    attack_block: Bytecode = field(default_factory=Bytecode)
    opcode: Op = Op.STATICCALL
    value: int = 0
    memory_size: int = 0
    target_code_size: int = 1024
    warm_access: bool = True
    contract_balance: int = 0
    _base_address: int = 0

    def _build_call_opcode(self, address_expr: Address | Bytecode) -> Bytecode:
        """Build the CALL opcode with value parameter for CALL/CALLCODE."""
        value = [self.value] if self.opcode in [Op.CALL, Op.CALLCODE] else []
        return self.opcode(
            Op.GAS,
            address_expr,
            *value,
            Op.PUSH0,
            self.memory_size,
            Op.PUSH0,
            Op.PUSH0,
        )

    def _deploy_warm_target(self, *, pre: Alloc) -> Address:
        """Deploy a single target contract for warm access."""
        target_code = Op.JUMPDEST * self.target_code_size

        self._target_contract_address = pre.deploy_contract(
            code=target_code,
            balance=self.contract_balance,
        )
        return self._target_contract_address

    def _setup_cold_base_address(self, *, pre: Alloc) -> int:
        """Set up base address for cold access targets."""
        self._base_address = int.from_bytes(pre.fund_eoa(), "big")
        return self._base_address

    def _build_warm_attack_block(self) -> Bytecode:
        """Build attack block for warm access."""
        call_opcode = self._build_call_opcode(self._target_contract_address)
        return Op.POP(call_opcode)

    def _build_cold_attack_block(self) -> Bytecode:
        """Build attack block for cold access (call to base + counter)."""
        call_opcode = self._build_call_opcode(
            Op.ADD(self._base_address, Op.DUP1)
        )
        return Op.POP(call_opcode) + Op.PUSH1(1) + Op.SWAP1 + Op.SUB

    def _build_fixed_count_loop(
        self, *, call_block: Bytecode, total_iterations: int
    ) -> Bytecode:
        """Build a fixed-count loop with counter from total_iterations down to 0."""
        prefix = Op.CALLDATACOPY(
            Op.PUSH0, Op.PUSH0, Op.CALLDATASIZE
        ) + Op.PUSH4(total_iterations)
        loop_body = (
            call_block
            + Op.DUP1
            + Op.ISZERO
            + Op.ISZERO
            + Op.PUSH1(len(prefix))
            + Op.JUMPI
        )
        return prefix + Op.JUMPDEST + loop_body + Op.STOP

    def _get_num_iterations(self) -> int:
        """Get number of iterations for cold access loop."""
        if self.fixed_opcode_count is not None:
            return self.fixed_opcode_count * 1000
        return 100000

    def deploy_contracts(self, *, pre: Alloc, fork: Fork) -> Address:
        """Deploy contracts for gas-benchmark-values mode."""
        if self.warm_access:
            self._deploy_warm_target(pre=pre)
            attack_block = self._build_warm_attack_block()
            setup = self.setup
        else:
            self._setup_cold_base_address(pre=pre)
            num_iterations = self._get_num_iterations()
            setup = Op.PUSH3(num_iterations)
            attack_block = self._build_cold_attack_block()

        caller_code = self.generate_repeated_code(
            setup=setup,
            repeated_code=attack_block,
            cleanup=self.cleanup,
            fork=fork,
        )

        self._contract_address = pre.deploy_contract(
            code=caller_code,
            balance=self.contract_balance,
        )
        return self._contract_address

    def deploy_fix_count_contracts(self, *, pre: Alloc, fork: Fork) -> Address:
        """Deploy contracts for fixed-opcode-count mode."""
        iterations = self.fixed_opcode_count
        assert iterations is not None, "fixed_opcode_count is not set"
        total_iterations = iterations * 1000

        if self.warm_access:
            self._deploy_warm_target(pre=pre)
            call_opcode = self._build_call_opcode(
                self._target_contract_address
            )
        else:
            self._setup_cold_base_address(pre=pre)
            call_opcode = self._build_call_opcode(
                Op.ADD(self._base_address, Op.DUP1)
            )
        call_block = Op.POP(call_opcode) + Op.PUSH1(1) + Op.SWAP1 + Op.SUB

        code = self._build_fixed_count_loop(
            call_block=call_block,
            total_iterations=total_iterations,
        )

        self._validate_code_size(code, fork)
        self._contract_address = pre.deploy_contract(
            code=code,
            balance=self.contract_balance,
        )
        return self._contract_address
