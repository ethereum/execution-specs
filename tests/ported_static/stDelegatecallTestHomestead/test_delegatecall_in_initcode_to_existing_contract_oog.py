"""
test_delegatecall_in_initcode_to_existing_contract_oog

Ported from:
state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToExistingContractOOGFiller.json
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
    ["state_tests/stDelegatecallTestHomestead/delegatecallInInitcodeToExistingContractOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegatecall_in_initcode_to_existing_contract_oog(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_delegatecall_in_initcode_to_existing_contract_oog"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x1000000000000000000000000000000000000000")
    contract_1 = Address("0x945304eb96065b2a98b57a48a06ae28d285a71b5")
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
        gas_limit=1000000,
    )

    # Source: lll
    # { (MSTORE 0 0x604060006040600073945304eb96065b2a98b57a48a06ae28d285a71b5620186) (MSTORE 32 0xa0f4600a5533600b550000000000000000000000000000000000000000000000) (CREATE 5 0 64) }
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x604060006040600073945304eb96065b2a98b57a48a06ae28d285a71b5620186)
        + Op.MSTORE(offset=0x20, value=0xa0f4600a5533600b550000000000000000000000000000000000000000000000)
        + Op.CREATE(value=0x5, offset=0x0, size=0x40) + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 2 1) }
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x945304eb96065b2a98b57a48a06ae28d285a71b5"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2386f26fc10000)


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=153096,
        nonce=0,
        gas_price=10,
    )

    post = {
        Address("0x13136008b64ff592819b2fa6d43f2835c452020e"): Account(balance=5),  # noqa: E501
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
