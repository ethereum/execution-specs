"""Test cases for the execution_testing.fixtures.base module."""

import pytest

from execution_testing.base_types import (
    Address,
    Bloom,
    Bytes,
    Hash,
    HeaderNonce,
)
from execution_testing.forks import Prague
from execution_testing.test_types import Transaction

from ..base import BaseFixture
from ..blockchain import (
    BlockchainEngineStatefulFixture,
    FixtureConfig,
    FixtureEngineNewPayload,
    FixtureHeader,
)
from ..file import Fixtures
from ..state import FixtureEnvironment, FixtureTransaction, StateFixture
from ..transaction import FixtureResult, TransactionFixture


def test_json_dict() -> None:
    """Test that the json_dict property does not include the info field."""
    fixture = TransactionFixture(
        transaction="0x1234",
        result={"Paris": FixtureResult(intrinsic_gas=0)},
    )
    assert "_info" not in fixture.json_dict, (
        "json_dict should exclude the 'info' field"
    )


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
                result={"Paris": FixtureResult(intrinsic_gas=0)},
            ),
            id="TransactionFixture",
        ),
        pytest.param(
            BlockchainEngineStatefulFixture(
                fork=Prague,
                last_block_hash=Hash(1),
                post_state_hash=Hash(2),
                config=FixtureConfig(fork=Prague),
                snapshot_block_number=0,
                snapshot_block_hash=Hash(0),
                setup_payloads=[
                    FixtureEngineNewPayload.from_fixture_header(
                        fork=Prague,
                        header=FixtureHeader(
                            parent_hash=Hash(0),
                            ommers_hash=Hash(1),
                            fee_recipient=Address(2),
                            state_root=Hash(3),
                            transactions_trie=Hash(4),
                            receipts_root=Hash(5),
                            logs_bloom=Bloom(6),
                            difficulty=7,
                            number=1,
                            gas_limit=9,
                            gas_used=10,
                            timestamp=11,
                            extra_data=Bytes([12]),
                            prev_randao=Hash(13),
                            nonce=HeaderNonce(14),
                            base_fee_per_gas=15,
                            withdrawals_root=Hash(16),
                            blob_gas_used=17,
                            excess_blob_gas=18,
                            parent_beacon_block_root=19,
                            requests_hash=20,
                        ),
                        transactions=[
                            Transaction(
                                max_fee_per_gas=7,
                            ).with_signature_and_sender(),
                        ],
                        withdrawals=[],
                        requests=[],
                    ),
                ],
                payloads=[
                    FixtureEngineNewPayload.from_fixture_header(
                        fork=Prague,
                        header=FixtureHeader(
                            parent_hash=Hash(10),
                            ommers_hash=Hash(1),
                            fee_recipient=Address(2),
                            state_root=Hash(3),
                            transactions_trie=Hash(4),
                            receipts_root=Hash(5),
                            logs_bloom=Bloom(6),
                            difficulty=7,
                            number=2,
                            gas_limit=9,
                            gas_used=10,
                            timestamp=12,
                            extra_data=Bytes([12]),
                            prev_randao=Hash(13),
                            nonce=HeaderNonce(14),
                            base_fee_per_gas=15,
                            withdrawals_root=Hash(16),
                            blob_gas_used=17,
                            excess_blob_gas=18,
                            parent_beacon_block_root=19,
                            requests_hash=20,
                        ),
                        transactions=[
                            Transaction(
                                max_fee_per_gas=7,
                            ).with_signature_and_sender(),
                        ],
                        withdrawals=[],
                        requests=[],
                    ),
                ],
            ),
            id="BlockchainEngineStatefulFixture",
        ),
    ],
)
def test_base_fixtures_parsing(fixture: BaseFixture) -> None:
    """Test that the Fixtures generic model can validate any fixture format."""
    fixture.fill_info(
        "t8n-version",
        "test_case_description",
        fixture_source_url="fixture_source_url",
        opcode_count=None,
        ref_spec=None,
        _info_metadata={},
    )
    json_dump = fixture.json_dict_with_info()
    assert json_dump is not None
    Fixtures.model_validate({"fixture": json_dump})
