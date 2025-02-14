"""Test cases for the ethereum_test_fixtures.base module."""

import pytest

from ..base import BaseFixture
from ..file import Fixtures
from ..state import FixtureEnvironment, FixtureTransaction, StateFixture
from ..transaction import FixtureResult, TransactionFixture


def test_json_dict():
    """Test that the json_dict property does not include the info field."""
    fixture = TransactionFixture(
        txbytes="0x1234",
        result={"fork": FixtureResult(intrinsic_gas=0)},
    )
    assert "_info" not in fixture.json_dict, "json_dict should exclude the 'info' field"


@pytest.mark.parametrize(
    "fixture",
    [
        pytest.param(
            StateFixture(
                env=FixtureEnvironment(),
                transaction=FixtureTransaction(
                    nonce=0,
                    gas_limit=[0],
                    value=[0],
                    data=[b""],
                ),
                pre={},
                post={},
                config={},
            ),
            id="StateFixture",
        ),
        pytest.param(
            TransactionFixture(
                transaction="0x1234",
                result={"fork": FixtureResult(intrinsic_gas=0)},
            ),
            id="TransactionFixture",
        ),
    ],
)
def test_base_fixtures_parsing(fixture: BaseFixture):
    """Test that the Fixtures generic model can validate any fixture format."""
    fixture.fill_info(
        "t8n-version",
        "test_case_description",
        fixture_source_url="fixture_source_url",
        ref_spec=None,
        _info_metadata={},
    )
    json_dump = fixture.json_dict_with_info()
    assert json_dump is not None
    Fixtures.model_validate({"fixture": json_dump})
