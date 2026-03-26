"""
test_call_goes_oog_on_second_level_with_mem_expanding_calls

Ported from:
state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevelWithMemExpandingCallsFiller.json
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
    ["state_tests/stMemExpandingEIP150Calls/CallGoesOOGOnSecondLevelWithMemExpandingCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_goes_oog_on_second_level_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_goes_oog_on_second_level_with_mem_expanding_calls"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x8d19f2b0d2f5689c1771fbca70476ca6e877a81ee15c3733de87fae38e5abcef
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

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: hex
    # 0x5a60085560ff60ff60ff60ff600073<contract:0x1000000000000000000000000000000000000110>620927c0f1600955
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(key=0x9, value=Op.CALL(gas=0x927c0, address=0xa27e20572430916b3d6772b27329cc460224904d, value=0x0, args_offset=0xff, args_size=0xff, ret_offset=0xff, ret_size=0xff)),  # noqa: E501
        nonce=0,
        address=Address("0xaf229807016a538dfcdab92a53337de38178d40f"),  # noqa: E501
    )
    # Source: hex
    # 0x5a600855600060006000f050600060006000f0505a6009555a600a55
    addr_0x1000000000000000000000000000000000000111 = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.POP(Op.CREATE(value=0x0, offset=0x0, size=0x0)) * 2
        + Op.SSTORE(key=0x9, value=Op.GAS) + Op.SSTORE(key=0xa, value=Op.GAS),
        nonce=0,
        address=Address("0x2ef686162bebf2542147767d5be471976860cceb"),  # noqa: E501
    )
    # Source: hex
    # 0x5a60085560ff60ff60ff60ff600073<contract:0x1000000000000000000000000000000000000111>620927c0f1600955
    addr_0x1000000000000000000000000000000000000110 = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(key=0x9, value=Op.CALL(gas=0x927c0, address=0x2ef686162bebf2542147767d5be471976860cceb, value=0x0, args_offset=0xff, args_size=0xff, ret_offset=0xff, ret_size=0xff)),  # noqa: E501
        nonce=0,
        address=Address("0xa27e20572430916b3d6772b27329cc460224904d"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=220000,
        nonce=0,
        gas_price=10,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={8: 0x30956}),
        addr_0x1000000000000000000000000000000000000110: Account(storage={}),
        addr_0x1000000000000000000000000000000000000111: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
