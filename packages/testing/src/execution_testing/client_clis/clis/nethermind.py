"""Interfaces for Nethermind CLIs."""

import json
import re
import shlex
import subprocess
import textwrap
from functools import cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from execution_testing.exceptions import (
    BlockException,
    ExceptionMapper,
    TransactionException,
)
from execution_testing.fixtures import (
    BlockchainFixture,
    FixtureFormat,
    StateFixture,
)

from ..ethereum_cli import EthereumCLI
from ..file_utils import dump_files_to_directory
from ..fixture_consumer_tool import FixtureConsumerTool


class Nethtest(EthereumCLI):
    """Nethermind `nethtest` binary base class."""

    default_binary = Path("nethtest")
    # new pattern allows e.g. '1.2.3', in the past that was denied
    detect_binary_pattern = re.compile(
        r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?(\+[a-f0-9]{40})?$"
    )
    version_flag: str = "--version"
    cached_version: Optional[str] = None

    def __init__(
        self,
        binary: Path,
        trace: bool = False,
        exception_mapper: ExceptionMapper | None = None,
    ):
        """Initialize the Nethtest class."""
        self.binary = binary
        self.trace = trace
        # TODO: Implement NethermindExceptionMapper
        self.exception_mapper = exception_mapper if exception_mapper else None

    def _run_command(self, command: List[str]) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise Exception("Command failed with non-zero status.") from e
        except Exception as e:
            raise Exception("Unexpected exception calling evm tool.") from e

    def _consume_debug_dump(
        self,
        command: Tuple[str, ...],
        result: subprocess.CompletedProcess,
        debug_output_path: Path,
    ) -> None:
        # our assumption is that each command element is a string
        assert all(isinstance(x, str) for x in command), (
            f"Not all elements of 'command' list are strings: {command}"
        )

        # ensure that flags with spaces are wrapped in double-quotes
        consume_direct_call = " ".join(shlex.quote(arg) for arg in command)

        consume_direct_script = textwrap.dedent(
            f"""\
            #!/bin/bash
            {consume_direct_call}
            """
        )

        dump_files_to_directory(
            debug_output_path,
            {
                "consume_direct_args.py": command,
                "consume_direct_returncode.txt": result.returncode,
                "consume_direct_stdout.txt": result.stdout,
                "consume_direct_stderr.txt": result.stderr,
                "consume_direct.sh+x": consume_direct_script,
            },
        )

    @cache  # noqa
    def help(self, subcommand: str | None = None) -> str:
        """Return the help string, optionally for a subcommand."""
        help_command = [str(self.binary)]
        if subcommand:
            help_command.append(subcommand)
        help_command.append("--help")
        return self._run_command(help_command).stdout


