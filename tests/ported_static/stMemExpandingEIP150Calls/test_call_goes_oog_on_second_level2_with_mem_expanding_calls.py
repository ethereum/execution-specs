"""
test_call_goes_oog_on_second_level2_with_mem_expanding_calls

Ported from:
state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevel2WithMemExpandingCallsFiller.json
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
    ["state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevel2WithMemExpandingCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_goes_oog_on_second_level2_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_goes_oog_on_second_level2_with_mem_expanding_calls"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xb51075bb33d347a23b516e327e1b71c54f63faa192d1d94b62c76e0c26cf98a
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xe8d4a510000)
    # Source: hex
    # 0x5a6008555a6009555a600a55
    addr_0x1000000000000000000000000000000000000114 = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS) + Op.SSTORE(key=0x9, value=Op.GAS)  # noqa: E501
        + Op.SSTORE(key=0xa, value=Op.GAS),
        nonce=0,
        address=Address("0x96983de02bfbcb5d0f4e0ee98fdde6d6f0c75fe0"),  # noqa: E501
    )
    # Source: hex
    # 0x5a60085560ff60ff60ff60ff600073<contract:0x1000000000000000000000000000000000000114>620927c0f1600955
    addr_0x1000000000000000000000000000000000000113 = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(key=0x9, value=Op.CALL(gas=0x927c0, address=0x96983de02bfbcb5d0f4e0ee98fdde6d6f0c75fe0, value=0x0, args_offset=0xff, args_size=0xff, ret_offset=0xff, ret_size=0xff)),  # noqa: E501
        nonce=0,
        address=Address("0xc10a98222464b07008ceb5a0ec44ed49920addda"),  # noqa: E501
    )
    # Source: hex
    # 0x5a60085560ff60ff60ff60ff600073<contract:0x1000000000000000000000000000000000000113>620927c0f1600955
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(key=0x9, value=Op.CALL(gas=0x927c0, address=0xc10a98222464b07008ceb5a0ec44ed49920addda, value=0x0, args_offset=0xff, args_size=0xff, ret_offset=0xff, ret_size=0xff)),  # noqa: E501
        nonce=0,
        address=Address("0x0700bb425d7d4c412ac658014015bd6c98652dc4"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=160000,
        nonce=0,
        gas_price=10,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={}),
        addr_0x1000000000000000000000000000000000000113: Account(storage={}),
        addr_0x1000000000000000000000000000000000000114: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
