"""
test_callcodecallcallcode_101_suicide_end

Ported from:
state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_SuicideEndFiller.json
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
    ["state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_SuicideEndFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcallcode_101_suicide_end(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_callcodecallcallcode_101_suicide_end"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (DELEGATECALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.DELEGATECALL(gas=0x249f0, address=0x77b749ffff7ec61d31c79ed104f230a7959b2879, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x2b30b637f37e3f5b8ca4ab846331d0779a3f4671"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.CALL(gas=0x186a0, address=0xac521409e2fa9526bfe6b827805783d2e307c4ce, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0x77b749ffff7ec61d31c79ed104f230a7959b2879"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 2 ]] (DELEGATECALL 50000 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (SELFDESTRUCT <contract:0x1000000000000000000000000000000000000001>) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=Op.DELEGATECALL(gas=0xc350, address=0x73b954ebc05bb0ff4a0f6a13a054d50ad1584099, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SELFDESTRUCT(address=0x77b749ffff7ec61d31c79ed104f230a7959b2879)
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0xac521409e2fa9526bfe6b827805783d2e307c4ce"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0x73b954ebc05bb0ff4a0f6a13a054d50ad1584099"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=3000000,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={0: 1, 1: 1, 2: 0, 3: 0}),
        addr_0x1000000000000000000000000000000000000001: Account(storage={1: 0, 3: 0}),
        addr_0x1000000000000000000000000000000000000002: Account(storage={2: 1, 3: 1}, balance=0),
        addr_0x1000000000000000000000000000000000000003: Account(storage={3: 0}),
        sender: Account(storage={1: 0, 2: 0, 3: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
