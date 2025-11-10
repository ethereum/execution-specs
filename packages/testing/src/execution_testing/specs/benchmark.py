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
    BaseFixture,
    BlockchainEngineFixture,
    BlockchainEngineXFixture,
    BlockchainFixture,
    FixtureFormat,
    LabeledFixtureFormat,
)
from execution_testing.forks import Fork
from execution_testing.test_types import Alloc, Environment, Transaction
from execution_testing.vm import Bytecode, Op

from .base import BaseTest
from .blockchain import Block, BlockchainTest


@dataclass(kw_only=True)
class BenchmarkCodeGenerator(ABC):
    """Abstract base class for generating benchmark bytecode."""

    attack_block: Bytecode
    setup: Bytecode = field(default_factory=Bytecode)
    cleanup: Bytecode = field(default_factory=Bytecode)
    tx_kwargs: Dict[str, Any] = field(default_factory=dict)
    _contract_address: Address | None = None

    @abstractmethod
    def deploy_contracts(self, *, pre: Alloc, fork: Fork) -> Address:
        """Deploy any contracts needed for the benchmark."""
        ...

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

        # TODO: Unify the PUSH0 and PUSH1 usage.
        code = setup + Op.JUMPDEST + repeated_code * max_iterations + cleanup
        code += Op.JUMP(len(setup)) if len(setup) > 0 else Op.PUSH0 + Op.JUMP
        self._validate_code_size(code, fork)

        return code

    def _validate_code_size(self, code: Bytecode, fork: Fork) -> None:
        """Validate that the generated code fits within size limits."""
        if len(code) > fork.max_code_size():
            raise ValueError(
                f"Generated code size {len(code)} exceeds maximum allowed size "
                f"{fork.max_code_size()}"
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
    code_generator: BenchmarkCodeGenerator | None = None

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
        "blockchain_test_engine_only": "Only generate a blockchain test engine fixture",
        "blockchain_test_only": "Only generate a blockchain test fixture",
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
                f"Exactly one must be set, but got {len(set_props)}: {', '.join(set_props)}"
            )

        blocks: List[Block] = self.setup_blocks

        if self.code_generator is not None:
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
                "Cannot create BlockchainTest without a code generator, transactions, or blocks"
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

    def generate_blockchain_test(self) -> BlockchainTest:
        """Create a BlockchainTest from this BenchmarkTest."""
        return BlockchainTest.from_test(
            base_test=self,
            genesis_environment=self.env,
            pre=self.pre,
            post=self.post,
            blocks=self.blocks,
        )

    def generate(
        self,
        t8n: TransitionTool,
        fixture_format: FixtureFormat,
    ) -> BaseFixture:
        """Generate the blockchain test fixture."""
        self.check_exception_test(
            exception=self.tx.error is not None if self.tx else False
        )
        if fixture_format in BlockchainTest.supported_fixture_formats:
            return self.generate_blockchain_test().generate(
                t8n=t8n, fixture_format=fixture_format
            )
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
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


BenchmarkTestSpec = Callable[[str], Generator[BenchmarkTest, None, None]]
BenchmarkTestFiller = Type[BenchmarkTest]
