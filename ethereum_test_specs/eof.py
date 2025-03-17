"""Ethereum EOF test spec definition and filler."""

import subprocess
import warnings
from pathlib import Path
from shutil import which
from subprocess import CompletedProcess
from typing import Callable, ClassVar, Dict, Generator, List, Optional, Sequence, Type

import pytest
from pydantic import Field

from ethereum_clis import EvmoneExceptionMapper, TransitionTool
from ethereum_test_base_types import Account, Bytes, HexNumber
from ethereum_test_exceptions.exceptions import EOFExceptionInstanceOrList, to_pipe_str
from ethereum_test_execution import (
    BaseExecute,
    ExecuteFormat,
    LabeledExecuteFormat,
    TransactionPost,
)
from ethereum_test_fixtures import (
    BaseFixture,
    EOFFixture,
    FixtureFormat,
    LabeledFixtureFormat,
)
from ethereum_test_fixtures.eof import Result, Vector
from ethereum_test_forks import Fork
from ethereum_test_types import EOA, Alloc, Environment, Transaction
from ethereum_test_types.eof.v1 import Container, ContainerKind, Section, SectionKind
from ethereum_test_vm import Opcodes as Op

from .base import BaseTest
from .state import StateTest

existing_tests: Dict[Bytes, str] = {}


class EOFBaseExceptionError(Exception):
    """Base exception class for exceptions raised when verifying EOF code."""

    def __init__(self, message):
        """Initialize the exception with the message."""
        super().__init__(message)

    @staticmethod
    def format_code(code: Bytes, max_length=60) -> str:
        """Avoid printing long bytecode strings in the terminal upon test failure."""
        if len(code) > max_length:
            half_length = max_length // 2 - 5  # Floor; adjust for ellipsis
            return f"{code[:half_length].hex()}...{code[-half_length:].hex()}"
        return code.hex()


class UnexpectedEOFExceptionError(EOFBaseExceptionError):
    """
    Exception used when valid EOF code unexpectedly raises an exception in
    eofparse.
    """

    def __init__(self, *, code: Bytes, got: str):
        """Initialize the exception with the code and the exception message."""
        message = (
            "Expected EOF code to be valid, but an exception occurred:\n"
            f"    Code: {self.format_code(code)}\n"
            f"Expected: No Exception\n"
            f"     Got: {got}"
        )
        super().__init__(message)


class ExpectedEOFExceptionError(EOFBaseExceptionError):
    """
    Exception used when EOF code is expected to raise an exception, but
    eofparse did not raise an exception.
    """

    def __init__(self, *, code: Bytes, expected: str):
        """Initialize the exception with the code and the expected exception message."""
        message = (
            "Expected EOF code to be invalid, but no exception was raised:\n"
            f"    Code: {self.format_code(code)}\n"
            f"Expected: {expected}\n"
            f"     Got: No Exception"
        )
        super().__init__(message)


class EOFExceptionMismatchError(EOFBaseExceptionError):
    """Exception used when the actual EOF exception differs from the expected one."""

    def __init__(self, code: Bytes, expected: str, got: str):
        """Initialize the exception with the code, the expected/actual exception message."""
        message = (
            "EOF code raised a different exception than expected:\n"
            f"    Code: {self.format_code(code)}\n"
            f"Expected: {expected}\n"
            f"     Got: {got}"
        )
        super().__init__(message)


class EOFParse:
    """evmone-eofparse binary."""

    binary: Path

    def __new__(cls):
        """Make EOF binary a singleton."""
        if not hasattr(cls, "instance"):
            cls.instance = super(EOFParse, cls).__new__(cls)
        return cls.instance

    def __init__(
        self,
        binary: Optional[Path | str] = None,
    ):
        """Initialize the EOF binary."""
        if binary is None:
            which_path = which("evmone-eofparse")
            if which_path is not None:
                binary = Path(which_path)
        if binary is None or not Path(binary).exists():
            raise FileNotFoundError(
                "`evmone-eofparse` binary executable not found/not executable."
            )
        self.binary = Path(binary)

    def run(self, *args: str, input_value: str | None = None) -> CompletedProcess:
        """Run evmone with the given arguments."""
        result = subprocess.run(
            [self.binary, *args],
            capture_output=True,
            text=True,
            input=input_value,
        )
        if result.returncode not in [0, 1]:
            raise Exception(
                f"`{self.binary.name}` call failed with return code {result.returncode}."
            )
        return result


