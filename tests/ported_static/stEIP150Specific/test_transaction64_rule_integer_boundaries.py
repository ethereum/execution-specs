"""
Danno Ferrin danno.ferrin@gmail.com.

Ported from:
state_tests/stEIP150Specific/Transaction64Rule_integerBoundariesFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
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
    [
        "state_tests/stEIP150Specific/Transaction64Rule_integerBoundariesFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="int8",
        ),
        pytest.param(
            1,
            0,
            0,
            id="uint8",
        ),
        pytest.param(
            2,
            0,
            0,
            id="int16",
        ),
        pytest.param(
            3,
            0,
            0,
            id="uint16",
        ),
        pytest.param(
            4,
            0,
            0,
            id="int32",
        ),
        pytest.param(
            5,
            0,
            0,
            id="uint32",
        ),
        pytest.param(
            6,
            0,
            0,
            id="int64",
        ),
        pytest.param(
            7,
            0,
            0,
            id="uint64",
        ),
        pytest.param(
            8,
            0,
            0,
            id="int128",
        ),
        pytest.param(
            9,
            0,
            0,
            id="uint128",
        ),
        pytest.param(
            10,
            0,
            0,
            id="int256",
        ),
        pytest.param(
            11,
            0,
            0,
            id="uint256",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_transaction64_rule_integer_boundaries(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Danno Ferrin danno."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x0000000000000000000000000000000000001000)
    contract_1 = Address(0x000000000000000000000000000000000000C0DE)
    sender = pre.fund_eoa(amount=0x10000000000000000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw
    # 0x600060FF00
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0] + Op.PUSH1[0xFF] + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: yul
    # berlin
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
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.GAS
        + Op.PUSH1[0x20]
        + Op.PUSH1[0x0]
        + Op.DUP2 * 2
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
            )
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
            )
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
            )
        )
        + Op.SSTORE(key=0x2, value=Op.LT(Op.GAS, Op.DUP7))
        + Op.POP(Op.STATICCALL)
        + Op.GAS
        + Op.SSTORE(key=0x3, value=Op.LT)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
    )

    tx_data = [
        Hash(0x7F),
        Hash(0x8F),
        Hash(0x7FFF),
        Hash(0x8FFF),
        Hash(0x7FFFFFFF),
        Hash(0x8FFFFFFF),
        Hash(0x7FFFFFFFFFFFFFFF),
        Hash(0x8FFFFFFFFFFFFFFF),
        Hash(0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
        Hash(0x8FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),
        Hash(
            0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
        Hash(
            0x8FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ),
    ]
    tx_gas = [800000]

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {contract_1: Account(storage={0: 1, 1: 1, 2: 1, 3: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
