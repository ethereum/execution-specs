"""
Measurement instrument: how many logs a value-bearing call produces.

EIP-7708 emits a `Transfer(address,address,uint256)` log from SYSTEM_ADDRESS
for every non-zero ETH movement, and `execute_code` emits it BEFORE the
callee's first opcode (amsterdam/vm/interpreter.py:418-430). So the callee's
own event, which used to sit at log index 0, moves to index 1.

Phase (a) counts logs on the pre-7708 forks; phase (b) counts them at
Amsterdam and pins the index shift.

FAILURES ARE THE MEASUREMENT.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    EOA,
    Hash,
    Op,
    StateTestFiller,
    Transaction,
    TransactionLog,
    TransactionReceipt,
    keccak256,
)

SYSTEM_ADDRESS = Address(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE)
ERC20_TRANSFER_TOPIC = Hash(keccak256(b"Transfer(address,address,uint256)"))
OWN_TOPIC = Hash(0x1111)
PAYLOAD = Bytes((0xCAFE).to_bytes(32, "big"))

EMITTER = Op.MSTORE(0, 0xCAFE) + Op.LOG1(0, 32, OWN_TOPIC) + Op.STOP


def _own(addr: Address) -> TransactionLog:
    return TransactionLog(address=addr, topics=[OWN_TOPIC], data=PAYLOAD)


def _transfer(a: Address, b: Address, v: int) -> TransactionLog:
    return TransactionLog(
        address=SYSTEM_ADDRESS,
        topics=[
            ERC20_TRANSFER_TOPIC,
            Hash(bytes(a).rjust(32, b"\x00")),
            Hash(bytes(b).rjust(32, b"\x00")),
        ],
        data=Bytes(v.to_bytes(32, "big")),
    )


@pytest.mark.parametrize("n_logs", [1, 2], ids=["one_log", "two_logs"])
@pytest.mark.valid_from("Prague")
def test_count(
    state_test: StateTestFiller, pre: Alloc, n_logs: int
) -> None:
    """Probe: how many logs does a value-bearing call to an emitter make?"""
    sender: EOA = pre.fund_eoa(amount=10**18)
    emitter = pre.deploy_contract(EMITTER)
    logs = [_own(emitter)]
    if n_logs == 2:
        logs = [_transfer(sender, emitter, 1), _own(emitter)]
    tx = Transaction(
        to=emitter,
        value=1,
        gas_limit=200_000,
        sender=sender,
        expected_receipt=TransactionReceipt(logs=logs),
    )
    state_test(pre=pre, post={emitter: Account(balance=1)}, tx=tx)


@pytest.mark.parametrize(
    "value", [0, 1], ids=["zero_value", "value_bearing"]
)
@pytest.mark.parametrize("n_logs", [1, 2], ids=["one_log", "two_logs"])
@pytest.mark.valid_from("Prague")
def test_zero_value(
    state_test: StateTestFiller, pre: Alloc, value: int, n_logs: int
) -> None:
    """Probe: does a ZERO-value call still produce one log only?"""
    sender: EOA = pre.fund_eoa(amount=10**18)
    emitter = pre.deploy_contract(EMITTER)
    logs = [_own(emitter)]
    if n_logs == 2:
        logs = [_transfer(sender, emitter, value), _own(emitter)]
    tx = Transaction(
        to=emitter,
        value=value,
        gas_limit=200_000,
        sender=sender,
        expected_receipt=TransactionReceipt(logs=logs),
    )
    state_test(pre=pre, post={emitter: Account(balance=value)}, tx=tx)
