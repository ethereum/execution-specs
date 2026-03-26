"""
test_raw_delegate_call_gas

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasFiller.json
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
    ["state_tests/stEIP150singleCodeGasPrices/RawDelegateCallGasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_raw_delegate_call_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_raw_delegate_call_gas"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { [[2]] (GAS) }
    addr_0x094f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address("0xe497cd0909c3691e0b6d2a42e26f36696fc27ba5"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { [0] (GAS) (DELEGATECALL 30000 <contract:0x094f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[1]] (SUB @0 (GAS)) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.DELEGATECALL(gas=0x7530, address=0xe497cd0909c3691e0b6d2a42e26f36696fc27ba5, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
        address=Address("0x8dfc4f381eee03447d510a61a1266821a480bd85"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=500000,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0x094f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}),
        target: Account(storage={1: 24736, 2: 29998}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
