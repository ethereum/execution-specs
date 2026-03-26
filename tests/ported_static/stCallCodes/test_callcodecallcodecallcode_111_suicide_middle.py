"""
CALLCODE -> CALLCODE -> (suicide) CALLCODE -> code

Ported from:
state_tests/stCallCodes/callcodecallcodecallcode_111_SuicideMiddleFiller.json
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
    ["state_tests/stCallCodes/callcodecallcodecallcode_111_SuicideMiddleFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcodecallcode_111_suicide_middle(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALLCODE -> CALLCODE -> (suicide) CALLCODE -> code"""
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
    # {  [[ 0 ]] (CALLCODE 150000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALLCODE(gas=0x249f0, address=0xeaf8c2ae0d01a880cea4e1aa88def5edd153d57b, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xa74ca10b765dcda3b60687f73f2881e2a56eda64"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (CALLCODE 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.CALLCODE(gas=0x186a0, address=0x23a077e1e6b0740d6bfbc41de582f2930abd1762, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0xeaf8c2ae0d01a880cea4e1aa88def5edd153d57b"),  # noqa: E501
    )
    # Source: lll
    # {  (SELFDESTRUCT <contract:target:0x1000000000000000000000000000000000000000>) [[ 2 ]] (CALLCODE 50000 <contract:0x1000000000000000000000000000000000000003> 0 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0xa74ca10b765dcda3b60687f73f2881e2a56eda64)
        + Op.SSTORE(key=0x2, value=Op.CALLCODE(gas=0xc350, address=0x73b954ebc05bb0ff4a0f6a13a054d50ad1584099, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0x23a077e1e6b0740d6bfbc41de582f2930abd1762"),  # noqa: E501
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
        addr_0x1000000000000000000000000000000000000001: Account(storage={0: 0, 1: 0, 2: 0}, balance=0x2540be400),
        addr_0x1000000000000000000000000000000000000002: Account(storage={3: 0}, balance=0x2540be400),
        addr_0x1000000000000000000000000000000000000003: Account(storage={3: 0}, balance=0x2540be400),
        target: Account(storage={0: 1, 1: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
