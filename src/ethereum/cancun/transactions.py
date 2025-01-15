"""
TODO: Generate a log every time a value-transferring CALL or 
SELFDESTRUCT happens. We also add a similar log for transfers in transactions, so that all ETH transfers can be tracked using one 
mechanism.

Transactions are atomic units of work created externally to Ethereum and
submitted to be executed. If Ethereum is viewed as a state machine,
transactions are the events that move between states.
"""

from dataclasses import dataclass
from typing import Tuple, Union

from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes0, Bytes32
from ethereum_types.frozen import slotted_freezable
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.elliptic_curve import SECP256K1N, secp256k1_recover
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import InvalidSignatureError

from .exceptions import TransactionTypeError
from .fork_types import Address, VersionedHash
from vm.instructions.log import log3

TX_BASE_COST = 21000
TX_DATA_COST_PER_NON_ZERO = 16
TX_DATA_COST_PER_ZERO = 4
TX_CREATE_COST = 32000
TX_ACCESS_LIST_ADDRESS_COST = 2400
TX_ACCESS_LIST_STORAGE_KEY_COST = 1900
MAGIC_LOG_KHASH = (
    "ccb1f717aa77602faf03a594761a36956b1c4cf44c6b336d1db57da799b331b8"
)


@slotted_freezable
@dataclass
class LegacyTransaction:
    """
    Atomic operation performed on the block chain.
    """

    nonce: U256
    gas_price: Uint
    gas: Uint
    to: Union[Bytes0, Address]
    value: U256
    data: Bytes
    v: U256
    r: U256
    s: U256


@slotted_freezable
@dataclass
class AccessListTransaction:
    """
    The transaction type added in EIP-2930 to support access lists.
    """

    chain_id: U64
    nonce: U256
    gas_price: Uint
    gas: Uint
    to: Union[Bytes0, Address]
    value: U256
    data: Bytes
    access_list: Tuple[Tuple[Address, Tuple[Bytes32, ...]], ...]
    y_parity: U256
    r: U256
    s: U256
    log: Bytes


@slotted_freezable
@dataclass
class FeeMarketTransaction:
    """
    The transaction type added in EIP-1559.
    """

    chain_id: U64
    nonce: U256
    max_priority_fee_per_gas: Uint
    max_fee_per_gas: Uint
    gas: Uint
    to: Union[Bytes0, Address]
    value: U256
    data: Bytes
    access_list: Tuple[Tuple[Address, Tuple[Bytes32, ...]], ...]
    y_parity: U256
    r: U256
    s: U256


@slotted_freezable
@dataclass
class BlobTransaction:
    """
    The transaction type added in EIP-4844.
    """

    chain_id: U64
    nonce: U256
    max_priority_fee_per_gas: Uint
    max_fee_per_gas: Uint
    gas: Uint
    to: Address
    value: U256
    data: Bytes
    access_list: Tuple[Tuple[Address, Tuple[Bytes32, ...]], ...]
    max_fee_per_blob_gas: U256
    blob_versioned_hashes: Tuple[VersionedHash, ...]
    y_parity: U256
    r: U256
    s: U256


Transaction = Union[
    LegacyTransaction,
    AccessListTransaction,
    FeeMarketTransaction,
    BlobTransaction,
]


def encode_transaction(tx: Transaction) -> Union[LegacyTransaction, Bytes]:
    """
    Encode a transaction. Needed because non-legacy transactions aren't RLP.
    """
    if isinstance(tx, LegacyTransaction):
        return tx
    elif isinstance(tx, AccessListTransaction):
        return b"\x01" + rlp.encode(tx)
    elif isinstance(tx, FeeMarketTransaction):
        return b"\x02" + rlp.encode(tx)
    elif isinstance(tx, BlobTransaction):
        return b"\x03" + rlp.encode(tx)
    else:
        raise Exception(f"Unable to encode transaction of type {type(tx)}")


