"""
test_transaction64_rule_d64m1

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
    """test_transaction64_rule_d64m1"""
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
    # { [0] (GAS) (CALL 160000 <contract:0x1000000000000000000000000000000000000118> 0 0 0 0 0) [[2]] (SUB @0 (GAS)) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.CALL(gas=0x27100, address=0x6b7466044211f090b767199794f6f7041829ba85, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x2, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
        address=Address("0x4cbc458d12c7f73a3b12ef4515c3eb1bb7430798"),  # noqa: E501
    )
    # Source: lll
    # { [[1]] 12 }
    addr_0x1000000000000000000000000000000000000118 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0xc) + Op.STOP,
        nonce=0,
        address=Address("0x6b7466044211f090b767199794f6f7041829ba85"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=160061,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0x1000000000000000000000000000000000000118: Account(storage={1: 12}),
        target: Account(storage={2: 24740}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
