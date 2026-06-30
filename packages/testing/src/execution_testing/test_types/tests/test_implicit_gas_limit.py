"""
Test suite for implicit transaction gas-limit resolution.

Covers `Transaction.set_gas_limit` and
`Transaction.calculate_max_gas_limit`: the even split of remaining
environment gas, gas limit cap clamping, the state gas reservoir
(EIP-8037) semantics, and the test correctness errors raised on
contradictory test definitions.
"""

from typing import List

import pytest

from execution_testing.forks import Amsterdam, Fork, Osaka, Prague

from ..transaction_types import Transaction

_osaka_cap = Osaka.transaction_gas_limit_cap()
assert _osaka_cap is not None
OSAKA_CAP: int = _osaka_cap
_amsterdam_cap = Amsterdam.transaction_gas_limit_cap()
assert _amsterdam_cap is not None
AMSTERDAM_CAP: int = _amsterdam_cap

assert Prague.transaction_gas_limit_cap() is None
assert not Prague.state_gas_reservoir_enabled()
assert not Osaka.state_gas_reservoir_enabled()
assert Amsterdam.state_gas_reservoir_enabled()


def calculate_max_transaction_gas_limit(
    txs: List[Transaction],
    *,
    env_gas_limit: int,
    fork: Fork,
) -> int:
    """Split the environment gas across `txs` for the given fork."""
    return Transaction.calculate_max_gas_limit(
        txs=txs,
        env_gas_limit=env_gas_limit,
        transaction_gas_limit_cap=fork.transaction_gas_limit_cap(),
        state_gas_reservoir_enabled=fork.state_gas_reservoir_enabled(),
    )


class TestTreatNoneGasLimitAsUnset:
    """
    Test that an explicit `None` gas limit is dropped at construction time,
    leaving the field unset and defaulted.

    Callers that build transactions programmatically (e.g. the system-contract
    request helpers) rely on `gas_limit=None` being equivalent to omitting the
    argument: the field stays out of `model_fields_set` so the implicit
    gas-limit machinery resolves it, rather than treating it as explicit.
    """

    def test_none_defaults_to_21000(self) -> None:
        """`gas_limit=None` defaults the field to the 21,000 base cost."""
        assert isinstance(Transaction(gas_limit=None).gas_limit, int)

    def test_none_not_in_model_fields_set(self) -> None:
        """`gas_limit=None` leaves the field unset (implicit)."""
        assert "gas_limit" not in Transaction(gas_limit=None).model_fields_set

    def test_none_matches_omitted(self) -> None:
        """`gas_limit=None` is indistinguishable from omitting it."""
        explicit_none = Transaction(gas_limit=None)
        omitted = Transaction()
        assert explicit_none.gas_limit == omitted.gas_limit
        assert explicit_none.model_fields_set == omitted.model_fields_set

    def test_explicit_value_is_set(self) -> None:
        """An explicit integer gas limit remains in `model_fields_set`."""
        tx = Transaction(gas_limit=21_000)
        assert "gas_limit" in tx.model_fields_set

    @pytest.mark.parametrize("alias", ["gas_limit", "gasLimit", "gas"])
    def test_none_dropped_for_all_aliases(self, alias: str) -> None:
        """A `None` value is dropped regardless of the field alias used."""
        tx = Transaction(**{alias: None})
        assert tx.gas_limit == 21_000
        assert "gas_limit" not in tx.model_fields_set


