"""Ethereum benchmark test spec definition and filler."""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Generator,
    List,
    Sequence,
    Type,
)

import pytest
from pydantic import ConfigDict, Field

from execution_testing.base_types import Address, HexNumber
from execution_testing.client_clis import TransitionTool
from execution_testing.client_clis.cli_types import OpcodeCount
from execution_testing.exceptions import (
    BlockException,
    TransactionException,
)
from execution_testing.execution import (
    BaseExecute,
    ExecuteFormat,
    LabeledExecuteFormat,
    TransactionPost,
)
from execution_testing.fixtures import (
    BlockchainEngineFixture,
    BlockchainEngineXFixture,
    BlockchainFixture,
    FixtureFormat,
    LabeledFixtureFormat,
)
from execution_testing.forks import Fork
from execution_testing.test_types import Alloc, Environment, Transaction
from execution_testing.vm import Bytecode, Op

from .base import BaseTest, FillResult
from .blockchain import Block, BlockchainTest


@dataclass(kw_only=True)
class BenchmarkCodeGenerator(ABC):
    """Abstract base class for generating benchmark bytecode."""

    attack_block: Bytecode
    setup: Bytecode = field(default_factory=Bytecode)
    cleanup: Bytecode = field(default_factory=Bytecode)
    tx_kwargs: Dict[str, Any] = field(default_factory=dict)
    fixed_opcode_count: float | None = None
    code_padding_opcode: Op | None = None
    _contract_address: Address | None = None
    _inner_iterations: int = 1000

    @abstractmethod
    def deploy_contracts(self, *, pre: Alloc, fork: Fork) -> Address:
        """Deploy any contracts needed for the benchmark."""
        ...

    def deploy_fix_count_contracts(self, *, pre: Alloc, fork: Fork) -> Address:
        """Deploy the contract with a fixed opcode count."""
        code = self.generate_repeated_code(
            repeated_code=self.attack_block,
            setup=self.setup,
            cleanup=self.cleanup,
            fork=fork,
        )
        self._target_contract_address = pre.deploy_contract(code=code)

        assert self.fixed_opcode_count is not None, (
            "fixed_opcode_count is not set"
        )
        # Adjust outer loop iterations based on inner iterations
        if self.fixed_opcode_count < 1.0:
            # < 1000 opcodes, outer = 1 as inner already set to exact count
            iterations = 1
        else:
            # >= 1000: calculate outer iterations from target / inner
            target_opcodes = int(self.fixed_opcode_count * 1000)
            iterations = target_opcodes // self._inner_iterations
        prefix = Op.CALLDATACOPY(
            Op.PUSH0, Op.PUSH0, Op.CALLDATASIZE
        ) + Op.PUSH4(iterations)

        is_state_changing_set = [
            Op.SSTORE,
            Op.TSTORE,
            Op.CREATE,
            Op.CREATE2,
            Op.CALL,
            Op.CALLCODE,
            Op.SELFDESTRUCT,
            Op.LOG0,
            Op.LOG1,
            Op.LOG2,
            Op.LOG3,
            Op.LOG4,
        ]

        # Select CALL for state-changing opcodes, STATICCALL otherwise
        uses_state_changing_opcode = any(
            bytes(opcode) in bytes(self.attack_block)
            for opcode in is_state_changing_set
        )
        call_opcode = Op.CALL if uses_state_changing_opcode else Op.STATICCALL

        opcode = (
            prefix
            + Op.JUMPDEST
            + Op.POP(
                call_opcode(
                    gas=Op.GAS,
                    address=self._target_contract_address,
                    args_offset=0,
                    args_size=Op.CALLDATASIZE,
                    ret_offset=0,
                    ret_size=0,
                )
            )
            + Op.PUSH1(1)
            + Op.SWAP1
            + Op.SUB
            + Op.DUP1
            + Op.ISZERO
            + Op.ISZERO
            + Op.PUSH1(len(prefix))
            + Op.JUMPI
            + Op.STOP
        )
        self._validate_code_size(opcode, fork)

        self._contract_address = pre.deploy_contract(code=opcode)
        return self._contract_address

    def generate_transaction(
        self, *, pre: Alloc, gas_benchmark_value: int
    ) -> Transaction:
        """Generate transaction that executes the looping contract."""
        assert self._contract_address is not None
        if "gas_limit" not in self.tx_kwargs:
            self.tx_kwargs["gas_limit"] = gas_benchmark_value

        return Transaction(
            to=self._contract_address,
            sender=pre.fund_eoa(),
            **self.tx_kwargs,
        )

    def generate_repeated_code(
        self,
        *,
        repeated_code: Bytecode,
        setup: Bytecode | None = None,
        cleanup: Bytecode | None = None,
        fork: Fork,
    ) -> Bytecode:
        """
        Calculate the maximum number of iterations that
        can fit in the code size limit.
        """
        assert len(repeated_code) > 0, "repeated_code cannot be empty"
        max_code_size = fork.max_code_size()
        if setup is None:
            setup = Bytecode()
        if cleanup is None:
            cleanup = Bytecode()
        overhead = (
            len(setup)
            + len(Op.JUMPDEST)
            + len(cleanup)
            + len(Op.JUMP(len(setup)))
        )
        available_space = max_code_size - overhead
        max_iterations = available_space // len(repeated_code)

        # Use fixed_opcode_count if provided, otherwise fill to max
        # Iteration Logic: The goal is to set the total operation count
        # proportional to a 'fixed_opcode_count' multiplied by 1000,
        # across two contracts (Loop M * Target N).

        # --- 1. Determine Inner Iterations (N) ---
        # The Target Contract's loop count is determined by block filling,
        # capped at 1000.
        #
        # 1a. Calculate 'max_iterations' to fill the block.
        # 1b. The Inner Iteration count (N) is capped at 1000.
        # 1c. If the calculated N is less than 1000, use 250 as fallback.

        # --- 2. Determine Outer Iterations (M) ---
        # The Loop Contract's call count (M) is set to ensure the final
        # total execution is consistent.
        #
        # 2a. If N=1000: M = fixed_opcode_count (Total: foc*1000)
        # 2b. If N=250: M = fixed_opcode_count*4 (Total: same as above)
        #
        # --- 3. Sub-1K Case (fixed_opcode_count < 1.0) ---
        # For Sub-1K counts (e.g., 0.25 = 250 opcodes): N = exact count, M = 1.
        if self.fixed_opcode_count is not None:
            if self.fixed_opcode_count < 0.001:
                raise ValueError(
                    f"fixed_opcode_count must be >= 0.001 (1 opcode), "
                    f"got {self.fixed_opcode_count}"
                )
            if self.fixed_opcode_count < 1.0:
                # < 1000 opcodes, inner = exact count, outer = 1
                self._inner_iterations = min(
                    max_iterations, int(self.fixed_opcode_count * 1000)
                )
            else:
                # >= 1000 opcodes: use 250 inner iterations (0.25K granularity)
                target_opcodes = int(self.fixed_opcode_count * 1000)

                if max_iterations >= 250 and target_opcodes % 250 == 0:
                    inner_iterations = 250
                elif max_iterations >= target_opcodes:
                    # Use exact count as inner with outer = 1
                    inner_iterations = target_opcodes
                else:
                    suggested_lo = ((target_opcodes // 250) * 250) / 1000
                    suggested_hi = ((target_opcodes // 250 + 1) * 250) / 1000
                    raise ValueError(
                        f"fixed_opcode_count {self.fixed_opcode_count} "
                        f"({target_opcodes} opcodes) exceeds max contract "
                        f"size for this attack block.\n"
                        f"Contract size limit allows up to {max_iterations} "
                        f"opcodes ({max_iterations / 1000:.3f}K) in the "
                        f"inner loop.\n"
                        f"For counts above this limit, use multiples of 0.25K "
                        f"(e.g., {suggested_lo:.2f} or {suggested_hi:.2f})."
                    )
                self._inner_iterations = inner_iterations

        # TODO: Unify the PUSH0 and PUSH1 usage.
        iterations = (
            self._inner_iterations
            if self.fixed_opcode_count
            else max_iterations
        )
        code = setup + Op.JUMPDEST + repeated_code * iterations
        if self.fixed_opcode_count is None:
            code += cleanup + (
                Op.JUMP(len(setup)) if len(setup) > 0 else Op.PUSH0 + Op.JUMP
            )
        # Pad the code to the maximum code size.
        if self.code_padding_opcode is not None:
            padding_size = max_code_size - len(code) - 1
            if padding_size > 0:
                code += Op.STOP + self.code_padding_opcode * padding_size
        self._validate_code_size(code, fork)

        return code

    def _validate_code_size(self, code: Bytecode, fork: Fork) -> None:
        """Validate that the generated code fits within size limits."""
        if len(code) > fork.max_code_size():
            raise ValueError(
                f"Generated code size {len(code)} exceeds maximum "
                f"allowed size {fork.max_code_size()}"
            )


class BenchmarkTest(BaseTest):
    """Test type designed specifically for benchmark test cases."""

    model_config = ConfigDict(extra="forbid")

    pre: Alloc = Field(default_factory=Alloc)
    post: Alloc = Field(default_factory=Alloc)
    tx: Transaction | None = None
    setup_blocks: List[Block] = Field(default_factory=list)
    blocks: List[Block] | None = None
    block_exception: (
        List[TransactionException | BlockException]
        | TransactionException
        | BlockException
        | None
    ) = None
    env: Environment = Field(default_factory=Environment)
    expected_benchmark_gas_used: int | None = None
    gas_benchmark_value: int = Field(
        default_factory=lambda: int(Environment().gas_limit)
    )
    fixed_opcode_count: float | None = None
    target_opcode: Op | None = None
    code_generator: BenchmarkCodeGenerator | None = None
    # By default, benchmark tests require neither of these
    include_full_post_state_in_output: bool = False
    include_tx_receipts_in_output: bool = False

    supported_fixture_formats: ClassVar[
        Sequence[FixtureFormat | LabeledFixtureFormat]
    ] = [
        BlockchainFixture,
        BlockchainEngineFixture,
        BlockchainEngineXFixture,
    ]

    supported_execute_formats: ClassVar[Sequence[LabeledExecuteFormat]] = [
        LabeledExecuteFormat(
            TransactionPost,
            "benchmark_test",
            "An execute test derived from a benchmark test",
        ),
    ]

    supported_markers: ClassVar[Dict[str, str]] = {
        "blockchain_test_engine_only": (
            "Only generate a blockchain test engine fixture"
        ),
        "blockchain_test_only": "Only generate a blockchain test fixture",
        "repricing": "Mark test as reference test for gas repricing analysis",
    }

    def model_post_init(self, __context: Any, /) -> None:
        """
        Model post-init to assert that the custom pre-allocation was
        provided and the default was not used.
        """
        super().model_post_init(__context)
        assert "pre" in self.model_fields_set, (
            "pre allocation was not provided"
        )

        set_props = [
            name
            for name, val in [
                ("code_generator", self.code_generator),
                ("blocks", self.blocks),
                ("tx", self.tx),
            ]
            if val is not None
        ]

        if len(set_props) != 1:
            raise ValueError(
                f"Exactly one must be set, but got {len(set_props)}: "
                f"{', '.join(set_props)}"
            )

        blocks: List[Block] = self.setup_blocks

        if (
            self.fixed_opcode_count is not None
            and self.code_generator is None
            and self.target_opcode is None
        ):
            pytest.skip(
                "Cannot run fixed opcode count tests without a "
                "code generator or a target opcode set"
            )

        if self.code_generator is not None:
            # Inject fixed_opcode_count into the code generator if provided
            self.code_generator.fixed_opcode_count = self.fixed_opcode_count

            # In fixed opcode count mode, skip gas validation since we're
            # measuring performance by operation count, not gas usage
            if self.fixed_opcode_count is not None:
                self.skip_gas_used_validation = True
                generated_blocks = (
                    self.generate_fixed_opcode_count_transactions()
                )
            else:
                generated_blocks = self.generate_blocks_from_code_generator()
            blocks += generated_blocks

        elif self.blocks is not None:
            blocks += self.blocks

        elif self.tx is not None:
            gas_limit = (
                self.fork.transaction_gas_limit_cap()
                or self.gas_benchmark_value
            )

            transactions = self.split_transaction(self.tx, gas_limit)

            blocks.append(Block(txs=transactions))

        else:
            raise ValueError(
                "Cannot create BlockchainTest without a code generator, "
                "transactions, or blocks"
            )

        self.blocks = blocks

    @classmethod
    def pytest_parameter_name(cls) -> str:
        """
        Return the parameter name used in pytest
        to select this spec type.
        """
        return "benchmark_test"

    @classmethod
    def discard_fixture_format_by_marks(
        cls,
        fixture_format: FixtureFormat,
        fork: Fork,
        markers: List[pytest.Mark],
    ) -> bool:
        """
        Discard a fixture format from filling if the
        appropriate marker is used.
        """
        del fork

        if "blockchain_test_only" in [m.name for m in markers]:
            return fixture_format != BlockchainFixture
        if "blockchain_test_engine_only" in [m.name for m in markers]:
            return fixture_format != BlockchainEngineFixture
        return False

    def get_genesis_environment(self) -> Environment:
        """Get the genesis environment for this benchmark test."""
        return self.generate_blockchain_test().get_genesis_environment()

    def split_transaction(
        self, tx: Transaction, gas_limit_cap: int | None
    ) -> List[Transaction]:
        """
        Split a transaction that exceeds the gas
        limit cap into multiple transactions.
        """
        if gas_limit_cap is None:
            tx.gas_limit = HexNumber(self.gas_benchmark_value)
            return [tx]

        if gas_limit_cap >= self.gas_benchmark_value:
            tx.gas_limit = HexNumber(self.gas_benchmark_value)
            return [tx]

        num_splits = math.ceil(self.gas_benchmark_value / gas_limit_cap)
        remaining_gas = self.gas_benchmark_value

        split_transactions = []
        for i in range(num_splits):
            split_tx = tx.model_copy()
            split_tx.gas_limit = HexNumber(
                remaining_gas if i == num_splits - 1 else gas_limit_cap
            )
            remaining_gas -= gas_limit_cap
            split_tx.nonce = HexNumber(tx.nonce + i)
            split_transactions.append(split_tx)

        return split_transactions

    def generate_blocks_from_code_generator(self) -> List[Block]:
        """Generate blocks using the code generator."""
        if self.code_generator is None:
            raise Exception("Code generator is not set")
        self.code_generator.deploy_contracts(pre=self.pre, fork=self.fork)
        gas_limit = (
            self.fork.transaction_gas_limit_cap() or self.gas_benchmark_value
        )
        benchmark_tx = self.code_generator.generate_transaction(
            pre=self.pre, gas_benchmark_value=gas_limit
        )

        execution_txs = self.split_transaction(benchmark_tx, gas_limit)
        execution_block = Block(txs=execution_txs)

        return [execution_block]

    def generate_fixed_opcode_count_transactions(self) -> List[Block]:
        """Generate transactions with a fixed opcode count."""
        if self.code_generator is None:
            raise Exception("Code generator is not set")
        self.code_generator.deploy_fix_count_contracts(
            pre=self.pre, fork=self.fork
        )
        gas_limit = (
            self.fork.transaction_gas_limit_cap() or self.gas_benchmark_value
        )
        benchmark_tx = self.code_generator.generate_transaction(
            pre=self.pre, gas_benchmark_value=gas_limit
        )
        execution_block = Block(txs=[benchmark_tx])
        return [execution_block]

    def generate_blockchain_test(self) -> BlockchainTest:
        """Create a BlockchainTest from this BenchmarkTest."""
        return BlockchainTest.from_test(
            base_test=self,
            genesis_environment=self.env,
            pre=self.pre,
            post=self.post,
            blocks=self.blocks,
            include_full_post_state_in_output=self.include_full_post_state_in_output,
            include_tx_receipts_in_output=self.include_tx_receipts_in_output,
        )

    def _verify_target_opcode_count(
        self, opcode_count: OpcodeCount | None
    ) -> None:
        """Verify target opcode was executed the expected number of times."""
        # Skip validation if opcode count is not available
        if opcode_count is None:
            return

        assert self.target_opcode is not None, "target_opcode is not set"
        assert self.fixed_opcode_count is not None, (
            "fixed_opcode_count is not set"
        )

        # fixed_opcode_count is in thousands units
        expected = self.fixed_opcode_count * 1000

        actual = opcode_count.root.get(self.target_opcode, 0)
        tolerance = expected * 0.05  # 5% tolerance

        if abs(actual - expected) > tolerance:
            raise ValueError(
                f"Target opcode {self.target_opcode} count mismatch: "
                f"expected ~{expected} (±5%), got {actual}"
            )

    def generate(
        self,
        t8n: TransitionTool,
        fixture_format: FixtureFormat,
    ) -> FillResult:
        """Generate the blockchain test fixture."""
        self.check_exception_test(
            exception=self.tx.error is not None if self.tx else False
        )
        if fixture_format in BlockchainTest.supported_fixture_formats:
            fill_result = self.generate_blockchain_test().generate(
                t8n=t8n, fixture_format=fixture_format
            )

            # Verify target opcode count if specified
            if (
                self.target_opcode is not None
                and self.fixed_opcode_count is not None
            ):
                self._verify_target_opcode_count(
                    fill_result.benchmark_opcode_count
                )
            return fill_result
        else:
            raise Exception(f"Unsupported fixture format: {fixture_format}")

    def execute(
        self,
        *,
        execute_format: ExecuteFormat,
    ) -> BaseExecute:
        """Execute the benchmark test by sending it to the live network."""
        if execute_format == TransactionPost:
            assert self.blocks is not None
            return TransactionPost(
                blocks=[block.txs for block in self.blocks],
                post=self.post,
                benchmark_mode=True,
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


BenchmarkTestSpec = Callable[[str], Generator[BenchmarkTest, None, None]]
BenchmarkTestFiller = Type[BenchmarkTest]
