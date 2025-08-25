"""Test variants of the deposit contract which adheres the log-style as described in EIP-6110."""

import pytest

from ethereum_test_exceptions.exceptions import BlockException
from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Header,
    Requests,
    Transaction,
)
from ethereum_test_tools import Macros as Om
from ethereum_test_tools import Opcodes as Op

from .helpers import DepositRequest, create_deposit_log_bytes
from .spec import Spec, ref_spec_6110

pytestmark = [
    pytest.mark.valid_from("Prague"),
    pytest.mark.execute(pytest.mark.skip(reason="modifies pre-alloc")),
]

REFERENCE_SPEC_GIT_PATH = ref_spec_6110.git_path
REFERENCE_SPEC_VERSION = ref_spec_6110.version

EVENT_ARGUMENTS_NAMES = ["pubkey", "withdrawal_credentials", "amount", "signature", "index"]
EVENT_ARGUMENTS_LAYOUT_TYPE = ["size", "offset"]
EVENT_ARGUMENTS = [
    f"{name}_{layout}" for name in EVENT_ARGUMENTS_NAMES for layout in EVENT_ARGUMENTS_LAYOUT_TYPE
]
EVENT_ARGUMENT_VALUES = ["zero", "max_uint256"]


DEFAULT_DEPOSIT_REQUEST = DepositRequest(
    pubkey=0x01,
    withdrawal_credentials=0x02,
    amount=120_000_000_000_000_000,
    signature=0x03,
    index=0x0,
)
DEFAULT_DEPOSIT_REQUEST_LOG_DATA_DICT = {
    "pubkey_data": bytes(DEFAULT_DEPOSIT_REQUEST.pubkey),
    "withdrawal_credentials_data": bytes(DEFAULT_DEPOSIT_REQUEST.withdrawal_credentials),
    # Note: after converting to bytes, it is converted to little-endian by `[::-1]`
    # (This happens on-chain also, but this is done by the solidity contract)
    "amount_data": bytes.fromhex("0" + DEFAULT_DEPOSIT_REQUEST.amount.hex()[2:])[::-1],
    "signature_data": bytes(DEFAULT_DEPOSIT_REQUEST.signature),
    "index_data": bytes(DEFAULT_DEPOSIT_REQUEST.index),
}
DEFAULT_REQUEST_LOG = create_deposit_log_bytes(**DEFAULT_DEPOSIT_REQUEST_LOG_DATA_DICT)  # type: ignore


@pytest.mark.parametrize(
    "include_deposit_event",
    [
        pytest.param(
            True,
            marks=pytest.mark.pre_alloc_group(
                "deposit_extra_logs_with_event",
                reason="Deposit contract with Transfer log AND deposit event",
            ),
        ),
        pytest.param(
            False,
            marks=pytest.mark.pre_alloc_group(
                "deposit_extra_logs_no_event",
                reason="Deposit contract with Transfer log but NO deposit event",
            ),
        ),
    ],
)
def test_extra_logs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    include_deposit_event: bool,
):
    """Test deposit contract emitting more log event types than the ones in mainnet."""
    # Supplant mainnet contract with a variant that emits a `Transfer`` log
    # If `include_deposit_event` is `True``, it will also emit a `DepositEvent` log`

    # ERC20 token transfer log (Sepolia)
    # https://sepolia.etherscan.io/tx/0x2d71f3085a796a0539c9cc28acd9073a67cf862260a41475f000dd101279f94f
    # JSON RPC:
    # curl https://sepolia.infura.io/v3/APIKEY \
    # -X POST \
    # -H "Content-Type: application/json" \
    # -d '{"jsonrpc": "2.0", "method": "eth_getLogs",
    # "params": [{"address": "0x7f02C3E3c98b133055B8B348B2Ac625669Ed295D",
    # "blockHash": "0x8062a17fa791f5dbd59ea68891422e3299ca4e80885a89acf3fc706c8bceef53"}],
    # "id": 1}'

    # {"jsonrpc":"2.0","id":1,"result":
    # [{"removed":false,"logIndex":"0x80","transactionIndex":"0x56",
    # "transactionHash":"0x2d71f3085a796a0539c9cc28acd9073a67cf862260a41475f000dd101279f94f",
    # "blockHash":"0x8062a17fa791f5dbd59ea68891422e3299ca4e80885a89acf3fc706c8bceef53",
    # "blockNumber":"0x794fb5",
    # "address":"0x7f02c3e3c98b133055b8b348b2ac625669ed295d",
    # "data":"0x0000000000000000000000000000000000000000000000000000000000000001",
    # "topics":["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
    # "0x0000000000000000000000006885e36bfcb68cb383dfe90023a462c03bcb2ae5",
    # "0x00000000000000000000000080b5dc88c98e528bf9cb4b7f0f076ac41da24651"]

    bytecode = Op.LOG3(
        # ERC-20 token transfer log
        # ERC-20 token transfers are LOG3, since the topic, the sender, and receiver
        # are all topics (the sender and receiver are `indexed` in the solidity event)
        0,
        32,
        0xDDF252AD1BE2C89B69C2B068FC378DAA952BA7F163C4A11628F55A4DF523B3EF,
        0x000000000000000000000000AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,
        0x000000000000000000000000BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB,
    )

    requests = Requests()

    if include_deposit_event:
        bytecode += Om.MSTORE(DEFAULT_REQUEST_LOG) + Op.LOG1(
            0,
            len(DEFAULT_REQUEST_LOG),
            Spec.DEPOSIT_EVENT_SIGNATURE_HASH,
        )
        requests = Requests(DEFAULT_DEPOSIT_REQUEST)
    bytecode += Op.STOP

    pre[Spec.DEPOSIT_CONTRACT_ADDRESS] = Account(
        code=bytecode,
        nonce=1,
        balance=0,
    )
    sender = pre.fund_eoa()

    tx = Transaction(
        to=Spec.DEPOSIT_CONTRACT_ADDRESS,
        sender=sender,
        gas_limit=100_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(
                    requests_hash=requests,
                ),
            ),
        ],
        post={},
    )


