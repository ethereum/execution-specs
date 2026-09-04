"""Verify execute-mode estimation, ordering, and failure handling."""

from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import Mock

import pytest
from pytest import FixtureRequest

from execution_testing.base_types import Account, Address
from execution_testing.exceptions import TransactionException
from execution_testing.forks import Amsterdam
from execution_testing.rpc import EthRPC, SendTransactionExceptionError
from execution_testing.test_types import (
    EOA,
    Alloc,
    AuthorizationTuple,
    Environment,
    Transaction,
    TransactionReceipt,
)

from ..transaction_post import TransactionPost


def prepare(txs: list[Transaction], **kwargs: Any) -> TransactionPost:
    """Prepare a funded execution plan without contacting a client."""
    plan = TransactionPost(blocks=[txs], post={}, **kwargs)
    plan.prepare_transactions(
        env=Environment(gas_limit=60_000_000),
        gas_price=10,
        max_fee_per_gas=10,
        max_priority_fee_per_gas=1,
        max_fee_per_blob_gas=10,
        fork=Amsterdam,
    )
    return plan


def execute(plan: TransactionPost, rpc: Mock) -> None:
    """Execute using a minimal request and mocked RPC."""
    plan.execute(
        fork=Amsterdam,
        eth_rpc=cast(EthRPC, rpc),
        engine_rpc=None,
        request=cast(
            FixtureRequest,
            SimpleNamespace(node=SimpleNamespace(nodeid="test_estimate_gas")),
        ),
    )


@pytest.fixture
def rpc() -> Mock:
    """Return an RPC that includes successful transactions."""
    rpc = Mock(spec=EthRPC)
    rpc.estimate_gas.return_value = 100_000
    rpc.get_transaction_receipt.return_value = {"status": "0x1"}
    rpc.get_alloc.return_value = Alloc()
    return rpc


@pytest.mark.parametrize("enabled", [False, True])
def test_estimate_before_signing(enabled: bool, rpc: Mock) -> None:
    """Sign the estimate while retaining the conservative funding bound."""
    sender = EOA(key=123)
    tx = Transaction(sender=sender)
    plan = prepare([tx], estimate_gas=enabled)
    budget = int(tx.gas_limit)
    assert (
        plan.get_required_sender_balances(fork=Amsterdam)[sender]
        == budget * 10
    )
    execute(plan, rpc)
    sent = rpc.send_wait_transactions.call_args.args[0][0]
    assert sent.gas_limit == (100_000 if enabled else budget)
    assert sent.hash == tx.with_signature_and_sender().hash
    assert rpc.estimate_gas.call_count == int(enabled)
    assert rpc.get_transaction_receipt.call_count == int(enabled)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"gas_limit": 123_456},
        {"state_gas_reservoir": 0},
        {"state_gas_reservoir": 1_000_000},
        {"expected_receipt": TransactionReceipt(status=0)},
        {"error": TransactionException.INTRINSIC_GAS_TOO_LOW},
    ],
)
def test_preserve_gas_sensitive_transactions(kwargs: dict, rpc: Mock) -> None:
    """Preserve explicit budgets and intentional failures."""
    tx = Transaction(sender=EOA(key=123), **kwargs)
    plan = prepare([tx], estimate_gas=True)
    budget = tx.gas_limit
    rpc.send_transaction.side_effect = SendTransactionExceptionError(
        "rejected"
    )
    execute(plan, rpc)
    rpc.estimate_gas.assert_not_called()
    assert tx.gas_limit == budget


def test_preserve_signed_transactions(rpc: Mock) -> None:
    """Do not invalidate an existing signature by replacing its gas limit."""
    tx = Transaction(
        sender=EOA(key=123), gas_limit=100_000
    ).with_signature_and_sender()
    plan = prepare([tx], estimate_gas=True)
    execute(plan, rpc)
    rpc.estimate_gas.assert_not_called()
    assert rpc.send_wait_transactions.call_args.args[0][0].hash == tx.hash


def test_preserve_benchmark_budgets(rpc: Mock) -> None:
    """Keep benchmark gas budgets and receipt accounting unchanged."""
    tx = Transaction(sender=EOA(key=123))
    plan = prepare([tx], estimate_gas=True, benchmark_mode=True)
    rpc.get_transaction_receipt.return_value["gasUsed"] = "0x5208"
    execute(plan, rpc)
    rpc.estimate_gas.assert_not_called()


