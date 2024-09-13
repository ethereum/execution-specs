"""
Ethereum EOF test spec definition and filler.
"""

import subprocess
import warnings
from pathlib import Path
from shutil import which
from subprocess import CompletedProcess
from typing import Any, Callable, ClassVar, Dict, Generator, List, Optional, Type

import pytest
from pydantic import Field, model_validator

from ethereum_test_base_types import Account, Bytes
from ethereum_test_exceptions import EvmoneExceptionMapper
from ethereum_test_exceptions.exceptions import EOFExceptionInstanceOrList, to_pipe_str
from ethereum_test_fixtures import BaseFixture, FixtureFormats
from ethereum_test_fixtures.eof import Fixture, Result, Vector
from ethereum_test_forks import Fork
from ethereum_test_types import Alloc, Environment, Transaction
from ethereum_test_types.eof.v1 import Container, ContainerKind
from evm_transition_tool import TransitionTool

from .base import BaseTest
from .state import StateTest

existing_tests: Dict[Bytes, str] = {}


class EOFBaseException(Exception):
    """
    Base exception class for exceptions raised when verifying EOF code.
    """

    def __init__(self, message):
        super().__init__(message)

    @staticmethod
    def format_code(code: Bytes, max_length=60) -> str:
        """
        Avoid printing long bytecode strings in the terminal upon test failure.
        """
        if len(code) > max_length:
            half_length = max_length // 2 - 5  # Floor; adjust for ellipsis
            return f"{code[:half_length].hex()}...{code[-half_length:].hex()}"
        return code.hex()


class UnexpectedEOFException(EOFBaseException):
    """
    Exception used when valid EOF code unexpectedly raises an exception in
    eofparse.
    """

    def __init__(self, *, code: Bytes, got: str):
        message = (
            "Expected EOF code to be valid, but an exception occurred:\n"
            f"    Code: {self.format_code(code)}\n"
            f"Expected: No Exception\n"
            f"     Got: {got}"
        )
        super().__init__(message)


class ExpectedEOFException(EOFBaseException):
    """
    Exception used when EOF code is expected to raise an exception, but
    eofparse did not raise an exception.
    """

    def __init__(self, *, code: Bytes, expected: str):
        message = (
            "Expected EOF code to be invalid, but no exception was raised:\n"
            f"    Code: {self.format_code(code)}\n"
            f"Expected: {expected}\n"
            f"     Got: No Exception"
        )
        super().__init__(message)


class EOFExceptionMismatch(EOFBaseException):
    """
    Exception used when the actual EOF exception differs from the expected one.
    """

    def __init__(self, code: Bytes, expected: str, got: str):
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
        if binary is None:
            which_path = which("evmone-eofparse")
            if which_path is not None:
                binary = Path(which_path)
        if binary is None or not Path(binary).exists():
            raise FileNotFoundError(
                "`evmone-eofparse` binary executable not found/not executable."
            )
        self.binary = Path(binary)

    def run(self, *args: str, input: str | None = None) -> CompletedProcess:
        """Run evmone with the given arguments"""
        result = subprocess.run(
            [self.binary, *args],
            capture_output=True,
            text=True,
            input=input,
        )
        if result.returncode not in [0, 1]:
            raise Exception(
                f"`{self.binary.name}` call failed with return code {result.returncode}."
            )
        return result


