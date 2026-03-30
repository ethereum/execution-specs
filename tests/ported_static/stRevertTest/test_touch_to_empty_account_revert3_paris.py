"""
Test_touch_to_empty_account_revert3_paris.

Ported from:
state_tests/stRevertTest/TouchToEmptyAccountRevert3_ParisFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
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
    """Test_touch_to_empty_account_revert3_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    addr = Address(0x76FAE819612A29489A1A43208613D8F8557B8898)
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    pre[addr] = Account(balance=10)
    # Source: lll
    # { [[0]](CALL 130000 <contract:0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[1]](CALL 130000 <contract:0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x1FBD0,
                address=0x51CD6399DE7E11930D3AA146D45A2E327B5894B9,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0x1FBD0,
                address=0x2620916B2F3D6B185F4D9DD1ECEE4A1F665D5C36,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xCD48E0C45933CFA7AA1345807CF2D6B02875F627),  # noqa: E501
    )
    # Source: lll
    # { [[2]](CALL 100000 <contract:0xe94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) (KECCAK256 0x00 0x2fffff) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x186A0,
                address=0x28207E524CCB9DBC79BB3044819ACD87D630F27A,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.STOP,
        nonce=0,
        address=Address(0x2620916B2F3D6B185F4D9DD1ECEE4A1F665D5C36),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <eoa:0x1000000000000000000000000000000000000000>) }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0x76FAE819612A29489A1A43208613D8F8557B8898
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x51CD6399DE7E11930D3AA146D45A2E327B5894B9),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <eoa:0x1000000000000000000000000000000000000000>) }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0x76FAE819612A29489A1A43208613D8F8557B8898
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x28207E524CCB9DBC79BB3044819ACD87D630F27A),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=200000,
    )

    post = {addr: Account(balance=10)}

    state_test(env=env, pre=pre, post=post, tx=tx)
