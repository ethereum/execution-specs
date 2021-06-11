import pytest

from eth1spec.base_types import U256, Bytes, Bytes8, Bytes32
from eth1spec.eth_types import Address, Bloom, Hash32, Header, Root, Uint
from eth1spec.spec import verify_header
from tests.helpers import hex2hash


def create_fake_parent_header(
    parent_hash: Hash32 = hex2hash(
        "0x0000000000000000000000000000000000000000000000000000000000000000"
    ),
    ommers_hash: Hash32 = hex2hash(
        "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
    ),
    coinbase: Address = hex2hash("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba"),
    state_root: Root = hex2hash(
        "0x4b4b7a0d58a2388c0e6b3b048c3c27edd6febc6f04171167ed15a77ab2e60b16"
    ),
    transactions_root: Root = hex2hash(
        "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
    ),
    receipt_root: Root = hex2hash(
        "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
    ),
    bloom: Bloom = hex2hash(
        "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    ),
    difficulty: Uint = Uint(131072),
    number: Uint = Uint(0),
    gas_limit: Uint = Uint(1000000),
    gas_used: Uint = Uint(0),
    timestamp: U256 = U256(950),
    extra_data: Bytes = hex2hash("0x42"),
    mix_digest: Bytes32 = hex2hash(
        "0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421"
    ),
    nonce: Bytes8 = hex2hash("0x0102030405060708"),
) -> Header:
    """
    Utility method to generate parent header
    """
    return Header(
        parent_hash=parent_hash,
        ommers_hash=ommers_hash,
        coinbase=coinbase,
        state_root=state_root,
        transactions_root=transactions_root,
        receipt_root=receipt_root,
        bloom=bloom,
        difficulty=difficulty,
        number=number,
        gas_limit=gas_limit,
        gas_used=gas_used,
        timestamp=timestamp,
        extra_data=extra_data,
        mix_digest=mix_digest,
        nonce=nonce,
    )


def create_fake_header(
    parent_hash: Hash32 = hex2hash(
        "0x26f4cb1cb9685bad697c0c16ca0d27fe0a4b09364f83ed8418cef0d523783625"
    ),
    ommers_hash: Hash32 = hex2hash(
        "0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347"
    ),
    coinbase: Address = hex2hash("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba"),
    state_root: Root = hex2hash(
        "0x328f16ca7b0259d7617b3ddf711c107efe6d5785cbeb11a8ed1614b484a6bc3a"
    ),
    transactions_root: Root = hex2hash(
        "0x93ca2a18d52e7c1846f7b104e2fc1e5fdc71ebe38187248f9437d39e74f43aab"
    ),
    receipt_root: Root = hex2hash(
        "0xe151c94b824bded58346fa03fc91fa275bd0cf94caac0ea4ebb9c8d32a574644"
    ),
    bloom: Bloom = hex2hash(
        "0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
    ),
    difficulty: Uint = Uint(131072),
    number: Uint = Uint(1),
    gas_limit: Uint = Uint(1000000),
    gas_used: Uint = Uint(41012),
    timestamp: U256 = U256(1000),
    extra_data: Bytes = hex2hash(""),
    mix_digest: Bytes32 = hex2hash(
        "0x0000000000000000000000000000000000000000000000000000000000000000"
    ),
    nonce: Bytes8 = hex2hash("0x0000000000000000"),
) -> Header:
    """
    Utility method to generate parent header
    """
    return Header(
        parent_hash=parent_hash,
        ommers_hash=ommers_hash,
        coinbase=coinbase,
        state_root=state_root,
        transactions_root=transactions_root,
        receipt_root=receipt_root,
        bloom=bloom,
        difficulty=difficulty,
        number=number,
        gas_limit=gas_limit,
        gas_used=gas_used,
        timestamp=timestamp,
        extra_data=extra_data,
        mix_digest=mix_digest,
        nonce=nonce,
    )


def test_validate_header_success() -> None:
    parent_header = create_fake_parent_header()
    header = create_fake_header()
    assert verify_header(header, parent_header) is True


def test_validate_header_incorrect_difficulty() -> None:
    parent_header = create_fake_parent_header()
    header = create_fake_header(difficulty=Uint(1))
    with pytest.raises(AssertionError):
        verify_header(header, parent_header)


def test_validate_header_gas_limit_less_than_minimum() -> None:
    parent_header = create_fake_parent_header()
    # 0 < GAS_LIMIT_MINIMUM
    header = create_fake_header(gas_limit=Uint(0))
    with pytest.raises(AssertionError):
        verify_header(header, parent_header)


def test_validate_header_gas_limit_gte_parent_plus_adj_delta() -> None:
    parent_header = create_fake_parent_header()
    # parent_gas_limit = 1000000
    # max_adjustment_delta = parent_gas_limit // GAS_LIMIT_ADJUSTMENT_FACTOR = 976
    # parent_gas_limit + max_adjustment_delta = 1000976
    header = create_fake_header(gas_limit=Uint(1000976))
    with pytest.raises(AssertionError):
        verify_header(header, parent_header)


def test_validate_header_gas_limit_gte_parent_minus_adj_delta() -> None:
    parent_header = create_fake_parent_header()
    # parent_gas_limit = 1000000
    # max_adjustment_delta = parent_gas_limit // GAS_LIMIT_ADJUSTMENT_FACTOR = 976
    # parent_gas_limit - max_adjustment_delta = 999024
    header = create_fake_header(gas_limit=Uint(999024))
    with pytest.raises(AssertionError):
        verify_header(header, parent_header)


def test_validate_header_timestamp_lt_parent() -> None:
    parent_header = create_fake_parent_header()
    header = create_fake_header(timestamp=parent_header.timestamp - 1)
    with pytest.raises(AssertionError):
        verify_header(header, parent_header)


def test_validate_header_number_lt_parent() -> None:
    parent_header = create_fake_parent_header()
    header = create_fake_header(number=parent_header.number)
    with pytest.raises(AssertionError):
        verify_header(header, parent_header)


def test_validate_header_extra_bytes_gt_32() -> None:
    parent_header = create_fake_parent_header()
    header = create_fake_header(extra_data=b"0" * 33)
    with pytest.raises(AssertionError):
        verify_header(header, parent_header)
