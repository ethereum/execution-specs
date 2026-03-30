"""
Test_static_call_goes_oog_on_second_level.

Ported from:
state_tests/stStaticCall/static_CallGoesOOGOnSecondLevelFiller.json
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
    ["state_tests/stStaticCall/static_CallGoesOOGOnSecondLevelFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_call_goes_oog_on_second_level(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_call_goes_oog_on_second_level."""
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
    # { (SSTORE 9 (STATICCALL 600000 <contract:0x1000000000000000000000000000000000000110> 0 0 0 0)) [[ 10 ]] (GAS) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x9,
            value=Op.STATICCALL(
                gas=0x927C0,
                address=0xA1202B00F0CB8ACDD112E4FC87899F33572541C6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0xA, value=Op.GAS)
        + Op.STOP,
        nonce=0,
        address=Address(0x6A2A170A903E470C3DD8BFD7974C77020C5FD8F9),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 8 (GAS)) (MSTORE 9 (STATICCALL 600000 <contract:0x1000000000000000000000000000000000000111> 0 0 0 0)) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x8, value=Op.GAS)
        + Op.MSTORE(
            offset=0x9,
            value=Op.STATICCALL(
                gas=0x927C0,
                address=0x44969261D9660FCC1A2E03DB83BA372EBF5F652D,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xA1202B00F0CB8ACDD112E4FC87899F33572541C6),  # noqa: E501
    )
    # Source: lll
    # {  (KECCAK256 0x00 0x2fffff) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SHA3(offset=0x0, size=0x2FFFFF) + Op.STOP,
        nonce=0,
        address=Address(0x44969261D9660FCC1A2E03DB83BA372EBF5F652D),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=220000,
    )

    post = {
        addr: Account(storage={}),
        addr_2: Account(storage={}),
        target: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
