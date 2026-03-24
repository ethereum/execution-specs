"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP150singleCodeGasPrices/gasCostJumpFiller.yml
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stEIP150singleCodeGasPrices/gasCostJumpFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000030000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
            {},
        ),
    ],
    ids=["case0", "case1", "case2"],
)
@pytest.mark.pre_alloc_mutable
def test_gas_cost_jump(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.JUMPDEST + Op.JUMPDEST + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.JUMP(pc=0x5) + Op.JUMPDEST + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000002000"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.JUMPI(pc=0x5, condition=0x1) + Op.JUMPDEST + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000003000"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.JUMPI(pc=0x5, condition=0x0) + Op.JUMPDEST + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000004000"),  # noqa: E501
    )
    # Source: LLL
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
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.CALL(
                    gas=0x10000,
                    address=0x1000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(
                offset=0x20, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS)
            )
            + Op.JUMPI(
                pc=0x2E, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x1)
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x4E)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.CALL(
                    gas=0x10000,
                    address=0x2000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(
                offset=0x40, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS)
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x5E, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x2)
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0x7E)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.CALL(
                    gas=0x10000,
                    address=0x3000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(
                offset=0x40, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS)
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x8E, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3)
            )
            + Op.POP(0x0)
            + Op.JUMP(pc=0xAE)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.CALL(
                    gas=0x10000,
                    address=0x4000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(
                offset=0x40, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS)
            )
            + Op.JUMPDEST
            + Op.SSTORE(
                key=0x0,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x40), Op.MLOAD(offset=0x20)),
                    Op.CALLDATALOAD(offset=0x24),
                ),
            )
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
