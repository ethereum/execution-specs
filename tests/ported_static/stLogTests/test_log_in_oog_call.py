"""
Test_log_in_oog_call.

Ported from:
state_tests/stLogTests/logInOOG_CallFiller.json
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
    ["state_tests/stLogTests/logInOOG_CallFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_log_in_oog_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_log_in_oog_call."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { [[ 0 ]] (CALL 100000 <contract:0x0f572e5295c57f15886f9b263e2f6d2d6c7b5ec6> 23 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x186A0,
                address=0x69B6134B97E638B919A7089DF82AF74961E71FF8,
                value=0x17,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x825DCC9FBF5CFF44E688BAE15B79E8E11951BE2A),  # noqa: E501
    )
    # Source: lll
    # { (LOG0 0 32) (MLOAD 0xffffffffffffffff) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.LOG0(offset=0x0, size=0x20)
        + Op.MLOAD(offset=0xFFFFFFFFFFFFFFFF)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x69B6134B97E638B919A7089DF82AF74961E71FF8),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=210000,
        value=0x186A0,
    )

    post = {target: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