class EOFTest(BaseTest):
    """
    Filler type that tests EOF containers.
    """

    data: Bytes
    expect_exception: EOFExceptionInstanceOrList | None = None
    container_kind: ContainerKind | None = None

    supported_fixture_formats: ClassVar[List[FixtureFormats]] = [
        FixtureFormats.EOF_TEST,
    ]

    @model_validator(mode="before")
    @classmethod
    def check_container_exception(cls, data: Any) -> Any:
        """
        Check if the container exception matches the expected exception.
        """
        if isinstance(data, dict):
            container = data.get("data")
            expect_exception = data.get("expect_exception")
            container_kind = data.get("container_kind")
            if container is not None and isinstance(container, Container):
                if (
                    "validity_error" in container.model_fields_set
                    and container.validity_error is not None
                ):
                    if expect_exception is not None:
                        assert container.validity_error == expect_exception, (
                            f"Container validity error {container.validity_error} "
                            f"does not match expected exception {expect_exception}."
                        )
                    if expect_exception is None:
                        data["expect_exception"] = container.validity_error
                if "kind" in container.model_fields_set:
                    if container_kind is not None:
                        assert container.kind == container_kind, (
                            f"Container kind type {str(container.kind)} "
                            f"does not match test {container_kind}."
                        )
                    if container.kind != ContainerKind.RUNTIME:
                        data["container_kind"] = container.kind
        return data

    @classmethod
    def pytest_parameter_name(cls) -> str:
        """
        Workaround for pytest parameter name.
        """
        return "eof_test"

    def make_eof_test_fixture(
        self,
        *,
        request: pytest.FixtureRequest,
        fork: Fork,
        eips: Optional[List[int]],
    ) -> Fixture:
        """
        Generate the EOF test fixture.
        """
        if self.data in existing_tests:
            pytest.fail(
                f"Duplicate EOF test: {self.data}, existing test: {existing_tests[self.data]}"
            )
        existing_tests[self.data] = request.node.nodeid
        vectors = [
            Vector(
                code=self.data,
                container_kind=self.container_kind,
                results={
                    fork.blockchain_test_network_name(): Result(
                        exception=self.expect_exception,
                        valid=self.expect_exception is None,
                    ),
                },
            )
        ]
        fixture = Fixture(vectors=dict(enumerate(vectors)))
        try:
            eof_parse = EOFParse()
        except FileNotFoundError as e:
            warnings.warn(f"{e} Skipping EOF fixture verification. Fixtures may be invalid!")
            return fixture

        for _, vector in fixture.vectors.items():
            expected_result = vector.results.get(fork.blockchain_test_network_name())
            if expected_result is None:
                raise Exception(f"EOF Fixture missing vector result for fork: {fork}")
            args = []
            if vector.container_kind == ContainerKind.INITCODE:
                args.append("--initcode")
            result = eof_parse.run(*args, input=str(vector.code))
            self.verify_result(result, expected_result, vector.code)

        return fixture

    def verify_result(self, result: CompletedProcess, expected_result: Result, code: Bytes):
        """
        Checks that the reported exception string matches the expected error.
        """
        parser = EvmoneExceptionMapper()
        actual_message = result.stdout.strip()
        actual_exception = parser.message_to_exception(actual_message)

        if expected_result.exception is None:
            if "OK" in actual_message:
                return
            else:
                raise UnexpectedEOFException(
                    code=code, got=f"{actual_exception} ({actual_message})"
                )
        else:
            expected_string = to_pipe_str(expected_result.exception)
            print(expected_string)
            print(actual_exception)
            if "OK" in actual_message:
                raise ExpectedEOFException(
                    code=code,
                    expected=f"{expected_string}",
                )
            elif actual_exception in expected_result.exception:
                return
            else:
                raise EOFExceptionMismatch(
                    code=code,
                    expected=f"{expected_string}",
                    got=f"{actual_exception} ({actual_message})",
                )

    def generate(
        self,
        *,
        request: pytest.FixtureRequest,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
        fixture_format: FixtureFormats,
        **_,
    ) -> BaseFixture:
        """
        Generate the BlockchainTest fixture.
        """
        if fixture_format == FixtureFormats.EOF_TEST:
            return self.make_eof_test_fixture(request=request, fork=fork, eips=eips)

        raise Exception(f"Unknown fixture format: {fixture_format}")


EOFTestSpec = Callable[[str], Generator[EOFTest, None, None]]
EOFTestFiller = Type[EOFTest]


