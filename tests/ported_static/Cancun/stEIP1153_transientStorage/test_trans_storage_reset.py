"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/Cancun/stEIP1153_transientStorage
transStorageResetFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/Cancun/stEIP1153_transientStorage/transStorageResetFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f1f1fe",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f1f1fd",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f1f100",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 48879, 1: 1}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 1}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f100fe",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f100fd",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f10000",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743, 1: 1}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 32343}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f1fe",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f1fd",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f100",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 48879, 1: 1, 16: 1}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f2fe",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f2fd",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f200",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 48879, 1: 1, 16: 1}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f4fe",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f4fd",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f400",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 48879, 1: 1, 16: 1}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f200fe",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f200fd",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f20000",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 0xBAD0BEEF, 1: 1, 16: 32343}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f1fe",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f1fd",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f100",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 48879, 1: 1, 16: 1}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f2fe",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f2fd",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f200",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 48879, 1: 1, 16: 1}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f4fe",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f4fd",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f400",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 48879, 1: 1, 16: 1}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f400fe",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f400fd",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 24743}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
        (
            "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f40000",  # noqa: E501
            {
                Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"): Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    }
                ),
                Address("0x9f075370ef41d4cd90151e731e33836e6f521669"): Account(
                    storage={0: 0xBAD0BEEF, 1: 1, 16: 32343}
                ),
                Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"): Account(
                    storage={16: 24743}
                ),
            },
        ),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
        "case8",
        "case9",
        "case10",
        "case11",
        "case12",
        "case13",
        "case14",
        "case15",
        "case16",
        "case17",
        "case18",
        "case19",
        "case20",
        "case21",
        "case22",
        "case23",
        "case24",
        "case25",
        "case26",
        "case27",
        "case28",
        "case29",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_trans_storage_reset(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x48DC5A9F099CAAAA557742CA3A990A94BE45B9969126A1BC74E5E8BE5A2B5B47
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: Yul
    # {
    #   let reverter := calldataload(4)
    #   let dead     := calldataload(36)
    #   let param := calldataload(68)
    #   sstore(0, reverter)
    #   mstore(0, reverter)
    #   mstore(32, dead)
    #   mstore(64, param)
    #   sstore(1, call(gas(), reverter, 0, 0, 96, 0, 0))
    # }
    contract = pre.deploy_contract(
        code=(
            Op.PUSH0
            + Op.DUP1
            + Op.PUSH1[0x60]
            + Op.DUP2
            + Op.DUP1
            + Op.CALLDATALOAD(offset=0x4)
            + Op.CALLDATALOAD(offset=0x24)
            + Op.CALLDATALOAD(offset=0x44)
            + Op.SWAP1
            + Op.SSTORE(key=Op.DUP5, value=Op.DUP3)
            + Op.MSTORE(offset=Op.DUP5, value=Op.DUP3)
            + Op.PUSH1[0x20]
            + Op.MSTORE
            + Op.PUSH1[0x40]
            + Op.MSTORE
            + Op.GAS
            + Op.SSTORE(key=0x1, value=Op.CALL)
            + Op.STOP
        ),
        address=Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=Op.PUSH0)
            + Op.CALLDATALOAD(offset=0x20)
            + Op.SWAP1
            + Op.PUSH0
            + Op.MSTORE
            + Op.MSTORE(offset=0x20, value=Op.DUP1)
            + Op.BYTE(0x1D, Op.CALLDATALOAD(offset=0x40))
            + Op.SWAP1
            + Op.PUSH1[0x19]
            + Op.PUSH0
            + Op.JUMP(pc=0xA8)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x39, condition=Op.ISZERO)
            + Op.PUSH2[0x60A7]
            + Op.PUSH1[0x27]
            + Op.PUSH0
            + Op.JUMP(pc=0xA8)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x2D, condition=Op.EQ)
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x37]
            + Op.PUSH2[0xBEEF]
            + Op.PUSH0
            + Op.JUMP(pc=0xAC)
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x43]
            + Op.PUSH2[0x60A7]
            + Op.PUSH0
            + Op.JUMP(pc=0xAC)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x40))
            + Op.PUSH0
            + Op.SWAP2
            + Op.DIV(Op.GAS, 0x2)
            + Op.SWAP1
            + Op.JUMPI(pc=0x96, condition=Op.EQ(0xF1, Op.DUP1))
            + Op.JUMPI(pc=0x84, condition=Op.EQ(0xF2, Op.DUP1))
            + Op.PUSH1[0xF4]
            + Op.JUMPI(pc=0x74, condition=Op.EQ)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x1, value=Op.DUP3)
            + Op.PUSH1[0x70]
            + Op.PUSH0
            + Op.JUMP(pc=0xA8)
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.SSTORE
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.DUP1
            + Op.SWAP4
            + Op.POP
            + Op.DUP1
            + Op.SWAP3
            + Op.PUSH1[0x60]
            + Op.SWAP3
            + Op.DELEGATECALL
            + Op.PUSH0
            + Op.DUP1
            + Op.JUMP(pc=0x65)
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH0
            + Op.DUP1
            + Op.DUP1
            + Op.SWAP5
            + Op.POP
            + Op.DUP1
            + Op.SWAP4
            + Op.PUSH1[0x60]
            + Op.SWAP4
            + Op.CALLCODE
            + Op.PUSH0
            + Op.DUP1
            + Op.JUMP(pc=0x65)
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH0
            + Op.DUP1
            + Op.DUP1
            + Op.SWAP5
            + Op.POP
            + Op.DUP1
            + Op.SWAP4
            + Op.PUSH1[0x60]
            + Op.SWAP4
            + Op.CALL
            + Op.PUSH0
            + Op.DUP1
            + Op.JUMP(pc=0x65)
            + Op.JUMPDEST
            + Op.TLOAD
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.TSTORE
            + Op.JUMP
        ),
        storage={0x1: 0x60A7},
        address=Address("0x9f075370ef41d4cd90151e731e33836e6f521669"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=Op.PUSH0)
            + Op.CALLDATALOAD(offset=0x20)
            + Op.MSTORE(offset=Op.PUSH0, value=Op.DUP2)
            + Op.PUSH1[0x20]
            + Op.MSTORE
            + Op.BYTE(0x1E, Op.CALLDATALOAD(offset=0x40))
            + Op.BYTE(0x1F, Op.CALLDATALOAD(offset=0x40))
            + Op.SWAP2
            + Op.PUSH2[0x7E57]
            + Op.SWAP2
            + Op.SWAP1
            + Op.JUMPI(pc=0x91, condition=Op.EQ(0xF1, Op.DUP2))
            + Op.JUMPI(pc=0x80, condition=Op.EQ(0xF2, Op.DUP2))
            + Op.JUMPI(pc=0x70, condition=Op.EQ(0xF4, Op.DUP2))
            + Op.POP
            + Op.JUMPI(pc=0x60, condition=Op.ISZERO)
            + Op.JUMPDEST
            + Op.PUSH1[0x10]
            + Op.SSTORE
            + Op.JUMPI(pc=0x5E, condition=Op.ISZERO(Op.DUP1))
            + Op.JUMPI(pc=0x5A, condition=Op.EQ(0xFD, Op.DUP1))
            + Op.JUMPI(pc=0x58, condition=Op.EQ(0xFE, Op.DUP1))
            + Op.PUSH1[0xFF]
            + Op.JUMPI(pc=0x55, condition=Op.EQ)
            + Op.STOP
            + Op.JUMPDEST
            + Op.SELFDESTRUCT(address=Op.PUSH0)
            + Op.JUMPDEST
            + Op.INVALID
            + Op.JUMPDEST
            + Op.REVERT(offset=Op.DUP1, size=Op.PUSH0)
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x6C]
            + Op.PUSH4[0xBAD0BEEF]
            + Op.PUSH0
            + Op.JUMP(pc=0xA2)
            + Op.JUMPDEST
            + Op.JUMP(pc=0x37)
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.DUP1
            + Op.SWAP4
            + Op.POP
            + Op.DUP1
            + Op.SWAP3
            + Op.POP
            + Op.PUSH1[0x40]
            + Op.SWAP2
            + Op.GAS
            + Op.DELEGATECALL
            + Op.JUMP(pc=0x37)
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.DUP1
            + Op.DUP1
            + Op.SWAP5
            + Op.POP
            + Op.DUP1
            + Op.SWAP4
            + Op.POP
            + Op.PUSH1[0x40]
            + Op.SWAP3
            + Op.GAS
            + Op.CALLCODE
            + Op.JUMP(pc=0x37)
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.DUP1
            + Op.DUP1
            + Op.SWAP5
            + Op.POP
            + Op.DUP1
            + Op.SWAP4
            + Op.POP
            + Op.PUSH1[0x40]
            + Op.SWAP3
            + Op.GAS
            + Op.CALL
            + Op.JUMP(pc=0x37)
            + Op.JUMPDEST
            + Op.TSTORE
            + Op.JUMP
        ),
        storage={0x10: 0x60A7},
        address=Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        nonce=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