class EOFTest(BaseTest):
    """
    Filler type that generates a test for EOF container validation.

    A state test is also automatically generated where the container is wrapped in a
    contract-creating transaction to test deployment/validation on the instantiated blockchain.
    """

    container: Container
    """
    EOF container that will be tested for validity.

    The only supported type at the moment is `ethereum_test_types.eof.v1.Container`.

    If an invalid container needs to be tested, and it cannot be generated using the
    Container class features, the `raw_bytes` field can be used to provide the raw
    container bytes.
    """
    expect_exception: EOFExceptionInstanceOrList | None = None
    """
    Expected exception that the container should raise when parsed by an EOF parser.

    Can be a single exception or a list of exceptions that the container is expected to raise,
    in which case the test will pass if any of the exceptions are raised.

    The list of supported exceptions can be found in the `ethereum_test_exceptions.EOFException`
    class.
    """
    container_kind: ContainerKind = ContainerKind.RUNTIME
    """
    Container kind type that the container should be treated as.

    The container kind can be one of the following:
    - `ContainerKind.INITCODE`: The container is an initcode container.
    - `ContainerKind.RUNTIME`: The container is a runtime container.

    The default value is `ContainerKind.RUNTIME`.
    """
    deployed_container: Container | None = None
    """
    To be used when the container is an initcode container and the expected deployed container is
    known.

    The value is only used when a State Test is generated from this EOF test to set the expected
    deployed container that should be found in the post state.

    If this field is not set, and the container is valid:
      - If the container kind is `ContainerKind.RUNTIME`, the deployed container is assumed to be
        the container itself, and an initcode container that wraps the container is generated
        automatically.
      - If the container kind is `ContainerKind.INITCODE`, `model_post_init` will attempt to infer
        the deployed container from the sections of the init-container, and the first
        container-type section will be used. An error will be raised if the deployed container
        cannot be inferred.

    If the value is set to `None`, it is assumed that the container is invalid and the test will
    expect that no contract is created.

    It is considered an error if:
      - The `deployed_container` field is set and the `container_kind` field is not set to
        `ContainerKind.INITCODE`.
      - The `deployed_container` field is set and the `expect_exception` is not `None`.

    The deployed container is **not** executed at any point during the EOF validation test nor
    the generated State Test. For container runtime testing use the `EOFStateTest` class.
    """
    pre: Alloc | None = None
    """
    Pre alloc object that is used during State Test generation.

    This field is automatically set by the test filler when generating a State Test from this EOF
    test and should otherwise be left unset.
    """
    post: Alloc | None = None
    """
    Post alloc object that is used during State Test generation.

    This field is automatically set by the test filler when generating a State Test from this EOF
    test and is normally not set by the user.
    """
    sender: EOA | None = None
    """
    Sender EOA object that is used during State Test generation.

    This field is automatically set by the `model_post_init` method and should otherwise be left
    unset.
    """

    supported_fixture_formats: ClassVar[Sequence[FixtureFormat | LabeledFixtureFormat]] = [
        EOFFixture
    ] + [
        LabeledFixtureFormat(
            fixture_format,
            f"{fixture_format.format_name}_from_eof_test",
            f"A {fixture_format.format_name} generated from an eof_test.",
        )
        for fixture_format in StateTest.supported_fixture_formats
    ]

    supported_execute_formats: ClassVar[Sequence[ExecuteFormat | LabeledExecuteFormat]] = [
        LabeledExecuteFormat(
            execute_format,
            f"{execute_format.format_name}_from_eof_test",
            f"A {execute_format.format_name} generated from an eof_test.",
        )
        for execute_format in StateTest.supported_execute_formats
    ]

    supported_markers: ClassVar[Dict[str, str]] = {
        "eof_test_only": "Only generate an EOF test fixture",
    }

    @classmethod
    def discard_fixture_format_by_marks(
        cls,
        fixture_format: FixtureFormat,
        fork: Fork,
        markers: List[pytest.Mark],
    ) -> bool:
        """Discard a fixture format from filling if the appropriate marker is used."""
        if "eof_test_only" in [m.name for m in markers]:
            return fixture_format != EOFFixture
        return False

    @classmethod
    def pytest_parameter_name(cls) -> str:
        """Workaround for pytest parameter name."""
        return "eof_test"

    def model_post_init(self, __context):
        """Prepare the test exception based on the container."""
        if self.container.validity_error is not None:
            if self.expect_exception is not None:
                assert self.expect_exception == self.container.validity_error, (
                    f"Container validity error {self.container.validity_error} "
                    f"does not match expected exception {self.expect_exception}."
                )
            self.expect_exception = self.container.validity_error
            assert self.deployed_container is None, (
                "deployed_container must be None for invalid containers."
            )
        if "kind" in self.container.model_fields_set or "container_kind" in self.model_fields_set:
            if (
                "kind" in self.container.model_fields_set
                and "container_kind" in self.model_fields_set
            ):
                assert self.container.kind == self.container_kind, (
                    f"Container kind type {str(self.container.kind)} "
                    f"does not match test {self.container_kind}."
                )
            elif "kind" in self.container.model_fields_set:
                self.container_kind = self.container.kind
            elif "container_kind" in self.model_fields_set:
                self.container.kind = self.container_kind

        assert self.pre is not None, "pre must be set to generate a StateTest."
        self.sender = self.pre.fund_eoa()
        if self.post is None:
            self.post = Alloc()

    def make_eof_test_fixture(
        self,
        *,
        request: pytest.FixtureRequest,
        fork: Fork,
        eips: Optional[List[int]],
    ) -> EOFFixture:
        """Generate the EOF test fixture."""
        container_bytes = Bytes(self.container)
        if container_bytes in existing_tests:
            pytest.fail(
                f"Duplicate EOF test: {container_bytes}, "
                f"existing test: {existing_tests[container_bytes]}"
            )
        existing_tests[container_bytes] = request.node.nodeid
        vectors = [
            Vector(
                code=container_bytes,
                container_kind=self.container_kind,
                results={
                    fork.blockchain_test_network_name(): Result(
                        exception=self.expect_exception,
                        valid=self.expect_exception is None,
                    ),
                },
            )
        ]
        fixture = EOFFixture(vectors=dict(enumerate(vectors)))
        try:
            eof_parse = EOFParse()
        except FileNotFoundError as e:
            warnings.warn(
                f"{e} Skipping EOF fixture verification. Fixtures may be invalid!", stacklevel=2
            )
            return fixture

        for _, vector in fixture.vectors.items():
            expected_result = vector.results.get(fork.blockchain_test_network_name())
            if expected_result is None:
                raise Exception(f"EOF Fixture missing vector result for fork: {fork}")
            args = []
            if vector.container_kind == ContainerKind.INITCODE:
                args.append("--initcode")
            result = eof_parse.run(*args, input_value=str(vector.code))
            self.verify_result(result, expected_result, vector.code)

        return fixture

    def verify_result(self, result: CompletedProcess, expected_result: Result, code: Bytes):
        """Check that the reported exception string matches the expected error."""
        parser = EvmoneExceptionMapper()
        actual_message = result.stdout.strip()
        actual_exception = parser.message_to_exception(actual_message)

        if expected_result.exception is None:
            if "OK" in actual_message:
                return
            else:
                raise UnexpectedEOFExceptionError(
                    code=code, got=f"{actual_exception} ({actual_message})"
                )
        else:
            expected_string = to_pipe_str(expected_result.exception)
            print(expected_string)
            print(actual_exception)
            if "OK" in actual_message:
                raise ExpectedEOFExceptionError(
                    code=code,
                    expected=f"{expected_string}",
                )
            elif actual_exception in expected_result.exception:
                return
            else:
                raise EOFExceptionMismatchError(
                    code=code,
                    expected=f"{expected_string}",
                    got=f"{actual_exception} ({actual_message})",
                )

    def generate_eof_contract_create_transaction(self) -> Transaction:
        """Generate a transaction that creates a contract."""
        assert self.sender is not None, "sender must be set to generate a StateTest."
        assert self.post is not None, "post must be set to generate a StateTest."

        initcode: Container
        deployed_container: Container | Bytes | None = None
        if self.container_kind == ContainerKind.INITCODE:
            initcode = self.container
            if "deployed_container" in self.model_fields_set:
                # In the case of an initcontainer where we know the deployed container,
                # we can use the initcontainer as-is.
                deployed_container = self.deployed_container
            elif self.expect_exception is None:
                # We have a valid init-container, but we don't know the deployed container.
                # Try to infer the deployed container from the sections of the init-container.
                assert self.container.raw_bytes is None, (
                    "deployed_container must be set for initcode containers with raw_bytes."
                )
                for section in self.container.sections:
                    if section.kind == SectionKind.CONTAINER:
                        deployed_container = section.data
                        break

                assert deployed_container is not None, (
                    "Unable to infer deployed container for init-container. "
                    "Use field `deployed_container` to set the expected deployed container."
                )
        else:
            assert self.deployed_container is None, (
                "deployed_container must be None for runtime containers."
            )
            initcode = Container(
                sections=[
                    Section.Code(Op.RETURNCODE[0](0, 0)),
                    Section.Container(self.container),
                ]
            )
            deployed_container = self.container

        tx = Transaction(
            sender=self.sender,
            to=None,
            gas_limit=10_000_000,
            data=initcode,
        )

        if self.expect_exception is not None or deployed_container is None:
            self.post[tx.created_contract] = None
        else:
            self.post[tx.created_contract] = Account(
                code=deployed_container,
            )
        return tx

    def generate_state_test(self, fork: Fork) -> StateTest:
        """Generate the StateTest filler."""
        return StateTest(
            pre=self.pre,
            tx=self.generate_eof_contract_create_transaction(),
            env=Environment(),
            post=self.post,
            t8n_dump_dir=self.t8n_dump_dir,
        )

    def generate(
        self,
        *,
        request: pytest.FixtureRequest,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
        fixture_format: FixtureFormat,
        **_,
    ) -> BaseFixture:
        """Generate the BlockchainTest fixture."""
        if fixture_format == EOFFixture:
            return self.make_eof_test_fixture(request=request, fork=fork, eips=eips)
        elif fixture_format in StateTest.supported_fixture_formats:
            return self.generate_state_test(fork).generate(
                request=request, t8n=t8n, fork=fork, fixture_format=fixture_format, eips=eips
            )
        raise Exception(f"Unknown fixture format: {fixture_format}")

    def execute(
        self,
        *,
        fork: Fork,
        execute_format: ExecuteFormat,
        eips: Optional[List[int]] = None,
    ) -> BaseExecute:
        """Generate the list of test fixtures."""
        if execute_format == TransactionPost:
            return self.generate_state_test(fork).execute(
                fork=fork, execute_format=execute_format, eips=eips
            )
        raise Exception(f"Unsupported execute format: {execute_format}")


