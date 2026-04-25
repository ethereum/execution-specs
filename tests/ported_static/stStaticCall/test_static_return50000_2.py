"""
Test_static_return50000_2.

Ported from:
state_tests/stStaticCall/static_Return50000_2Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_Return50000_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_return50000_2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_return50000_2."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89250000,
    )

    # Source: lll
    # { (MSTORE 0 (CALLDATALOAD 49999)) (RETURN (MLOAD 0) 1) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0xC34F))
        + Op.RETURN(offset=Op.MLOAD(offset=0x0), size=0x1)
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) [[ 0 ]] (STATICCALL 1564 <contract:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 50000 0 0) ) [[ 1 ]] @i }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x3D, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x61C,
                address=addr,
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
    )
    # Source: lll
    # { [[ 0 ]] (CALL (GAS) <contract:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[ 1 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=Op.GAS,
                address=addr_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=15500000,
        value=10,
    )

    post = {
        target: Account(storage={0: 1, 1: 1}, nonce=0),
        addr_2: Account(
            storage={0: 1, 1: 50000},
            balance=0xFFFFFFFFFFFFF,
            nonce=0,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
