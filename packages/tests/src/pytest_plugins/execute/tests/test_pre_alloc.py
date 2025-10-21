"""Test the pre-allocation models used during test execution."""

from typing import Any

import pytest

from ethereum_test_base_types import Address

from ..pre_alloc import AddressStubs


@pytest.mark.parametrize(
    "input_value,expected",
    [
        pytest.param(
            "{}",
            AddressStubs({}),
            id="empty_address_stubs_string",
        ),
        pytest.param(
            '{"some_address": "0x0000000000000000000000000000000000000001"}',
            AddressStubs(
                {
                    "some_address": Address(
                        "0x0000000000000000000000000000000000000001"
                    )
                }
            ),
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
            "empty.yaml",
            "",
            AddressStubs({}),
            id="empty_address_stubs_yaml",
        ),
        pytest.param(
            "one_address.json",
            '{"DEPOSIT_CONTRACT_ADDRESS": "0x00000000219ab540356cbb839cbe05303d7705fa"}',
            AddressStubs(
                {
                    "DEPOSIT_CONTRACT_ADDRESS": Address(
                        "0x00000000219ab540356cbb839cbe05303d7705fa"
                    ),
                }
            ),
            id="single_address_json",
        ),
        pytest.param(
            "one_address.yaml",
            "DEPOSIT_CONTRACT_ADDRESS: 0x00000000219ab540356cbb839cbe05303d7705fa",
            AddressStubs(
                {
                    "DEPOSIT_CONTRACT_ADDRESS": Address(
                        "0x00000000219ab540356cbb839cbe05303d7705fa"
                    ),
                }
            ),
            id="single_address_yaml",
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
