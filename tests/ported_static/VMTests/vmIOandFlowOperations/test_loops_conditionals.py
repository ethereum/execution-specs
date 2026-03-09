"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmIOandFlowOperations
loopsConditionalsFiller.yml
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
        "tests/static/state_tests/VMTests/vmIOandFlowOperations/loopsConditionalsFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={1: 0x10000}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000009",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 55}
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 55}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000007",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={1: 0x10000}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 2989}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={0: 24589}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={1: 0x10000}
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_loops_conditionals(
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

    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0xF, condition=Op.ISZERO(Op.GT(0x1, 0x0)))
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0xF, condition=Op.ISZERO(Op.LT(0x1, 0x0)))
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0xE, condition=Op.GT(0x1, 0x0))
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0xE, condition=Op.LT(0x1, 0x0))
            + Op.SSTORE(key=0x0, value=0x600D)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0xE, condition=Op.GT(0x1, 0x0))
            + Op.PUSH2[0x60A7]
            + Op.JUMP(pc=0x12)
            + Op.JUMPDEST
            + Op.PUSH2[0x600D]
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SSTORE
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPI(pc=0xE, condition=Op.LT(0x1, 0x0))
            + Op.PUSH2[0x60A7]
            + Op.JUMP(pc=0x12)
            + Op.JUMPDEST
            + Op.PUSH2[0x600D]
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.SSTORE
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x10)
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x27, condition=Op.ISZERO(Op.SLOAD(key=0x0)))
            + Op.SSTORE(key=0x0, value=Op.SUB(Op.SLOAD(key=0x0), 0x1))
            + Op.SSTORE(key=0x1, value=Op.MUL(Op.SLOAD(key=0x1), 0x2))
            + Op.JUMP(pc=0xA)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x10)
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x29, condition=Op.EQ(Op.SLOAD(key=0x0), 0x0))
            + Op.SSTORE(key=0x0, value=Op.SUB(Op.SLOAD(key=0x0), 0x1))
            + Op.SSTORE(key=0x1, value=Op.MUL(Op.SLOAD(key=0x1), 0x2))
            + Op.JUMP(pc=0xA)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001007"),  # noqa: E501
    )
    # Source: LLL
    # {
    #     (for
    #       { [[0]] 0x10  [[1]] 0x01 }         ; initialization
    #       (> @@0 0)                          ; predicate
    #       [[0]] (- @@0 1)                    ; post
    #       [[1]] (* @@1 2)                    ; body
    #     )   ; for loop
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x10)
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x2A, condition=Op.ISZERO(Op.GT(Op.SLOAD(key=0x0), 0x0))
            )
            + Op.SSTORE(key=0x1, value=Op.MUL(Op.SLOAD(key=0x1), 0x2))
            + Op.SSTORE(key=0x0, value=Op.SUB(Op.SLOAD(key=0x0), 0x1))
            + Op.JUMP(pc=0xA)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001008"),  # noqa: E501
    )
    # Source: LLL
    # {
    #     (def 'i 0x80)
    #     (def 'j 0xA0)
    #
    #     (for [i] 10        ; init
    #          (> @i 0)      ; predicate
    #          [i] (- @i 1)  ; post
    #          [j] (+ @i @j) ; body
    #     )    ; for loop
    #
    #     [[0]] @j
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x80, value=0xA)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x26,
                condition=Op.ISZERO(Op.GT(Op.MLOAD(offset=0x80), 0x0)),
            )
            + Op.MSTORE(
                offset=0xA0,
                value=Op.ADD(Op.MLOAD(offset=0x80), Op.MLOAD(offset=0xA0)),
            )
            + Op.MSTORE(offset=0x80, value=Op.SUB(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x5)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0xA0))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001009"),  # noqa: E501
    )
    # Source: LLL
    # {
    #     (def 'i 0x80)
    #     (def 'j 0xA0)
    #
    #     (for [i] 0         ; init
    #          (<= @i 10)    ; predicate
    #          [i] (+ @i 1)  ; post
    #          [j] (+ @i @j) ; body
    #     )    ; for loop
    #
    #     [[0]] @j
    # }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x80, value=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x27,
                condition=Op.ISZERO(
                    Op.ISZERO(Op.GT(Op.MLOAD(offset=0x80), 0xA))
                ),
            )
            + Op.MSTORE(
                offset=0xA0,
                value=Op.ADD(Op.MLOAD(offset=0x80), Op.MLOAD(offset=0xA0)),
            )
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x5)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0xA0))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)
    # Source: LLL
    # {
    #     (delegatecall (gas) (+ 0x1000 $4) 0 0 0 0)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
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
