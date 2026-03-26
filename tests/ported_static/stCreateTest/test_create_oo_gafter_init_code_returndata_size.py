"""
Calls a contract that runs CREATE which deploy a code. then OOG happens upon deployment of the actual code. check the RETURNDATASIZE after create. fails with OOG if RETURNDATASIZE != 0

Ported from:
state_tests/stCreateTest/CreateOOGafterInitCodeReturndataSizeFiller.json
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
    ["state_tests/stCreateTest/CreateOOGafterInitCodeReturndataSizeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_oo_gafter_init_code_returndata_size(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Calls a contract that runs CREATE which deploy a code."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
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
    # { (MSTORE 0 0x6960016001556001600255600052600a6016f3) (CREATE 0 13 19) (EXP 2 (RETURNDATASIZE)) }
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x6960016001556001600255600052600a6016f3)
        + Op.POP(Op.CREATE(value=0x0, offset=0xd, size=0x13))
        + Op.EXP(0x2, Op.RETURNDATASIZE) + Op.STOP,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=55054,
        value=1,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(balance=1),
        Address("0xf1ecf98489fa9ed60a664fc4998db699cfa39d40"): Account.NONEXISTENT,  # noqa: E501
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
