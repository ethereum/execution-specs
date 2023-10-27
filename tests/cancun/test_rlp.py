import pytest

import ethereum.rlp as rlp
from ethereum.base_types import U64, U256, Bytes, Bytes0, Bytes8, Bytes32, Uint
from ethereum.cancun.fork_types import (
    AccessListTransaction,
    Block,
    FeeMarketTransaction,
    Header,
    LegacyTransaction,
    Log,
    Receipt,
    Transaction,
    Withdrawal,
    decode_transaction,
    encode_transaction,
)
from ethereum.cancun.utils.hexadecimal import hex_to_address
from ethereum.crypto.hash import keccak256
from ethereum.utils.hexadecimal import hex_to_bytes256

hash1 = keccak256(b"foo")
hash2 = keccak256(b"bar")
hash3 = keccak256(b"baz")
hash4 = keccak256(b"foobar")
hash5 = keccak256(b"quux")
hash6 = keccak256(b"foobarbaz")

address1 = hex_to_address("0x00000000219ab540356cbb839cbe05303d7705fa")
address2 = hex_to_address("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2")
address3 = hex_to_address("0xbe0eb53f46cd790cd13851d5eff43d12404d33e8")

bloom = hex_to_bytes256(
    "0x886480c00200620d84180d0470000c503081160044d05015808"
    "0037401107060120040105281100100104500414203040a208003"
    "4814200610da1208a638d16e440c024880800301e1004c2b02285"
    "0602000084c3249a0c084569c90c2002001586241041e8004035a"
    "4400a0100938001e041180083180b0340661372060401428c0200"
    "87410402b9484028100049481900c08034864314688d001548c30"
    "00828e542284180280006402a28a0264da00ac223004006209609"
    "83206603200084040122a4739080501251542082020a4087c0002"
    "81c08800898d0900024047380000127038098e090801080000429"
    "0c84201661040200201c0004b8490ad588804"
)

legacy_transaction = LegacyTransaction(
    U256(1),
    Uint(2),
    Uint(3),
    Bytes0(),
    U256(4),
    Bytes(b"foo"),
    U256(27),
    U256(5),
    U256(6),
)

access_list_transaction = AccessListTransaction(
    U64(1),
    U256(1),
    Uint(2),
    Uint(3),
    Bytes0(),
    U256(4),
    Bytes(b"bar"),
    ((address1, (hash1, hash2)), (address2, tuple())),
    U256(27),
    U256(5),
    U256(6),
)

transaction_1559 = FeeMarketTransaction(
    U64(1),
    U256(1),
    Uint(7),
    Uint(2),
    Uint(3),
    Bytes0(),
    U256(4),
    Bytes(b"bar"),
    ((address1, (hash1, hash2)), (address2, tuple())),
    U256(27),
    U256(5),
    U256(6),
)

withdrawal = Withdrawal(U64(0), U64(1), address1, U256(2))


header = Header(
    parent_hash=hash1,
    ommers_hash=hash2,
    coinbase=address1,
    state_root=hash3,
    transactions_root=hash4,
    receipt_root=hash5,
    bloom=bloom,
    difficulty=Uint(1),
    number=Uint(2),
    gas_limit=Uint(3),
    gas_used=Uint(4),
    timestamp=U256(5),
    extra_data=Bytes(b"foobar"),
    prev_randao=Bytes32(b"1234567890abcdef1234567890abcdef"),
    nonce=Bytes8(b"12345678"),
    base_fee_per_gas=Uint(6),
    withdrawals_root=hash6,
)

block = Block(
    header=header,
    transactions=(
        encode_transaction(legacy_transaction),
        encode_transaction(access_list_transaction),
        encode_transaction(transaction_1559),
    ),
    ommers=(),
    withdrawals=(withdrawal,),
)

log1 = Log(
    address=address1,
    topics=(hash1, hash2),
    data=Bytes(b"foobar"),
)

log2 = Log(
    address=address1,
    topics=(hash1,),
    data=Bytes(b"quux"),
)

receipt = Receipt(
    succeeded=True,
    cumulative_gas_used=Uint(1),
    bloom=bloom,
    logs=(log1, log2),
)


@pytest.mark.parametrize(
    "rlp_object",
    [
        legacy_transaction,
        access_list_transaction,
        transaction_1559,
        header,
        block,
        log1,
        log2,
        receipt,
        withdrawal,
    ],
)
def test_cancun_rlp(rlp_object: rlp.RLP) -> None:
    encoded = rlp.encode(rlp_object)
    assert rlp.decode_to(type(rlp_object), encoded) == rlp_object


@pytest.mark.parametrize(
    "tx", [legacy_transaction, access_list_transaction, transaction_1559]
)
def test_transaction_encoding(tx: Transaction) -> None:
    encoded = encode_transaction(tx)
    assert decode_transaction(encoded) == tx
