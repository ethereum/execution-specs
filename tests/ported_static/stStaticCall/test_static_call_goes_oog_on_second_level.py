"""
test_static_call_goes_oog_on_second_level

Ported from:
state_tests/stStaticCall/static_CallGoesOOGOnSecondLevelFiller.json
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
    ["state_tests/stStaticCall/static_CallGoesOOGOnSecondLevelFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_call_goes_oog_on_second_level(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_call_goes_oog_on_second_level"""
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
    # { (SSTORE 9 (STATICCALL 600000 <contract:0x1000000000000000000000000000000000000110> 0 0 0 0)) [[ 10 ]] (GAS) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x9, value=Op.STATICCALL(gas=0x927c0, address=0xa1202b00f0cb8acdd112e4fc87899f33572541c6, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xa, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address("0x6a2a170a903e470c3dd8bfd7974c77020c5fd8f9"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 8 (GAS)) (MSTORE 9 (STATICCALL 600000 <contract:0x1000000000000000000000000000000000000111> 0 0 0 0)) }
    addr_0x1000000000000000000000000000000000000110 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x8, value=Op.GAS)
        + Op.MSTORE(offset=0x9, value=Op.STATICCALL(gas=0x927c0, address=0x44969261d9660fcc1a2e03db83ba372ebf5f652d, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.STOP,
        nonce=0,
        address=Address("0xa1202b00f0cb8acdd112e4fc87899f33572541c6"),  # noqa: E501
    )
    # Source: lll
    # {  (KECCAK256 0x00 0x2fffff) }
    addr_0x1000000000000000000000000000000000000111 = pre.deploy_contract(
        code=Op.SHA3(offset=0x0, size=0x2fffff) + Op.STOP,
        nonce=0,
        address=Address("0x44969261d9660fcc1a2e03db83ba372ebf5f652d"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=220000,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0x1000000000000000000000000000000000000110: Account(storage={}),
        addr_0x1000000000000000000000000000000000000111: Account(storage={}),
        target: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
