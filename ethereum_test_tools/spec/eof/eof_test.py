"""
Ethereum EOF test spec definition and filler.
"""

import subprocess
import warnings
from pathlib import Path
from shutil import which
from subprocess import CompletedProcess
from typing import Callable, ClassVar, Generator, List, Optional, Type

from ethereum_test_forks import Fork
from evm_transition_tool import FixtureFormats

from ...common.base_types import Bytes
from ...exceptions import EOFException, EvmoneExceptionMapper
from ..base.base_test import BaseFixture, BaseTest
from .types import Fixture, Result


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
            f"   Code: {self.format_code(code)}\n"
            "Expected: No Exception\n"
            f"    Got: {got}"
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
            "      Got: No Exception"
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
    expect_exception: EOFException | None = None

    supported_fixture_formats: ClassVar[List[FixtureFormats]] = [
        # TODO: Potentially generate a state test and blockchain test too.
        FixtureFormats.EOF_TEST,
    ]

    def make_eof_test_fixture(
        self,
        *,
        fork: Fork,
        eips: Optional[List[int]],
    ) -> Fixture:
        """
        Generate the EOF test fixture.
        """
        fixture = Fixture(
            vectors={
                "0": {
                    "code": self.data,
                    "results": {
                        fork.blockchain_test_network_name(): {
                            "exception": self.expect_exception,
                            "valid": self.expect_exception is None,
                        }
                    },
                }
            }
        )
        try:
            eof_parse = EOFParse()
        except FileNotFoundError as e:
            warnings.warn(f"{e} Skipping EOF fixture verification. Fixtures may be invalid!")
            return fixture

        for _, vector in fixture.vectors.items():
            expected_result = vector.results.get(str(fork))
            if expected_result is None:
                raise Exception(f"EOF Fixture missing vector result for fork: {fork}")
            result = eof_parse.run(input=str(vector.code))
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

        expected_exception = expected_result.exception
        expected_message = parser.exception_to_message(expected_exception)

        if "OK" in actual_message:
            raise ExpectedEOFException(
                code=code, expected=f"{expected_exception} ({expected_message})"
            )

        if expected_exception != actual_exception:
            raise EOFExceptionMismatch(
                code=code,
                expected=f"{expected_exception} ({expected_message})",
                got=f"{actual_exception} ({actual_message})",
            )

    def generate(
        self,
        *,
        fork: Fork,
        eips: Optional[List[int]] = None,
        fixture_format: FixtureFormats,
        **_,
    ) -> BaseFixture:
        """
        Generate the BlockchainTest fixture.
        """
        if fixture_format == FixtureFormats.EOF_TEST:
            return self.make_eof_test_fixture(fork=fork, eips=eips)

        raise Exception(f"Unknown fixture format: {fixture_format}")


EOFTestSpec = Callable[[str], Generator[EOFTest, None, None]]
EOFTestFiller = Type[EOFTest]
