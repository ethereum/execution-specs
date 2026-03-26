"""
test_callcodecallcallcode_101_suicide_middle

Ported from:
state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_SuicideMiddleFiller.json
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
    ["state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_SuicideMiddleFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcallcode_101_suicide_middle(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_callcodecallcallcode_101_suicide_middle"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x1000000000000000000000000000000000000000")
    contract_1 = Address("0x1000000000000000000000000000000000000001")
    contract_2 = Address("0x1000000000000000000000000000000000000002")
    contract_3 = Address("0x1000000000000000000000000000000000000003")
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
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (DELEGATECALL 150000 0x1000000000000000000000000000000000000001 0 64 0 64 ) }
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.DELEGATECALL(gas=0x249f0, address=0x1000000000000000000000000000000000000001, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (CALL 100000 0x1000000000000000000000000000000000000002 0 0 64 0 64 ) }
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.CALL(gas=0x186a0, address=0x1000000000000000000000000000000000000002, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT 0x1000000000000000000000000000000000000000) [[ 2 ]] (DELEGATECALL 50000 0x1000000000000000000000000000000000000003 0 64 0 64 ) }
    contract_2 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0x1000000000000000000000000000000000000000)
        + Op.SSTORE(key=0x2, value=Op.DELEGATECALL(gas=0xc350, address=0x1000000000000000000000000000000000000003, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000002"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) }
    contract_3 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        balance=0x2540be400,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000003"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=3000000,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(storage={0: 1, 1: 1}, balance=0xde0b6b5fb6fe400),
        contract_2: Account(
                storage={},
                code=bytes.fromhex("731000000000000000000000000000000000000000ff604060006040600073100000000000000000000000000000000000000361c350f460025500"),  # noqa: E501
                balance=0,
                nonce=0,
            ),
        contract_3: Account(storage={3: 0}, balance=0x2540be400),
        sender: Account(storage={1: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
