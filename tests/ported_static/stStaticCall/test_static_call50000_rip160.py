"""
Test_static_call50000_rip160.

Ported from:
state_tests/stStaticCall/static_Call50000_rip160Filler.json
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
    ["state_tests/stStaticCall/static_Call50000_rip160Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call50000_rip160(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call50000_rip160."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=39250000000,
    )

    # Source: lll
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLVALUE,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xC0E4183389EB57F779A986D8C878F89B9401DC8E),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) [[ 0 ]] (STATICCALL 78200 3 0 50000 0 0) ) [[ 1 ]] @i}  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x2B, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x13178,
                address=0x3,
                args_offset=0x0,
                args_size=0xC350,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address(0xF50714EA64904A573FEE759CA74A1C3C93FEF59F),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (MSTORE 0 (STATICCALL 78200 3 0 50000 0 0)) ) (MSTORE 32 @i) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x2B, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.MSTORE(
            offset=0x0,
            value=Op.STATICCALL(
                gas=0x13178,
                address=0x3,
                args_offset=0x0,
                args_size=0xC350,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x20, value=Op.MLOAD(offset=0x80))
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address(0x4689CAD8BBC0E90B346E8B4BC385E68BA03F307C),  # noqa: E501
    )

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_2, left_padding=True),
    ]
    tx_gas = [3925000000]
    tx_value = [10]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        sender: Account(storage={}, nonce=1),
        addr: Account(
            storage={0: 0, 1: 0},
            code=bytes.fromhex(
                "5b61c3506080511015602b576000600061c3506000600362013178fa6000556001608051016080526000565b60805160015500"  # noqa: E501
            ),
            nonce=0,
        ),
        target: Account(storage={0: 0, 1: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