EOFTestSpec = Callable[[str], Generator[EOFTest, None, None]]
EOFTestFiller = Type[EOFTest]


class EOFStateTest(EOFTest, Transaction):
    """
    Filler type that generates an EOF test for container validation, and also tests the container
    during runtime using a state test (and blockchain test).

    In the state or blockchain test, the container is first deployed to the pre-allocation and
    then a transaction is sent to the deployed container.

    Container deployment/validation is **not** tested like in the `EOFTest` unless the container
    under test is an initcode container.

    All fields from `ethereum_test_types.Transaction` are available for use in the test.
    """

    gas_limit: HexNumber = Field(HexNumber(10_000_000), serialization_alias="gas")
    """
    Gas limit for the transaction that deploys the container.
    """
    tx_sender_funding_amount: int = 1_000_000_000_000_000_000_000
    """
    Amount of funds to send to the sender EOA before the transaction.
    """
    env: Environment = Field(default_factory=Environment)
    """
    Environment object that is used during State Test generation.
    """
    container_post: Account = Field(default_factory=Account)
    """
    Account object used to verify the container post state.
    """

    supported_fixture_formats: ClassVar[Sequence[FixtureFormat | LabeledFixtureFormat]] = [
        EOFFixture
    ] + [
        LabeledFixtureFormat(
            fixture_format,
            f"eof_{fixture_format.format_name}",
            f"Tests that generate an EOF {fixture_format.format_name}.",
        )
        for fixture_format in StateTest.supported_fixture_formats
    ]

    supported_execute_formats: ClassVar[Sequence[ExecuteFormat | LabeledExecuteFormat]] = [
        LabeledExecuteFormat(
            execute_format,
            f"eof_{execute_format.format_name}",
            f"Tests that generate an EOF {execute_format.format_name}.",
        )
        for execute_format in StateTest.supported_execute_formats
    ]

    @classmethod
    def pytest_parameter_name(cls) -> str:
        """Workaround for pytest parameter name."""
        return "eof_state_test"

    def model_post_init(self, __context):
        """Prepare the transaction parameters required to fill the test."""
        assert self.pre is not None, "pre must be set to generate a StateTest."

        EOFTest.model_post_init(self, __context)

        self.sender = self.pre.fund_eoa(amount=self.tx_sender_funding_amount)
        if self.post is None:
            self.post = Alloc()

        if self.expect_exception is not None:  # Invalid EOF
            self.to = None  # Make EIP-7698 create transaction
            self.data = Bytes(
                bytes(self.container) + self.data
            )  # by concatenating container and tx data.

            # Run transaction model validation
            Transaction.model_post_init(self, __context)

            self.post[self.created_contract] = None  # Expect failure.
        elif self.container_kind == ContainerKind.INITCODE:
            self.to = None  # Make EIP-7698 create transaction
            self.data = Bytes(
                bytes(self.container) + self.data
            )  # by concatenating container and tx data.

            # Run transaction model validation
            Transaction.model_post_init(self, __context)

            self.post[self.created_contract] = self.container_post  # Successful.
        else:
            self.to = self.pre.deploy_contract(code=self.container)

            # Run transaction model validation
            Transaction.model_post_init(self, __context)

            self.post[self.to] = self.container_post

    def generate_state_test(self, fork: Fork) -> StateTest:
        """Generate the StateTest filler."""
        assert self.pre is not None, "pre must be set to generate a StateTest."
        assert self.post is not None, "post must be set to generate a StateTest."

        return StateTest(
            pre=self.pre,
            tx=self,
            env=self.env,
            post=self.post,
            t8n_dump_dir=self.t8n_dump_dir,
        )

    def generate(
        self,
        *,
        request: pytest.FixtureRequest,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
        fixture_format: FixtureFormat,
        **_,
    ) -> BaseFixture:
        """Generate the BlockchainTest fixture."""
        if fixture_format == EOFFixture:
            if Bytes(self.container) in existing_tests:
                # Gracefully skip duplicate tests because one EOFStateTest can generate multiple
                # state fixtures with the same data.
                pytest.skip(f"Duplicate EOF container on EOFStateTest: {request.node.nodeid}")
            return self.make_eof_test_fixture(request=request, fork=fork, eips=eips)
        elif fixture_format in StateTest.supported_fixture_formats:
            return self.generate_state_test(fork).generate(
                request=request, t8n=t8n, fork=fork, fixture_format=fixture_format, eips=eips
            )

        raise Exception(f"Unknown fixture format: {fixture_format}")


EOFStateTestSpec = Callable[[str], Generator[EOFStateTest, None, None]]
EOFStateTestFiller = Type[EOFStateTest]
