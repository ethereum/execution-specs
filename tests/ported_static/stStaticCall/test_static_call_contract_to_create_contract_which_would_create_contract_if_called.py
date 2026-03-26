"""
test_static_call_contract_to_create_contract_which_would_create_contract_if_called

Ported from:
state_tests/stStaticCall/static_CallContractToCreateContractWhichWouldCreateContractIfCalledFiller.json
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
    ["state_tests/stStaticCall/static_CallContractToCreateContractWhichWouldCreateContractIfCalledFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_call_contract_to_create_contract_which_would_create_contract_if_called(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_call_contract_to_create_contract_which_would_create_con..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
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
        gas_limit=100000000,
    )

    # Source: lll
    # {(MSTORE 0 0x600c60005566602060406000f060205260076039f3) [[ 0 ]](CREATE 1 11 21) [[ 1 ]] (STATICCALL 150000 (SLOAD 0) 0 0 0 0)}
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x600c60005566602060406000f060205260076039f3)
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x1, offset=0xb, size=0x15))
        + Op.SSTORE(key=0x1, value=Op.STATICCALL(gas=0x249f0, address=Op.SLOAD(key=0x0), args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2540be400)


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=300000,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(
                storage={
            0: 0xd2571607e241ecf590ed94b12d87c94babe36db6,
            1: 0,
        },
                nonce=1,
            ),
        Address("0x62c01474f089b07dae603491675dc5b5748f7049"): Account.NONEXISTENT,  # noqa: E501
        sender: Account(nonce=1),
        Address("0xd2571607e241ecf590ed94b12d87c94babe36db6"): Account(storage={0: 12}, balance=1, nonce=1),  # noqa: E501
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