def decode_transaction(tx: Union[LegacyTransaction, Bytes]) -> Transaction:
    """
    Decode a transaction. Needed because non-legacy transactions aren't RLP.
    """
    if isinstance(tx, Bytes):
        if tx[0] == 1:
            return rlp.decode_to(AccessListTransaction, tx[1:])
        elif tx[0] == 2:
            return rlp.decode_to(FeeMarketTransaction, tx[1:])
        elif tx[0] == 3:
            return rlp.decode_to(BlobTransaction, tx[1:])
        else:
            raise TransactionTypeError(tx[0])
    else:
        return tx


def validate_transaction(tx: Transaction) -> bool:
    """
    Verifies a transaction.

    The gas in a transaction gets used to pay for the intrinsic cost of
    operations, therefore if there is insufficient gas then it would not
    be possible to execute a transaction and it will be declared invalid.

    Additionally, the nonce of a transaction must not equal or exceed the
    limit defined in `EIP-2681 <https://eips.ethereum.org/EIPS/eip-2681>`_.
    In practice, defining the limit as ``2**64-1`` has no impact because
    sending ``2**64-1`` transactions is improbable. It's not strictly
    impossible though, ``2**64-1`` transactions is the entire capacity of the
    Ethereum blockchain at 2022 gas limits for a little over 22 years.

    Parameters
    ----------
    tx :
        Transaction to validate.

    Returns
    -------
    verified : `bool`
        True if the transaction can be executed, or False otherwise.
    """
    from .vm.interpreter import MAX_CODE_SIZE

    if calculate_intrinsic_cost(tx) > tx.gas:
        return False
    if tx.nonce >= U256(U64.MAX_VALUE):
        return False
    if tx.to == Bytes0(b"") and len(tx.data) > 2 * MAX_CODE_SIZE:
        return False

    return True


def emit_transaction_logs(tx: Transaction) -> None:
    """
    From EIP 7708, ensure that for every value transferring CALL or SELFDESTRUCT opcode is present in the data, there is a corresponding LOG3 in the transaction that specifies the sender and receiver of these operations. The transaction itself must also contain a call to LOG3 that matches the sender and receiver of the transaction.


    CALL<F1>(gas, addr, val, argOst, argLen, retOst, retLen):
        Calls another contract

    _Params_
        gas: the gas included by the invoker to pay for the transaction? the estimated cost of the transaction? The upper limit that the invoker will pay for this transaction?
        addr: the address that all ETH is sent to

    SELFDESTRUCT<FF>(addr):
        Sends all ETH to addr; if executed in the same transaction as a contract was created it destroys the contract

    _Params_
        addr: The address that all ETH is sent to. This will be topic2 in our log call.


    LOG3<A3>(ost, len, topic0, topic1, topic2):

        Emits our special LOG3

    _Params_
        topic0: the magic keccak-256 hash of 42 which will indicate this type of log. Specified above as MAGIC_LOG_KHASH


    Parameters
    ----------
    tx :
        Transaction to insert logs into

    Returns
    -------
    Transaction : `ethereum.base_types.Uint`
        The intrinsic cost of the transaction.

    TODO Questions:
     - If the op is a SELFDESTRUCT, does that mean the corresponding LOG3 should specify topic1 as the initiator of the transaction, and the "addr" parameter then should be topic2?
     - I see the "to" field of the transaction, but where do I get the address of the wallet (... contractId? address?) that originated the transaction?
     - Do I need to check their transaction and see if they emit their own logs of the TX and each SD/CALL, or just assume that's on them, don't bother to check, and emit the "txlogs" (my term) anyway?
     - Why are my imports breaking? I'm in the 3.10.* venv, and I can see the 3.10 type definitions for ethereum_types.numeric under ./.mypy_cache/3.10/ethereum_types/numeric.data.json. I can even click through to the class, and the popup definition appears as well, but somehow it can't import it?
    """

    # First version, check transaction for any CALLs or SELFDESTRUCTs
    loggable_operations = []
    logs = []
    for byte in tx.data:
        if byte == Bytes32(b"FF") or byte == Bytes32(b"F1"):
            loggable_operations.append("""What goes here?""")
        elif byte == Bytes32(b"A3"):
            logs.append("""What goes here?""")

        """
        Are the next bytes the parameters of the opcode?
        
        e.g. The opcode is FF (SELFDESTRUCT). Does that mean the next byte in the transaction data is necessarily the 'addr' parameter?
        
        e.g. 2 The opcode is F1 (CALL). Does that mean the next seven bytes are the "gas, addr, val, argOst, argLen, retOst, retLen" parameters? 

        I guess I'd need to keep track of my position within the array and then append [ current_pos : current_pos+1 ] for SD and    [ current_pos : current_pos+7 ].

        Or wait, is this information actually on the stack and I should be popping it off? Do all the parameters of the tx data get pushed onto the stack at some point, and then I pop them off in order?

        I'm starting to think I need to push the appropriate parameters onto the stack for this loggable operation (once I figure out how to get them) and then invoke log3?
        """

    for loggable in loggable_operations:
        # If checking for their own logs
        """
        if loggable not in logs:
            evm.stack.push(ost)
            evm.stack.push(len)
            evm.stack.push(receiver_addr)
            evm.stack.push(sender_addr)
            evm.stack.push(MAGIC_LOG_KHASH)
            log3()
        """

        # If just emitting logs regardless
        # evm.stack.push(ost)
        # evm.stack.push(len)
        # evm.stack.push(receiver_addr)
        # evm.stack.push(sender_addr)
        # evm.stack.push(MAGIC_LOG_KHASH)
        log3()


