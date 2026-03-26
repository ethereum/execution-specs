"""
test_deleagate_call_after_value_transfer

Ported from:
state_tests/stDelegatecallTestHomestead/deleagateCallAfterValueTransferFiller.json
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
    ["state_tests/stDelegatecallTestHomestead/deleagateCallAfterValueTransferFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_deleagate_call_after_value_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_deleagate_call_after_value_transfer"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x3722faab4d25b944622d559ea4bcf38b4bcf3caf07a6d2c6fd99321c1a66c974
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
    # { (MSTORE 0 0x01) (DELEGATECALL 100000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x1)
        + Op.DELEGATECALL(gas=0x186a0, address=0x346aa231cb52f55ddf201dc19ca469cc73e6495, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40)
        + Op.STOP,
        balance=0x10c8e0,
        nonce=0,
        address=Address("0xdd657898b318b3d967472eaa82bb75c4141b6735"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 (CALLVALUE)) (SSTORE 1 (CALLER)) (SSTORE 2 (CALLDATALOAD 0)) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALLVALUE)
        + Op.SSTORE(key=0x1, value=Op.CALLER)
        + Op.SSTORE(key=0x2, value=Op.CALLDATALOAD(offset=0x0)) + Op.STOP,
        nonce=0,
        address=Address("0x0346aa231cb52f55ddf201dc19ca469cc73e6495"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2386f26fc10000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=453081,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={
            0: 0,
            1: 0x6fda566d1950d7e0a4dac1de87109b2ca7d12da4,
            2: 1,
        },
            ),
        addr_0x1000000000000000000000000000000000000001: Account(storage={0: 0, 1: 0, 2: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
