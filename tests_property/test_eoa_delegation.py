"""
Properties of EIP-7702 authorizations and delegation indicators.

The framework signs each authorization, so its authority is known apart
from the spec. The per-authorization check is then pinned on both sides of
each of EIP-7702's rules, from an authorization that passes them all.
"""

from dataclasses import dataclass, replace
from types import ModuleType
from typing import Callable, Dict, Optional, Set, Tuple

import pytest
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U64, U256, Uint
from execution_testing import AuthorizationTuple
from execution_testing.forks import Fork
from hypothesis import assume, given
from hypothesis import strategies as st

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import InvalidSignatureError
from ethereum.state import EMPTY_CODE_HASH, Account, Address
from ethereum.state_mpt import State
from ethereum_spec_tools.forks import Hardfork

from .forks import requires
from .spec_api import spec_authorization, validate_authorization, zeroed
from .strategies import (
    MAX_U64,
    MAX_U256,
    SIGNATURE_BREAKS,
    addresses,
    highest_s,
    ints,
    private_keys,
)

pytestmark = requires(lambda fork: fork.is_eip_enabled(7702))

# EIP-7702: a delegation indicator is `0xef0100 || address`.
DELEGATION_PREFIX = b"\xef\x01\x00"
# Any other code makes the authority a contract, which EIP-7702 refuses.
CONTRACT_CODE = b"\x60\x00"
# Each rule flips at its bound, so the first values past it and the top of
# the field are the offsets that matter.
OFFSETS = st.sampled_from([0, 1, 2, 2**64, MAX_U256])


@pytest.fixture(scope="session")
def delegation(spec: Hardfork) -> ModuleType:
    """Return the EIP-7702 module of the fork under test."""
    return spec.module("vm.eoa_delegation")


@pytest.mark.parametrize("break_name", sorted(SIGNATURE_BREAKS))
@given(
    chain_id=ints(MAX_U256),
    address=addresses(),
    nonce=ints(MAX_U64),
    key=private_keys,
    offset=OFFSETS,
)
def test_authority_signature_values_past_their_bounds_are_rejected(
    fork: Fork,
    spec: Hardfork,
    delegation: ModuleType,
    break_name: str,
    chain_id: int,
    address: Address,
    nonce: int,
    key: int,
    offset: int,
) -> None:
    """
    A signed authorization recovers the framework's signer, also with the
    largest `s` EIP-2 allows, and is rejected with one signature value at
    or past its bound.
    """
    framework = AuthorizationTuple(
        chain_id=chain_id, address=address, nonce=nonce, secret_key=key
    )
    auth = spec_authorization(spec.module("fork_types"), framework)
    assert delegation.recover_authority(auth) == framework.signer
    delegation.recover_authority(replace(auth, s=U256(highest_s(fork))))

    with pytest.raises(InvalidSignatureError):
        broken = SIGNATURE_BREAKS[break_name](auth, fork=fork, offset=offset)
        delegation.recover_authority(broken)


@given(
    address=addresses(),
    extra=st.binary(min_size=1, max_size=1),
    index=st.integers(0, len(DELEGATION_PREFIX) - 1),
    flip=st.integers(1, 255),
)
def test_only_a_delegation_indicator_names_an_address(
    delegation: ModuleType,
    address: Address,
    extra: bytes,
    index: int,
    flip: int,
) -> None:
    """
    The 23 bytes `0xef0100 || address` name `address`, and one byte fewer,
    one byte more or any other prefix name nothing.
    """
    indicator = DELEGATION_PREFIX + address
    other_prefix = bytearray(DELEGATION_PREFIX)
    other_prefix[index] ^= flip

    assert delegation.get_delegated_code_address(indicator) == address
    assert delegation.get_delegated_code_address(indicator[:-1]) is None
    assert delegation.get_delegated_code_address(indicator + extra) is None
    assert (
        delegation.get_delegated_code_address(bytes(other_prefix) + address)
        is None
    )


@dataclass(frozen=True)
class Authority:
    """The chain, an authorization's fields, and its authority's account."""

    chain_id: int
    authorization_chain_id: int
    authorization_nonce: int
    nonce: int
    code: bytes


@dataclass(frozen=True)
class Case:
    """One change from a valid authorization, and the check's verdict."""

    valid: bool
    warmed: bool
    """Whether the check adds the authority to the accessed addresses."""
    change: Callable[[Authority], Authority]


