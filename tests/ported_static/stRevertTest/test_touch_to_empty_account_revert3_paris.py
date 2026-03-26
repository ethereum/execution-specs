"""
test_touch_to_empty_account_revert3_paris

Ported from:
state_tests/stRevertTest/TouchToEmptyAccountRevert3_ParisFiller.json
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
    ["state_tests/stRevertTest/TouchToEmptyAccountRevert3_ParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_touch_to_empty_account_revert3_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_touch_to_empty_account_revert3_paris"""
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
    # { [[0]](CALL 130000 <contract:0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[1]](CALL 130000 <contract:0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALL(gas=0x1fbd0, address=0x51cd6399de7e11930d3aa146d45a2e327b5894b9, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.CALL(gas=0x1fbd0, address=0x2620916b2f3d6b185f4d9dd1ecee4a1f665d5c36, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0xcd48e0c45933cfa7aa1345807cf2d6b02875f627"),  # noqa: E501
    )
    # Source: lll
    # { [[2]](CALL 100000 <contract:0xe94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) (KECCAK256 0x00 0x2fffff) }
    addr_0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=Op.CALL(gas=0x186a0, address=0x28207e524ccb9dbc79bb3044819acd87d630f27a, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SHA3(offset=0x0, size=0x2fffff) + Op.STOP,
        nonce=0,
        address=Address("0x2620916b2f3d6b185f4d9dd1ecee4a1f665d5c36"),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <eoa:0x1000000000000000000000000000000000000000>) }
    addr_0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x76fae819612a29489a1a43208613d8f8557b8898)
        + Op.STOP,
        nonce=0,
        address=Address("0x51cd6399de7e11930d3aa146d45a2e327b5894b9"),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <eoa:0x1000000000000000000000000000000000000000>) }
    addr_0xe94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x76fae819612a29489a1a43208613d8f8557b8898)
        + Op.STOP,
        nonce=0,
        address=Address("0x28207e524ccb9dbc79bb3044819acd87d630f27a"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=200000,
        nonce=0,
        gas_price=10,
    )

    post = {addr_0x1000000000000000000000000000000000000000: Account(balance=10)}

    state_test(env=env, pre=pre, post=post, tx=tx)
