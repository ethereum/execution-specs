"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmArithmeticTest/sdivFiller.yml
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
    ["tests/static/state_tests/VMTests/vmArithmeticTest/sdivFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000000b",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000000c",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000000100c"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000001000"): Account(
                    storage={
                        0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
                    }
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000006",  # noqa: E501
            {},
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000001005"): Account(
                    storage={
                        0: 0x8000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000000f",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000000100f"): Account(
                    storage={
                        0: 0x8000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000001003"): Account(
                    storage={
                        0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE  # noqa: E501
                    }
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000001004"): Account(
                    storage={
                        0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
                    }
                )
            },
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000000e",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000000100e"): Account(
                    storage={
                        0: 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
                    }
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000001001"): Account(
                    storage={
                        0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
                    }
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000009",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000001009"): Account(
                    storage={
                        0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
                    }
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000007",  # noqa: E501
            {},
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000010",  # noqa: E501
            {},
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000008",  # noqa: E501
            {
                Address("0x0000000000000000000000000000000000001008"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000000a",  # noqa: E501
            {},
        ),
        (
            "693c6139000000000000000000000000000000000000000000000000000000000000000d",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000000100d"): Account(
                    storage={
                        0: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
                    }
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_sdiv(
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
            Op.SSTORE(
                key=0x0,
                value=Op.SDIV(
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    Op.SUB(
                        0x0,
                        0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    ),
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000110"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.SDIV(
                    Op.SUB(
                        0x0,
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    ),
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.SDIV(
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    Op.SUB(
                        0x0,
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    ),
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0, value=Op.SDIV(Op.SUB(0x0, 0x2), Op.SUB(0x0, 0x4))
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SDIV(0x4, Op.SUB(0x0, 0x2))) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SDIV(0x5, Op.SUB(0x0, 0x4))) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.SDIV(
                    Op.SUB(
                        0x0,
                        0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    ),
                    Op.SUB(0x0, 0x1),
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.SDIV(
                    Op.SUB(
                        0x0,
                        0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    ),
                    0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SDIV(Op.SUB(0x0, 0x1), 0x19)) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001007"),  # noqa: E501
    )
    # Source: LLL
    # {  ; (-1)/(-1) = 1
    #
    #    [[0]] (sdiv (- 0 1) (- 0 1))
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0, value=Op.SDIV(Op.SUB(0x0, 0x1), Op.SUB(0x0, 0x1))
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001008"),  # noqa: E501
    )
    # Source: LLL
    # {  ; (-1)/1 = -1
    #
    #    [[0]] (sdiv (- 0 1) 1)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SDIV(Op.SUB(0x0, 0x1), 0x1)) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001009"),  # noqa: E501
    )
    # Source: LLL
    # {  ; (-3)/0 = 0
    #    ; x/0 = 0 in evm
    #
    #    [[0]] (sdiv (- 0 3) (- 0 0))
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0, value=Op.SDIV(Op.SUB(0x0, 0x3), Op.SUB(0x0, 0x0))
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100a"),  # noqa: E501
    )
    # Source: LLL
    # {  ; (0-(-1))/0 = 0
    #    ;
    #    ; -1 = 2^256-1
    #    (def 'neg1 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)  # noqa: E501
    #
    #    [[0]] (sdiv (- 0 neg1) 0)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.SDIV(
                    Op.SUB(
                        0x0,
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                    ),
                    0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100b"),  # noqa: E501
    )
    # Source: LLL
    # {  ; (0-(-1))/0 + 1 = 1
    #    ;
    #    ; -1 = 2^256-1
    #    (def 'neg1 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)  # noqa: E501
    #
    #    [[0]] (+ (sdiv (- 0 neg1) 0) 1)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.ADD(
                    Op.SDIV(
                        Op.SUB(
                            0x0,
                            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                        ),
                        0x0,
                    ),
                    0x1,
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100c"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.SDIV(Op.SUB(0x0, 0x9), 0x5)) + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100d"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    ; A negative number sdiv -1 is the absolute value of that number
    #    (def 'pow2_255 0x8000000000000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #    (def 'pow2_255_min1 (- pow2_255 1))
    #    [[0]] (sdiv (- 0 pow2_255_min1) (- 0 1))
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.SDIV(
                    Op.SUB(
                        0x0,
                        Op.SUB(
                            0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                            0x1,
                        ),
                    ),
                    Op.SUB(0x0, 0x1),
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100e"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    ; A negative number sdiv -1 is the absolute value of that number
    #    (def 'pow2_255 0x8000000000000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #    [[0]] (sdiv (- 0 pow2_255) (- 0 1))
    #    ; 2^255 = -2^255 in evm (modulo 2^256)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.SDIV(
                    Op.SUB(
                        0x0,
                        0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    ),
                    Op.SUB(0x0, 0x1),
                ),
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100f"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
    # {
    #     (call 0xffffff (+ 0x1000 $4) 0 0 0 0 0)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0xFFFFFF,
                address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
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
