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
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
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
        address=Address("0x4cbc458d12c7f73a3b12ef4515c3eb1bb7430798"),  # noqa: E501
    )
    # Source: lll
    # { [[1]] 12 }
    addr_0x1000000000000000000000000000000000000118 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0xC) + Op.STOP,
        nonce=0,
        address=Address("0x6b7466044211f090b767199794f6f7041829ba85"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=160061,
        gas_price=10,
    )

    post = {
        addr_0x1000000000000000000000000000000000000118: Account(
            storage={1: 12}
        ),
        target: Account(storage={2: 24740}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
