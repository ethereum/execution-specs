import json
import os
from typing import List, Sequence, Tuple, Union

import pytest

from eth1spec import rlp
from eth1spec.eth_types import Bytes, Uint
from eth1spec.rlp import RLP

from .helpers import hex2bytes

#
# Tests for RLP decode
#


@pytest.mark.parametrize(
    "raw_data, expected_encoded_data",
    [
        # Empty raw data
        (b"", bytearray([128])),
        (bytearray(), bytearray([128])),
        # raw data of length 1 with byte val < 128
        (b"x", bytearray([120])),
        (bytearray(b"x"), bytearray([120])),
        # raw data of length 1 with byte val >= 128
        (b"\x83", bytearray([129, 131])),
        (bytearray(b"\x83"), bytearray([129, 131])),
        # raw data of length 55
        (b"\x83" * 55, bytearray([183]) + bytearray(b"\x83" * 55)),
        (bytearray(b"\x83") * 55, bytearray([183]) + bytearray(b"\x83" * 55)),
        # raw data of length 2**20 (I would have done 2**64 - 1, but that needs a
        # lot of RAM to just test).
        (
            b"\x83" * 2 ** 20,
            bytearray([186])
            + bytearray(b"\x10\x00\x00")
            + bytearray(b"\x83" * 2 ** 20),
        ),
        (
            bytearray(b"\x83") * 2 ** 20,
            bytearray([186])
            + bytearray(b"\x10\x00\x00")
            + bytearray(b"\x83" * 2 ** 20),
        ),
    ],
)
def test_rlp_encode_bytes(
    raw_data: Bytes, expected_encoded_data: Bytes
) -> None:
    assert rlp.encode_bytes(raw_data) == expected_encoded_data


@pytest.mark.parametrize(
    "raw_data, expected_encoded_data",
    [
        (Uint(0), b"\x80"),
        (Uint(255), b"\x81\xff"),
    ],
)
def test_rlp_encode_uint(raw_data: Uint, expected_encoded_data: Bytes) -> None:
    assert rlp.encode(raw_data) == expected_encoded_data


@pytest.mark.parametrize(
    "raw_data, expected_encoded_data",
    [
        ("", b"\x80"),
        ("h", b"h"),
        ("hello", b"\x85hello"),
    ],
)
def test_rlp_encode_str(raw_data: str, expected_encoded_data: Bytes) -> None:
    assert rlp.encode(raw_data) == expected_encoded_data


@pytest.mark.parametrize(
    ("raw_data", "expected_encoded_data"),
    [
        # Empty sequence
        ([], bytearray([192])),
        # Sequence of single element of each bytes and Uint
        ([b"hello"], bytearray([198]) + bytearray(b"\x85hello")),
        ([Uint(255)], bytearray([194]) + bytearray(b"\x81\xff")),
        # Sequence of 5 bytes and 5 ints
        (
            [b"hello"] * 5 + [Uint(35)] * 5,  # type: ignore
            bytearray([227])
            + bytearray(b"\x85hello\x85hello\x85hello\x85hello\x85hello#####"),
        ),
        # Sequence of 10 bytes and 10 ints
        (
            [b"hello"] * 10 + [Uint(35)] * 10,  # type: ignore
            bytearray([248])
            + bytearray(b"F")
            + bytearray(
                b"\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello##########"
            ),
        ),
        # Nested Sequence
        (
            [b"hello", Uint(255), [b"how", [b"are", b"you", [b"doing"]]]],
            bytearray(
                b"\xdd\x85hello\x81\xff\xd4\x83how\xcf\x83are\x83you\xc6\x85doing"
            ),
        ),
    ],
)
def test_rlp_encode_sequence(
    raw_data: Sequence[RLP], expected_encoded_data: Bytes
) -> None:
    assert rlp.encode_sequence(raw_data) == expected_encoded_data


@pytest.mark.parametrize(
    "raw_data, expected_encoded_data",
    [
        (b"", bytearray([128])),
        (b"\x83" * 55, bytearray([183]) + bytearray(b"\x83" * 55)),
        (Uint(0), b"\x80"),
        (Uint(255), b"\x81\xff"),
        ([], bytearray([192])),
        (
            [b"hello"] * 5 + [Uint(35)] * 5,  # type: ignore
            bytearray([227])
            + bytearray(b"\x85hello\x85hello\x85hello\x85hello\x85hello#####"),
        ),
        (
            [b"hello", Uint(255), [b"how", [b"are", b"you", [b"doing"]]]],
            bytearray(
                b"\xdd\x85hello\x81\xff\xd4\x83how\xcf\x83are\x83you\xc6\x85doing"
            ),
        ),
    ],
)
def test_rlp_encode_successfully(
    raw_data: RLP, expected_encoded_data: Bytes
) -> None:
    assert rlp.encode(raw_data) == expected_encoded_data


