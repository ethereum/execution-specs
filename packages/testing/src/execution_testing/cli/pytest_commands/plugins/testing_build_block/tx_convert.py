"""Convert spamoor-helper transaction dicts into signed EST Transactions."""

from typing import Any

from execution_testing.base_types import Address, Bytes, Hash, HexNumber
from execution_testing.forks import Fork
from execution_testing.test_types import (
    EOA,
    Blob,
    Transaction,
)


def _optional_address(value: Any) -> Address | None:
    """
    Return an ``Address`` from *value* or ``None`` for contract creation.

    Spamoor uses ``"to": ""`` to flag contract creation, while EST expects
    ``None``.
    """
    if value is None or value == "":
        return None
    return Address(value)


def _data_bytes(value: Any) -> Bytes:
    """Return ``Bytes`` payload from *value*, tolerating ``None``/empty."""
    if value is None or value == "":
        return Bytes(b"")
    return Bytes(value)


def spamoor_dict_to_transaction(
    tx_dict: dict[str, Any],
    signer: EOA,
    chain_id: int,
    *,
    nonce_override: int | None = None,
    fork: Fork | None = None,
    blob_seed: int = 0,
) -> Transaction:
    """
    Convert a spamoor helpers dict into a signed EST ``Transaction``.

    Key mapping: ``type`` -> ``ty``, ``to`` -> ``to`` (``""`` means
    contract creation), ``value`` -> ``value``, ``data`` -> ``input``,
    ``gas`` -> ``gas_limit``, ``maxFeePerGas`` and
    ``maxPriorityFeePerGas`` are forwarded as-is, and ``accessList``
    maps to ``access_list``. ``chainId`` is always overridden with
    *chain_id* because spamoor hard-codes ``1``.
    """
    if nonce_override is not None:
        nonce_value = nonce_override
    elif "nonce" in tx_dict:
        nonce_value = int(tx_dict["nonce"])
    else:
        nonce_value = int(signer.nonce)

    access_list = tx_dict.get("accessList", [])
    ty = int(tx_dict["type"])

    tx_kwargs: dict[str, Any] = dict(
        ty=HexNumber(ty),
        nonce=HexNumber(nonce_value),
        to=_optional_address(tx_dict.get("to")),
        value=HexNumber(int(tx_dict["value"])),
        data=_data_bytes(tx_dict.get("data")),
        gas_limit=HexNumber(int(tx_dict["gas"])),
        max_fee_per_gas=HexNumber(int(tx_dict["maxFeePerGas"])),
        max_priority_fee_per_gas=HexNumber(
            int(tx_dict["maxPriorityFeePerGas"])
        ),
        chain_id=chain_id,
        access_list=access_list,
        secret_key=signer.key,
        sender=signer,
    )

    if ty == 3:
        if fork is None:
            raise ValueError("fork is required for type-3 (blob) transactions")
        blob_count = int(
            tx_dict.get(
                "blobCount",
                len(tx_dict.get("blobVersionedHashes", [])) or 1,
            )
        )
        blob_objects = [
            Blob.from_fork(fork, seed=blob_seed + i) for i in range(blob_count)
        ]
        versioned_hashes = [Hash(blob.versioned_hash) for blob in blob_objects]
        tx_kwargs["max_fee_per_blob_gas"] = HexNumber(
            int(tx_dict.get("maxFeePerBlobGas", 1))
        )
        tx_kwargs["blob_versioned_hashes"] = versioned_hashes
        # Block-form RLP (payload only). testing_commitBlockV1 does not
        # take sidecars; it verifies versioned hashes from the payload.
        _ = blob_objects  # kept for potential future sidecar wiring
        tx = Transaction(**tx_kwargs).with_signature_and_sender()
        return tx

    tx = Transaction(**tx_kwargs)
    return tx.with_signature_and_sender()