class NethtestFixtureConsumer(
    Nethtest,
    FixtureConsumerTool,
    fixture_formats=[StateFixture, BlockchainFixture],
):
    """Nethermind implementation of the fixture consumer."""

    def _build_command_with_options(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> Tuple[str, ...]:
        assert fixture_name, "Fixture name must be provided for nethtest."
        command = [str(self.binary)]
        if fixture_format is BlockchainFixture:
            command += [
                "--blockTest",
                "--filter",
                f"{re.escape(fixture_name)}",
            ]
        elif fixture_format is StateFixture:
            # TODO: consider using `--filter` here to readily access traces
            # from the output
            pass  # no additional options needed
        else:
            raise Exception(
                f"Fixture format {fixture_format.format_name} "
                f"not supported by {self.binary}"
            )
        command += ["--input", str(fixture_path)]
        if debug_output_path:
            command += ["--trace"]
        return tuple(command)

    @cache  # noqa
    def consume_state_test_file(
        self,
        fixture_path: Path,
        command: Tuple[str, ...],
        debug_output_path: Optional[Path] = None,
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Consume an entire state test file.

        The `evm statetest` will always execute all the tests contained in a
        file without the possibility of selecting a single test, so this
        function is cached in order to only call the command once and
        `consume_state_test` can simply select the result that was requested.
        """
        del fixture_path
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if debug_output_path:
            self._consume_debug_dump(command, result, debug_output_path)

        if result.returncode != 0:
            raise Exception(
                f"Unexpected exit code:\n{' '.join(command)}\n\n"
                f"Error:\n{result.stderr}"
            )

        try:
            result_json = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise Exception(
                f"Failed to parse JSON output on stdout from nethtest:\n"
                f"{result.stdout}"
            ) from e

        if not isinstance(result_json, list):
            raise Exception(
                f"Unexpected result from evm statetest: {result_json}"
            )
        return result_json, result.stderr

    def consume_state_test(
        self,
        command: Tuple[str, ...],
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """
        Consume a single state test.

        Uses the cached result from `consume_state_test_file` in order to not
        call the command every time and select a single result from there.
        """
        file_results, stderr = self.consume_state_test_file(
            fixture_path=fixture_path,
            command=command,
            debug_output_path=debug_output_path,
        )

        if fixture_name:
            # TODO: this check is too fragile; extend for ethereum/tests?
            nethtest_suffix = "_d0g0v0_"
            assert all(
                test_result["name"].endswith(nethtest_suffix)
                for test_result in file_results
            ), (
                "consume direct with nethtest doesn't support the "
                "multi-data statetest format used in ethereum/tests (yet)"
            )
            test_result = [
                test_result
                for test_result in file_results
                if test_result["name"].removesuffix(nethtest_suffix)
                == f"{fixture_name.split('/')[-1]}"
            ]
            assert len(test_result) < 2, (
                f"Multiple test results for {fixture_name}"
            )
            assert len(test_result) == 1, (
                f"Test result for {fixture_name} missing"
            )
            assert test_result[0]["pass"], (
                f"State test '{fixture_name}' failed, "
                f"available stderr:\n {stderr}"
            )
        else:
            if any(not test_result["pass"] for test_result in file_results):
                exception_text = "State test failed: \n" + "\n".join(
                    f"{test_result['name']}: " + test_result["error"]
                    for test_result in file_results
                    if not test_result["pass"]
                )
                raise Exception(exception_text)

    def consume_blockchain_test(
        self,
        command: Tuple[str, ...],
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """Execute the the fixture at `fixture_path` via `nethtest`."""
        del fixture_path
        del fixture_name
        result = subprocess.run(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )

        if debug_output_path:
            self._consume_debug_dump(command, result, debug_output_path)

        if result.returncode != 0:
            raise Exception(
                f"nethtest exited with non-zero exit code "
                f"({result.returncode}).\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}\n"
                f"{' '.join(command)}"
            )

    def consume_fixture(
        self,
        fixture_format: FixtureFormat,
        fixture_path: Path,
        fixture_name: Optional[str] = None,
        debug_output_path: Optional[Path] = None,
    ) -> None:
        """
        Execute the appropriate geth fixture consumer for the fixture at
        `fixture_path`.
        """
        command = self._build_command_with_options(
            fixture_format, fixture_path, fixture_name, debug_output_path
        )
        if fixture_format == BlockchainFixture:
            self.consume_blockchain_test(
                command=command,
                fixture_path=fixture_path,
                fixture_name=fixture_name,
                debug_output_path=debug_output_path,
            )
        elif fixture_format == StateFixture:
            self.consume_state_test(
                command=command,
                fixture_path=fixture_path,
                fixture_name=fixture_name,
                debug_output_path=debug_output_path,
            )
        else:
            raise Exception(
                f"Fixture format {fixture_format.format_name} "
                f"not supported by {self.binary}"
            )


class NethermindExceptionMapper(ExceptionMapper):
    """Nethermind exception mapper."""

    mapping_substring = {
        TransactionException.SENDER_NOT_EOA: "sender has deployed code",
        TransactionException.INTRINSIC_GAS_TOO_LOW: "intrinsic gas too low",
        TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST: (
            "intrinsic gas too low"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            "miner premium is negative"
        ),
        TransactionException.PRIORITY_GREATER_THAN_MAX_FEE_PER_GAS: (
            "InvalidMaxPriorityFeePerGas: Cannot be higher than maxFeePerGas"
        ),
        TransactionException.GAS_ALLOWANCE_EXCEEDED: (
            "Block gas limit exceeded"
        ),
        TransactionException.NONCE_IS_MAX: "NonceTooHigh",
        TransactionException.INITCODE_SIZE_EXCEEDED: (
            "max initcode size exceeded"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: (
            "transaction nonce is too low"
        ),
        TransactionException.NONCE_MISMATCH_TOO_HIGH: (
            "transaction nonce is too high"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            "InsufficientMaxFeePerBlobGas: Not enough to cover blob gas fee"
        ),
        TransactionException.INVALID_SIGNATURE_VRS: (
            "InvalidTxSignature: Signature is invalid."
        ),
        TransactionException.TYPE_1_TX_PRE_FORK: (
            "InvalidTxType: Transaction type in Custom is not supported"
        ),
        TransactionException.TYPE_2_TX_PRE_FORK: (
            "InvalidTxType: Transaction type in Custom is not supported"
        ),
        TransactionException.TYPE_3_TX_PRE_FORK: (
            "InvalidTxType: Transaction type in Custom is not supported"
        ),
        TransactionException.TYPE_3_TX_ZERO_BLOBS: (
            "blob transaction must have at least 1 blob"
        ),
        TransactionException.TYPE_3_TX_INVALID_BLOB_VERSIONED_HASH: (
            "InvalidBlobVersionedHashVersion: Blob version not supported"
        ),
        TransactionException.TYPE_3_TX_CONTRACT_CREATION: (
            "blob transaction of type create"
        ),
        TransactionException.TYPE_4_EMPTY_AUTHORIZATION_LIST: (
            "EIP-7702 transaction with empty auth list"
        ),
        TransactionException.TYPE_4_TX_CONTRACT_CREATION: (
            "EIP-7702 transaction cannot be used to create contract"
        ),
        TransactionException.TYPE_4_TX_PRE_FORK: (
            "InvalidTxType: Transaction type in Custom is not supported"
        ),
        BlockException.INCORRECT_BLOB_GAS_USED: (
            "HeaderBlobGasMismatch: "
            "Blob gas in header does not match calculated"
        ),
        BlockException.INVALID_REQUESTS: (
            "InvalidRequestsHash: Requests hash mismatch in block"
        ),
        BlockException.INVALID_GAS_USED_ABOVE_LIMIT: (
            "ExceededGasLimit: Gas used exceeds gas limit."
        ),
        BlockException.RLP_BLOCK_LIMIT_EXCEEDED: (
            "ExceededBlockSizeLimit: Exceeded block size limit"
        ),
        BlockException.INVALID_DEPOSIT_EVENT_LAYOUT: (
            "DepositsInvalid: Invalid deposit event layout:"
        ),
        BlockException.INVALID_BASEFEE_PER_GAS: (
            "InvalidBaseFeePerGas: Does not match calculated"
        ),
        BlockException.INVALID_BLOCK_TIMESTAMP_OLDER_THAN_PARENT: (
            "InvalidTimestamp: "
            "Timestamp in header cannot be lower than ancestor"
        ),
        BlockException.INVALID_BLOCK_NUMBER: (
            "InvalidBlockNumber: Block number does not match the parent"
        ),
        BlockException.EXTRA_DATA_TOO_BIG: (
            "InvalidExtraData: Extra data in header is not valid"
        ),
        BlockException.INVALID_GASLIMIT: (
            "InvalidGasLimit: Gas limit is not correct"
        ),
        BlockException.INVALID_RECEIPTS_ROOT: (
            "InvalidReceiptsRoot: Receipts root in header does not match"
        ),
        BlockException.INVALID_LOG_BLOOM: (
            "InvalidLogsBloom: Logs bloom in header does not match"
        ),
        BlockException.INVALID_STATE_ROOT: (
            "InvalidStateRoot: State root in header does not match"
        ),
        BlockException.GAS_USED_OVERFLOW: ("Block gas limit exceeded"),
        BlockException.BLOCK_ACCESS_LIST_GAS_LIMIT_EXCEEDED: (
            "BlockAccessListGasLimitExceeded:"
        ),
    }
    mapping_regex = {
        TransactionException.INSUFFICIENT_ACCOUNT_FUNDS: (
            r"insufficient sender balance|"
            r"insufficient MaxFeePerGas for sender balance"
            r"|insufficient funds for gas \* price \+ value"
            r"|insufficient funds for transfer|insufficient funds for gas"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_GAS: (
            r"max fee per gas less than block base fee"
        ),
        TransactionException.INSUFFICIENT_MAX_FEE_PER_BLOB_GAS: (
            r"max fee per blob gas less than block blob gas fee"
        ),
        TransactionException.NONCE_MISMATCH_TOO_LOW: (r"nonce too low"),
        TransactionException.NONCE_MISMATCH_TOO_HIGH: (r"nonce too high"),
        TransactionException.INVALID_CHAINID: (
            r"InvalidTxChainId|Signature is invalid."
        ),
        # `Transaction \d+ is not valid: <cause>` is the wrapper the client
        # puts around any payload transaction that fails to RLP-decode, so
        # this entry alone cannot tell one decode failure from another. It is
        # kept broad because the mapper is additive: a fixture passes when its
        # expected exception is among those matched, and the entries below
        # supply the discriminating labels for the causes that have one.
        TransactionException.TYPE_3_TX_WITH_FULL_BLOBS: (
            r"Transaction \d+ is not valid"
        ),
        # Frame transaction static constraints: frame count, mode, flags,
        # value placement, atomic batch, expiry verifier, signature entry
        # structure, nonce and blob fields.
        TransactionException.TYPE_6_INVALID_FRAME_FORMAT: (
            r"frame transaction must contain between 1 and 64 frames"
            r"|frame transaction sender must be set"
            r"|frame mode must be DEFAULT, VERIFY, SENDER, or POST_TX"
            r"|POST_TX frames must form a trailing suffix of the frame list"
            r"|POST_TX frames are not enabled"
            r"|frame flags must not use reserved bits"
            r"|frame value is only allowed in SENDER mode"
            r"|frames allowed to approve execution must target the sender"
            r"|the last frame must not have the atomic batch flag set"
            r"|the atomic batch flag must not be set on a VERIFY frame"
            r"|the atomic batch flag must not be set on a POST_TX frame"
            r"|an atomic batch frame must not be followed by a VERIFY frame"
            r"|an atomic batch frame must not be followed by a POST_TX frame"
            r"|frames belonging to an atomic batch must not carry approval"
            r" scope"
            r"|total frame gas must not exceed 2\^64 - 1"
            r"|expiry verifier frame must have zero flags, zero value, and"
            r" 8-byte data"
            r"|at most one expiry verifier frame is allowed"
            r"|unknown signature scheme"
            r"|ARBITRARY signatures must not name a signer"
            r"|signature msg must be empty or a 32-byte digest"
            r"|explicit signature msg must not be the zero digest"
            r"|max fee per blob gas must be 0 when there are no blob hashes"
            r"|keyed nonces are not enabled"
            r"|legacy nonce is not allowed"
            r"|malformed nonce key set"
            r"|at most 16 recent root references are allowed"
            r"|frame transaction SECP256K1 signer does not match the"
            r" recovered address"
            r"|frame transaction P256 signer does not match the public key"
            # Decode-time rejections of a frame field too wide or too long
            # for its type, which the fixtures also file as format failures.
            # Generic decoder wordings carrying no frame context, so they
            # widen the label rather than pinpoint it.
            r"|Expected a sequence prefix to be in the range of <192, 255>"
            r"|Unexpected length of integer value"
            r"|Unexpected RLP prefix"
            r"|Collection count"
            r"|An RLP limit exceeded"
        ),
        # Signature entries that fail protocol validation. Disjoint from the
        # format set above, which files a signer not matching the recovered
        # key as a format failure rather than a signature failure.
        TransactionException.TYPE_6_INVALID_SIGNATURE: (
            r"frame transaction has an invalid signature"
            r"|frame transaction signature has the wrong length"
            r"|frame transaction signature must use a 0/1 recovery id and a"
            r" canonical low s value"
            r"|frame transaction P256 signature must be canonical with a low"
            r" s value"
            r"|frame transaction P256 signatures require the secp256r1"
            r" precompile"
        ),
        # A well-formed, correctly signed transaction that frame execution
        # then invalidates. Never a bare "frame": that would also catch the
        # format and signature wordings above.
        TransactionException.TYPE_6_INVALID_FRAME_EXECUTION: (
            r"VERIFY frame reverted"
            r"|validation prefix frame reverted"
            r"|SENDER frame before execution approval"
            r"|never set a payer"
        ),
        # A fee field wider than 32 bytes trips the decoder length guard,
        # which names neither the field nor the transaction type, so both fee
        # labels take the same pattern. The second wording is the same guard
        # with the client trace logging enabled.
        TransactionException.GASPRICE_OVERFLOW: (
            r"Collection count|An RLP limit exceeded"
        ),
        TransactionException.PRIORITY_OVERFLOW: (
            r"Collection count|An RLP limit exceeded"
        ),
        TransactionException.TYPE_3_TX_MAX_BLOB_GAS_ALLOWANCE_EXCEEDED: (
            r"BlockBlobGasExceeded: A block cannot have more than "
            r"\d+ blob gas, blobs count \d+, blobs gas used: \d+"
        ),
        TransactionException.TYPE_3_TX_BLOB_COUNT_EXCEEDED: (
            r"BlobTxGasLimitExceeded: Transaction's totalDataGas=\d+ "
            r"exceeded MaxBlobGas per transaction=\d+"
        ),
        # A frame transaction reports the per-transaction gas cap against its
        # own reservation rather than through the shared prefix.
        TransactionException.GAS_LIMIT_EXCEEDS_MAXIMUM: (
            r"TxGasLimitCapExceeded:|exceeds the transaction gas cap of"
        ),
        # Reached only when gas limit * price (+ value) overflows, never on a
        # plain balance shortfall. The client composes this onto its
        # insufficient-funds wording, so both labels match and the fixture
        # picks the one it named.
        TransactionException.GASLIMIT_PRICE_PRODUCT_OVERFLOW: (
            r"required balance exceeds 256 bits"
        ),
        BlockException.INCORRECT_EXCESS_BLOB_GAS: (
            r"HeaderExcessBlobGasMismatch: Excess blob gas in header "
            r"does not match calculated|Overflow in excess blob gas"
        ),
        BlockException.INVALID_BLOCK_HASH: (
            r"Invalid block hash 0x[0-9a-f]+ does not match "
            r"calculated hash 0x[0-9a-f]+"
        ),
        BlockException.SYSTEM_CONTRACT_EMPTY: (
            r"(Withdrawals|Consolidations|BuilderDeposits|BuilderExits)"
            r"Empty: Contract is not deployed\."
        ),
        BlockException.SYSTEM_CONTRACT_CALL_FAILED: (
            r"(Withdrawals|Consolidations|BuilderDeposits|BuilderExits)"
            r"Failed: Contract execution failed\."
        ),
        # BAL Exceptions — specific exceptions have unique patterns, but
        # INVALID_BLOCK_ACCESS_LIST and INCORRECT_BLOCK_FORMAT intentionally
        # overlap because the test framework requires `want in got` matching.
        # BAL Exceptions
        BlockException.INVALID_BAL_HASH: (r"InvalidBlockLevelAccessListHash:"),
        BlockException.INVALID_BLOCK_ACCESS_LIST: (
            r"InvalidBlockLevelAccessListHash:"
            r"|InvalidBlockLevelAccessList:"
            r"|BlockLevelAccessListIndexOutOfRange:"
            r"|could not be parsed as a block: "
            r"Error decoding block access list:"
            r"|Error decoding block access list:"
        ),
        BlockException.INCORRECT_BLOCK_FORMAT: (
            r"could not be parsed as a block: "
            r"Error decoding block access list:"
            r"|Error decoding block access list:"
        ),
        TransactionException.GAS_ALLOWANCE_EXCEEDED: (
            r"TxGasLimitCapExceeded:"
            r"|BlockAccessListGasLimitExceeded:"
        ),
    }