# EIP-7702 checks the chain id (step 1), the nonce cap (step 2) and the
# signature (step 3), then warms the authority (step 4) before it checks the
# authority's code (step 5) and nonce (step 6). Only those last two failures
# leave the authority warm.
CASES: Dict[str, Case] = {
    "chain_id_zero": Case(
        True, True, lambda a: replace(a, authorization_chain_id=0)
    ),
    "chain_id_one_above": Case(
        False,
        False,
        lambda a: replace(a, authorization_chain_id=a.chain_id + 1),
    ),
    "chain_id_one_below": Case(
        False,
        False,
        lambda a: replace(a, authorization_chain_id=a.chain_id - 1),
    ),
    "nonce_at_the_last_valid": Case(
        True,
        True,
        lambda a: replace(
            a, authorization_nonce=MAX_U64 - 1, nonce=MAX_U64 - 1
        ),
    ),
    "nonce_at_the_limit": Case(
        False,
        False,
        lambda a: replace(a, authorization_nonce=MAX_U64, nonce=MAX_U64),
    ),
    "authority_nonce_one_above": Case(
        False, True, lambda a: replace(a, nonce=a.nonce + 1)
    ),
    "authority_nonce_one_below": Case(
        False, True, lambda a: replace(a, nonce=a.nonce - 1)
    ),
    "authority_delegated": Case(
        True,
        True,
        lambda a: replace(a, code=DELEGATION_PREFIX + b"\x01" * 20),
    ),
    "authority_is_a_contract": Case(
        False, True, lambda a: replace(a, code=CONTRACT_CODE)
    ),
}


def check(
    spec: Hardfork, authority: Authority, address: Address, key: int
) -> Tuple[AuthorizationTuple, Optional[Address], Set[Address]]:
    """
    Sign an authorization for `authority` and run the spec's check of it,
    returning the framework's authorization, the authority the spec
    recovers, and the addresses the check warms.
    """
    vm = spec.module("vm")
    tracker = spec.module("state_tracker")
    framework = AuthorizationTuple(
        chain_id=authority.authorization_chain_id,
        address=address,
        nonce=authority.authorization_nonce,
        secret_key=key,
    )
    assert framework.signer is not None

    block_state = tracker.BlockState(pre_state=State())
    code_hash = keccak256(authority.code) if authority.code else None
    block_state.account_writes[Address(framework.signer)] = Account(
        nonce=Uint(authority.nonce),
        balance=U256(0),
        code_hash=code_hash or EMPTY_CODE_HASH,
    )
    if code_hash is not None:
        block_state.code_writes[code_hash] = Bytes(authority.code)
    block_env = zeroed(
        vm.BlockEnvironment,
        state=block_state,
        chain_id=U64(authority.chain_id),
    )
    tx_env = zeroed(
        vm.TransactionEnvironment,
        state=tracker.TransactionState(parent=block_state),
    )
    auth = spec_authorization(spec.module("fork_types"), framework)
    return framework, *validate_authorization(vm, block_env, tx_env, auth)


@pytest.mark.parametrize("case_name", sorted(CASES))
@given(
    # One below the chain's id must not be 0, which every chain accepts.
    chain_id=ints(MAX_U64).filter(lambda chain_id: chain_id > 1),
    address=addresses(),
    nonce=ints(MAX_U64 - 1),
    key=private_keys,
)
def test_authorization_rule_boundary(
    spec: Hardfork,
    case_name: str,
    chain_id: int,
    address: Address,
    nonce: int,
    key: int,
) -> None:
    """
    An authorization for the chain at its authority's nonce, from an
    account without code, is valid, and the case's change keeps it valid
    or makes the check return None, warming the authority when EIP-7702
    says it does.
    """
    case = CASES[case_name]
    valid = Authority(
        chain_id=chain_id,
        authorization_chain_id=chain_id,
        authorization_nonce=nonce,
        nonce=nonce,
        code=b"",
    )
    framework, authority, warmed = check(spec, valid, address, key)
    assert authority == framework.signer
    assert warmed == {framework.signer}

    changed = case.change(valid)
    assume(changed.nonce >= 0)
    framework, authority, warmed = check(spec, changed, address, key)
    assert authority == (framework.signer if case.valid else None)
    assert warmed == ({framework.signer} if case.warmed else set())


# EIP-7702: an authorization for the zero address clears the delegation.
CLEARING_ADDRESS = Address(b"\x00" * 20)
STARTING_CODE = {
    "none": b"",
    "delegated": DELEGATION_PREFIX + b"\x02" * 20,
    "contract": CONTRACT_CODE,
}


@dataclass
class ModelAuthority:
    """An authority's account as the model tracks it."""

    exists: bool
    nonce: int
    code: bytes
    delegated_before: bool
    delegation_set: bool = False
    write_paid: bool = False


