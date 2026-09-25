"""
Test fork-aware construction of engine API payload attributes.

Every ``engine_payload_attribute_*`` fork predicate must be honored by
both ``PayloadAttributes`` producers: ``PayloadAttributes.for_fork``
(used by ``execute`` and ``fill-stateful`` to build blocks live) and
``FixtureEngineNewPayload.get_payload_attributes`` (used by ``consume``
to have a client build fixture blocks). A fork that adds a payload
attribute fails these tests until both producers populate it.
"""

from typing import List

import pytest

from execution_testing.base_types import Account, Address, Hash
from execution_testing.client_clis import TransitionTool
from execution_testing.fixtures import BlockchainEngineReorgFixture
from execution_testing.fixtures.blockchain import (
    FixtureEngineNewPayload,
    FixtureHeader,
)
from execution_testing.fixtures.reorg import (
    ForkchoiceUpdatedStep,
    NewPayloadStep,
)
from execution_testing.forks import (
    Amsterdam,
    Fork,
    get_deployed_forks,
    get_development_forks,
)
from execution_testing.rpc.rpc_types import PayloadAttributes
from execution_testing.specs import ReorgBlock, ReorgTest
from execution_testing.specs.blockchain import GENESIS_ENVIRONMENT_DEFAULTS
from execution_testing.test_types import (
    Alloc,
    BlockAccessList,
    Environment,
    Transaction,
)

ENGINE_PAYLOAD_ATTRIBUTE_PREFIX = "engine_payload_attribute_"

ALL_FORKS: List[Fork] = get_deployed_forks() + get_development_forks()
ENGINE_FORKS: List[Fork] = [
    fork
    for fork in ALL_FORKS
    if fork.engine_forkchoice_updated_version() is not None
]


def engine_payload_attribute_predicates(fork: Fork) -> List[str]:
    """Return the fork's engine payload attribute predicate names."""
    return [
        name
        for name in dir(fork)
        if name.startswith(ENGINE_PAYLOAD_ATTRIBUTE_PREFIX)
    ]


def assert_attributes_cover_fork(
    attributes: PayloadAttributes, fork: Fork
) -> None:
    """
    Assert every predicate-gated payload attribute is populated exactly
    when the fork requires it.
    """
    for predicate_name in engine_payload_attribute_predicates(fork):
        field = predicate_name.removeprefix(ENGINE_PAYLOAD_ATTRIBUTE_PREFIX)
        assert field in PayloadAttributes.model_fields, (
            f"{predicate_name} has no matching `{field}` field on "
            "PayloadAttributes"
        )
        required = getattr(fork, predicate_name)()
        populated = getattr(attributes, field) is not None
        assert populated == required, (
            f"`{field}` must be {'set' if required else 'unset'} for {fork}"
        )


def test_predicate_discovery() -> None:
    """The predicate discovery must find the known predicate family."""
    names = engine_payload_attribute_predicates(ALL_FORKS[0])
    assert f"{ENGINE_PAYLOAD_ATTRIBUTE_PREFIX}slot_number" in names


@pytest.mark.parametrize("fork", ALL_FORKS, ids=lambda fork: fork.name())
def test_for_fork_covers_every_engine_payload_attribute(fork: Fork) -> None:
    """``for_fork`` must populate every attribute the fork requires."""
    attributes = PayloadAttributes.for_fork(
        fork,
        timestamp=2,
        target_gas_limit=30_000_000,
        slot_number=7,
    )
    assert_attributes_cover_fork(attributes, fork)
    if fork.engine_payload_attribute_slot_number():
        assert attributes.slot_number == 7
    if fork.engine_payload_attribute_target_gas_limit():
        assert attributes.target_gas_limit == 30_000_000


@pytest.mark.parametrize("fork", ENGINE_FORKS, ids=lambda fork: fork.name())
def test_fixture_payload_covers_every_engine_payload_attribute(
    fork: Fork,
) -> None:
    """
    Attributes rebuilt from a fixture payload must populate every
    attribute the fork requires.
    """
    env = Environment(**GENESIS_ENVIRONMENT_DEFAULTS).set_fork_requirements(
        fork
    )
    header = FixtureHeader.genesis(fork, env, Hash(0))
    payload = FixtureEngineNewPayload.from_fixture_header(
        fork=fork,
        header=header,
        transactions=[],
        withdrawals=[] if fork.header_withdrawals_required() else None,
        requests=[] if fork.engine_new_payload_requests() else None,
        block_access_list=(
            BlockAccessList().rlp
            if fork.engine_execution_payload_block_access_list()
            else None
        ),
    )
    assert_attributes_cover_fork(payload.get_payload_attributes(), fork)


def test_reorg_fill_covers_every_amsterdam_payload_attribute(
    default_t8n: TransitionTool,
) -> None:
    """
    A reorg fixture's FCU-with-attributes request must populate every
    payload attribute Amsterdam requires, the same as the two producers
    above (PR3556-R0001).
    """
    sender = Address(0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    test = ReorgTest(
        fork=Amsterdam,
        genesis_environment=Environment(),
        pre=Alloc({sender: Account(balance=10**21, nonce=0)}),
        blocks=[
            ReorgBlock(
                label="a1",
                txs=[
                    Transaction(
                        nonce=0,
                        to=Address(0xC0DE),
                        value=1,
                        gas_limit=21_000,
                        gas_price=10,
                        secret_key=Hash(
                            0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
                        ),
                    )
                ],
            )
        ],
        steps=[
            NewPayloadStep(block="a1"),
            ForkchoiceUpdatedStep(
                head="a1",
                payload_attributes=PayloadAttributes(
                    timestamp=0,
                    prev_randao=Hash(0),
                    suggested_fee_recipient=Address(0),
                ),
            ),
        ],
    )
    fixture = test.generate(
        t8n=default_t8n, fixture_format=BlockchainEngineReorgFixture
    ).fixture
    assert isinstance(fixture, BlockchainEngineReorgFixture)
    fcu = fixture.steps[1]
    assert isinstance(fcu, ForkchoiceUpdatedStep)
    assert fcu.payload_attributes is not None
    assert_attributes_cover_fork(fcu.payload_attributes, Amsterdam)