class TestSetGasLimit:
    """Test `Transaction.set_gas_limit` resolution of unset limits."""

    def test_unset_no_cap(self) -> None:
        """An unset gas limit resolves to the maximum, uncapped."""
        tx = Transaction()
        tx.set_gas_limit(max_gas_limit=100, transaction_gas_limit_cap=None)
        assert tx.gas_limit == 100

    def test_unset_clamped_to_cap(self) -> None:
        """An unset gas limit is clamped to the gas limit cap."""
        tx = Transaction()
        tx.set_gas_limit(max_gas_limit=100, transaction_gas_limit_cap=60)
        assert tx.gas_limit == 60

    def test_unset_cap_above_max(self) -> None:
        """A cap above the maximum does not raise the gas limit."""
        tx = Transaction()
        tx.set_gas_limit(max_gas_limit=100, transaction_gas_limit_cap=200)
        assert tx.gas_limit == 100

    def test_explicit_gas_limit_untouched(self) -> None:
        """An explicit gas limit is never modified."""
        tx = Transaction(gas_limit=21_000)
        tx.set_gas_limit(max_gas_limit=100, transaction_gas_limit_cap=60)
        assert tx.gas_limit == 21_000

    def test_explicit_none_treated_as_unset(self) -> None:
        """An explicit `gas_limit=None` is treated as unset."""
        tx = Transaction(gas_limit=None)
        tx.set_gas_limit(max_gas_limit=100, transaction_gas_limit_cap=None)
        assert tx.gas_limit == 100

    def test_resolution_is_sticky(self) -> None:
        """A second call does not overwrite the resolved gas limit."""
        tx = Transaction()
        tx.set_gas_limit(max_gas_limit=100, transaction_gas_limit_cap=None)
        tx.set_gas_limit(max_gas_limit=50, transaction_gas_limit_cap=None)
        assert tx.gas_limit == 100

    def test_signing_requires_gas_limit(self) -> None:
        """Signing a transaction with an unset gas limit raises."""
        with pytest.raises(ValueError, match="gas_limit must be set"):
            Transaction().with_signature_and_sender()


class TestSetGasLimitStateGasReservoir:
    """Test the state gas reservoir (EIP-8037) gas-limit semantics."""

    def test_reservoir_unset_keeps_full_maximum(self) -> None:
        """With the reservoir unset, the cap does not clamp the limit."""
        tx = Transaction()
        tx.set_gas_limit(
            max_gas_limit=100,
            transaction_gas_limit_cap=60,
            state_gas_reservoir_enabled=True,
        )
        assert tx.gas_limit == 100

    def test_reservoir_zero_pins_to_cap(self) -> None:
        """An explicit zero reservoir pins the limit to exactly the cap."""
        tx = Transaction(state_gas_reservoir=0)
        tx.set_gas_limit(
            max_gas_limit=100,
            transaction_gas_limit_cap=60,
            state_gas_reservoir_enabled=True,
        )
        assert tx.gas_limit == 60

    def test_reservoir_pins_to_cap_plus_reservoir(self) -> None:
        """A positive reservoir pins the limit to cap plus reservoir."""
        tx = Transaction(state_gas_reservoir=40)
        tx.set_gas_limit(
            max_gas_limit=200,
            transaction_gas_limit_cap=60,
            state_gas_reservoir_enabled=True,
        )
        assert tx.gas_limit == 100

    def test_reservoir_ignored_with_explicit_gas_limit(self) -> None:
        """A reservoir is ignored when the gas limit is explicit."""
        tx = Transaction(gas_limit=21_000, state_gas_reservoir=40)
        tx.set_gas_limit(
            max_gas_limit=200,
            transaction_gas_limit_cap=60,
            state_gas_reservoir_enabled=True,
        )
        assert tx.gas_limit == 21_000

    def test_reservoir_exceeding_available_gas_raises(self) -> None:
        """A reservoir that does not fit the available gas raises."""
        tx = Transaction(state_gas_reservoir=50)
        with pytest.raises(
            Exception, match="test correctness: the requested state"
        ):
            tx.set_gas_limit(
                max_gas_limit=100,
                transaction_gas_limit_cap=60,
                state_gas_reservoir_enabled=True,
            )

    @pytest.mark.parametrize(
        "gas_limit",
        [
            pytest.param(None, id="implicit_gas_limit"),
            pytest.param(21_000, id="explicit_gas_limit"),
        ],
    )
    def test_reservoir_on_unsupported_fork_raises(
        self, gas_limit: int | None
    ) -> None:
        """A positive reservoir raises if the fork has no reservoir."""
        tx = Transaction(gas_limit=gas_limit, state_gas_reservoir=1)
        with pytest.raises(
            Exception, match="test correctness: transaction requests"
        ):
            tx.set_gas_limit(
                max_gas_limit=100,
                transaction_gas_limit_cap=60,
                state_gas_reservoir_enabled=False,
            )

    def test_reservoir_zero_on_unsupported_fork_clamps_to_cap(self) -> None:
        """An explicit zero reservoir is valid on forks without one."""
        tx = Transaction(state_gas_reservoir=0)
        tx.set_gas_limit(
            max_gas_limit=100,
            transaction_gas_limit_cap=60,
            state_gas_reservoir_enabled=False,
        )
        assert tx.gas_limit == 60

    def test_reservoir_without_cap_is_internal_invariant(self) -> None:
        """A reservoir request without a cap violates an invariant."""
        tx = Transaction(state_gas_reservoir=1)
        with pytest.raises(AssertionError, match="must also define a cap"):
            tx.set_gas_limit(
                max_gas_limit=100,
                transaction_gas_limit_cap=None,
                state_gas_reservoir_enabled=True,
            )


