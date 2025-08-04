"""Abstract base class to help create Python interfaces to Ethereum CLIs."""

import os
import shutil
import subprocess
from itertools import groupby
from pathlib import Path
from re import Pattern
from typing import Any, List, Optional, Type

from pytest_plugins.logging import get_logger

logger = get_logger(__name__)


class UnknownCLIError(Exception):
    """Exception raised if an unknown CLI is encountered."""

    pass


class CLINotFoundInPathError(Exception):
    """Exception raised if the specified CLI binary is not found in the path."""

    def __init__(self, message="The CLI binary was not found in the path", binary=None):
        """Initialize the exception."""
        if binary:
            message = f"{message} ({binary})"
        super().__init__(message)


class EthereumCLI:
    """
    Abstract base class to help create Python interfaces to Ethereum CLIs.

    This base class helps handle the special case of EVM subcommands, such as
    the EVM transition tool `t8n`, which have multiple implementations, one
    from each client team. In the case of these tools, this class mainly serves
    to help instantiate the correct subclass based on the output of the CLI's
    version flag.
    """

    registered_tools: List[Type[Any]] = []
    default_tool: Optional[Type[Any]] = None
    binary: Path
    default_binary: Path
    detect_binary_pattern: Pattern
    version_flag: str = "-v"
    cached_version: Optional[str] = None

    def __init__(self, *, binary: Optional[Path] = None):
        """Abstract initialization method that all subclasses must implement."""
        if binary is None:
            binary = self.default_binary
        else:
            # improve behavior of which by resolving the path: ~/relative paths don't work
            resolved_path = Path(os.path.expanduser(binary)).resolve()
            if resolved_path.exists():
                binary = resolved_path
        binary = shutil.which(binary)  # type: ignore
        if not binary:
            raise CLINotFoundInPathError(binary=binary)
        self.binary = Path(binary)

    @classmethod
    def register_tool(cls, tool_subclass: Type[Any]):
        """Register a given subclass as tool option."""
        cls.registered_tools.append(tool_subclass)  # raise NotImplementedError

    @classmethod
    def set_default_tool(cls, tool_subclass: Type[Any]):
        """Register the default tool subclass."""
        cls.default_tool = tool_subclass

    @classmethod
    def from_binary_path(cls, *, binary_path: Optional[Path], **kwargs) -> Any:
        """
        Instantiate the appropriate CLI subclass derived from the CLI's `binary_path`.

        This method will attempt to detect the CLI version and instantiate the appropriate
        subclass based on the version output by running the CLI with the version flag.
        """
        assert cls.default_tool is not None, "default CLI implementation was never set"

        # ensure provided t8n binary can be found and used
        if binary_path is None:
            logger.debug("Binary path of provided t8n is None!")
            return cls.default_tool(binary=binary_path, **kwargs)

        expanded_path = Path(os.path.expanduser(binary_path))
        logger.debug(f"Expanded path of provided t8n: {expanded_path}")

        resolved_path = expanded_path.resolve()
        logger.debug(f"Resolved path of provided t8n: {resolved_path}")

        if resolved_path.exists():
            logger.debug("Resolved path exists")
            binary = Path(resolved_path)
        else:
            logger.debug(
                f"Resolved path does not exist: {resolved_path}\nTrying to find it via `which`"
            )

            # it might be that the provided binary exists in path
            filename = os.path.basename(resolved_path)
            binary = shutil.which(filename)  # type: ignore
            logger.debug(f"Output of 'which {binary_path}': {binary}")

            if binary is None:
                logger.error(f"Resolved t8n binary path does not exist: {resolved_path}")
                raise CLINotFoundInPathError(binary=resolved_path)

            assert binary is not None
            logger.debug(f"Successfully located the path of the t8n binary: {binary}")
            binary = Path(binary)

        # Group the tools by version flag, so we only have to call the tool once for all the
        # classes that share the same version flag
        for version_flag, subclasses in groupby(
            cls.registered_tools, key=lambda x: x.version_flag
        ):
            logger.debug(
                f"Trying this `version` flag to determine if t8n supported: {version_flag}"
            )
            # adding more logging reveals we check for `-v` twice..

            try:
                result = subprocess.run(
                    [binary, version_flag], stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                logger.debug(
                    f"Subprocess:\n\tstdout: {result.stdout}\n\n\n\tstderr: {result.stderr}\n\n\n"  # type: ignore
                )

                if result.returncode != 0:
                    logger.debug(f"Subprocess returncode is not 0! It is: {result.returncode}")
                    continue  # don't raise exception, you are supposed to keep trying different version flags  # noqa: E501

                if result.stderr:
                    logger.debug(f"Stderr detected: {result.stderr}")  # type: ignore
                    continue

                binary_output = ""
                if result.stdout:
                    binary_output = result.stdout.decode().strip()
                    # e.g. 1.31.10+f62cfede9b4abfb5cd62d6f138240668620a2b0d should be treated as 1.31.10  # noqa: E501
                    # if "+" in binary_output:
                    #     binary_output = binary_output.split("+")[0]

                    logger.debug(f"Stripped subprocess stdout: {binary_output}")

                for subclass in subclasses:
                    logger.debug(f"Trying subclass {subclass}")

                    if subclass.detect_binary(binary_output):
                        return subclass(binary=binary, **kwargs)

                    logger.debug(
                        f"T8n with version {binary_output} does not belong to subclass {subclass}"
                    )

            except Exception as e:
                logger.debug(
                    f"Trying to determine t8n version with flag `{version_flag}` failed: {e}"
                )
                continue

        raise UnknownCLIError(f"Unknown CLI: {binary}")

    @classmethod
    def detect_binary(cls, binary_output: str) -> bool:
        """Return True if a CLI's `binary_output` matches the class's expected output."""
        assert cls.detect_binary_pattern is not None

        return cls.detect_binary_pattern.match(binary_output) is not None

    @classmethod
    def is_installed(cls, binary_path: Optional[Path] = None) -> bool:
        """Return whether the tool is installed in the current system."""
        if binary_path is None:
            binary_path = cls.default_binary
        else:
            resolved_path = Path(os.path.expanduser(binary_path)).resolve()
            if resolved_path.exists():
                binary_path = resolved_path
        binary = shutil.which(binary_path)
        return binary is not None

    def version(self) -> str:
        """Return the name and version of the CLI as reported by the CLI's version flag."""
        if self.cached_version is None:
            result = subprocess.run(
                [str(self.binary), self.version_flag],
                stdout=subprocess.PIPE,
            )

            if result.returncode != 0:
                raise Exception("failed to evaluate: " + result.stderr.decode())

            self.cached_version = result.stdout.decode().strip()

        return self.cached_version
