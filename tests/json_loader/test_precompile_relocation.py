"""Test relocating a precompile through the block environment."""

import importlib
from dataclasses import MISSING, fields, replace
from typing import Callable, Dict, Mapping, Optional

import pytest
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint
from execution_testing import Op

from ethereum.crypto.hash import Hash32
from ethereum.forks.amsterdam import vm as amsterdam_vm
from ethereum.forks.amsterdam.block_access_lists import (
    BlockAccessListBuilder,
)
from ethereum.forks.amsterdam.fork_types import ExecutionGas, StateGas
from ethereum.forks.amsterdam.state_tracker import (
    BlockState as AmsterdamBlockState,
)
from ethereum.forks.amsterdam.state_tracker import (
    TransactionState as AmsterdamTransactionState,
)
from ethereum.forks.amsterdam.vm.interpreter import (
    process_top_level as amsterdam_process_top_level,
)
from ethereum.forks.amsterdam.vm.precompiled_contracts import (
    IDENTITY_ADDRESS,
)
from ethereum.forks.amsterdam.vm.precompiled_contracts.mapping import (
    PRE_COMPILED_CONTRACTS as AMSTERDAM_PRE_COMPILED_CONTRACTS,
)
from ethereum.forks.frontier import vm as frontier_vm
from ethereum.forks.frontier.state_tracker import (
    BlockState as FrontierBlockState,
)
from ethereum.forks.frontier.state_tracker import (
    TransactionState as FrontierTransactionState,
)
from ethereum.forks.frontier.vm.interpreter import (
    process_message_call as frontier_process_message_call,
)
from ethereum.forks.frontier.vm.precompiled_contracts.mapping import (
    PRE_COMPILED_CONTRACTS as FRONTIER_PRE_COMPILED_CONTRACTS,
)
from ethereum.forks.osaka import vm as osaka_vm
from ethereum.forks.osaka.state_tracker import (
    BlockState as OsakaBlockState,
)
from ethereum.forks.osaka.state_tracker import (
    TransactionState as OsakaTransactionState,
)
from ethereum.forks.osaka.transactions import (
    LegacyTransaction as OsakaTransaction,
)
from ethereum.forks.osaka.utils.message import (
    prepare_message as osaka_prepare_message,
)
from ethereum.forks.osaka.vm.interpreter import (
    process_message_call as osaka_process_message_call,
)
from ethereum.forks.osaka.vm.precompiled_contracts.mapping import (
    PRE_COMPILED_CONTRACTS as OSAKA_PRE_COMPILED_CONTRACTS,
)
from ethereum.state import EMPTY_CODE_HASH, Account, Address
from ethereum.state_mpt import State, set_account, store_code
from ethereum_spec_tools.forks import Hardfork

# Somewhere no precompile has ever answered, and no account here lives.
RELOCATED_ADDRESS = Address(bytes.fromhex("00" * 19 + "42"))
SENDER = Address(b"\xaa" * 20)
CALLER_CONTRACT = Address(b"\xcc" * 20)
COINBASE = Address(b"\x00" * 20)
GAS = Uint(1_000_000)
PAYLOAD = Bytes(b"the identity precompile echoes whatever it is handed")

Call = Callable[[Address, Optional[Mapping[Address, Callable]]], Bytes]


def forwarding_code(target: Address) -> Bytes:
    """
    Return code that calls `target` with its own input and returns the
    answer.

    This is the shape the capability exists for: a contract calling a
    precompile, rather than a transaction addressed straight at one.
    """
    return Bytes(
        bytes(
            Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + Op.POP(
                Op.CALL(
                    Op.GAS, int.from_bytes(target), 0, 0, Op.CALLDATASIZE, 0, 0
                )
            )
            + Op.RETURNDATACOPY(0, 0, Op.RETURNDATASIZE)
            + Op.RETURN(0, Op.RETURNDATASIZE)
        )
    )


