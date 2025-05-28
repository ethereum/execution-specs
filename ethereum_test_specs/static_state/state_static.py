"""Ethereum General State Test filler static test spec parser."""

from functools import cached_property
from typing import Any, Callable, ClassVar, Dict, List, Tuple

import pytest
from _pytest.mark.structures import ParameterSet

from ethereum_test_base_types import (
    Account,
    Address,
    Hash,
    HexNumber,
    Storage,
    ZeroPaddedHexNumber,
)
from ethereum_test_exceptions import TransactionExceptionInstanceOrList
from ethereum_test_forks import Fork
from ethereum_test_types import Alloc, Environment, Transaction

from ..base_static import BaseStaticTest
from ..state import StateTestFiller
from .common import AddressInFiller
from .expect_section import (
    AccountInExpectSection,
)
from .state_test_filler import StateTestInFiller, StateTestVector


class StateStaticTest(StateTestInFiller, BaseStaticTest):
    """General State Test static filler from ethereum/tests."""

    test_name: str = ""
    vectors: List[StateTestVector] | None = None
    format_name: ClassVar[str] = "state_test"

    def model_post_init(self, context):
        """Initialize StateStaticTest."""
        super().model_post_init(context)

    def fill_function(self) -> Callable:
        """Return a StateTest spec from a static file."""
        d_g_v_parameters: List[ParameterSet] = []
        for d in range(len(self.transaction.data)):
            for g in range(len(self.transaction.gas_limit)):
                for v in range(len(self.transaction.value)):
                    exception_test = False
                    for expect in self.expect:
                        if expect.has_index(d, g, v) and expect.expect_exception is not None:
                            exception_test = True
                    # TODO: This does not take into account exceptions that only happen on
                    #       specific forks, but this requires a covariant parametrize
                    marks = [pytest.mark.exception_test] if exception_test else []
                    d_g_v_parameters.append(
                        pytest.param(d, g, v, marks=marks, id=f"d{d}-g{g}-v{v}")
                    )

        @pytest.mark.valid_at(*self.get_valid_at_forks())
        @pytest.mark.parametrize("d,g,v", d_g_v_parameters)
        def test_state_vectors(
            state_test: StateTestFiller,
            fork: Fork,
            d: int,
            g: int,
            v: int,
        ):
            for expect in self.expect:
                if expect.has_index(d, g, v):
                    if fork.name() in expect.network:
                        post, tx = self._make_vector(
                            d,
                            g,
                            v,
                            expect.result,
                            exception=None
                            if expect.expect_exception is None
                            else expect.expect_exception[fork.name()],
                        )
                        return state_test(
                            env=self._get_env,
                            pre=self._get_pre,
                            post=post,
                            tx=tx,
                        )
            pytest.fail(f"Expectation not found for d={d}, g={g}, v={v}, fork={fork}")

        if self.info and self.info.pytest_marks:
            for mark in self.info.pytest_marks:
                apply_mark = getattr(pytest.mark, mark)
                test_state_vectors = apply_mark(test_state_vectors)

        return test_state_vectors

    def get_valid_at_forks(self) -> List[str]:
        """Return list of forks that are valid for this test."""
        fork_list: List[str] = []
        for expect in self.expect:
            for fork in expect.network:
                if fork not in fork_list:
                    fork_list.append(fork)
        return fork_list

    @cached_property
    def _get_env(self) -> Environment:
        """Parse environment."""
        # Convert Environment data from .json filler into pyspec type
        test_env = self.env
        env = Environment(
            fee_recipient=Address(test_env.current_coinbase),
            difficulty=ZeroPaddedHexNumber(test_env.current_difficulty)
            if test_env.current_difficulty is not None
            else None,
            prev_randao=ZeroPaddedHexNumber(test_env.current_random)
            if test_env.current_random is not None
            else None,
            gas_limit=ZeroPaddedHexNumber(test_env.current_gas_limit),
            number=ZeroPaddedHexNumber(test_env.current_number),
            timestamp=ZeroPaddedHexNumber(test_env.current_timestamp),
            base_fee_per_gas=ZeroPaddedHexNumber(test_env.current_base_fee)
            if test_env.current_base_fee is not None
            else None,
            excess_blob_gas=ZeroPaddedHexNumber(test_env.current_excess_blob_gas)
            if test_env.current_excess_blob_gas is not None
            else None,
        )
        return env

    @cached_property
    def _get_pre(self) -> Alloc:
        """Parse pre."""
        # Convert pre state data from .json filler into pyspec type
        pre = Alloc()
        for account_address, account in self.pre.items():
            storage: Storage = Storage()
            for key, value in account.storage.items():
                storage[key] = value

            pre[account_address] = Account(
                balance=account.balance,
                nonce=account.nonce,
                code=account.code.compiled,
                storage=storage,
            )
        return pre

    def _make_vector(
        self,
        d: int,
        g: int,
        v: int,
        expect_result: Dict[AddressInFiller, AccountInExpectSection],
        exception: TransactionExceptionInstanceOrList | None,
    ) -> Tuple[Alloc, Transaction]:
        """Compose test vector from test data."""
        general_tr = self.transaction
        data_box = general_tr.data[d]

        tr: Transaction = Transaction(
            data=data_box.data.compiled,
            access_list=data_box.access_list,
            gas_limit=HexNumber(general_tr.gas_limit[g]),
            value=HexNumber(general_tr.value[v]),
            gas_price=general_tr.gas_price,
            max_fee_per_gas=general_tr.max_fee_per_gas,
            max_priority_fee_per_gas=general_tr.max_priority_fee_per_gas,
            max_fee_per_blob_gas=general_tr.max_fee_per_blob_gas,
            blob_versioned_hashes=general_tr.blob_versioned_hashes,
            nonce=HexNumber(general_tr.nonce),
            to=Address(general_tr.to) if general_tr.to is not None else None,
            secret_key=Hash(general_tr.secret_key),
            error=exception,
        )

        post = Alloc()
        for address, account in expect_result.items():
            if account.expected_to_not_exist is not None:
                post[address] = Account.NONEXISTENT
                continue

            account_kwargs: Dict[str, Any] = {}
            if account.storage is not None:
                storage = Storage()
                for key, value in account.storage.items():
                    if value != "ANY":
                        storage[key] = value
                    else:
                        storage.set_expect_any(key)
                account_kwargs["storage"] = storage
            if account.code is not None:
                account_kwargs["code"] = account.code.compiled
            if account.balance is not None:
                account_kwargs["balance"] = account.balance
            if account.nonce is not None:
                account_kwargs["nonce"] = account.nonce

            post[address] = Account(**account_kwargs)

        return post, tr