class TestCalculateMaxTransactionGasLimit:
    """Test the even split of environment gas across transactions."""

    def test_no_implicit_transactions(self) -> None:
        """Return 0 when all transactions have explicit gas limits."""
        txs = [Transaction(gas_limit=200_000)]
        assert (
            calculate_max_transaction_gas_limit(
                txs, env_gas_limit=100_000, fork=Prague
            )
            == 0
        )

    def test_empty_transaction_list(self) -> None:
        """Return 0 for an empty transaction list."""
        assert (
            calculate_max_transaction_gas_limit(
                [], env_gas_limit=100_000, fork=Prague
            )
            == 0
        )

    def test_single_implicit_transaction(self) -> None:
        """A single implicit transaction gets the full environment gas."""
        txs = [Transaction()]
        assert (
            calculate_max_transaction_gas_limit(
                txs, env_gas_limit=100_000, fork=Prague
            )
            == 100_000
        )

    def test_explicit_limits_reduce_available_gas(self) -> None:
        """Explicit gas limits are deducted from the environment gas."""
        txs = [Transaction(gas_limit=40_000), Transaction()]
        assert (
            calculate_max_transaction_gas_limit(
                txs, env_gas_limit=100_000, fork=Prague
            )
            == 60_000
        )

    def test_even_split_across_implicit_transactions(self) -> None:
        """Remaining gas is split evenly across implicit transactions."""
        txs = [Transaction(gas_limit=10_000), Transaction(), Transaction()]
        assert (
            calculate_max_transaction_gas_limit(
                txs, env_gas_limit=100_000, fork=Prague
            )
            == 45_000
        )

    def test_split_clamped_to_cap(self) -> None:
        """The per-transaction share is clamped to the fork's cap."""
        env_gas_limit = 100_000_000
        assert env_gas_limit > OSAKA_CAP
        txs = [Transaction()]
        assert (
            calculate_max_transaction_gas_limit(
                txs, env_gas_limit=env_gas_limit, fork=Osaka
            )
            == OSAKA_CAP
        )

    def test_state_gas_reservoir_fork_removes_cap(self) -> None:
        """A fork with the state gas reservoir does not clamp the share."""
        env_gas_limit = 100_000_000
        assert env_gas_limit > AMSTERDAM_CAP
        txs = [Transaction()]
        assert (
            calculate_max_transaction_gas_limit(
                txs, env_gas_limit=env_gas_limit, fork=Amsterdam
            )
            == env_gas_limit
        )

    @pytest.mark.parametrize(
        "explicit_gas_limit",
        [
            pytest.param(100_000, id="exactly_consumed"),
            pytest.param(150_000, id="over_consumed"),
        ],
    )
    def test_no_remaining_gas_raises(self, explicit_gas_limit: int) -> None:
        """Raise when explicit limits leave implicit transactions no gas."""
        txs = [Transaction(gas_limit=explicit_gas_limit), Transaction()]
        with pytest.raises(
            Exception, match="test correctness: unable to automatically"
        ):
            calculate_max_transaction_gas_limit(
                txs, env_gas_limit=100_000, fork=Prague
            )

    def test_no_remaining_gas_all_explicit_does_not_raise(self) -> None:
        """Over-consumption without implicit transactions returns 0."""
        txs = [Transaction(gas_limit=150_000)]
        assert (
            calculate_max_transaction_gas_limit(
                txs, env_gas_limit=100_000, fork=Prague
            )
            == 0
        )
