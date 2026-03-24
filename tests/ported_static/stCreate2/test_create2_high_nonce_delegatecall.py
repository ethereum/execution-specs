"""
Delegate calls CREATE/CREATE2 from an account with max allowed nonce/max...

Ported from:
tests/static/state_tests/stCreate2/CREATE2_HighNonceDelegatecallFiller.yml
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
        "tests/static/state_tests/stCreate2/CREATE2_HighNonceDelegatecallFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x09f07a698496a643301174853c4f7f1eaab166be"): Account(
                    storage={1: 1}
                ),
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={
                        1: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        2: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    storage={1: 1}
                ),
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={
                        1: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        2: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x09f07a698496a643301174853c4f7f1eaab166be"): Account(
                    storage={1: 1}
                ),
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={
                        1: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        2: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    storage={1: 1}
                ),
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={
                        1: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        2: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x1cfc908bb573719841cad6a8bc34e7c1ce5ee020"): Account(
                    storage={1: 1}
                ),
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={
                        2: 0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={
                        1: 0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020,
                        65535: 0xFFFFFFFFFFFFFFFE,
                    }
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x99f1bfb202fdf527e07fb8eb682a03c713aeaf11"): Account(
                    storage={1: 1}
                ),
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={
                        2: 0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={
                        1: 0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11,
                        65535: 0xFFFFFFFFFFFFFFFE,
                    }
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x09f07a698496a643301174853c4f7f1eaab166be"): Account(
                    storage={1: 1}
                ),
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={
                        1: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        2: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    storage={1: 1}
                ),
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={
                        1: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        2: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x09f07a698496a643301174853c4f7f1eaab166be"): Account(
                    storage={1: 1}
                ),
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={
                        1: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        2: 0x9F07A698496A643301174853C4F7F1EAAB166BE,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fffffffffffffffe000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x74f5960e3479218ec095e853ed1fc95e285adc3b"): Account(
                    storage={1: 1}
                ),
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={
                        1: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        2: 0x74F5960E3479218EC095E853ED1FC95E285ADC3B,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x1cfc908bb573719841cad6a8bc34e7c1ce5ee020"): Account(
                    storage={1: 1}
                ),
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={
                        2: 0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={
                        1: 0x1CFC908BB573719841CAD6A8BC34E7C1CE5EE020,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x99f1bfb202fdf527e07fb8eb682a03c713aeaf11"): Account(
                    storage={1: 1}
                ),
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={
                        2: 0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={
                        1: 0x99F1BFB202FDF527E07FB8EB682A03C713AEAF11,
                        65535: 0xFFFFFFFFFFFFFFFF,
                    }
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000cf7dd310db9459fa2e6eec97d4b972ba24ff23eb0000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
            },
        ),
        (
            "917694f90000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000e51bc07f90c9661fa42db3bde8dd52b942ac69e00000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFE}
                ),
                Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
                ),
                Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"): Account(
                    storage={65535: 0xFFFFFFFFFFFFFFFF}
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2_high_nonce_delegatecall(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Delegate calls CREATE/CREATE2 from an account with max allowed..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    pre[sender] = Account(balance=0x3B9ACA00)
    pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.SLOAD(key=0xFFFF)
            + Op.MSTORE(offset=0x0, value=0x6005600C60003960056000F36001600155)
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.JUMPI(pc=0x5E, condition=Op.EQ(Op.DUP2, 0x0))
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.JUMPI(pc=0x4F, condition=Op.EQ)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x2, value=Op.DUP2)
            + Op.JUMPI(pc=0x43, condition=Op.GT(Op.DUP3, 0x0))
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.MSTORE
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.SSTORE(key=0xFFFF, value=Op.ADD)
            + Op.CODESIZE
            + Op.JUMP(pc=0x39)
            + Op.JUMPDEST
            + Op.SWAP1
            + Op.POP
            + Op.CREATE2(value=0x0, offset=0xF, size=0x11, salt=Op.DUP1)
            + Op.SWAP1
            + Op.JUMP(pc=0x2D)
            + Op.JUMPDEST
            + Op.SWAP2
            + Op.POP
            + Op.PUSH1[0x1]
            + Op.CREATE(value=0x0, offset=0xF, size=0x11)
            + Op.SWAP3
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x26)
        ),
        storage={0xFFFF: 0xFFFFFFFFFFFFFFFE},
        nonce=18446744073709551614,
        address=Address("0xcf7dd310db9459fa2e6eec97d4b972ba24ff23eb"),  # noqa: E501
    )
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x4)
            + Op.CALLDATALOAD(offset=0x24)
            + Op.SWAP1
            + Op.CALLDATALOAD(offset=0x44)
            + Op.SWAP1
            + Op.CALLDATALOAD(offset=0x64)
            + Op.SLOAD(key=0xFFFF)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8B, condition=Op.LT(Op.DUP2, Op.DUP5))
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.MSTORE
            + Op.PUSH1[0x2]
            + Op.SWAP1
            + Op.JUMPI(pc=0x79, condition=Op.ISZERO(Op.DUP1))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x66, condition=Op.EQ(Op.DUP2, 0x1))
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x52, condition=Op.EQ)
            + Op.JUMPDEST
            + Op.POP
            + Op.MLOAD(offset=0x0)
            + Op.SSTORE(key=0x1, value=Op.DUP1)
            + Op.JUMPI(pc=0x43, condition=Op.GT(Op.DUP2, 0x0))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.SWAP5
            + Op.SUB(Op.GAS, 0x3E8)
            + Op.CALL
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x20]
            + Op.DUP2
            + Op.DUP1
            + Op.DUP3
            + Op.SWAP5
            + Op.SUB(Op.GAS, 0x3E8)
            + Op.POP(Op.CALL)
            + Op.DUP1
            + Op.JUMP(pc=0x32)
            + Op.JUMPDEST
            + Op.POP(
                Op.CALLCODE(
                    gas=Op.SUB(Op.GAS, 0x3E8),
                    address=Op.DUP8,
                    value=Op.DUP1,
                    args_offset=Op.DUP2,
                    args_size=Op.DUP2,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.JUMP(pc=0x2D)
            + Op.JUMPDEST
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.SUB(Op.GAS, 0x3E8),
                    address=Op.DUP7,
                    args_offset=Op.DUP2,
                    args_size=Op.DUP2,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.JUMP(pc=0x25)
            + Op.JUMPDEST
            + Op.PUSH5[0x60016000F3]
            + Op.PUSH1[0x0]
            + Op.SWAP1
            + Op.DUP2
            + Op.MSTORE
            + Op.CREATE(value=Op.DUP3, offset=0x1B, size=0x5)
            + Op.JUMPI(pc=0xAA, condition=Op.GT)
            + Op.JUMPDEST
            + Op.POP
            + Op.SLOAD(key=0xFFFF)
            + Op.JUMP(pc=0x12)
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.SSTORE(key=0xFFFF, value=Op.ADD)
            + Op.CODESIZE
            + Op.JUMP(pc=0xA1)
        ),
        storage={0xFFFF: 0xFFFFFFFFFFFFFFFE},
        nonce=18446744073709551614,
        address=Address("0xd7d7b37fc131964cd181d47c9b705028776fe3d4"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.SLOAD(key=0xFFFF)
            + Op.MSTORE(offset=0x0, value=0x6005600C60003960056000F36001600155)
            + Op.PUSH1[0x0]
            + Op.SWAP2
            + Op.JUMPI(pc=0x5E, condition=Op.EQ(Op.DUP2, 0x0))
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.JUMPI(pc=0x4F, condition=Op.EQ)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x2, value=Op.DUP2)
            + Op.JUMPI(pc=0x43, condition=Op.GT(Op.DUP3, 0x0))
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.MSTORE
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x1]
            + Op.SSTORE(key=0xFFFF, value=Op.ADD)
            + Op.CODESIZE
            + Op.JUMP(pc=0x39)
            + Op.JUMPDEST
            + Op.SWAP1
            + Op.POP
            + Op.CREATE2(value=0x0, offset=0xF, size=0x11, salt=Op.DUP1)
            + Op.SWAP1
            + Op.JUMP(pc=0x2D)
            + Op.JUMPDEST
            + Op.SWAP2
            + Op.POP
            + Op.PUSH1[0x1]
            + Op.CREATE(value=0x0, offset=0xF, size=0x11)
            + Op.SWAP3
            + Op.SWAP1
            + Op.POP
            + Op.JUMP(pc=0x26)
        ),
        storage={0xFFFF: 0xFFFFFFFFFFFFFFFF},
        nonce=18446744073709551615,
        address=Address("0xe51bc07f90c9661fa42db3bde8dd52b942ac69e0"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
