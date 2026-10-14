"""Tests EIP-7805 FOCIL inclusion-list handling across transaction types."""

import ethereum_rlp as eth_rlp
import pytest
from ethereum_types.numeric import Uint
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Bytes,
    Fork,
    Op,
    Transaction,
)
from spec256k1 import PrivateKey

from .spec import ref_spec_7805

REFERENCE_SPEC_GIT_PATH = ref_spec_7805.git_path
REFERENCE_SPEC_VERSION = ref_spec_7805.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.blockchain_test_engine_only,
]


@pytest.mark.parametrize(
    "scenario",
    [
        "type_0_protected",
        "type_0_unprotected",
        "type_0_creation",
        "type_1_access_list",
        "type_1_creation",
        "type_2",
        "type_2_creation",
        "type_4_delegation",
    ],
)
def test_included_il_tx_of_each_type_is_readable(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    scenario: str,
) -> None:
    """
    Every transaction type is decodable in the inclusion list.

    Each scenario places one transaction of a given type in both the block
    body and the inclusion list. Because the transaction is present in the
    block body, the inclusion list check is satisfied only if the execution
    layer can decode it as a transaction type valid for the active fork.
    The post-state confirms the transaction also executed as expected.
    """
    sender = pre.fund_eoa()
    post: dict = {}

    match scenario:
        case "type_0_protected":
            recipient = pre.nonexistent_account()
            il_tx = Transaction(
                ty=0, sender=sender, to=recipient, value=1, protected=True
            )
            post[recipient] = Account(balance=1)
        case "type_0_unprotected":
            recipient = pre.nonexistent_account()
            il_tx = Transaction(
                ty=0, sender=sender, to=recipient, value=1, protected=False
            )
            post[recipient] = Account(balance=1)
        case "type_0_creation":
            il_tx = Transaction(ty=0, sender=sender, to=None, data=Op.STOP)
            post[il_tx.created_contract] = Account(nonce=1)
        case "type_1_access_list":
            recipient = pre.nonexistent_account()
            il_tx = Transaction(
                ty=1,
                sender=sender,
                to=recipient,
                value=1,
                access_list=[
                    AccessList(address=recipient, storage_keys=[0x01])
                ],
            )
            post[recipient] = Account(balance=1)
        case "type_1_creation":
            il_tx = Transaction(
                ty=1,
                sender=sender,
                to=None,
                data=Op.STOP,
                access_list=[AccessList(address=sender, storage_keys=[0x01])],
            )
            post[il_tx.created_contract] = Account(nonce=1)
        case "type_2":
            recipient = pre.nonexistent_account()
            il_tx = Transaction(ty=2, sender=sender, to=recipient, value=1)
            post[recipient] = Account(balance=1)
        case "type_2_creation":
            il_tx = Transaction(ty=2, sender=sender, to=None, data=Op.STOP)
            post[il_tx.created_contract] = Account(nonce=1)
        case "type_4_delegation":
            authority = pre.fund_eoa()
            delegate_target = pre.deploy_contract(code=Op.STOP)
            il_tx = Transaction(
                ty=4,
                sender=sender,
                to=sender,
                authorization_list=[
                    AuthorizationTuple(
                        address=delegate_target, signer=authority
                    )
                ],
            )
            # A valid authorization bumps the authority's nonce and sets its
            # delegation designation.
            post[authority] = Account(nonce=1)
        case _:
            raise ValueError(f"unknown scenario: {scenario}")

    blockchain_test(
        pre=pre,
        post=post,
        blocks=[
            Block(
                txs=[il_tx],
                inclusion_list_txs=[il_tx],
                expected_inclusion_list_satisfied=True,
            )
        ],
    )


# L2 transaction types, whose type bytes Bogota does not define.
FEE_TOKEN_TX_TYPE = 0x7D
PRIVILEGED_TX_TYPE = 0x7E


def l2_typed_entry(type_byte: int, tx: Transaction) -> Bytes:
    """
    Re-encode a type-2 `tx` as an L2 transaction type: 0x7e carries its
    sender in place of a signature, 0x7d adds a fee token and is signed.
    """
    fields = tx.to_list(signing=True)
    if type_byte == PRIVILEGED_TX_TYPE:
        payload = [*fields, tx.sender]
    elif type_byte == FEE_TOKEN_TX_TYPE:
        assert tx.sender is not None and tx.sender.key is not None
        # No check reads the fee token, so any address will do.
        unsigned = [*fields, Address(0)]
        signing_hash = Bytes(
            bytes([type_byte]) + eth_rlp.encode(unsigned)
        ).keccak256()
        signature = PrivateKey(tx.sender.key).sign_recoverable(signing_hash)
        payload = [
            *unsigned,
            Uint(signature[64]),
            Uint(int.from_bytes(signature[0:32], "big")),
            Uint(int.from_bytes(signature[32:64], "big")),
        ]
    else:
        raise ValueError(f"unknown type byte: {type_byte:#x}")
    return Bytes(bytes([type_byte]) + eth_rlp.encode(payload))


# Positions in a signed type-2 payload.
CHAIN_ID_FIELD = 0
TO_FIELD = 5


