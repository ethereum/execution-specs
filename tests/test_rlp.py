import json
import os
from typing import List, Sequence, Tuple, Union, cast

import pytest

from ethereum import rlp
from ethereum.exceptions import RLPDecodingError, RLPEncodingError
from ethereum.frontier.fork_types import U256, Bytes, Uint
from ethereum.rlp import RLP
from ethereum.utils.hexadecimal import hex_to_bytes
from tests.helpers import TEST_FIXTURES

ETHEREUM_TESTS_PATH = TEST_FIXTURES["ethereum_tests"]["fixture_path"]


#
# Tests for RLP encode
#

#
# Testing bytes encoding
#


def test_rlp_encode_empty_bytes() -> None:
    assert rlp.encode_bytes(b"") == bytearray([0x80])
    assert rlp.encode_bytes(bytearray()) == bytearray([0x80])


def test_rlp_encode_single_byte_val_less_than_128() -> None:
    assert rlp.encode_bytes(b"x") == bytearray([0x78])
    assert rlp.encode_bytes(bytearray(b"x")) == bytearray([0x78])


def test_rlp_encode_single_byte_val_equal_128() -> None:
    assert rlp.encode_bytes(b"\x80") == b"\x81\x80"
    assert rlp.encode_bytes(bytearray(b"\x80")) == b"\x81\x80"


def test_rlp_encode_single_byte_val_greater_than_128() -> None:
    assert rlp.encode_bytes(b"\x83") == bytearray([0x81, 0x83])
    assert rlp.encode_bytes(bytearray(b"\x83")) == bytearray([0x81, 0x83])


def test_rlp_encode_55_bytes() -> None:
    assert rlp.encode_bytes(b"\x83" * 55) == bytearray([0xB7]) + bytearray(
        b"\x83" * 55
    )
    assert rlp.encode_bytes(bytearray(b"\x83") * 55) == bytearray(
        [0xB7]
    ) + bytearray(b"\x83" * 55)


def test_rlp_encode_large_bytes() -> None:
    assert rlp.encode_bytes(b"\x83" * 2**20) == (
        bytearray([0xBA])
        + bytearray(b"\x10\x00\x00")
        + bytearray(b"\x83" * 2**20)
    )
    assert rlp.encode_bytes(bytearray(b"\x83") * 2**20) == (
        bytearray([0xBA])
        + bytearray(b"\x10\x00\x00")
        + bytearray(b"\x83" * 2**20)
    )


#
# Testing uint and u256 encoding
#


def test_rlp_encode_uint_0() -> None:
    assert rlp.encode(Uint(0)) == b"\x80"


def test_rlp_encode_uint_byte_max() -> None:
    assert rlp.encode(Uint(255)) == b"\x81\xff"


def test_rlp_encode_uint256_0() -> None:
    assert rlp.encode(U256(0)) == b"\x80"


def test_rlp_encode_uint256_byte_max() -> None:
    assert rlp.encode(U256(255)) == b"\x81\xff"


#
# Testing str encoding
#


def test_rlp_encode_empty_str() -> None:
    assert rlp.encode("") == b"\x80"


def test_rlp_encode_one_char_str() -> None:
    assert rlp.encode("h") == b"h"


def test_rlp_encode_multi_char_str() -> None:
    assert rlp.encode("hello") == b"\x85hello"


#
# Testing sequence encoding
#


def test_rlp_encode_empty_sequence() -> None:
    assert rlp.encode_sequence([]) == bytearray([0xC0])


def test_rlp_encode_single_elem_list_byte() -> None:
    assert rlp.encode_sequence([b"hello"]) == bytearray([0xC6]) + b"\x85hello"


def test_rlp_encode_single_elem_list_uint() -> None:
    assert rlp.encode_sequence([Uint(255)]) == bytearray([0xC2]) + b"\x81\xff"


def test_rlp_encode_10_elem_byte_uint_combo() -> None:
    raw_data = [b"hello"] * 5 + [Uint(35)] * 5
    expected = (
        bytearray([0xE3])
        + b"\x85hello\x85hello\x85hello\x85hello\x85hello#####"
    )
    assert rlp.encode_sequence(raw_data) == expected


def test_rlp_encode_20_elem_byte_uint_combo() -> None:
    raw_data = [Uint(35)] * 10 + [b"hello"] * 10
    expected = (
        bytearray([0xF8])
        + b"F"
        + b"##########\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello"
    )
    assert rlp.encode_sequence(raw_data) == expected