def calculate_intrinsic_cost(tx: Transaction) -> Uint:
    """
    Calculates the gas that is charged before execution is started.

    The intrinsic cost of the transaction is charged before execution has
    begun. Functions/operations in the EVM cost money to execute so this
    intrinsic cost is for the operations that need to be paid for as part of
    the transaction. Data transfer, for example, is part of this intrinsic
    cost. It costs ether to send data over the wire and that ether is
    accounted for in the intrinsic cost calculated in this function. This
    intrinsic cost must be calculated and paid for before execution in order
    for all operations to be implemented.

    Parameters
    ----------
    tx :
        Transaction to compute the intrinsic cost of.

    Returns
    -------
    verified : `ethereum.base_types.Uint`
        The intrinsic cost of the transaction.
    """
    from .vm.gas import init_code_cost

    data_cost = 0

    for byte in tx.data:
        if byte == 0:
            data_cost += TX_DATA_COST_PER_ZERO
        else:
            data_cost += TX_DATA_COST_PER_NON_ZERO

    if tx.to == Bytes0(b""):
        create_cost = TX_CREATE_COST + int(init_code_cost(Uint(len(tx.data))))
    else:
        create_cost = 0

    access_list_cost = 0
    if isinstance(
        tx, (AccessListTransaction, FeeMarketTransaction, BlobTransaction)
    ):
        for _address, keys in tx.access_list:
            access_list_cost += TX_ACCESS_LIST_ADDRESS_COST
            access_list_cost += len(keys) * TX_ACCESS_LIST_STORAGE_KEY_COST

    return Uint(TX_BASE_COST + data_cost + create_cost + access_list_cost)


