"""Test the caller-asserted sender path through ``check_transaction``."""

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

import pytest
from ethereum_types.bytes import Bytes, Bytes32
from ethereum_types.numeric import U64, U256, Uint

from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import InvalidSenderError
from ethereum.forks.amsterdam import fork as amsterdam_fork
from ethereum.forks.amsterdam import vm as amsterdam_vm
from ethereum.forks.amsterdam.block_access_lists import (
    BlockAccessListBuilder,
)
from ethereum.forks.amsterdam.state_tracker import (
    BlockState as AmsterdamBlockState,
)
from ethereum.forks.amsterdam.transactions import (
    LegacyTransaction as AmsterdamTransaction,
)
from ethereum.forks.amsterdam.transactions import (
    recover_sender as amsterdam_recover_sender,
)
from ethereum.forks.cancun import fork as cancun_fork
from ethereum.forks.cancun import vm as cancun_vm
from ethereum.forks.cancun.state_tracker import (
    BlockState as CancunBlockState,
)
from ethereum.forks.cancun.state_tracker import (
    TransactionState as CancunTransactionState,
)
from ethereum.forks.cancun.transactions import (
    LegacyTransaction as CancunTransaction,
)
from ethereum.forks.cancun.transactions import (
    recover_sender as cancun_recover_sender,
)
from ethereum.forks.prague import fork as prague_fork
from ethereum.forks.prague import vm as prague_vm
from ethereum.forks.prague.state_tracker import (
    BlockState as PragueBlockState,
)
from ethereum.forks.prague.state_tracker import (
    TransactionState as PragueTransactionState,
)
from ethereum.forks.prague.transactions import (
    LegacyTransaction as PragueTransaction,
)
from ethereum.forks.prague.transactions import (
    recover_sender as prague_recover_sender,
)
from ethereum.state import EMPTY_CODE_HASH, Account, Address, BlockDiff, Root

# An arbitrary point on the curve. The signature is never checked against
# a known key: the tests only need it to recover to *some* address, which
# they then compare against the address the caller asserts.
SIGNATURE_R = U256(1)
SIGNATURE_S = U256(2)
SIGNATURE_V = U256(27)

ASSERTED_SENDER = Address(b"\xaa" * 20)
RECIPIENT = Address(b"\xbb" * 20)
GAS_PRICE = Uint(1)
GAS_LIMIT = Uint(100_000)
BALANCE = U256(10**18)

# Not a delegation designation, so the forks that consult
# ``is_valid_delegation`` reject it for the same reason the earlier ones
# do: the account has code.
SENDER_CODE = Bytes(b"\x60\x00")


@dataclass
class InMemoryPreState:
    """A ``PreState`` holding a handful of accounts, for one transaction."""

    accounts: Dict[Address, Account] = field(default_factory=dict)
    codes: Dict[Hash32, Bytes] = field(default_factory=dict)

    def get_account_optional(self, address: Address) -> Optional[Account]:
        """Return the account at `address`, or ``None``."""
        return self.accounts.get(address)

    def get_storage(
        self,
        address: Address,  # noqa: ARG002
        key: Bytes32,  # noqa: ARG002
    ) -> U256:
        """Return zero; these tests set no storage."""
        return U256(0)

    def get_code(self, code_hash: Hash32) -> Bytes:
        """Return the bytecode for `code_hash`, or empty."""
        return self.codes.get(code_hash, Bytes(b""))

    def account_has_storage(self, address: Address) -> bool:  # noqa: ARG002
        """Return ``False``; these tests set no storage."""
        return False

    def compute_state_root(self, block_diff: BlockDiff) -> Root:
        """Refuse; these tests never commit a block."""
        raise NotImplementedError


def fund(pre_state: InMemoryPreState, address: Address, code: Bytes) -> None:
    """Give `address` a spendable balance and, optionally, some code."""
    code_hash = keccak256(code) if code else EMPTY_CODE_HASH
    pre_state.accounts[address] = Account(
        nonce=Uint(0), balance=BALANCE, code_hash=code_hash
    )
    if code:
        pre_state.codes[code_hash] = code


def check_cancun(
    pre_state: InMemoryPreState, asserted_sender: Optional[Address]
) -> Address:
    """Admit a transaction at Cancun and report the sender used."""
    tx = CancunTransaction(
        nonce=U256(0),
        gas_price=GAS_PRICE,
        gas=GAS_LIMIT,
        to=RECIPIENT,
        value=U256(0),
        data=Bytes(b""),
        v=SIGNATURE_V,
        r=SIGNATURE_R,
        s=SIGNATURE_S,
    )
    block_env = cancun_vm.BlockEnvironment(
        chain_id=U64(1),
        state=CancunBlockState(pre_state=pre_state),
        block_gas_limit=Uint(30_000_000),
        block_hashes=[],
        coinbase=Address(b"\x00" * 20),
        number=Uint(1),
        base_fee_per_gas=Uint(0),
        time=U256(0),
        prev_randao=Bytes32(b"\x00" * 32),
        excess_blob_gas=U64(0),
        parent_beacon_block_root=Hash32(b"\x00" * 32),
    )
    block_output = cancun_vm.BlockOutput()
    tx_state = CancunTransactionState(parent=block_env.state)
    if asserted_sender is None:
        # Called exactly as consensus block execution calls it.
        return cancun_fork.check_transaction(
            block_env, block_output, tx, tx_state
        )[0]
    return cancun_fork.check_transaction(
        block_env,
        block_output,
        tx,
        tx_state,
        asserted_sender=asserted_sender,
    )[0]


