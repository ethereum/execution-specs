"""
Test_stack_overflow.

Ported from:
state_tests/stStackTests/stackOverflowFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStackTests/stackOverflowFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7",
        ),
        pytest.param(
            8,
            0,
            0,
            id="d8",
        ),
        pytest.param(
            9,
            0,
            0,
            id="d9",
        ),
        pytest.param(
            10,
            0,
            0,
            id="d10",
        ),
        pytest.param(
            11,
            0,
            0,
            id="d11",
        ),
        pytest.param(
            12,
            0,
            0,
            id="d12",
        ),
        pytest.param(
            13,
            0,
            0,
            id="d13",
        ),
        pytest.param(
            14,
            0,
            0,
            id="d14",
        ),
        pytest.param(
            15,
            0,
            0,
            id="d15",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_stack_overflow(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_stack_overflow."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    pre[contract_0] = Account(balance=0xE8D4A5100000000000)
    pre[sender] = Account(balance=0xE8D4A5100000000000)

    tx_data = [
        Op.ADDRESS * 1025,
        Op.ORIGIN * 1025,
        Op.CALLER * 1025,
        Op.CALLVALUE * 1025,
        Op.CALLDATASIZE * 1025,
        Op.CODESIZE * 1025,
        Op.GASPRICE * 1025,
        Op.COINBASE * 1025,
        Op.TIMESTAMP * 1025,
        Op.NUMBER * 1025,
        Op.PREVRANDAO * 1025,
        Op.GASLIMIT * 1025,
        Op.PC * 1025,
        Op.MSIZE * 1025,
        Op.GAS * 1025,
        Op.PUSH1[0x0] * 1025,
    ]
    tx_gas = [6000000]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
