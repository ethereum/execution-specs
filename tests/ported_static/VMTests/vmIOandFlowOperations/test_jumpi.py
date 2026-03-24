"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmIOandFlowOperations/jumpiFiller.yml
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
    ["tests/static/state_tests/VMTests/vmIOandFlowOperations/jumpiFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "693c61390000000000000000000000000000000000000000000000000000000000001005",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000100a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000001009",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000001007",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000001006",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000001008",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000001001",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000001003",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000100d",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000100e",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000100f",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000001000",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000100b",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000100c",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000001004",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000001002",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000110",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000111",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000208",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000201",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000203",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000020d",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000020e",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000020f",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000200",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000202",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
        "case8",
        "case9",
        "case10",
        "case11",
        "case12",
        "case13",
        "case14",
        "case15",
        "case16",
        "case17",
        "case18",
        "case19",
        "case20",
        "case21",
        "case22",
        "case23",
        "case24",
        "case25",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_jumpi(
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
            Op.JUMPI(pc=0xE, condition=0x1)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000110"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.MSTORE(offset=0x0, value=0x10)
            + Op.JUMPDEST
            + Op.SUB(Op.MLOAD(offset=0x0), 0x1)
            + Op.MSTORE(offset=0x0, value=Op.DUP1)
            + Op.PUSH1[0xB]
            + Op.JUMPI
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000111"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x0)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000200"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x0)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000201"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x6, condition=0x0)
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000202"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=0xFFFFFFF, condition=0x0)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000203"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=Op.ADD(0x5, 0x4), condition=0x0)
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000208"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x1000000000000000D, condition=0x0)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000020d"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x100000009, condition=0x0)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000020e"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   @0 (- 0 1)
    #   (asm 0 0 mload jumpi 0x600D 0x00 sstore)
    # }
    pre.deploy_contract(
        code=(
            Op.POP(Op.MLOAD(offset=0x0))
            + Op.POP(Op.SUB(0x0, 0x1))
            + Op.JUMPI(pc=Op.MLOAD(offset=0x0), condition=0x0)
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000020f"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=Op.MUL(0x20, 0x10), condition=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x6, condition=0x1)
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=0xFFFFFFF, condition=0xFF)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x23]
            + Op.JUMPI(pc=0x8, condition=0x1)
            + Op.PUSH1[0x1]
            + Op.JUMPDEST
            + Op.PUSH1[0x2]
            + Op.SSTORE
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x6, condition=0x6)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.PUSH2[0x600D]
            + Op.JUMPI(pc=0xA, condition=0x1)
            + Op.PUSH1[0xFF]
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SSTORE
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMP(pc=0xB)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x3, condition=0x1)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001007"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=Op.ADD(0x5, 0x4), condition=0x1)
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001008"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x7, condition=0x1)
            + Op.STOP
            + Op.PUSH1[0x5B]
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001009"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x7, condition=0x1)
            + Op.STOP
            + Op.PUSH1[0x1]
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100a"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=0xD, condition=0x1)
            + Op.GAS
            + Op.JUMPDEST
            + Op.SSTORE(key=0x1, value=Op.GAS)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPI(pc=0xB, condition=0x1)
            + Op.GAS
            + Op.JUMPDEST
            + Op.SSTORE(key=0x1, value=Op.GAS)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x1000000000000000D, condition=0x11)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100d"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0x100000009, condition=0x11)
            + Op.JUMPDEST
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=0x600D)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100e"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   @0 (- 0 1)
    #   (asm 1 0 mload jumpi 0x600D 0x00 sstore)
    # }
    pre.deploy_contract(
        code=(
            Op.POP(Op.MLOAD(offset=0x0))
            + Op.POP(Op.SUB(0x0, 0x1))
            + Op.JUMPI(pc=Op.MLOAD(offset=0x0), condition=0x1)
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100f"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)
    # Source: LLL
    # {
    #     ; limited gas because of the endless loop
    #     (delegatecall 0x10000 $4 0 0 0 0)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=0x10000,
                address=Op.CALLDATALOAD(offset=0x4),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        storage={0x0: 0xBAD},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

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
