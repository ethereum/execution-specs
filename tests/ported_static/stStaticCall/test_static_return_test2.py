"""
test_static_return_test2

Ported from:
state_tests/stStaticCall/static_ReturnTest2Filler.json
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
    ["state_tests/stStaticCall/static_ReturnTest2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_return_test2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_return_test2"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x194f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_1 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000,
    )

    # Source: lll
    # {(MSTORE 0 0x15)(STATICCALL 7000 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 32 32 32) [[0]](MLOAD 0) [[1]](MLOAD 32) (RETURN 0 64)}
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x15)
        + Op.POP(Op.STATICCALL(gas=0x1b58, address=0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b, args_offset=0x0, args_size=0x20, ret_offset=0x20, ret_size=0x20))
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.RETURN(offset=0x0, size=0x40) + Op.STOP,
        nonce=0,
        address=Address("0x194f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5f5e100)
    # Source: lll
    # {(MSTORE 0 (MUL 3 (CALLDATALOAD 0)))(RETURN 0 32)}
    contract_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.MUL(0x3, Op.CALLDATALOAD(offset=0x0)))
        + Op.RETURN(offset=0x0, size=0x20) + Op.STOP,
        balance=0x186a0,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=250000,
        nonce=0,
        gas_price=10,
    )

    post = {contract_0: Account(storage={0: 21, 1: 63})}

    state_test(env=env, pre=pre, post=post, tx=tx)
