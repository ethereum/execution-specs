"""
test_static_return_test

Ported from:
state_tests/stStaticCall/static_ReturnTestFiller.json
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
    ["state_tests/stStaticCall/static_ReturnTestFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_return_test(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_return_test"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x194f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_1 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
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

    # Source: lll
    # {(STATICCALL 2000 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 30 1 31 1) [[0]](MLOAD 0) (RETURN 30 2)}
    contract_0 = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=0x7d0, address=0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b, args_offset=0x1e, args_size=0x1, ret_offset=0x1f, ret_size=0x1))
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.RETURN(offset=0x1e, size=0x2) + Op.STOP,
        nonce=0,
        address=Address("0x194f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5f5e100)
    # Source: lll
    # {(MSTORE 0 0x15) (RETURN 31 1)}
    contract_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x15) + Op.RETURN(offset=0x1f, size=0x1)
        + Op.STOP,
        balance=0x186a0,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=300000,
        nonce=0,
        gas_price=10,
    )

    post = {contract_0: Account(storage={0: 21})}

    state_test(env=env, pre=pre, post=post, tx=tx)
