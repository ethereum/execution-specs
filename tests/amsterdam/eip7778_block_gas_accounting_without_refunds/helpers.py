"""Helpers used in EIP-7778 tests."""

from enum import Enum
from typing import Any, Dict, List, Self, Set

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Bytecode,
    Fork,
    RecipientType,
    RefundTypes,
    Transaction,
    TransactionReceipt,
    add_kzg_version,
)
from execution_testing.base_types import HashInt
from execution_testing.vm import Op
from pydantic import Field


class TransactionFailure(Enum):
    """Types of failures that the transactions can have."""

    REVERT = "reverts"
    OOG = "oog"
    INVALID = "halts"
    UPPER_REVERT = "upper_revert"

    @classmethod
    def with_all_tx_failures(cls) -> Any:
        """Return the parametrization for all transaction failures."""
        return pytest.mark.parametrize(
            "refund_tx_failure",
            [
                pytest.param(failure, id=f"refund_tx_{failure.value}")
                for failure in cls
            ]
            + [
                pytest.param(None, id=""),
            ],
        )


class RefundTransaction(Transaction):
    """Transaction modeled to produce a refund."""

    sender: EOA
    expected_receipt: TransactionReceipt = Field(exclude=True)
    receipt_gas_used: int = Field(exclude=True)
    gas_used_pre_refund: int = Field(exclude=True)
    state_gas: int = Field(exclude=True)
    call_data_floor_cost: int = Field(exclude=True)

    code: Bytecode = Field(exclude=True)
    storage_slots: List[HashInt] = Field(exclude=True)
    tx_failure: TransactionFailure | None = Field(exclude=True)
    empty_storage_on_success: bool = Field(exclude=True)
    blob_gas_fee: int = Field(exclude=True)
    inner_code: Bytecode | None = Field(None, exclude=True)
    inner_address: Address | None = Field(None, exclude=True)

    @classmethod
    def build(
        cls,
        *,
        fork: Fork,
        sender: EOA,
        refund_types: Set[RefundTypes],
        refunds_count: int = 1,
        tx_failure: TransactionFailure | None = None,
        call_data: bytes = b"",
        refund_tx_has_gas_limit_slack: bool = False,
        ty: int = 0,
        authorization_list: List[AuthorizationTuple] | None = None,
        emit_log: bool = False,
    ) -> Self:
        """Build a transaction that has different refund types from a fork."""
        # All essential calc functions
        intrinsic_cost_calc = fork.transaction_intrinsic_cost_calculator()
        max_refund_quotient = fork.max_refund_quotient()
        data_floor_calc = fork.transaction_data_floor_cost_calculator()

        if ty == 4 and not authorization_list:
            raise ValueError(
                "a type-4 transaction needs a non-empty authorization list"
            )
        if ty != 4 and authorization_list:
            raise ValueError(
                f"a type-{ty} transaction cannot carry an authorization list"
            )
        # A blob transaction needs at least one blob to be valid; blob gas
        # is its own dimension and does not enter block gas accounting.
        blob_versioned_hashes = (
            add_kzg_version([0x01], 0x01) if ty == 3 else None
        )
        blob_gas_fee = 0
        if blob_versioned_hashes is not None:
            blob_gas_price = fork.blob_gas_price_calculator()(
                excess_blob_gas=0
            )
            blob_gas_fee = (
                len(blob_versioned_hashes)
                * fork.blob_gas_per_blob()
                * blob_gas_price
            )

        # Expectations are recorded here as each one is established.
        expected_receipt: Dict[str, Any] = {}

        # Initialize other aspects of pre-alloc
        code = Bytecode()
        refund_counter = 0
        storage_slots = list(range(HashInt(refunds_count)))

        empty_storage_on_success = False
        refund_tx_gas_limit_slack = 1 if refund_tx_has_gas_limit_slack else 0

        # Sort by name so iteration order is deterministic.
        for refund_type in sorted(refund_types, key=lambda r: r.name):
            match refund_type:
                case RefundTypes.STORAGE_CLEAR:
                    for slot in storage_slots:
                        code += Op.SSTORE(
                            slot,
                            Op.PUSH0,
                            # Gas accounting
                            original_value=1,
                            new_value=0,
                        )
                    empty_storage_on_success = True

                case _:
                    raise ValueError(
                        f"Unknown refund type: {refund_type} "
                        "(Test needs update)"
                    )

        if emit_log:
            topic = 0
            code += Op.LOG1(offset=0, size=0, topic_1=topic)
            if tx_failure is None:
                expected_receipt["logs"] = [{"topics": [topic], "data": b""}]

        inner_code: Bytecode | None = None
        match tx_failure:
            case TransactionFailure.INVALID:
                code += Op.INVALID
            case TransactionFailure.OOG:
                code += Op.MSTORE8(2**64, 1)
            case TransactionFailure.REVERT:
                code += Op.REVERT(0, 0)
            case TransactionFailure.UPPER_REVERT:
                inner_code = code + Op.STOP
                code = Op.CALL(
                    gas=Op.GAS,
                    address=Op.PUSH20(data_placeholder="subcall_address"),
                    address_warm=False,
                ) + Op.REVERT(0, 0)
            case None:
                code += Op.STOP

        # EIP-2780 charges each authorization at the top frame rather
        # than in the intrinsic; both terms are zero without one.
        top_frame_execution = fork.transaction_top_frame_execution_gas(
            recipient_type=RecipientType.CONTRACT,
            authorizations=authorization_list or (),
        )
        top_frame_state = fork.transaction_top_frame_state_gas(
            recipient_type=RecipientType.CONTRACT,
            authorizations=authorization_list or (),
        )

        inner_gas_used = (
            0 if inner_code is None else inner_code.execution_cost(fork)
        )

        # State gas affects calculation, ensure none was used
        assert code.state_cost(fork) == 0, (
            f"code should not consume state gas: {code.state_cost(fork)}"
        )
        assert inner_code is None or inner_code.state_cost(fork) == 0, (
            "inner code should not consume state gas: "
            f"{inner_code.state_cost(fork) if inner_code else 0}"
        )

        # Gas consumed pre-refund (execution gas only)
        gas_used_pre_refund = (
            intrinsic_cost_calc(
                calldata=call_data,
                return_cost_deducted_prior_execution=True,
                authorization_list_or_count=authorization_list,
            )
            + top_frame_execution
            + code.execution_cost(fork)
            + inner_gas_used
        )

        # Calculate refund (still applied to user's balance)
        if tx_failure is None:
            refund_counter += code.refund(fork)

        # The STORAGE_CLEAR path creates no state; only an EIP-7702
        # authorization contributes state gas at the top frame.
        state_gas = top_frame_state

        # In the spec, the refund cap uses tx_gas_used_before_refund which is
        # tx.gas - gas_left - state_gas_left (combined execution + remaining
        # state).
        combined_before_refund = gas_used_pre_refund + state_gas

        effective_refund = min(
            refund_counter, combined_before_refund // max_refund_quotient
        )
        receipt_gas_used = combined_before_refund - effective_refund
        call_data_floor_cost = data_floor_calc(data=call_data)

        # gas_used_post_refund is the "combined after refund" value used for
        # calldata floor comparisons and balance computation
        gas_used_post_refund = receipt_gas_used
        refund_tx_gas_used = max(call_data_floor_cost, gas_used_post_refund)

        call_forwarding_reserve = (
            0 if inner_code is None else inner_gas_used // 63 + 1
        )

        # gas_limit must cover combined gas (execution + state)
        refund_tx_gas_limit = (
            max(call_data_floor_cost, combined_before_refund)
            + refund_tx_gas_limit_slack
            + call_forwarding_reserve
        )

        if tx_failure in [TransactionFailure.INVALID, TransactionFailure.OOG]:
            # A non-revertable abort consumes the whole limit, but the
            # state gas already charged at the top frame belongs to the
            # state dimension rather than the execution one.
            gas_used_pre_refund = refund_tx_gas_limit - state_gas
            receipt_gas_used = refund_tx_gas_limit
            refund_tx_gas_used = refund_tx_gas_limit

        expected_receipt["gas_used"] = refund_tx_gas_used

        # Build refund transaction
        return cls(
            ty=ty,
            to=None,
            data=call_data,
            gas_limit=refund_tx_gas_limit,
            sender=sender,
            authorization_list=authorization_list,
            blob_versioned_hashes=blob_versioned_hashes,
            expected_receipt=expected_receipt,
            receipt_gas_used=receipt_gas_used,
            gas_used_pre_refund=gas_used_pre_refund,
            state_gas=state_gas,
            call_data_floor_cost=call_data_floor_cost,
            code=code,
            storage_slots=storage_slots,
            tx_failure=tx_failure,
            empty_storage_on_success=empty_storage_on_success,
            blob_gas_fee=blob_gas_fee,
            inner_code=inner_code,
        )

    def block_execution(self) -> int:
        """Execution gas reported by the block."""
        return max(self.gas_used_pre_refund, self.call_data_floor_cost)

    def block_gas_used(self) -> int:
        """
        EIP-8037 block gas_used, with the calldata floor binding the execution
        dimension.
        """
        return max(
            self.gas_used_pre_refund, self.call_data_floor_cost, self.state_gas
        )

    def set_pre(self, pre: Alloc) -> None:
        """Set the pre-allocation required for the refund transaction."""
        emitter: Address
        if self.inner_code is not None:
            emitter = pre.deploy_contract(
                code=self.inner_code,
                storage=dict.fromkeys(self.storage_slots, 1),
            )
            self.inner_address = emitter
            self.code.substitute(
                subcall_address=int.from_bytes(self.inner_address)
            )
            self.to = pre.deploy_contract(
                code=self.code,
            )
        else:
            emitter = pre.deploy_contract(
                code=self.code,
                storage=dict.fromkeys(self.storage_slots, 1),
            )
            self.to = emitter
        # A log carries the address of the frame that emitted it.
        for log in self.expected_receipt.logs or []:
            log.address = emitter

    def post(self, pre: Alloc, block_is_invalid: bool = False) -> Alloc:
        """Set transaction post expectations."""
        post = Alloc()
        refund_tx_gas_price = (
            self.gas_price if self.gas_price else self.max_fee_per_gas
        )
        contract_address = (
            self.to if self.inner_address is None else self.inner_address
        )
        assert contract_address is not None, "need to call set_pre first"
        if (
            self.tx_failure is not None
            or block_is_invalid
            or not self.empty_storage_on_success
        ):
            post[contract_address] = Account(
                storage=dict.fromkeys(self.storage_slots, 1),
            )
        else:
            post[contract_address] = Account(
                storage=dict.fromkeys(self.storage_slots, 0),
            )

        assert refund_tx_gas_price is not None, (
            "refund_tx_gas_price should not be None"
        )
        pre_sender = pre[Address(self.sender)]
        assert pre_sender is not None
        initial_fund = pre_sender.balance
        assert initial_fund is not None
        receipt_gas_used = self.expected_receipt.gas_used
        assert receipt_gas_used is not None
        expected_balance = (
            initial_fund
            - (receipt_gas_used * refund_tx_gas_price)
            - self.blob_gas_fee
        )

        if not block_is_invalid:
            post[self.sender] = Account(balance=expected_balance)
        return post
