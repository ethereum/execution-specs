"""Test the empty system contracts that a block adds to the BAL."""

from unittest.mock import Mock

import pytest

from execution_testing.base_types import Address, Bloom, Bytes, Hash
from execution_testing.client_clis import BlockExceptionWithMessage
from execution_testing.client_clis.cli_types import (
    EnginePayloadMetadata,
    LazyAllocJson,
    Result,
    TransitionToolOutput,
)
from execution_testing.exceptions import BlockException
from execution_testing.forks import Amsterdam, Requests, SystemCallPhase
from execution_testing.test_types import (
    Account,
    Alloc,
    Environment,
    Withdrawal,
)
from execution_testing.test_types.block_access_list import (
    BlockAccessList,
    BlockAccessListExpectation,
)

from ..blockchain import (
    Block,
    BlockchainTest,
    BuiltBlock,
    Header,
    empty_system_contracts,
)

AFTER_TRANSACTIONS = [
    address
    for address, phase in Amsterdam.system_contract_call_phases().items()
    if phase == SystemCallPhase.AFTER_TRANSACTIONS
]


def deployed_system_contracts() -> Alloc:
    """Return an allocation in which every system contract has code."""
    return Alloc(
        {
            address: Account(code=b"\x00")
            for address in Amsterdam.system_contract_call_phases()
        }
    )


def test_deployed_contracts_are_not_listed() -> None:
    """Test that no contract is returned when all of them have code."""
    assert empty_system_contracts(Amsterdam, deployed_system_contracts()) == []


def test_missing_and_codeless_contracts_are_listed() -> None:
    """
    Test that a contract absent from the allocation, and one that holds
    only a balance, are both returned.
    """
    missing, codeless = AFTER_TRANSACTIONS[:2]
    alloc = deployed_system_contracts()
    del alloc[missing]
    alloc[codeless] = Account(balance=1)

    assert sorted(empty_system_contracts(Amsterdam, alloc)) == sorted(
        [missing, codeless]
    )


def test_contracts_called_before_transactions_are_not_listed() -> None:
    """
    Test that a contract the block calls before its transactions is not
    returned, because that call does not reject a block for empty code.
    """
    before_transactions = [
        address
        for address, phase in Amsterdam.system_contract_call_phases().items()
        if phase == SystemCallPhase.BEFORE_TRANSACTIONS
    ]
    assert before_transactions
    alloc = deployed_system_contracts()
    for address in before_transactions:
        del alloc[address]

    assert empty_system_contracts(Amsterdam, alloc) == []


def generate_block(
    block: Block,
    bal: BlockAccessList,
    *,
    lazy: bool = False,
    client_built: bool = False,
) -> BuiltBlock:
    """Generate a block from a backend that omits an empty system contract."""
    alloc = deployed_system_contracts()
    del alloc[AFTER_TRANSACTIONS[0]]
    lazy_alloc = LazyAllocJson(
        raw=alloc.model_dump(mode="json"), _state_root=Hash(0)
    )
    result = Result(
        state_root=Hash(0),
        transactions_trie=Hash(0),
        receipts_root=Hash(0),
        logs_hash=Hash(0),
        logs_bloom=Bloom(0),
        receipts=[],
        gas_used=0,
        withdrawals_root=Withdrawal.list_root([]),
        requests=[],
        requests_hash=Hash(Requests(requests_lists=[])),
        block_access_list=bal.rlp,
        block_access_list_hash=Hash(bal.rlp.keccak256()),
    )
    result.block_exception = BlockExceptionWithMessage(
        exceptions=[BlockException.SYSTEM_CONTRACT_EMPTY],
        message="Empty system contract",
    )
    backend = Mock()
    backend.attests_block_access_list_hash = True
    backend.exception_mapper.reliable = True
    backend.evaluate.return_value = TransitionToolOutput(
        alloc=lazy_alloc,
        result=result,
        engine_payload=Mock(spec=EnginePayloadMetadata)
        if client_built
        else None,
    )
    test = BlockchainTest(
        fork=Amsterdam, pre=alloc, post=Alloc(), blocks=[block]
    )
    return test.generate_block_data(
        t8n=backend,
        block=block,
        previous_env=Environment(parent_timestamp=0),
        previous_alloc=lazy_alloc if lazy else alloc,
    )


