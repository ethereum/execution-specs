"""
Test_call_sha256_1_nonzero_value.

Ported from:
state_tests/stPreCompiledContracts2/CallSha256_1_nonzeroValueFiller.json
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
    [
        "state_tests/stPreCompiledContracts2/CallSha256_1_nonzeroValueFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_sha256_1_nonzero_value(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_call_sha256_1_nonzero_value."""
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
        gas_limit=100000000,
    )

    # Source: lll
    # { [[ 2 ]] (CALL 200000 2 0x13 0 0 0 32) [[ 0 ]] (MLOAD 0)}
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x30D40,
                address=0x2,
                value=0x13,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xBEBC200,
        nonce=0,
        address=Address(0x39BAF944BD1B21E643D8D207A7073EE34A5D2116),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=365224,
        value=0x186A0,
    )

    post = {
        Address(0x0000000000000000000000000000000000000002): Account(
            balance=19
        ),
        target: Account(
            storage={
                0: 0xE3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855,  # noqa: E501
                2: 1,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