@requires(lambda fork: fork.state_gas_reservoir_enabled())
@pytest.mark.parametrize("gas_side", ["exact", "one_short"])
@given(data=st.data())
def test_set_delegation_applies_and_charges(
    fork: Fork, spec: Hardfork, gas_side: str, data: st.DataObject
) -> None:
    """
    Each valid authorization sets or clears its authority's delegation and
    bumps its nonce, charging a new account (state gas) for an authority
    that did not exist, one account write (execution gas) per authority
    the transaction has not paid to write, and a delegation indicator
    (state gas) the first time the transaction sets one on an authority
    that had none before it, as EIP-2780's "EIP-7702 authorization
    processing" section sets them. The charges spend exactly the gas
    given, and one less runs out.
    """
    vm = spec.module("vm")
    tracker = spec.module("state_tracker")
    gas = spec.module("vm.gas")
    costs = fork.gas_costs()
    keys = data.draw(
        st.lists(private_keys, min_size=1, max_size=3, unique=True)
    )
    signers = [
        Address(
            AuthorizationTuple(
                chain_id=0, address=0, nonce=0, secret_key=k
            ).signer
        )
        for k in keys
    ]
    assume(len(set(signers)) == len(signers))

    block_state = tracker.BlockState(pre_state=State())
    model: Dict[Address, ModelAuthority] = {}
    for signer in signers:
        start = data.draw(st.sampled_from(["missing", *STARTING_CODE]))
        code = STARTING_CODE.get(start, b"")
        nonce = 0 if start == "missing" else data.draw(st.integers(0, 3))
        model[signer] = ModelAuthority(
            exists=start != "missing",
            nonce=nonce,
            code=code,
            delegated_before=start == "delegated",
            write_paid=data.draw(st.booleans()),
        )
        if start != "missing":
            block_state.account_writes[signer] = Account(
                nonce=Uint(nonce),
                # EIP-7523: an account that exists is never empty.
                balance=U256(1),
                code_hash=keccak256(code) if code else EMPTY_CODE_HASH,
            )
            if code:
                block_state.code_writes[keccak256(code)] = Bytes(code)
    paid = {signer for signer in signers if model[signer].write_paid}

    execution_gas = state_gas = 0
    authorizations = []
    for _ in range(data.draw(st.integers(1, 4))):
        index = data.draw(st.integers(0, len(keys) - 1))
        account = model[signers[index]]
        target = data.draw(st.one_of(st.just(CLEARING_ADDRESS), addresses()))
        nonce = account.nonce + data.draw(st.sampled_from([0, 0, 1]))
        authorizations.append(
            AuthorizationTuple(
                chain_id=0, address=target, nonce=nonce, secret_key=keys[index]
            )
        )
        refused = account.code and not account.code.startswith(
            DELEGATION_PREFIX
        )
        if refused or nonce != account.nonce:
            continue
        if not account.exists:
            state_gas += costs.NEW_ACCOUNT
        if not account.write_paid:
            execution_gas += costs.ACCOUNT_WRITE
        if target != CLEARING_ADDRESS:
            if not account.delegated_before and not account.delegation_set:
                state_gas += costs.AUTH_BASE
            account.delegation_set = True
            account.code = DELEGATION_PREFIX + target
        else:
            account.code = b""
        account.exists = account.write_paid = True
        account.nonce += 1

    reservoir = data.draw(ints(2 * state_gas))
    needed = execution_gas + max(0, state_gas - reservoir)
    assume(gas_side == "exact" or needed > 0)
    gas_left = needed if gas_side == "exact" else needed - 1
    meter = gas.GasMeter(
        gas_left=Uint(gas_left),
        state_gas_left=Uint(reservoir),
        state_gas_baseline=Uint(reservoir),
    )
    tx_state = tracker.TransactionState(parent=block_state)
    tx_env = zeroed(
        vm.TransactionEnvironment,
        state=tx_state,
        authorizations=tuple(
            spec_authorization(spec.module("fork_types"), a)
            for a in authorizations
        ),
        accounts_with_paid_writes=set(paid),
    )
    block_env = zeroed(vm.BlockEnvironment, state=block_state, chain_id=U64(1))

    if gas_side == "one_short":
        with pytest.raises(spec.module("vm.exceptions").OutOfGasError):
            vm.eoa_delegation.set_delegation(block_env, tx_env, meter)
        return

    warmed = vm.eoa_delegation.set_delegation(block_env, tx_env, meter)
    assert warmed == {Address(a.signer) for a in authorizations}
    assert int(meter.gas_left) == 0
    assert int(meter.state_gas_left) == max(0, reservoir - state_gas)
    for signer, account in model.items():
        assert tracker.account_exists(tx_state, signer) == account.exists
        if account.exists:
            actual = tracker.get_account(tx_state, signer)
            assert int(actual.nonce) == account.nonce
            assert tracker.get_code(tx_state, actual.code_hash) == account.code
    assert tx_env.accounts_with_paid_writes == {
        signer for signer, account in model.items() if account.write_paid
    }
