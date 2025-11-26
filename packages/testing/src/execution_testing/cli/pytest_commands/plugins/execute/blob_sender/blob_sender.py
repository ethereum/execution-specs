"""Blob sender plugin."""

import pytest
from eth_account import Account
from eth_keys import keys
from eth_utils import to_checksum_address

from execution_testing.base_types.base_types import Address, Bytes
from execution_testing.forks import ForkSetAdapter
from execution_testing.logging import (
    get_logger,
)
from execution_testing.rpc import EthRPC
from execution_testing.test_types.blob_types import Blob

logger = get_logger(__name__)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options to pytest."""
    blob_sender_group = parser.getgroup(
        "blob_sender", "Arguments defining blob_sender behavior"
    )
    blob_sender_group.addoption(
        "--blob-seed",
        action="store",
        dest="blob_seed",
        required=False,
        type=int,
        default=1,
        help=(
            "Blob data is dynamically derived from this seed.\nNote: "
            "This is the starting seed. If you send more than one blob, each "
            "additional blob will have its seed increased by 1.\nMax value: 6"
        ),
    )
    blob_sender_group.addoption(
        "--blob-amount",
        action="store",
        dest="blob_amount",
        required=False,
        type=int,
        default=1,
        help=("Amount of blobs to generate and send"),
    )


# --------------------------- Helper functions --------------------------------


def hex_to_bytes(s: str) -> bytes:
    """Takes hex string and returns it as bytes."""
    s = s[2:] if s[:2].lower() == "0x" else s
    if len(s) % 2:
        s = "0" + s
    return bytes.fromhex(s)


def privkey_hex_to_addr(*, privkey_hex: str) -> str:
    """Takes private key hex string and returns derived checksum address."""
    # convert hex to bytes
    privkey_bytes = hex_to_bytes(privkey_hex)

    # derive pubkey
    pk = keys.PrivateKey(privkey_bytes)

    # derive address
    addr = pk.public_key.to_checksum_address()
    return addr


def gwei_float_to_wei_int(gwei: float) -> int:
    """Convert gwei float to wei int."""
    return int(gwei * (10**9))


# -----------------------------------------------------------------------------


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """
    Set the provided command-line arguments.
    """
    # skip validation if we're just showing help
    if config.option.help:
        return

    blob_seed = config.getoption("blob_seed")

    blob_amount = config.getoption("blob_amount")
    assert blob_amount <= 6, (
        "you may only send up to 6 blobs per tx, but you tried to "
        f"send {blob_amount} blobs in one tx!"
    )

    fork_str = config.getoption("single_fork")
    chain_id = config.getoption("chain_id")
    rpc_endpoint = config.getoption("rpc_endpoint")

    sender_privkey_hex = config.getoption("rpc_seed_key")
    sender_address = privkey_hex_to_addr(privkey_hex=sender_privkey_hex)

    if not fork_str:
        pytest.exit(
            "ERROR: --fork is required for blob-sender command.\n"
            "Example Usage: uv run execute blob-sender -v -s --fork=Osaka --rpc-seed-key=0000000000000000000000000000000000000000000000000000000000000001 --rpc-endpoint=http://example.org --chain-id=11155111 --eest-log-level=INFO --blob-seed=5 --blob-amount=3",  # noqa: E501
            returncode=pytest.ExitCode.USAGE_ERROR,
        )

    # Convert fork string to Fork instance
    fork_set = ForkSetAdapter.validate_python(fork_str)
    fork = next(iter(fork_set))

    # get sender nonce on target network
    eth_rpc = EthRPC(rpc_endpoint)
    nonce = eth_rpc.get_transaction_count(Address(sender_address))

    logger.info(
        "\nBlob Sender Plugin Configuration:"
        f"\n\tFork: {fork}"
        f"\n\tAmount of blobs to send: {blob_amount}"
        f"\n\tStarting seed for blob generation: {blob_seed}"
        f"\n\tSender Address: {sender_address}"
        f"\n\tSender Nonce: {nonce}"
        f"\n\tChain ID: {chain_id}"
    )

    versioned_hashes: list[Bytes] = []
    blob_list: list[Bytes] = []
    for current_seed in range(blob_seed, blob_seed + blob_amount):
        print(f"Generating blob with seed {current_seed} for fork {fork}..")
        b = Blob.from_fork(fork, seed=current_seed)
        # blobs.append(b)
        print("Successfully generated blob file:", b.name)

        # extract relevant info from blob
        data_hex = b.data.hex()
        if data_hex.startswith("0x"):
            data_hex = data_hex[2:]

        assert len(data_hex) == 131072 * 2, (
            f"Data should be 128KB, got {len(data_hex)} bytes"
        )

        blob_bytes = Bytes(data_hex)
        blob_list.append(blob_bytes)

        versioned_hashes.append(Bytes(b.versioned_hash))

    # define type 3 tx
    max_priority_fee_per_gas = 2  # gwei
    max_fee_per_gas = 3.7  # gwei
    max_fee_per_blob_gas = 6  # gwei

    tx_dict = {
        "type": 3,  # EIP-4844 blob transaction
        "chainId": chain_id,
        "nonce": nonce,
        "from": to_checksum_address(sender_address),
        "to": to_checksum_address(
            sender_address
        ),  # just send it to yourself, on mainnet some L2's put "FF000....00<decimal-chainid>" as address  # noqa: E501
        "value": 0,
        "gas": 21_000,
        "maxPriorityFeePerGas": gwei_float_to_wei_int(
            max_priority_fee_per_gas
        ),
        "maxFeePerGas": gwei_float_to_wei_int(max_fee_per_gas),
        "maxFeePerBlobGas": gwei_float_to_wei_int(max_fee_per_blob_gas),
        "data": "0x",
        "accessList": [],
        "blobVersionedHashes": versioned_hashes,
    }

    signed_tx_obj = Account.sign_transaction(
        tx_dict, sender_privkey_hex, blobs=blob_list
    )
    # signed_raw_tx_hex = "0x" + signed_tx_obj.raw_transaction.hex()
    # logger.info(
    #     "done. you can send this now via "
    #     f"eth_sendRawTransaction: {signed_raw_tx_hex}"
    # )

    # send raw tx
    raw_tx = Bytes(signed_tx_obj.raw_transaction)
    tx_hash = eth_rpc.send_raw_transaction(raw_tx)
    logger.info(f"\nSuccess!\nTx Hash: {tx_hash}")