def test_rlp_encode_nested_sequence() -> None:
    nested_sequence: Sequence["RLP"] = [
        b"hello",
        Uint(255),
        [b"how", [b"are", b"you", [b"doing"]]],
    ]
    expected: Bytes = (
        b"\xdd\x85hello\x81\xff\xd4\x83how\xcf\x83are\x83you\xc6\x85doing"
    )
    assert rlp.encode_sequence(nested_sequence) == expected


def test_rlp_encode_successfully() -> None:
    test_cases = [
        (b"", bytearray([0x80])),
        (b"\x83" * 55, bytearray([0xB7]) + bytearray(b"\x83" * 55)),
        (Uint(0), b"\x80"),
        (Uint(255), b"\x81\xff"),
        ([], bytearray([0xC0])),
        (
            [b"hello"] * 5 + [Uint(35)] * 5,
            bytearray([0xE3])
            + bytearray(b"\x85hello\x85hello\x85hello\x85hello\x85hello#####"),
        ),
        (
            [b"hello", Uint(255), [b"how", [b"are", b"you", [b"doing"]]]],
            bytearray(
                b"\xdd\x85hello\x81\xff\xd4\x83how\xcf\x83are\x83you\xc6\x85doing"
            ),
        ),
    ]
    for raw_data, expected_encoding in test_cases:
        assert rlp.encode(cast(RLP, raw_data)) == expected_encoding


def test_rlp_encode_fails() -> None:
    test_cases = [
        123,
        [b"hello", Uint(255), [b"how", [b"are", [b"you", [123]]]]],
    ]
    for raw_data in test_cases:
        with pytest.raises(RLPEncodingError):
            rlp.encode(cast(RLP, raw_data))


#
# Tests for RLP decode
#

#
# Testing bytes decoding
#


def test_rlp_decode_to_empty_bytes() -> None:
    assert rlp.decode_to_bytes(bytearray([0x80])) == b""


def test_rlp_decode_to_single_byte_less_than_128() -> None:
    assert rlp.decode_to_bytes(bytearray([0])) == bytearray([0])
    assert rlp.decode_to_bytes(bytearray([0x78])) == bytearray([0x78])


def test_rlp_decode_to_single_byte_gte_128() -> None:
    assert rlp.decode_to_bytes(bytearray([0x81, 0x83])) == b"\x83"
    assert rlp.decode_to_bytes(b"\x81\x80") == b"\x80"


def test_rlp_decode_to_55_bytes() -> None:
    encoding = bytearray([0xB7]) + bytearray(b"\x83" * 55)
    expected_raw_data = bytearray(b"\x83") * 55
    assert rlp.decode_to_bytes(encoding) == expected_raw_data


def test_rlp_decode_to_large_bytes() -> None:
    encoding = bytearray([0xBA]) + b"\x10\x00\x00" + b"\x83" * (2**20)
    expected_raw_data = b"\x83" * (2**20)
    assert rlp.decode_to_bytes(encoding) == expected_raw_data


#
# Testing uint decoding
#


def test_rlp_decode_to_zero_uint() -> None:
    assert rlp.decode(b"\x80") == Uint(0).to_be_bytes()


def test_rlp_decode_to_255_uint() -> None:
    assert rlp.decode(b"\x81\xff") == Uint(255).to_be_bytes()


#
# Testing string decoding
#


def test_rlp_decode_empty_str() -> None:
    assert rlp.decode(b"\x80") == "".encode()


def test_rlp_decode_one_char_str() -> None:
    assert rlp.decode(b"h") == "h".encode()


def test_rlp_decode_multi_char_str() -> None:
    assert rlp.decode(b"\x85hello") == "hello".encode()


#
# Testing sequence decoding
#


def test_rlp_decode_to_empty_sequence() -> None:
    assert rlp.decode_to_sequence(bytearray([0xC0])) == []


def test_rlp_decode_to_1_elem_sequence_of_byte() -> None:
    assert rlp.decode_to_sequence(bytearray([0xC6]) + b"\x85hello") == [
        b"hello"
    ]


def test_rlp_decode_to_1_elem_sequence_of_uint() -> None:
    assert rlp.decode_to_sequence(bytearray([0xC2]) + b"\x81\xff") == [
        Uint(255).to_be_bytes()
    ]


def test_rlp_decode_to_10_elem_sequence_of_bytes_and_uints() -> None:
    encoded_data = (
        bytearray([0xE3])
        + b"\x85hello\x85hello\x85hello\x85hello\x85hello#####"
    )
    expected_raw_data = [b"hello"] * 5 + [Uint(35).to_be_bytes()] * 5
    assert rlp.decode_to_sequence(encoded_data) == expected_raw_data


