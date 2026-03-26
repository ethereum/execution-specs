"""
test_static_refund_call_a

Ported from:
state_tests/stStaticCall/static_refund_CallAFiller.json
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
    ["state_tests/stStaticCall/static_refund_CallAFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_refund_call_a(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_refund_call_a"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xd28ce7e8c6ca72f9b2dd5aa5c41f48198119e86e443c50de70f3fba602247fe8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { [[ 0 ]] (STATICCALL 5500 <contract:0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa> 0 0 0 0 ) [[ 1 ]] 1}
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.STATICCALL(gas=0x157c, address=0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        storage={1: 1},
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xd15bdaf597badaa25173c995d18f65d1b514a062"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xbebc200)
    # Source: lll
    # { [[ 1 ]] 0 }
    addr_0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x0) + Op.STOP,
        storage={1: 1},
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xf4c9fc42faeda49049e3b8e2b97a17cc2fe95718"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=200000,
        value=10,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={0: 0, 1: 1}, balance=0xde0b6b3a764000a),
        addr_0xaaae7baea6a6c7c4c2dfeb977efac326af552aaa: Account(storage={1: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