def check_prague(
    pre_state: InMemoryPreState, asserted_sender: Optional[Address]
) -> Address:
    """Admit a transaction at Prague and report the sender used."""
    tx = PragueTransaction(
        nonce=U256(0),
        gas_price=GAS_PRICE,
        gas=GAS_LIMIT,
        to=RECIPIENT,
        value=U256(0),
        data=Bytes(b""),
        v=SIGNATURE_V,
        r=SIGNATURE_R,
        s=SIGNATURE_S,
    )
    block_env = prague_vm.BlockEnvironment(
        chain_id=U64(1),
        state=PragueBlockState(pre_state=pre_state),
        block_gas_limit=Uint(30_000_000),
        block_hashes=[],
        coinbase=Address(b"\x00" * 20),
        number=Uint(1),
        base_fee_per_gas=Uint(0),
        time=U256(0),
        prev_randao=Bytes32(b"\x00" * 32),
        excess_blob_gas=U64(0),
        parent_beacon_block_root=Hash32(b"\x00" * 32),
    )
    block_output = prague_vm.BlockOutput()
    tx_state = PragueTransactionState(parent=block_env.state)
    if asserted_sender is None:
        return prague_fork.check_transaction(
            block_env, block_output, tx, tx_state
        )[0]
    return prague_fork.check_transaction(
        block_env,
        block_output,
        tx,
        tx_state,
        asserted_sender=asserted_sender,
    )[0]


def check_amsterdam(
    pre_state: InMemoryPreState, asserted_sender: Optional[Address]
) -> Address:
    """Admit a transaction at Amsterdam and report the sender used."""
    tx = AmsterdamTransaction(
        nonce=U256(0),
        gas_price=GAS_PRICE,
        gas=GAS_LIMIT,
        to=RECIPIENT,
        value=U256(0),
        data=Bytes(b""),
        v=SIGNATURE_V,
        r=SIGNATURE_R,
        s=SIGNATURE_S,
    )
    block_env = amsterdam_vm.BlockEnvironment(
        chain_id=U64(1),
        state=AmsterdamBlockState(pre_state=pre_state),
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
    block_output = amsterdam_vm.BlockOutput()
    # Amsterdam's fourth positional argument is the transaction index,
    # not the transaction state; the keyword-only parameter is what keeps
    # that difference from mattering to callers.
    if asserted_sender is None:
        return amsterdam_fork.check_transaction(
            block_env, block_output, tx, Uint(0)
        ).origin
    return amsterdam_fork.check_transaction(
        block_env,
        block_output,
        tx,
        Uint(0),
        asserted_sender=asserted_sender,
    ).origin


def recover_cancun() -> Address:
    """Return the address Cancun recovers from the shared signature."""
    return cancun_recover_sender(
        CancunTransaction(
            nonce=U256(0),
            gas_price=GAS_PRICE,
            gas=GAS_LIMIT,
            to=RECIPIENT,
            value=U256(0),
            data=Bytes(b""),
            v=SIGNATURE_V,
            r=SIGNATURE_R,
            s=SIGNATURE_S,
        )
    )


def recover_prague() -> Address:
    """Return the address Prague recovers from the shared signature."""
    return prague_recover_sender(
        PragueTransaction(
            nonce=U256(0),
            gas_price=GAS_PRICE,
            gas=GAS_LIMIT,
            to=RECIPIENT,
            value=U256(0),
            data=Bytes(b""),
            v=SIGNATURE_V,
            r=SIGNATURE_R,
            s=SIGNATURE_S,
        )
    )


def recover_amsterdam() -> Address:
    """Return the address Amsterdam recovers from the shared signature."""
    return amsterdam_recover_sender(
        AmsterdamTransaction(
            nonce=U256(0),
            gas_price=GAS_PRICE,
            gas=GAS_LIMIT,
            to=RECIPIENT,
            value=U256(0),
            data=Bytes(b""),
            v=SIGNATURE_V,
            r=SIGNATURE_R,
            s=SIGNATURE_S,
        )
    )


Check = Callable[[InMemoryPreState, Optional[Address]], Address]
Recover = Callable[[], Address]

# Cancun tests the sender's code hash on its own; Prague and Amsterdam
# also consult ``is_valid_delegation``. Both shapes must behave the same
# way when the sender is asserted.
FORKS = [
    pytest.param(check_cancun, recover_cancun, id="cancun"),
    pytest.param(check_prague, recover_prague, id="prague"),
    pytest.param(check_amsterdam, recover_amsterdam, id="amsterdam"),
]


@pytest.mark.parametrize("check, recover", FORKS)
def test_asserted_sender_replaces_recovery(
    check: Check, recover: Recover
) -> None:
    """An asserted sender is used verbatim, in place of the recovered one."""
    recovered = recover()
    assert recovered != ASSERTED_SENDER

    pre_state = InMemoryPreState()
    fund(pre_state, recovered, Bytes(b""))
    fund(pre_state, ASSERTED_SENDER, Bytes(b""))

    assert check(pre_state, None) == recovered
    assert check(pre_state, ASSERTED_SENDER) == ASSERTED_SENDER


@pytest.mark.parametrize("check, recover", FORKS)
def test_asserted_sender_may_have_code(check: Check, recover: Recover) -> None:
    """
    A sender with code is admitted when asserted and rejected when signed.

    The requirement that a sender be an externally owned account applies
    only to a sender derived from a signature, so asserting one lifts it.
    """
    recovered = recover()
    pre_state = InMemoryPreState()
    fund(pre_state, recovered, SENDER_CODE)
    fund(pre_state, ASSERTED_SENDER, SENDER_CODE)

    assert check(pre_state, ASSERTED_SENDER) == ASSERTED_SENDER

    with pytest.raises(InvalidSenderError):
        check(pre_state, None)