def move_identity_to(
    address: Address,
    original: Mapping[Address, Callable],
) -> Dict[Address, Callable]:
    """
    Return `original` with the identity precompile moved to `address`.

    Identity answers at its new address and nowhere else, which is what
    makes the relocation observable from both ends.
    """
    relocated = dict(original)
    relocated[address] = relocated.pop(IDENTITY_ADDRESS)
    return relocated


def funded_pre_state(forwards_to: Optional[Address] = None) -> State:
    """
    Return a pre-state holding the sender and, when asked, a contract
    that forwards its input to `forwards_to`.
    """
    pre_state = State()
    set_account(
        pre_state,
        SENDER,
        Account(
            nonce=Uint(0), balance=U256(10**18), code_hash=EMPTY_CODE_HASH
        ),
    )
    if forwards_to is not None:
        code_hash = store_code(pre_state, forwarding_code(forwards_to))
        set_account(
            pre_state,
            CALLER_CONTRACT,
            Account(nonce=Uint(1), balance=U256(0), code_hash=code_hash),
        )
    return pre_state


def call_frontier(
    target: Address,
    precompiles: Optional[Mapping[Address, Callable]],
) -> Bytes:
    """
    Call `target` with `PAYLOAD` at Frontier and report what came back.

    Pass `None` for `precompiles` to run the call exactly as consensus
    execution runs it, taking the fork's own arrangement.
    """
    block_state = FrontierBlockState(pre_state=funded_pre_state())
    block_env = frontier_vm.BlockEnvironment(
        chain_id=U64(1),
        state=block_state,
        block_gas_limit=Uint(30_000_000),
        block_hashes=[],
        coinbase=COINBASE,
        number=Uint(1),
        time=U256(0),
        difficulty=Uint(0),
    )
    if precompiles is not None:
        block_env = replace(block_env, precompiles=precompiles)
    tx_env = frontier_vm.TransactionEnvironment(
        origin=SENDER,
        gas_price=Uint(0),
        gas=GAS,
        state=FrontierTransactionState(parent=block_state),
        index_in_block=Uint(0),
        tx_hash=None,
    )
    message = frontier_vm.Message(
        block_env=block_env,
        tx_env=tx_env,
        caller=SENDER,
        target=target,
        current_target=target,
        gas=GAS,
        value=U256(0),
        data=PAYLOAD,
        code_address=target,
        code=Bytes(b""),
        depth=Uint(0),
        parent_evm=None,
    )
    output = frontier_process_message_call(message)
    assert output.error is None
    return output.return_data


def osaka_message(
    target: Address,
    precompiles: Optional[Mapping[Address, Callable]],
) -> osaka_vm.Message:
    """Prepare the top-level message a call to `target` runs as."""
    block_state = OsakaBlockState(pre_state=funded_pre_state())
    block_env = osaka_vm.BlockEnvironment(
        chain_id=U64(1),
        state=block_state,
        block_gas_limit=Uint(30_000_000),
        block_hashes=[],
        coinbase=COINBASE,
        number=Uint(1),
        base_fee_per_gas=Uint(0),
        time=U256(0),
        prev_randao=Bytes32(b"\x00" * 32),
        excess_blob_gas=U64(0),
        parent_beacon_block_root=Hash32(b"\x00" * 32),
    )
    if precompiles is not None:
        block_env = replace(block_env, precompiles=precompiles)
    tx_env = osaka_vm.TransactionEnvironment(
        origin=SENDER,
        gas_price=Uint(0),
        gas=GAS,
        access_list_addresses=set(),
        access_list_storage_keys=set(),
        state=OsakaTransactionState(parent=block_state),
        blob_versioned_hashes=(),
        authorizations=(),
        index_in_block=None,
        tx_hash=None,
    )
    tx = OsakaTransaction(
        nonce=U256(0),
        gas_price=Uint(0),
        gas=GAS,
        to=target,
        value=U256(0),
        data=PAYLOAD,
        v=U256(27),
        r=U256(1),
        s=U256(2),
    )
    return osaka_prepare_message(block_env, tx_env, tx)