class EOFStateTest(EOFTest):
    """
    Filler type that tests EOF containers and also generates a state/blockchain test.
    """

    deploy_tx: bool = False
    tx_gas_limit: int = 10_000_000
    tx_data: Bytes = Bytes(b"")
    tx_sender_funding_amount: int = 1_000_000_000_000_000_000_000
    env: Environment = Field(default_factory=Environment)
    container_post: Account = Field(default_factory=Account)
    pre: Alloc | None = None

    supported_fixture_formats: ClassVar[List[FixtureFormats]] = [
        FixtureFormats.EOF_TEST,
        FixtureFormats.STATE_TEST,
        FixtureFormats.BLOCKCHAIN_TEST,
        FixtureFormats.BLOCKCHAIN_TEST_ENGINE,
    ]

    @model_validator(mode="before")
    @classmethod
    def check_container_type(cls, data: Any) -> Any:
        """
        Check if the container exception matches the expected exception.
        """
        if isinstance(data, dict):
            container = data.get("data")
            deploy_tx = data.get("deploy_tx")
            container_kind = data.get("container_kind")
            if deploy_tx is None:
                if (
                    container is not None
                    and isinstance(container, Container)
                    and "kind" in container.model_fields_set
                    and container.kind == ContainerKind.INITCODE
                ) or (container_kind is not None and container_kind == ContainerKind.INITCODE):
                    data["deploy_tx"] = True
        return data

    @classmethod
    def pytest_parameter_name(cls) -> str:
        """
        Workaround for pytest parameter name.
        """
        return "eof_state_test"

    def generate_state_test(self) -> StateTest:
        """
        Generate the StateTest filler.
        """
        assert self.pre is not None, "pre must be set to generate a StateTest."
        tx = Transaction(
            sender=self.pre.fund_eoa(amount=self.tx_sender_funding_amount),
            gas_limit=self.tx_gas_limit,
        )
        post = Alloc()
        if self.expect_exception is not None:  # Invalid EOF
            tx.to = None  # Make EIP-7698 create transaction
            tx.data = Bytes(self.data + self.tx_data)  # by concatenating container and tx data.
            post[tx.created_contract] = None  # Expect failure.
        elif self.deploy_tx:
            tx.to = None  # Make EIP-7698 create transaction
            tx.data = Bytes(self.data + self.tx_data)  # by concatenating container and tx data.
            post[tx.created_contract] = self.container_post  # Successful.
        else:
            tx.to = self.pre.deploy_contract(code=self.data)
            tx.data = self.tx_data
            post[tx.to] = self.container_post
        return StateTest(
            pre=self.pre,
            tx=tx,
            env=self.env,
            post=post,
            t8n_dump_dir=self.t8n_dump_dir,
        )

    def generate(
        self,
        *,
        request: pytest.FixtureRequest,
        t8n: TransitionTool,
        fork: Fork,
        eips: Optional[List[int]] = None,
        fixture_format: FixtureFormats,
        **_,
    ) -> BaseFixture:
        """
        Generate the BlockchainTest fixture.
        """
        if fixture_format == FixtureFormats.EOF_TEST:
            if self.data in existing_tests:
                # Gracefully skip duplicate tests because one EOFStateTest can generate multiple
                # state fixtures with the same data.
                pytest.skip(f"Duplicate EOF container on EOFStateTest: {request.node.nodeid}")
            return self.make_eof_test_fixture(request=request, fork=fork, eips=eips)
        elif fixture_format in (
            FixtureFormats.STATE_TEST,
            FixtureFormats.BLOCKCHAIN_TEST,
            FixtureFormats.BLOCKCHAIN_TEST_ENGINE,
        ):
            return self.generate_state_test().generate(
                request=request, t8n=t8n, fork=fork, fixture_format=fixture_format, eips=eips
            )

        raise Exception(f"Unknown fixture format: {fixture_format}")


EOFStateTestSpec = Callable[[str], Generator[EOFStateTest, None, None]]
EOFStateTestFiller = Type[EOFStateTest]
