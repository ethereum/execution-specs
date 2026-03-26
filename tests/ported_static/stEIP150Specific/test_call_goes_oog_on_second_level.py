"""
test_call_goes_oog_on_second_level

Ported from:
state_tests/stEIP150Specific/CallGoesOOGOnSecondLevelFiller.json
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
    ["state_tests/stEIP150Specific/CallGoesOOGOnSecondLevelFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_goes_oog_on_second_level(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_call_goes_oog_on_second_level"""
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
    # { (SSTORE 8 (GAS)) (SSTORE 9 (CALL 600000 <contract:0x1000000000000000000000000000000000000110> 0 0 0 0 0)) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(key=0x9, value=Op.CALL(gas=0x927c0, address=0x66f77b181e0e662e17d427c7320267adf2fd624, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0x3c6dca5471c6305d0642c6210d39d4613b5ea30b"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 8 (GAS)) (SSTORE 9 (CALL 300000 <contract:0x1000000000000000000000000000000000000111> 0 0 0 0 0)) [[12]] 1}
    addr_0x1000000000000000000000000000000000000110 = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.SSTORE(key=0x9, value=Op.CALL(gas=0x493e0, address=0xccc0159bd2ef7118b5e7b8d958e72237f02493fe, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xc, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x066f77b181e0e662e17d427c7320267adf2fd624"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 8 (GAS)) (KECCAK256 0x00 0x2fffff) (SSTORE 9 (GAS)) (SSTORE 10 (GAS)) }
    addr_0x1000000000000000000000000000000000000111 = pre.deploy_contract(
        code=Op.SSTORE(key=0x8, value=Op.GAS)
        + Op.POP(Op.SHA3(offset=0x0, size=0x2fffff))
        + Op.SSTORE(key=0x9, value=Op.GAS) + Op.SSTORE(key=0xa, value=Op.GAS)
        + Op.STOP,
        nonce=0,
        address=Address("0xccc0159bd2ef7118b5e7b8d958e72237f02493fe"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=2200000,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0x1000000000000000000000000000000000000110: Account(storage={8: 0x927be, 12: 1}),
        addr_0x1000000000000000000000000000000000000111: Account(storage={}),
        target: Account(storage={8: 0x213fb6, 9: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
