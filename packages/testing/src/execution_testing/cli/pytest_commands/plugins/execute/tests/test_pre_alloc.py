"""Test the pre-allocation models used during test execution."""

from typing import Any

import pytest

from execution_testing.base_types import Address, Hash

from ...shared.address_stubs import StubAddress, StubEOA
from ..pre_alloc import AddressStubs

ADDR_1 = Address("0x0000000000000000000000000000000000000001")
DEPOSIT_ADDR = Address("0x00000000219ab540356cbb839cbe05303d7705fa")
TEST_PKEY = Hash(
    0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
)
TEST_ADDR = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")


@pytest.mark.parametrize(
    "input_value,expected",
    [
        pytest.param(
            "{}",
            AddressStubs({}),
            id="empty_address_stubs_string",
        ),
        pytest.param(
            '{"some_address": {"addr": "0x0000000000000000000000000000000000000001"}}',  # noqa: E501
            AddressStubs({"some_address": StubAddress(addr=ADDR_1)}),
            id="address_stubs_string_with_some_address",
        ),
    ],
)
def test_address_stubs(input_value: Any, expected: AddressStubs) -> None:
    """Test the address stubs."""
    assert AddressStubs.model_validate_json_or_file(input_value) == expected


@pytest.mark.parametrize(
    "file_name,file_contents,expected",
    [
        pytest.param(
            "empty.json",
            "{}",
            AddressStubs({}),
            id="empty_address_stubs_json",
        ),
        pytest.param(
            "one_address.json",
            '{"DEPOSIT_CONTRACT_ADDRESS": {"addr": "0x00000000219ab540356cbb839cbe05303d7705fa"}}',  # noqa: E501
            AddressStubs(
                {
                    "DEPOSIT_CONTRACT_ADDRESS": StubAddress(
                        addr=DEPOSIT_ADDR,
                    ),
                }
            ),
            id="single_address_json",
        ),
    ],
)
def test_address_stubs_from_files(
    pytester: pytest.Pytester,
    file_name: str,
    file_contents: str,
    expected: AddressStubs,
) -> None:
    """Test the address stubs."""
    filename = pytester.path.joinpath(file_name)
    filename.write_text(file_contents)

    assert AddressStubs.model_validate_json_or_file(str(filename)) == expected


def test_address_stubs_file_not_found(pytester: pytest.Pytester) -> None:
    """Test that a missing JSON file raises FileNotFoundError."""
    missing_test = pytester.path.joinpath("nonexistent.json")
    with pytest.raises(FileNotFoundError):
        AddressStubs.model_validate_json_or_file(str(missing_test))


def test_address_stubs_getitem_returns_address() -> None:
    """Verify __getitem__ returns the Address, not the stub entry."""
    stubs = AddressStubs({"label": StubAddress(addr=ADDR_1)})
    assert stubs["label"] == ADDR_1
    assert isinstance(stubs["label"], Address)


def test_address_stubs_contains() -> None:
    """Verify __contains__ checks for label presence."""
    stubs = AddressStubs({"label": StubAddress(addr=ADDR_1)})
    assert "label" in stubs
    assert "other" not in stubs


def test_address_stubs_with_pkey() -> None:
    """Parse a JSON string with a private key entry."""
    json_str = (
        '{"eoa": {"addr": "' + str(TEST_ADDR) + '", '
        '"pkey": "' + str(TEST_PKEY) + '"}}'
    )
    stubs = AddressStubs.model_validate_json_or_file(json_str)
    assert stubs["eoa"] == TEST_ADDR
    assert stubs.is_eoa("eoa")
    entry = stubs.get_entry("eoa")
    assert isinstance(entry, StubEOA)
    assert entry.pkey == TEST_PKEY


def test_address_stubs_is_eoa() -> None:
    """Verify is_eoa distinguishes entries."""
    stubs = AddressStubs(
        {
            "contract": StubAddress(addr=ADDR_1),
            "eoa": StubEOA(addr=TEST_ADDR, pkey=TEST_PKEY),
        }
    )
    assert not stubs.is_eoa("contract")
    assert stubs.is_eoa("eoa")
    assert not stubs.is_eoa("nonexistent")
