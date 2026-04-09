"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP150singleCodeGasPrices/gasCostExpFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/gasCostExpFiller.yml"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_gas_cost_exp(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # {
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Initialization
    #
    #   ; Variables (0x20 byte wide)
    #   (def 'powerOf           0x000)  ; A to the power of @powerOf
    #   (def 'expectedCost      0x020)  ; Expected gas cost
    #   (def 'gasB4             0x040)  ; Before the action being measured
    #   (def 'gasAfter          0x060)  ; After the action being measured
    #
    #   ; Understand CALLDATA. It is four bytes of function
    #   ; selector (irrelevant) followed by 32 byte words
    #   ; of the parameters
    #   [powerOf]       $4
    #   [expectedCost]  $36
    #
    #
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Run the operation
    #   [gasB4]    (gas)
    #   (exp 2 @powerOf)
    #   [gasAfter] (gas)
    #
    #
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Return value
    #
    #   [[0]] (- @gasB4 @gasAfter @expectedCost)
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x4))
        + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x24))
        + Op.MSTORE(offset=0x40, value=Op.GAS)
        + Op.POP(Op.EXP(0x2, Op.MLOAD(offset=0x0)))
        + Op.MSTORE(offset=0x60, value=Op.GAS)
        + Op.SSTORE(
            key=0x0,
            value=Op.SUB(
                Op.SUB(Op.MLOAD(offset=0x40), Op.MLOAD(offset=0x60)),
                Op.MLOAD(offset=0x20),
            ),
        )
        + Op.STOP,
        storage={0: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
    )

    tx_data = [
        Bytes("c5b5a1ae") + Hash(0x0) + Hash(0x20),
        Bytes("c5b5a1ae") + Hash(0x1) + Hash(0x52),
        Bytes("c5b5a1ae") + Hash(0xFF) + Hash(0x52),
        Bytes("c5b5a1ae") + Hash(0x100) + Hash(0x84),
        Bytes("c5b5a1ae") + Hash(0xFFFF) + Hash(0x84),
        Bytes("c5b5a1ae") + Hash(0x10000) + Hash(0xB6),
        Bytes("c5b5a1ae") + Hash(0xFFFFFF) + Hash(0xB6),
        Bytes("c5b5a1ae") + Hash(0x1000000) + Hash(0xE8),
        Bytes("c5b5a1ae") + Hash(0xFFFFFFFF) + Hash(0xE8),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {target: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