def call_osaka(
    target: Address,
    precompiles: Optional[Mapping[Address, Callable]],
) -> Bytes:
    """
    Call `target` with `PAYLOAD` at Osaka and report what came back.

    Pass `None` for `precompiles` to run the call exactly as consensus
    execution runs it, taking the fork's own arrangement.
    """
    output = osaka_process_message_call(osaka_message(target, precompiles))
    assert output.error is None
    return output.return_data


def run_amsterdam(
    recipient: Address,
    precompiles: Optional[Mapping[Address, Callable]],
    pre_state: State,
) -> Bytes:
    """
    Send `PAYLOAD` to `recipient` at Amsterdam and report what came
    back.

    Pass `None` for `precompiles` to run the call exactly as consensus
    execution runs it, taking the fork's own arrangement.
    """
    block_state = AmsterdamBlockState(pre_state=pre_state)
    block_env = amsterdam_vm.BlockEnvironment(
        chain_id=U64(1),
        state=block_state,
        block_gas_limit=Uint(30_000_000),
        block_hashes=[],
        coinbase=COINBASE,
        number=Uint(1),
        base_fee_per_gas=Uint(0),
        time=U256(0),
        prev_randao=Bytes32(b"\x00" * 32),
        excess_blob_gas=U64(0),
        parent_beacon_block_root=Hash32(b"\x00" * 32),
        block_access_list_builder=BlockAccessListBuilder(),
        slot_number=U64(0),
    )
    if precompiles is not None:
        block_env = replace(block_env, precompiles=precompiles)
    tx_env = amsterdam_vm.TransactionEnvironment(
        origin=SENDER,
        recipient=recipient,
        is_create=False,
        data=PAYLOAD,
        value=U256(0),
        gas_limit=GAS,
        effective_gas_price=Uint(0),
        execution_gas_grant=ExecutionGas(GAS),
        state_gas_reservoir=StateGas(GAS),
        calldata_floor=Uint(0),
        access_list_addresses=set(),
        access_list_storage_keys=set(),
        accounts_with_paid_writes=set(),
        state=AmsterdamTransactionState(parent=block_state),
        blob_versioned_hashes=(),
        authorizations=(),
        index_in_block=None,
        tx_hash=None,
    )
    output = amsterdam_process_top_level(block_env, tx_env)
    assert output.error is None
    return output.return_data


def call_amsterdam(
    target: Address,
    precompiles: Optional[Mapping[Address, Callable]],
) -> Bytes:
    """Address the transaction straight at `target` at Amsterdam."""
    return run_amsterdam(target, precompiles, funded_pre_state())


def call_amsterdam_from_a_contract(
    target: Address,
    precompiles: Optional[Mapping[Address, Callable]],
) -> Bytes:
    """Reach `target` at Amsterdam through a contract that calls it."""
    return run_amsterdam(
        CALLER_CONTRACT, precompiles, funded_pre_state(forwards_to=target)
    )


# Three shapes of dispatch, one fork each: Frontier reaches the mapping
# through `evm.message.block_env` and warms nothing; Osaka does the same
# but warms the precompiles at the start of a transaction and can
# disable them for a delegation; Amsterdam has no `Message` at all and
# reaches the environment through `evm.block_env`. The last case runs
# the same fork one frame deeper, from a contract rather than from the
# transaction, since that is how a precompile is usually reached.
FORKS = [
    pytest.param(
        call_frontier, FRONTIER_PRE_COMPILED_CONTRACTS, id="frontier"
    ),
    pytest.param(call_osaka, OSAKA_PRE_COMPILED_CONTRACTS, id="osaka"),
    pytest.param(
        call_amsterdam, AMSTERDAM_PRE_COMPILED_CONTRACTS, id="amsterdam"
    ),
    pytest.param(
        call_amsterdam_from_a_contract,
        AMSTERDAM_PRE_COMPILED_CONTRACTS,
        id="amsterdam-nested",
    ),
]


@pytest.mark.parametrize("call, canonical", FORKS)
def test_precompile_answers_at_its_canonical_address(
    call: Call, canonical: Mapping[Address, Callable]
) -> None:
    """Left alone, the identity precompile answers where it always has."""
    assert call(IDENTITY_ADDRESS, None) == PAYLOAD
    assert call(RELOCATED_ADDRESS, None) == Bytes(b"")