@pytest.mark.parametrize("lazy", [False, True])
@pytest.mark.parametrize("already_present", [False, True])
def test_generated_bal_and_header(lazy: bool, already_present: bool) -> None:
    """List the empty contract once and commit to the augmented BAL."""
    address = AFTER_TRANSACTIONS[0]
    bal = BlockAccessList().with_accounts([Address(0x1234)])
    if already_present:
        bal = bal.with_accounts([address])
    built = generate_block(
        Block(exception=BlockException.SYSTEM_CONTRACT_EMPTY), bal, lazy=lazy
    )
    expected = bal.with_accounts([address])
    assert built.block_access_list == expected
    assert built.header.block_access_list_hash == Hash(
        expected.rlp.keccak256()
    )


@pytest.mark.parametrize(
    "block",
    [
        Block(
            exception=BlockException.SYSTEM_CONTRACT_EMPTY,
            rlp_modifier=Header(block_access_list_hash=Hash(0x1234)),
        ),
        Block(
            exception=BlockException.SYSTEM_CONTRACT_EMPTY,
            engine_new_payload_block_access_list=Bytes("0xc0"),
        ),
    ],
    ids=["header-hash", "payload-bytes"],
)
def test_explicit_bal_is_preserved(block: Block) -> None:
    """Keep the test author's BAL overrides intact."""
    bal = BlockAccessList()
    built = generate_block(block, bal)
    assert built.block_access_list == bal
    expected_hash = (
        block.rlp_modifier.block_access_list_hash
        if block.rlp_modifier is not None
        else Hash(bal.rlp.keccak256())
    )
    assert built.header.block_access_list_hash == expected_hash
    assert (
        built.engine_new_payload_block_access_list
        == block.engine_new_payload_block_access_list
    )


@pytest.mark.parametrize("over_limit", [False, True])
def test_augmented_bal_size_limit(over_limit: bool) -> None:
    """Accept the final BAL at the cap and reject one item above it."""
    gas_limit = Amsterdam.minimum_block_gas_limit()
    max_items = gas_limit // Amsterdam.gas_costs().BLOCK_ACCESS_LIST_ITEM
    bal = BlockAccessList().with_accounts(
        [Address(i + 1) for i in range(max_items - 1 + over_limit)]
    )
    block = Block(
        gas_limit=gas_limit, exception=BlockException.SYSTEM_CONTRACT_EMPTY
    )
    if over_limit:
        with pytest.raises(Exception, match="over the EIP-7928 cap"):
            generate_block(block, bal)
    else:
        built = generate_block(block, bal)
        assert built.block_access_list is not None
        assert built.block_access_list.item_count() == max_items


def test_client_built_bal_is_preserved() -> None:
    """Keep the BAL and commitment supplied by the client."""
    bal = BlockAccessList()
    built = generate_block(
        Block(exception=BlockException.SYSTEM_CONTRACT_EMPTY),
        bal,
        client_built=True,
    )
    assert built.block_access_list == bal
    assert built.header.block_access_list_hash == Hash(bal.rlp.keccak256())


def test_bal_modifier_is_preserved() -> None:
    """Do not augment a BAL deliberately changed by the test."""
    bal = BlockAccessList()
    modified = bal.with_accounts([Address(0x1234)])
    built = generate_block(
        Block(
            exception=BlockException.SYSTEM_CONTRACT_EMPTY,
            expected_block_access_list=BlockAccessListExpectation().modify(
                lambda _: modified
            ),
        ),
        bal,
    )
    assert built.block_access_list == modified
    assert built.header.block_access_list_hash == Hash(
        modified.rlp.keccak256()
    )
