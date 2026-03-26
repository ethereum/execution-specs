"""
CALLCODE -> (CALL -> code) (suicide)

Ported from:
state_tests/stCallCodes/callcodecall_10_SuicideEndFiller.json
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
    ["state_tests/stCallCodes/callcodecall_10_SuicideEndFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecall_10_suicide_end(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALLCODE -> (CALL -> code) (suicide)"""
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
        code=Op.SSTORE(key=0x0, value=Op.CALLCODE(gas=0x249f0, address=0xf741cfee7b7fb1025dccef3db5a3cbc8ffb776f8, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xa74ca10b765dcda3b60687f73f2881e2a56eda64"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (CALL 50000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) (SELFDESTRUCT <contract:target:0x1000000000000000000000000000000000000000>) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.CALL(gas=0xc350, address=0x703b936fd4d674f0ff5d6957f61097152f8781b8, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SELFDESTRUCT(address=0xa74ca10b765dcda3b60687f73f2881e2a56eda64)
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0xf741cfee7b7fb1025dccef3db5a3cbc8ffb776f8"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 2 1) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x1) + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0x703b936fd4d674f0ff5d6957f61097152f8781b8"),  # noqa: E501
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
        addr_0x1000000000000000000000000000000000000001: Account(storage={0: 0, 1: 0}, balance=0x2540be400),
        addr_0x1000000000000000000000000000000000000002: Account(storage={2: 1}, balance=0x2540be400),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