@pytest.mark.parametrize(
    "raw_data",
    [
        123,
        [b"hello", Uint(255), [b"how", [b"are", [b"you", [123]]]]],
    ],
)
def test_rlp_encode_fails(raw_data: RLP) -> None:
    with pytest.raises(TypeError):
        rlp.encode(raw_data)


#
# Tests for RLP decode
#


@pytest.mark.parametrize(
    "encoded_data, expected_raw_data",
    [
        # Empty raw data
        (bytearray([128]), bytearray()),
        # raw data of length 1 with byte val < 128
        (bytearray([120]), bytearray(b"x")),
        # raw data of length 1 with byte val >= 128
        (bytearray([129, 131]), bytearray(b"\x83")),
        # raw data of length 55
        (bytearray([183]) + bytearray(b"\x83" * 55), bytearray(b"\x83") * 55),
        # raw data of length 2**20 (I would have done 2**64 - 1, but that needs a
        # lot of RAM to just test).
        (
            bytearray([186])
            + bytearray(b"\x10\x00\x00")
            + bytearray(b"\x83" * (2 ** 20)),
            bytearray(b"\x83") * (2 ** 20),
        ),
    ],
)
def test_rlp_decode_bytes(
    encoded_data: Bytes, expected_raw_data: Bytes
) -> None:
    assert rlp.decode_to_bytes(encoded_data) == expected_raw_data


@pytest.mark.parametrize(
    "encoded_data, expected_raw_data",
    [
        (b"\x80", Uint(0).to_be_bytes()),
        (b"\x81\xff", Uint(255).to_be_bytes()),
    ],
)
def test_rlp_decode_uint(
    encoded_data: Bytes, expected_raw_data: Bytes
) -> None:
    assert rlp.decode(encoded_data) == expected_raw_data


@pytest.mark.parametrize(
    "encoded_data, expected_raw_data",
    [
        # Empty sequence
        (bytearray([192]), []),
        # Sequence of single element of each bytes and Uint
        (bytearray([198]) + bytearray(b"\x85hello"), [b"hello"]),
        (bytearray([194]) + bytearray(b"\x81\xff"), [Uint(255).to_be_bytes()]),
        (
            bytearray([210]) + bytearray(b"\x85hello\x85hello\x85hello"),
            [b"hello"] * 3,
        ),
        (
            bytearray([198]) + bytearray(b"\x81\xff\x81\xff\x81\xff"),
            [Uint(255).to_be_bytes()] * 3,
        ),
        # Sequence of 5 bytes and 5 ints
        (
            bytearray([227])
            + bytearray(b"\x85hello\x85hello\x85hello\x85hello\x85hello#####"),
            [b"hello"] * 5 + [Uint(35).to_be_bytes()] * 5,
        ),
        # Sequence of 10 bytes and 10 ints
        (
            bytearray([248])
            + bytearray(b"F")
            + bytearray(
                b"\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello\x85hello##########"
            ),
            [b"hello"] * 10 + [Uint(35).to_be_bytes()] * 10,
        ),
        # Nested Sequence
        (
            b"\xdf\x85hello\x81\xff\xd6\x83how\xd1\x83are\x83you\xc8\x85doing\xc1#",
            [
                b"hello",
                Uint(255).to_be_bytes(),
                [
                    b"how",
                    [b"are", b"you", [b"doing", [Uint(35).to_be_bytes()]]],
                ],
            ],
        ),
    ],
)
def test_rlp_decode_sequence(
    encoded_data: Bytes, expected_raw_data: Sequence[RLP]
) -> None:
    assert rlp.decode_to_sequence(encoded_data) == expected_raw_data


@pytest.mark.parametrize(
    "encoded_data, expected_raw_data",
    [
        (bytearray([128]), bytearray()),
        (bytearray([183]) + bytearray(b"\x83" * 55), bytearray(b"\x83") * 55),
        (bytearray([192]), []),
        (
            b"\xdb\x85hello\xd4\x83how\xcf\x83are\x83you\xc6\x85doing",
            [b"hello", [b"how", [b"are", b"you", [b"doing"]]]],
        ),
    ],
)
def test_rlp_decode_successfully(
    encoded_data: Bytes, expected_raw_data: RLP
) -> None:
    assert rlp.decode(encoded_data) == expected_raw_data


@pytest.mark.parametrize(
    "encoded_data",
    [
        b"",
    ],
)
def test_rlp_decode_failure(encoded_data: Bytes) -> None:
    with pytest.raises(Exception):
        rlp.decode(encoded_data)


@pytest.mark.parametrize(
    "raw_data",
    [
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
    ],
)
def test_roundtrip_encoding_and_decoding(raw_data: RLP) -> None:
    assert rlp.decode(rlp.encode(raw_data)) == raw_data


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
    base_path = "tests/fixtures/RLPTests/"

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
                hex2bytes(test_details["out"]),
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
def test_ethtest_fixtures_for_successfull_rlp_decoding(
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
    with pytest.raises(Exception):
        rlp.decode(encoded_data)