def type_2_entry(
    tx: Transaction,
    raw_fields: dict[int, bytes] | None = None,
    list_length_leading_zero: bool = False,
) -> Bytes:
    """
    Re-encode a signed type-2 `tx`, swapping in raw encodings for some
    fields and optionally padding its list length with a zero byte.
    """
    decoded = eth_rlp.decode(tx.rlp()[1:])
    assert isinstance(decoded, list)
    fields = [eth_rlp.encode(item) for item in decoded]
    for index, raw_field in (raw_fields or {}).items():
        fields[index] = raw_field
    body = b"".join(fields)
    # A payload this long always takes the long-form list header.
    assert len(body) >= 56
    length = len(body).to_bytes((len(body).bit_length() + 7) // 8, "big")
    if list_length_leading_zero:
        length = b"\x00" + length
    return Bytes(b"\x02" + bytes([0xF7 + len(length)]) + length + body)


@pytest.mark.parametrize(
    "entry",
    [
        "type_2_control",
        "legacy_control",
        "empty",
        "type_0x00_with_legacy_payload",
        "undefined_type",
        "type_0x7f",
        "type_0xff",
        "l2_fee_token_0x7d",
        "l2_privileged_0x7e",
        "type_1_with_type_2_payload",
        "type_2_trailing_byte",
        "truncated_legacy",
        "type_2_chain_id_leading_zero",
        "type_2_chain_id_byte_as_string",
        "type_2_to_long_form_length",
        "type_2_list_length_leading_zero",
    ],
)
@pytest.mark.parametrize(
    "appendable_tx_follows",
    [
        pytest.param(False, id="alone"),
        pytest.param(True, id="before_appendable_tx"),
    ],
)
def test_undecodable_il_entry_is_skipped(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    entry: str,
    appendable_tx_follows: bool,
) -> None:
    """
    An inclusion list entry that is not a transaction is skipped.

    Alone it leaves the payload satisfied. Followed by an appendable
    transaction, the check moves on past it and the payload is unsatisfied.
    The control entries show the payloads the others reuse are appendable.
    """
    # Entries built from raw bytes are signed here, before the framework
    # would set their gas limit.
    transfer_gas = fork.transaction_intrinsic_cost_calculator()()
    type_2_tx = Transaction(
        ty=2,
        sender=pre.fund_eoa(),
        to=pre.nonexistent_account(),
        gas_limit=transfer_gas,
    ).with_signature_and_sender()
    type_2_payload = type_2_tx.rlp()[1:]
    legacy_tx = Transaction(
        ty=0,
        sender=pre.fund_eoa(),
        to=pre.nonexistent_account(),
        gas_limit=transfer_gas,
    ).with_signature_and_sender()
    undefined_type = max(fork.tx_types()) + 1
    assert undefined_type < 0x7F
    assert FEE_TOKEN_TX_TYPE not in fork.tx_types()
    assert PRIVILEGED_TX_TYPE not in fork.tx_types()
    # The non-canonical entries re-encode the type-2 control field by field.
    assert type_2_entry(type_2_tx) == type_2_tx.rlp()
    decoded = eth_rlp.decode(type_2_payload)
    assert isinstance(decoded, list)
    chain_id, to = decoded[CHAIN_ID_FIELD], decoded[TO_FIELD]
    assert isinstance(chain_id, bytes) and isinstance(to, bytes)
    assert len(chain_id) == 1 and chain_id[0] < 0x80
    assert len(to) == 20

    entry_appendable = False
    if entry == "type_2_control":
        il_entry = Bytes(type_2_tx.rlp())
        entry_appendable = True
    elif entry == "legacy_control":
        il_entry = Bytes(legacy_tx.rlp())
        entry_appendable = True
    elif entry == "empty":
        il_entry = Bytes(b"")
    elif entry == "type_0x00_with_legacy_payload":
        il_entry = Bytes(b"\x00" + legacy_tx.rlp())
    elif entry == "undefined_type":
        il_entry = Bytes(bytes([undefined_type]) + type_2_payload)
    elif entry == "type_0x7f":
        il_entry = Bytes(b"\x7f" + type_2_payload)
    elif entry == "type_0xff":
        il_entry = Bytes(b"\xff" + type_2_payload)
    elif entry == "l2_fee_token_0x7d":
        il_entry = l2_typed_entry(FEE_TOKEN_TX_TYPE, type_2_tx)
    elif entry == "l2_privileged_0x7e":
        il_entry = l2_typed_entry(PRIVILEGED_TX_TYPE, type_2_tx)
    elif entry == "type_1_with_type_2_payload":
        il_entry = Bytes(b"\x01" + type_2_payload)
    elif entry == "type_2_trailing_byte":
        il_entry = Bytes(type_2_tx.rlp() + b"\x00")
    elif entry == "truncated_legacy":
        il_entry = Bytes(legacy_tx.rlp()[:-1])
    elif entry == "type_2_chain_id_leading_zero":
        il_entry = type_2_entry(
            type_2_tx, {CHAIN_ID_FIELD: b"\x82\x00" + chain_id}
        )
    elif entry == "type_2_chain_id_byte_as_string":
        il_entry = type_2_entry(
            type_2_tx, {CHAIN_ID_FIELD: b"\x81" + chain_id}
        )
    elif entry == "type_2_to_long_form_length":
        il_entry = type_2_entry(type_2_tx, {TO_FIELD: b"\xb8\x14" + to})
    elif entry == "type_2_list_length_leading_zero":
        il_entry = type_2_entry(type_2_tx, list_length_leading_zero=True)
    else:
        raise ValueError(f"unknown entry: {entry}")

    inclusion_list: list[Transaction | Bytes] = [il_entry]
    if appendable_tx_follows:
        inclusion_list.append(
            Transaction(sender=pre.fund_eoa(), to=pre.nonexistent_account())
        )

    blockchain_test(
        pre=pre,
        post={},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=inclusion_list,
                expected_inclusion_list_satisfied=not (
                    entry_appendable or appendable_tx_follows
                ),
            )
        ],
    )