@pytest.mark.parametrize(
    "log_argument,value",
    [
        pytest.param(
            arg,
            val,
            marks=pytest.mark.pre_alloc_group(
                f"deposit_layout_{arg}_{val}",
                reason=f"Deposit contract with invalid {arg} set to {val}",
            ),
        )
        for arg in EVENT_ARGUMENTS
        for val in EVENT_ARGUMENT_VALUES
    ],
)
@pytest.mark.exception_test
def test_invalid_layout(
    blockchain_test: BlockchainTestFiller, pre: Alloc, log_argument: str, value: str
):
    """Test deposit contract emitting logs with invalid layouts (sizes/offsets)."""
    log_params = {**DEFAULT_DEPOSIT_REQUEST_LOG_DATA_DICT}
    log_params[log_argument] = 0 if value == "zero" else 2**256 - 1  # type: ignore

    deposit_request_log = create_deposit_log_bytes(**log_params)  # type: ignore

    bytecode = Om.MSTORE(deposit_request_log) + Op.LOG1(
        0,
        len(deposit_request_log),
        Spec.DEPOSIT_EVENT_SIGNATURE_HASH,
    )
    bytecode += Op.STOP

    pre[Spec.DEPOSIT_CONTRACT_ADDRESS] = Account(
        code=bytecode,
        nonce=1,
        balance=0,
    )
    sender = pre.fund_eoa()

    tx = Transaction(
        to=Spec.DEPOSIT_CONTRACT_ADDRESS,
        sender=sender,
        gas_limit=100_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], exception=BlockException.INVALID_DEPOSIT_EVENT_LAYOUT),
        ],
        post={},
    )


@pytest.mark.parametrize(
    "slice_bytes",
    [
        pytest.param(
            True,
            marks=pytest.mark.pre_alloc_group(
                "deposit_log_length_short", reason="Deposit contract with shortened log data"
            ),
        ),
        pytest.param(
            False,
            marks=pytest.mark.pre_alloc_group(
                "deposit_log_length_long", reason="Deposit contract with lengthened log data"
            ),
        ),
    ],
)
@pytest.mark.exception_test
def test_invalid_log_length(blockchain_test: BlockchainTestFiller, pre: Alloc, slice_bytes: bool):
    """Test deposit contract emitting logs with invalid log length (one byte more or less)."""
    changed_log = DEFAULT_REQUEST_LOG[:-1] if slice_bytes else DEFAULT_REQUEST_LOG + b"\x00"

    bytecode = Om.MSTORE(changed_log) + Op.LOG1(
        0,
        len(changed_log),
        Spec.DEPOSIT_EVENT_SIGNATURE_HASH,
    )
    bytecode += Op.STOP

    pre[Spec.DEPOSIT_CONTRACT_ADDRESS] = Account(
        code=bytecode,
        nonce=1,
        balance=0,
    )
    sender = pre.fund_eoa()

    tx = Transaction(
        to=Spec.DEPOSIT_CONTRACT_ADDRESS,
        sender=sender,
        gas_limit=100_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], exception=BlockException.INVALID_DEPOSIT_EVENT_LAYOUT),
        ],
        post={},
    )