@pytest.mark.parametrize("explicit_first", [False, True])
def test_settle_dependencies(explicit_first: bool, rpc: Mock) -> None:
    """Include earlier transactions before estimating dependent ones."""
    sender = EOA(key=123)
    first = Transaction(
        sender=sender, gas_limit=200_000 if explicit_first else None
    )
    second = Transaction(sender=sender)
    plan = prepare([first, second], estimate_gas=True)
    events = []

    def estimate(transaction: dict, **_: Any) -> int:
        events.append(("estimate", int(transaction["nonce"], 16)))
        return 100_000

    rpc.estimate_gas.side_effect = estimate
    rpc.send_wait_transactions.side_effect = lambda txs: events.extend(
        ("included", int(tx.nonce)) for tx in txs
    )
    execute(plan, rpc)
    expected = [] if explicit_first else [("estimate", 0)]
    assert events == expected + [
        ("included", 0),
        ("estimate", 1),
        ("included", 1),
    ]


@pytest.mark.parametrize("estimate", [0, -1, 60_000_001])
def test_reject_invalid_estimate(estimate: int, rpc: Mock) -> None:
    """Fail before sending if the estimate cannot fit the funded budget."""
    plan = prepare([Transaction(sender=EOA(key=123))], estimate_gas=True)
    rpc.estimate_gas.return_value = estimate
    with pytest.raises(AssertionError, match="outside the funded"):
        execute(plan, rpc)
    rpc.send_wait_transactions.assert_not_called()


def test_estimation_error_is_not_hidden(rpc: Mock) -> None:
    """Propagate RPC errors rather than falling back to the default limit."""
    plan = prepare([Transaction(sender=EOA(key=123))], estimate_gas=True)
    rpc.estimate_gas.side_effect = RuntimeError("estimation failed")
    with pytest.raises(RuntimeError, match="estimation failed"):
        execute(plan, rpc)
    rpc.send_wait_transactions.assert_not_called()


def test_underestimate_fails_even_with_empty_post(rpc: Mock) -> None:
    """Catch an included transaction that halts with the estimated gas."""
    plan = prepare([Transaction(sender=EOA(key=123))], estimate_gas=True)
    rpc.get_transaction_receipt.return_value = {"status": "0x0"}
    with pytest.raises(AssertionError, match="failed with eth_estimateGas"):
        execute(plan, rpc)


def test_post_state_is_still_checked(rpc: Mock) -> None:
    """Reject a successful receipt whose state changes are incorrect."""
    plan = prepare([Transaction(sender=EOA(key=123))], estimate_gas=True)
    plan.post = Alloc({Address(1): Account(storage={0: 1})})
    rpc.get_alloc.return_value = Alloc({Address(1): Account(storage={0: 2})})
    with pytest.raises(Exception, match="incorrect value"):
        execute(plan, rpc)


@pytest.mark.parametrize(
    "ty,creation",
    [
        (0, False),
        (1, False),
        (2, False),
        (4, False),
        (0, True),
        (1, True),
        (2, True),
    ],
)
def test_rpc_fields(ty: int, creation: bool, rpc: Mock) -> None:
    """Preserve RPC fields without exposing signing material."""
    kwargs: dict[str, Any] = {}
    if ty == 4:
        kwargs["authorization_list"] = [
            AuthorizationTuple(signer=EOA(key=456), address=Address(789))
        ]
    tx = Transaction(
        ty=ty,
        sender=EOA(key=123),
        to=None if creation else Address(789),
        data=b"\x01\x02",
        value=7,
        **kwargs,
    )
    plan = prepare([tx], estimate_gas=True)
    execute(plan, rpc)
    call = rpc.estimate_gas.call_args
    payload = call.args[0]
    assert call.kwargs == {"block_number": "latest"}
    assert payload["from"] == str(tx.sender)
    assert payload["input"] == "0x0102"
    assert payload["value"] == "0x7"
    assert payload["type"] == hex(ty)
    assert payload["gas"] == hex(60_000_000)
    assert ("to" not in payload) if creation else payload["to"] == str(tx.to)
    assert (
        not {"secretKey", "sender", "v", "r", "s", "metadata"} & payload.keys()
    )
    if ty < 2:
        assert payload["gasPrice"] == "0xa"
        assert "maxFeePerGas" not in payload
    else:
        assert payload["maxFeePerGas"] == "0xa"
        assert "gasPrice" not in payload
    if ty == 4:
        assert set(payload["authorizationList"][0]) == {
            "chainId",
            "address",
            "nonce",
            "yParity",
            "r",
            "s",
        }


def test_estimate_can_exceed_execution_cap(rpc: Mock) -> None:
    """Allow state gas to raise Amsterdam estimates above the execution cap."""
    cap = Amsterdam.transaction_gas_limit_cap()
    assert cap is not None
    rpc.estimate_gas.return_value = cap + 1_000_000
    tx = Transaction(sender=EOA(key=123))
    execute(prepare([tx], estimate_gas=True), rpc)
    assert tx.gas_limit == cap + 1_000_000
