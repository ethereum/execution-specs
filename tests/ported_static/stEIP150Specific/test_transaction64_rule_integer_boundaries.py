"""
Danno Ferrin danno.ferrin@gmail.com.

Ported from:
tests/static/state_tests/stEIP150Specific
Transaction64Rule_integerBoundariesFiller.yml
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
        "tests/static/state_tests/stEIP150Specific/Transaction64Rule_integerBoundariesFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "000000000000000000000000000000007fffffffffffffffffffffffffffffff",
            {
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={0: 1, 1: 1, 2: 1, 3: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000007fff",
            {
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={0: 1, 1: 1, 2: 1, 3: 1}
                )
            },
        ),
        (
            "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            {
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={0: 1, 1: 1, 2: 1, 3: 1}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000007fffffff",
            {
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={0: 1, 1: 1, 2: 1, 3: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000007fffffffffffffff",
            {
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={0: 1, 1: 1, 2: 1, 3: 1}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000007f",
            {
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={0: 1, 1: 1, 2: 1, 3: 1}
                )
            },
        ),
        (
            "000000000000000000000000000000008fffffffffffffffffffffffffffffff",
            {
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={0: 1, 1: 1, 2: 1, 3: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000008fff",
            {
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={0: 1, 1: 1, 2: 1, 3: 1}
                )
            },
        ),
        (
            "8fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
            {
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={0: 1, 1: 1, 2: 1, 3: 1}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000008fffffff",
            {
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={0: 1, 1: 1, 2: 1, 3: 1}
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000008fffffffffffffff",
            {
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={0: 1, 1: 1, 2: 1, 3: 1}
                )
            },
        ),
        (
            "000000000000000000000000000000000000000000000000000000000000008f",
            {
                Address("0x000000000000000000000000000000000000c0de"): Account(
                    storage={0: 1, 1: 1, 2: 1, 3: 1}
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_transaction64_rule_integer_boundaries(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Danno Ferrin danno.ferrin@gmail.com."""
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
        code=Op.PUSH1[0x0] + Op.PUSH1[0xFF] + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    # Source: Yul
    # {
    #   let initialgas := gas()
    #   let callgas := calldataload(0)
    #
    #   pop(call(callgas, 0x1000, 0, 0, 0, 0, 0x20))
    #   sstore(0, lt(gas(), initialgas))
    #
    #   pop(callcode(callgas, 0x1000, 0, 0, 0, 0, 0x20))
    #   sstore(1, lt(gas(), initialgas))
    #
    #   pop(delegatecall(callgas, 0x1000, 0, 0x20, 0, 0x20))
    #   sstore(2, lt(gas(), initialgas))
    #
    #   pop(staticcall(callgas, 0x1000, 0, 0x20, 0, 0x20))
    #   sstore(3, lt(gas(), initialgas))
    # }
    contract = pre.deploy_contract(
        code=(
            Op.GAS
            + Op.PUSH1[0x20]
            + Op.PUSH1[0x0]
            + Op.DUP2
            + Op.DUP2
            + Op.PUSH2[0x1000]
            + Op.CALLDATALOAD(offset=Op.DUP2)
            + Op.POP(
                Op.CALL(
                    gas=Op.DUP7,
                    address=Op.DUP7,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP4,
                    ret_size=Op.DUP4,
                ),
            )
            + Op.SSTORE(key=Op.DUP4, value=Op.LT(Op.GAS, Op.DUP7))
            + Op.POP(
                Op.CALLCODE(
                    gas=Op.DUP7,
                    address=Op.DUP7,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP4,
                    ret_size=Op.DUP4,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.LT(Op.GAS, Op.DUP7))
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.DUP6,
                    address=Op.DUP6,
                    args_offset=Op.DUP2,
                    args_size=Op.DUP2,
                    ret_offset=Op.DUP4,
                    ret_size=Op.DUP4,
                ),
            )
            + Op.SSTORE(key=0x2, value=Op.LT(Op.GAS, Op.DUP7))
            + Op.POP(Op.STATICCALL)
            + Op.GAS
            + Op.SSTORE(key=0x3, value=Op.LT)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000c0de"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x10000000000000000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=800000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
