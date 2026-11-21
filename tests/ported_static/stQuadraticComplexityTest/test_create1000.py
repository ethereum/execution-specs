"""
CREATE in a loop until the count is reached or the gas runs out.

The filler ran 1000 iterations; the count is now the number of
creations that fit in a 2**24 gas transaction. With 50000-byte init
code the first CREATE exceeds the init code size limit.

Ported from:
state_tests/stQuadraticComplexityTest/Create1000Filler.json
state_tests/stQuadraticComplexityTest/Create1000ByzantiumFiller.json
state_tests/stQuadraticComplexityTest/Create1000ShnghaiFiller.json

@manually-enhanced: Do not overwrite. Loop count derived from the
gas budget; the whole creation sequence is asserted.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_GAS = 2**24
SHORT_TX_GAS = 150_000
FILLER_COUNT = 1000
COUNTER = 0x80
ITERATION_OVERHEAD = 1_000
LOOP_MARGIN = 100_000


@pytest.mark.ported_from(
    [
        "state_tests/stQuadraticComplexityTest/Create1000Filler.json",
        "state_tests/stQuadraticComplexityTest/Create1000ByzantiumFiller.json",  # noqa: E501
        "state_tests/stQuadraticComplexityTest/Create1000ShnghaiFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "initcode_size",
    [
        pytest.param(10, id="create1000_shnghai"),
        pytest.param(50_000, id="create1000"),
    ],
)
@pytest.mark.parametrize("short_gas", [True, False], ids=["g0", "g1"])
def test_create1000(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode_size: int,
    short_gas: bool,
) -> None:
    """Store the last created address and the iteration count."""
    create = Op.CREATE(
        value=1,
        offset=0,
        size=initcode_size,
        init_code_size=initcode_size,
        new_memory_size=initcode_size,
    )
    count = min(
        FILLER_COUNT,
        (TX_GAS - LOOP_MARGIN) // (create.gas_cost(fork) + ITERATION_OVERHEAD),
    )
    assert count * create.gas_cost(fork) > SHORT_TX_GAS

    loop_body = (
        Op.SSTORE(
            key=0x0, value=Op.CREATE(value=1, offset=0, size=initcode_size)
        )
        + Op.MSTORE(offset=COUNTER, value=Op.ADD(Op.MLOAD(offset=COUNTER), 1))
        + Op.JUMP(pc=0)
    )
    loop_head_size = len(
        Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0],
            condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=COUNTER), count)),
        )
    )
    exit_pc = loop_head_size + len(loop_body)
    code = (
        Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[exit_pc],
            condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=COUNTER), count)),
        )
        + loop_body
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=COUNTER))
        + Op.STOP
    )
    balance = 0xFFFFFFFFFFFFF
    contract = pre.deploy_contract(code=code, balance=balance)
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=SHORT_TX_GAS if short_gas else TX_GAS,
        value=10,
    )

    created = [
        compute_create_address(address=contract, nonce=nonce)
        for nonce in range(1, count + 1)
    ]
    post: dict = {}
    if short_gas or initcode_size > fork.max_initcode_size():
        post[contract] = Account(storage={}, nonce=1, balance=balance)
        post[created[0]] = Account.NONEXISTENT
    else:
        post[contract] = Account(
            storage={0: created[-1], 1: count},
            nonce=1 + count,
            balance=balance + tx.value - count,
        )
        for address in created:
            post[address] = Account(code=b"", balance=1, nonce=1)

    state_test(pre=pre, post=post, tx=tx)