@pytest.mark.parametrize("call, canonical", FORKS)
def test_supplied_mapping_moves_a_precompile(
    call: Call, canonical: Mapping[Address, Callable]
) -> None:
    """
    A mapping supplied to the environment relocates a precompile.

    The new address answers and the old one falls silent, behaving like
    the account with no code that it now is.
    """
    relocated = move_identity_to(RELOCATED_ADDRESS, canonical)

    assert call(RELOCATED_ADDRESS, relocated) == PAYLOAD
    assert call(IDENTITY_ADDRESS, relocated) == Bytes(b"")


@pytest.mark.parametrize("call, canonical", FORKS)
def test_supplied_mapping_does_not_leak(
    call: Call, canonical: Mapping[Address, Callable]
) -> None:
    """
    A relocation reaches no further than the execution that asked for it.

    An earlier attempt at this moved precompiles by editing the fork's
    own mapping, which left every later execution in the process looking
    at the moved arrangement. Run the relocated execution first, then
    one that supplies nothing, and the second must find the fork
    untouched.
    """
    relocated = move_identity_to(RELOCATED_ADDRESS, canonical)
    assert call(RELOCATED_ADDRESS, relocated) == PAYLOAD

    assert call(IDENTITY_ADDRESS, None) == PAYLOAD
    assert call(RELOCATED_ADDRESS, None) == Bytes(b"")


def test_warming_follows_the_relocation() -> None:
    """
    A relocated precompile is warm where it answers, not where it left.

    From Berlin on, a transaction starts with the precompile addresses
    warm. That set is drawn from the same arrangement dispatch reads, so
    the two cannot disagree about where a precompile is.
    """
    relocated = move_identity_to(
        RELOCATED_ADDRESS, OSAKA_PRE_COMPILED_CONTRACTS
    )
    warm = osaka_message(SENDER, relocated).accessed_addresses

    assert RELOCATED_ADDRESS in warm
    assert IDENTITY_ADDRESS not in warm

    canonical_warm = osaka_message(SENDER, None).accessed_addresses
    assert IDENTITY_ADDRESS in canonical_warm
    assert RELOCATED_ADDRESS not in canonical_warm


ALL_FORKS = [
    pytest.param(fork.short_name, id=fork.short_name)
    for fork in Hardfork.discover()
]


@pytest.mark.parametrize("short_name", ALL_FORKS)
def test_every_fork_carries_its_precompiles_on_the_environment(
    short_name: str,
) -> None:
    """
    Every fork hangs its precompiles off the block environment.

    Each fork is a complete copy of its predecessor, so this is checked
    by looking at all of them rather than by reading a few and trusting
    the rest. The set of precompiles differs from fork to fork; the way
    the environment reaches them does not.
    """
    fork = Hardfork.by_short_name(short_name)
    vm = importlib.import_module(f"{fork.name}.vm")
    mapping = importlib.import_module(
        f"{fork.name}.vm.precompiled_contracts.mapping"
    )
    interpreter = importlib.import_module(f"{fork.name}.vm.interpreter")

    # The default is a field default, so no construction site can
    # forget it, and it is the fork's own mapping rather than a copy.
    (precompiles,) = [
        field
        for field in fields(vm.BlockEnvironment)
        if field.name == "precompiles"
    ]
    assert precompiles.default_factory is not MISSING
    assert precompiles.default_factory() is mapping.PRE_COMPILED_CONTRACTS

    # And that mapping is read-only, so there is no global left to move
    # a precompile in and a relocation has nowhere to escape to.
    with pytest.raises(TypeError):
        mapping.PRE_COMPILED_CONTRACTS[RELOCATED_ADDRESS] = None

    # Nothing dispatches off the module global any more, so there is one
    # arrangement in play and the environment names it.
    assert not hasattr(interpreter, "PRE_COMPILED_CONTRACTS")
    try:
        message = importlib.import_module(f"{fork.name}.utils.message")
    except ModuleNotFoundError:
        return
    assert not hasattr(message, "PRE_COMPILED_CONTRACTS")
