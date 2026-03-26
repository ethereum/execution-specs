"""
test_call_goes_oog_on_second_level2

Ported from:
state_tests/stEIP150Specific/CallGoesOOGOnSecondLevel2Filler.json
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
    ["state_tests/stEIP150Specific/CallGoesOOGOnSecondLevel2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_goes_oog_on_second_level2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_goes_oog_on_second_level2"""
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

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { (SSTORE 8 (GAS)) (SSTORE 9 (CALL 600000 <contract:0x1000000000000000000000000000000000000113> 0 0 0 0 0)) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(key=0x9, value=Op.CALL(gas=0x927c0, address=0xe1d370a0538366eaffbc9fcd571af7b1e80d377c, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0x171742e7809e3b571e899f0d4d9d35cd5deeacf1"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 8 (GAS)) (SSTORE 9 (CALL 600000 <contract:0x1000000000000000000000000000000000000114> 0 0 0 0 0)) }
    addr_0x1000000000000000000000000000000000000113 = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(key=0x9, value=Op.CALL(gas=0x927c0, address=0xbfb2b65e4ef26a144a185b32c7baf39ef8e40b4b, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0xe1d370a0538366eaffbc9fcd571af7b1e80d377c"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 8 (GAS)) (KECCAK256 0x00 0x2fffff) }
    addr_0x1000000000000000000000000000000000000114 = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS) + Op.SHA3(offset=0x0, size=0x2fffff)  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0xbfb2b65e4ef26a144a185b32c7baf39ef8e40b4b"),  # noqa: E501
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
        addr_0x1000000000000000000000000000000000000113: Account(storage={}),
        addr_0x1000000000000000000000000000000000000114: Account(storage={}),
        target: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
