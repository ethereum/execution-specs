"""Test relocating a precompile through the block environment."""

from typing import Callable, Dict, Mapping, Optional

import pytest
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint

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
from ethereum.state import EMPTY_CODE_HASH, Account, Address
from ethereum.state_mpt import State, set_account

# Somewhere no precompile has ever lived, and no test account occupies.
RELOCATED_ADDRESS = Address(bytes.fromhex("00" * 19 + "42"))
SENDER = Address(b"\xaa" * 20)
PAYLOAD = Bytes(b"the identity precompile echoes whatever it is handed")

Relocate = Callable[[Address, Optional[Mapping[Address, Callable]]], Bytes]


def move_identity_to(
    address: Address,
    original: Mapping[Address, Callable],
) -> Dict[Address, Callable]:
    """
    Return `original` with the identity precompile moved to `address`.

    The precompile answers at its new address and nowhere else, which is
    what makes the relocation observable from both ends.
    """
    relocated = dict(original)
    relocated[address] = relocated.pop(IDENTITY_ADDRESS)
    return relocated


def call_amsterdam(
    target: Address,
    precompiles: Optional[Mapping[Address, Callable]],
) -> Bytes:
    """
    Call `target` with `PAYLOAD` at Amsterdam and report what came back.

    Pass `None` for `precompiles` to run the block exactly as consensus
    execution runs it, taking the fork's own arrangement.
    """
    pre_state = State()
    set_account(
        pre_state,
        SENDER,
        Account(
            nonce=Uint(0), balance=U256(10**18), code_hash=EMPTY_CODE_HASH
        ),
    )
    block_state = AmsterdamBlockState(pre_state=pre_state)
    if precompiles is None:
        block_env = amsterdam_vm.BlockEnvironment(
            chain_id=U64(1),
            state=block_state,
            block_gas_limit=Uint(30_000_000),
            block_hashes=[],
            coinbase=Address(b"\x00" * 20),
            number=Uint(1),
            base_fee_per_gas=Uint(0),
            time=U256(0),
            prev_randao=Bytes32(b"\x00" * 32),
            excess_blob_gas=U64(0),
            parent_beacon_block_root=Hash32(b"\x00" * 32),
            block_access_list_builder=BlockAccessListBuilder(),
            slot_number=U64(0),
        )
    else:
        block_env = amsterdam_vm.BlockEnvironment(
            chain_id=U64(1),
            state=block_state,
            block_gas_limit=Uint(30_000_000),
            block_hashes=[],
            coinbase=Address(b"\x00" * 20),
            number=Uint(1),
            base_fee_per_gas=Uint(0),
            time=U256(0),
            prev_randao=Bytes32(b"\x00" * 32),
            excess_blob_gas=U64(0),
            parent_beacon_block_root=Hash32(b"\x00" * 32),
            block_access_list_builder=BlockAccessListBuilder(),
            slot_number=U64(0),
            precompiles=precompiles,
        )
    tx_env = amsterdam_vm.TransactionEnvironment(
        origin=SENDER,
        recipient=target,
        is_create=False,
        data=PAYLOAD,
        value=U256(0),
        gas_limit=Uint(1_000_000),
        effective_gas_price=Uint(0),
        execution_gas_grant=ExecutionGas(Uint(1_000_000)),
        state_gas_reservoir=StateGas(Uint(1_000_000)),
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


FORKS = [
    pytest.param(
        call_amsterdam,
        AMSTERDAM_PRE_COMPILED_CONTRACTS,
        id="amsterdam",
    ),
]


@pytest.mark.parametrize("call, canonical", FORKS)
def test_precompile_answers_at_its_canonical_address(
    call: Relocate, canonical: Mapping[Address, Callable]
) -> None:
    """Left alone, the identity precompile answers where it always has."""
    assert call(IDENTITY_ADDRESS, None) == PAYLOAD
    assert call(RELOCATED_ADDRESS, None) == Bytes(b"")


@pytest.mark.parametrize("call, canonical", FORKS)
def test_supplied_mapping_moves_a_precompile(
    call: Relocate, canonical: Mapping[Address, Callable]
) -> None:
    """
    A mapping supplied to the environment relocates a precompile.

    The new address answers and the old one falls silent: an account
    with no code, returning nothing.
    """
    relocated = move_identity_to(RELOCATED_ADDRESS, canonical)

    assert call(RELOCATED_ADDRESS, relocated) == PAYLOAD
    assert call(IDENTITY_ADDRESS, relocated) == Bytes(b"")


@pytest.mark.parametrize("call, canonical", FORKS)
def test_supplied_mapping_does_not_leak(
    call: Relocate, canonical: Mapping[Address, Callable]
) -> None:
    """
    A relocation reaches no further than the execution that asked for it.

    An earlier spike moved precompiles by editing the fork's own
    mapping, which left every later execution in the process looking at
    the moved arrangement. Run the relocated execution first, then one
    that supplies nothing, and the second must see the fork untouched.
    """
    relocated = move_identity_to(RELOCATED_ADDRESS, canonical)
    assert call(RELOCATED_ADDRESS, relocated) == PAYLOAD

    assert call(IDENTITY_ADDRESS, None) == PAYLOAD
    assert call(RELOCATED_ADDRESS, None) == Bytes(b"")


@pytest.mark.parametrize("call, canonical", FORKS)
def test_canonical_mapping_refuses_to_be_edited(
    call: Relocate, canonical: Mapping[Address, Callable]
) -> None:
    """
    The fork's own mapping cannot be rearranged in place.

    This is the structural half of the guarantee above: there is no
    global to move a precompile in, so a relocation has nowhere to
    escape to.
    """
    with pytest.raises(TypeError):
        canonical[RELOCATED_ADDRESS] = canonical[  # type: ignore[index]
            IDENTITY_ADDRESS
        ]
