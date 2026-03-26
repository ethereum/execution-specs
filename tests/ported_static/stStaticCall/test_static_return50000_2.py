"""
test_static_return50000_2

Ported from:
state_tests/stStaticCall/static_Return50000_2Filler.json
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
    ["state_tests/stStaticCall/static_Return50000_2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_return50000_2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_return50000_2"""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xe7c72b378297589acee4e0ba3272841bcfc5e220f86de253f890274cfee9e474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=89250000,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff)
    # Source: lll
    # { (MSTORE 0 (CALLDATALOAD 49999)) (RETURN (MLOAD 0) 1) }
    addr_0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0xc34f))
        + Op.RETURN(offset=Op.MLOAD(offset=0x0), size=0x1) + Op.STOP,
        balance=0xfffffffffffff,
        nonce=0,
        address=Address("0x0d08fb89197bd8f97c770ed75e28ed610a3016e9"),  # noqa: E501
    )
    # Source: lll
    # { [[ 0 ]] (CALL (GAS) <contract:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=Op.GAS, address=0xdf43bba207127b641624b20497fa07055f4a3939, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0xfffffffffffff,
        nonce=0,
        address=Address("0x9a8ca98b299a0220faad60948d01ce83ccc97831"),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) [[ 0 ]] (STATICCALL 1564 <contract:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 50000 0 0) ) [[ 1 ]] @i }
    addr_0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.JUMPI(pc=0x3d, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xc350)))
        + Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x61c, address=0xd08fb89197bd8f97c770ed75e28ed610a3016e9, args_offset=0x0, args_size=0xc350, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0) + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80)) + Op.STOP,
        balance=0xfffffffffffff,
        nonce=0,
        address=Address("0xdf43bba207127b641624b20497fa07055f4a3939"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=15500000,
        value=10,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={0: 1, 1: 1}, nonce=0),
        addr_0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                storage={0: 1, 1: 50000},
                balance=0xfffffffffffff,
                nonce=0,
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