def test_rlp_decode_to_20_elem_sequence_of_bytes_and_uints() -> None:
    encoded_data = (
        bytearray([0xF8])
        + b"F"
        + b"\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello##########"
    )
    expected_raw_data = [b"hello"] * 10 + [Uint(35).to_be_bytes()] * 10
    assert rlp.decode_to_sequence(encoded_data) == expected_raw_data


def test_rlp_decode_to_nested_sequence() -> None:
    encoded_data = (
        b"\xdf\x85hello\x81\xff\xd6\x83how\xd1\x83are\x83you\xc8\x85doing\xc1#"
    )
    expected_raw_data = [
        b"hello",
        Uint(255).to_be_bytes(),
        [
            b"how",
            [b"are", b"you", [b"doing", [Uint(35).to_be_bytes()]]],
        ],
    ]
    assert rlp.decode_to_sequence(encoded_data) == expected_raw_data


def test_rlp_decode_successfully() -> None:
    test_cases = [
        (bytearray([0x80]), bytearray()),
        (bytearray([0xB7]) + bytearray(b"\x83" * 55), bytearray(b"\x83") * 55),
        (bytearray([0xC0]), []),
        (
            b"\xdb\x85hello\xd4\x83how\xcf\x83are\x83you\xc6\x85doing",
            [b"hello", [b"how", [b"are", b"you", [b"doing"]]]],
        ),
    ]
    for encoding, expected_raw_data in test_cases:
        assert rlp.decode(encoding) == expected_raw_data


def test_rlp_decode_failure_empty_bytes() -> None:
    with pytest.raises(RLPDecodingError):
        rlp.decode(b"")


def test_roundtrip_encoding_and_decoding() -> None:
    test_cases = [
        b"",
        b"h",
        b"hello how are you doing today?",
        Uint(35).to_be_bytes(),
        Uint(255).to_be_bytes(),
        [],
        [
            b"hello",
            [b"how", [b"are", b"you", [b"doing", [Uint(255).to_be_bytes()]]]],
        ],
        [[b"hello", b"world"], [b"how", b"are"], [b"you", b"doing"]],
    ]
    for raw_data in test_cases:
        assert rlp.decode(rlp.encode(cast(RLP, raw_data))) == raw_data


#
# Running ethereum/tests for rlp
#


def convert_to_rlp_native(
    obj: Union[str, int, Sequence[Union[str, int]]]
) -> RLP:
    if isinstance(obj, str):
        return bytes(obj, "utf-8")
    elif isinstance(obj, int):
        return Uint(obj)

    # It's a sequence
    return [convert_to_rlp_native(element) for element in obj]


def ethtest_fixtures_as_pytest_fixtures(
    *test_files: str,
) -> List[Tuple[RLP, Bytes]]:
    base_path = f"{ETHEREUM_TESTS_PATH}/RLPTests/"

    test_data = dict()
    for test_file in test_files:
        with open(os.path.join(base_path, test_file), "r") as fp:
            test_data.update(json.load(fp))

    pytest_fixtures = []
    for test_details in test_data.values():
        if isinstance(test_details["in"], str) and test_details[
            "in"
        ].startswith("#"):
            test_details["in"] = int(test_details["in"][1:])

        pytest_fixtures.append(
            (
                convert_to_rlp_native(test_details["in"]),
                hex_to_bytes(test_details["out"]),
            )
        )

    return pytest_fixtures


@pytest.mark.parametrize(
    "raw_data, expected_encoded_data",
    ethtest_fixtures_as_pytest_fixtures("rlptest.json"),
)
def test_ethtest_fixtures_for_rlp_encoding(
    raw_data: RLP, expected_encoded_data: Bytes
) -> None:
    assert rlp.encode(raw_data) == expected_encoded_data


@pytest.mark.parametrize(
    "raw_data, encoded_data",
    ethtest_fixtures_as_pytest_fixtures("RandomRLPTests/example.json"),
)
def test_ethtest_fixtures_for_successfully_rlp_decoding(
    raw_data: Bytes, encoded_data: Bytes
) -> None:
    decoded_data = rlp.decode(encoded_data)
    assert rlp.encode(decoded_data) == encoded_data


@pytest.mark.parametrize(
    "raw_data, encoded_data",
    ethtest_fixtures_as_pytest_fixtures("invalidRLPTest.json"),
)
def test_ethtest_fixtures_for_fails_in_rlp_decoding(
    raw_data: Bytes, encoded_data: Bytes
) -> None:
    with pytest.raises(RLPDecodingError):
        rlp.decode(encoded_data)
