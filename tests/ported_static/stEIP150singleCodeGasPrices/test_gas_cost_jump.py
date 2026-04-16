"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP150singleCodeGasPrices/gasCostJumpFiller.yml
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
    ["state_tests/stEIP150singleCodeGasPrices/gasCostJumpFiller.yml"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_gas_cost_jump(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x0000000000000000000000000000000000001000)
    contract_1 = Address(0x0000000000000000000000000000000000002000)
    contract_2 = Address(0x0000000000000000000000000000000000003000)
    contract_3 = Address(0x0000000000000000000000000000000000004000)
    contract_4 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw
    # 0x600060005B5B00
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0] * 2 + Op.JUMPDEST * 2 + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: raw
    # 0x60006005565B00
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0] + Op.JUMP(pc=0x5) + Op.JUMPDEST + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000002000),  # noqa: E501
    )
    # Source: raw
    # 0x60016005575B00
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0x5, condition=0x1) + Op.JUMPDEST + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000003000),  # noqa: E501
    )
    # Source: raw
    # 0x60006005575B00
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(pc=0x5, condition=0x0) + Op.JUMPDEST + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000004000),  # noqa: E501
    )
    # Source: lll
    # {
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Initialization
    #
    #   ; Variables (0x20 byte wide)
    #   (def 'gasB4             0x000)  ; Before the action being measured
    #
    #   ; Gas cost for a baseline operation (call a contract that does mstore
    #   ; and then mload)
    #   (def 'gasBaseline       0x020)
    #
    #   ; Gas for for the action intself (call a contract plus <whatever>)
    #   (def 'gasAction         0x040)
    #
    #   ; Understand CALLDATA. It is four bytes of function
    #   ; selector (irrelevant) followed by 32 byte words
    #   ; of the parameters
    #   (def 'action        $4 )
    #   (def 'expectedCost  $36)
    #
    #   ; Constants
    #   (def  'NOP    0) ; No operation (for if statements)
    #
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Define the actions
    #
    #   ; Store the gas amount
    #   (def 'gas0 [gasB4]    (gas))
    #
    #   ; Get the baseline cost
    # ... (51 more lines)
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=contract_0,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x20, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.JUMPI(pc=0x2E, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x1))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x4E)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x40, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x5E, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x2))
        + Op.POP(0x0)
        + Op.JUMP(pc=0x7E)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x40, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x8E, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3))
        + Op.POP(0x0)
        + Op.JUMP(pc=0xAE)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x40, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.JUMPDEST
        + Op.SSTORE(
            key=0x0,
            value=Op.SUB(
                Op.SUB(Op.MLOAD(offset=0x40), Op.MLOAD(offset=0x20)),
                Op.CALLDATALOAD(offset=0x24),
            ),
        )
        + Op.STOP,
        storage={0: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
    )

    tx_data = [
        Bytes("c5b5a1ae") + Hash(0x1) + Hash(0x4),
        Bytes("c5b5a1ae") + Hash(0x2) + Hash(0x6),
        Bytes("c5b5a1ae") + Hash(0x3) + Hash(0x6),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_4,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {contract_4: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
