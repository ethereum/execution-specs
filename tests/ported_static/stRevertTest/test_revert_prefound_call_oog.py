"""
test_revert_prefound_call_oog

Ported from:
state_tests/stRevertTest/RevertPrefoundCallOOGFiller.json
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
    ["state_tests/stRevertTest/RevertPrefoundCallOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_prefound_call_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_revert_prefound_call_oog"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    addr_0x7db299e0885c85039f56fa504a13dd8ce8a56aa7 = Address("0x85fdde91fd0ce22a2968e1f1b2ebb9f9e5a180ba")  # noqa: E501
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
    pre[addr_0x7db299e0885c85039f56fa504a13dd8ce8a56aa7] = Account(balance=1)
    # Source: lll
    # { [[0]] (CALL 50000 <eoa:0x7db299e0885c85039f56fa504a13dd8ce8a56aa7> 0 0 32 0 32) [[1]]12 [[2]]12 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0xc350, address=0x85fdde91fd0ce22a2968e1f1b2ebb9f9e5a180ba, value=0x0, args_offset=0x0, args_size=0x20, ret_offset=0x0, ret_size=0x20))  # noqa: E501
        + Op.SSTORE(key=0x1, value=0xc) + Op.SSTORE(key=0x2, value=0xc) + Op.STOP,  # noqa: E501
        balance=1,
        nonce=0,
        address=Address("0xf679bfe5f61e7640b9a66db191d5d86abc7b5c0a"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=63000,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0x7db299e0885c85039f56fa504a13dd8ce8a56aa7: Account(storage={}, code=b"", balance=1, nonce=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
