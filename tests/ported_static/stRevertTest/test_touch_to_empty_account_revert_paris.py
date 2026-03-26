"""
test_touch_to_empty_account_revert_paris

Ported from:
state_tests/stRevertTest/TouchToEmptyAccountRevert_ParisFiller.json
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
    ["state_tests/stRevertTest/TouchToEmptyAccountRevert_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_touch_to_empty_account_revert_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_touch_to_empty_account_revert_paris"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    addr_0x1000000000000000000000000000000000000000 = Address("0x76fae819612a29489a1a43208613d8f8557b8898")  # noqa: E501
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
    pre[addr_0x1000000000000000000000000000000000000000] = Account(balance=10)
    # Source: lll
    # { [[0]](CALL 30000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] 1 }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0x7530, address=0xba4d09eb64fddcec11d7587e1f51ac0b07c5069c, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x68b5e303da0ad3dfba8b2134bab64274de666f37"),  # noqa: E501
    )
    # Source: lll
    # { [[1]](CALL 30000 <eoa:0x1000000000000000000000000000000000000000> 0 0 0 0 0) }
    addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.CALL(gas=0x7530, address=0x76fae819612a29489a1a43208613d8f8557b8898, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0xba4d09eb64fddcec11d7587e1f51ac0b07c5069c"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=70000,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0x1000000000000000000000000000000000000000: Account(storage={}, code=b"", balance=10, nonce=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