def recover_sender(chain_id: U64, tx: Transaction) -> Address:
    """
    Extracts the sender address from a transaction.

    The v, r, and s values are the three parts that make up the signature
    of a transaction. In order to recover the sender of a transaction the two
    components needed are the signature (``v``, ``r``, and ``s``) and the
    signing hash of the transaction. The sender's public key can be obtained
    with these two values and therefore the sender address can be retrieved.

    Parameters
    ----------
    tx :
        Transaction of interest.
    chain_id :
        ID of the executing chain.

    Returns
    -------
    sender : `ethereum.fork_types.Address`
        The address of the account that signed the transaction.
    """
    r, s = tx.r, tx.s
    if U256(0) >= r or r >= SECP256K1N:
        raise InvalidSignatureError("bad r")
    if U256(0) >= s or s > SECP256K1N // U256(2):
        raise InvalidSignatureError("bad s")

    if isinstance(tx, LegacyTransaction):
        v = tx.v
        if v == 27 or v == 28:
            public_key = secp256k1_recover(
                r, s, v - U256(27), signing_hash_pre155(tx)
            )
        else:
            chain_id_x2 = U256(chain_id) * U256(2)
            if v != U256(35) + chain_id_x2 and v != U256(36) + chain_id_x2:
                raise InvalidSignatureError("bad v")
            public_key = secp256k1_recover(
                r,
                s,
                v - U256(35) - chain_id_x2,
                signing_hash_155(tx, chain_id),
            )
    elif isinstance(tx, AccessListTransaction):
        public_key = secp256k1_recover(
            r, s, tx.y_parity, signing_hash_2930(tx)
        )
    elif isinstance(tx, FeeMarketTransaction):
        public_key = secp256k1_recover(
            r, s, tx.y_parity, signing_hash_1559(tx)
        )
    elif isinstance(tx, BlobTransaction):
        public_key = secp256k1_recover(
            r, s, tx.y_parity, signing_hash_4844(tx)
        )

    return Address(keccak256(public_key)[12:32])


def signing_hash_pre155(tx: LegacyTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a legacy (pre EIP 155) signature.

    Parameters
    ----------
    tx :
        Transaction of interest.

    Returns
    -------
    hash : `ethereum.crypto.hash.Hash32`
        Hash of the transaction.
    """
    return keccak256(
        rlp.encode(
            (
                tx.nonce,
                tx.gas_price,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
            )
        )
    )


def signing_hash_155(tx: LegacyTransaction, chain_id: U64) -> Hash32:
    """
    Compute the hash of a transaction used in a EIP 155 signature.

    Parameters
    ----------
    tx :
        Transaction of interest.
    chain_id :
        The id of the current chain.

    Returns
    -------
    hash : `ethereum.crypto.hash.Hash32`
        Hash of the transaction.
    """
    return keccak256(
        rlp.encode(
            (
                tx.nonce,
                tx.gas_price,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                chain_id,
                Uint(0),
                Uint(0),
            )
        )
    )


def signing_hash_2930(tx: AccessListTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a EIP 2930 signature.

    Parameters
    ----------
    tx :
        Transaction of interest.

    Returns
    -------
    hash : `ethereum.crypto.hash.Hash32`
        Hash of the transaction.
    """
    return keccak256(
        b"\x01"
        + rlp.encode(
            (
                tx.chain_id,
                tx.nonce,
                tx.gas_price,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                tx.access_list,
            )
        )
    )


def signing_hash_1559(tx: FeeMarketTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a EIP 1559 signature.

    Parameters
    ----------
    tx :
        Transaction of interest.

    Returns
    -------
    hash : `ethereum.crypto.hash.Hash32`
        Hash of the transaction.
    """
    return keccak256(
        b"\x02"
        + rlp.encode(
            (
                tx.chain_id,
                tx.nonce,
                tx.max_priority_fee_per_gas,
                tx.max_fee_per_gas,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                tx.access_list,
            )
        )
    )


def signing_hash_4844(tx: BlobTransaction) -> Hash32:
    """
    Compute the hash of a transaction used in a EIP-4844 signature.

    Parameters
    ----------
    tx :
        Transaction of interest.

    Returns
    -------
    hash : `ethereum.crypto.hash.Hash32`
        Hash of the transaction.
    """
    return keccak256(
        b"\x03"
        + rlp.encode(
            (
                tx.chain_id,
                tx.nonce,
                tx.max_priority_fee_per_gas,
                tx.max_fee_per_gas,
                tx.gas,
                tx.to,
                tx.value,
                tx.data,
                tx.access_list,
                tx.max_fee_per_blob_gas,
                tx.blob_versioned_hashes,
            )
        )
    )
