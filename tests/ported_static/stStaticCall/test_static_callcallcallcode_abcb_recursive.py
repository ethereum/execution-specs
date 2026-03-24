"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcallcallcode_ABCB_RECURSIVEFiller.json
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
    [
        "tests/static/state_tests/stStaticCall/static_callcallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcallcallcode_abcb_recursive(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x1)
            + Op.POP(
                Op.STATICCALL(
                    gas=0xF4240,
                    address=0x458E20B622EC33A82F2A43A90EDC52A429639916,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x1F, value=0x1)
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x34baf5e282fcbde0d147efd6f95e606cc8c27485"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x1)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0x7A120,
                    address=0x34BAF5E282FCBDE0D147EFD6F95E606CC8C27485,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x15, value=0x1)
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x458e20b622ec33a82f2a43a90edc52a429639916"),  # noqa: E501
    )
    # Source: LLL
    # {  (MSTORE 1 1) (STATICCALL 25000000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) (MSTORE 31 1)}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x1)
            + Op.POP(
                Op.STATICCALL(
                    gas=0x17D7840,
                    address=0x34BAF5E282FCBDE0D147EFD6F95E606CC8C27485,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x1F, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x5ee4b6a55558049d98b92269841db0f86fd1a59a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=600000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
