"""
Test_transaction64_rule_d64m1.

Ported from:
state_tests/stEIP150Specific/Transaction64Rule_d64m1Filler.json
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
    ["state_tests/stEIP150Specific/Transaction64Rule_d64m1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_transaction64_rule_d64m1(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_transaction64_rule_d64m1."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
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
    # Source: lll
    # { [0] (GAS) (CALL 160000 <contract:0x1000000000000000000000000000000000000118> 0 0 0 0 0) [[2]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x27100,
                address=0x6B7466044211F090B767199794F6F7041829BA85,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x2, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
        address=Address(0x4CBC458D12C7F73A3B12EF4515C3EB1BB7430798),  # noqa: E501
    )
    # Source: lll
    # { [[1]] 12 }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0xC) + Op.STOP,
        nonce=0,
        address=Address(0x6B7466044211F090B767199794F6F7041829BA85),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=160061,
    )

    post = {
        addr: Account(storage={1: 12}),
        target: Account(storage={2: 24740}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
