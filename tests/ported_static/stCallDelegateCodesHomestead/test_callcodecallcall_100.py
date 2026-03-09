"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCallDelegateCodesHomestead
callcodecallcall_100Filler.json
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
    [
        "tests/static/state_tests/stCallDelegateCodesHomestead/callcodecallcall_100Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcall_100(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x3, value=0x1)
            + Op.SSTORE(key=0x4, value=Op.CALLER)
            + Op.SSTORE(key=0x7, value=Op.CALLVALUE)
            + Op.SSTORE(key=0x14A, value=Op.ADDRESS)
            + Op.SSTORE(key=0x14C, value=Op.ORIGIN)
            + Op.SSTORE(key=0x150, value=Op.CALLDATASIZE)
            + Op.SSTORE(key=0x152, value=Op.CODESIZE)
            + Op.SSTORE(key=0x154, value=Op.GASPRICE)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x181b4ed322e192361633cc3c0a418f259ab0cf4b"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=0x493E0,
                    address=0x5F6EACDE5A1E97F48C5DB4EE84FDF614F9DD9756,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x5, value=Op.CALLER)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x3c83297c6dcbc0520cd68714f85dc444469fb287"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=0x3D090,
                    address=0x181B4ED322E192361633CC3C0A418F259AB0CF4B,
                    value=0x2,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x5f6eacde5a1e97f48c5db4ee84fdf614f9dd9756"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (DELEGATECALL 350000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.DELEGATECALL(
                    gas=0x55730,
                    address=0x3C83297C6DCBC0520CD68714F85DC444469FB287,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xd26e26d5a4796d450bfa296d70c05f02dbc1a4b9"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=3000000,
    )

    post = {
        callee: Account(
            storage={
                3: 1,
                4: 0x5F6EACDE5A1E97F48C5DB4EE84FDF614F9DD9756,
                7: 2,
                330: 0x181B4ED322E192361633CC3C0A418F259AB0CF4B,
                332: 0xEBAF50DEBF10E08302FE4280C32DF010463CA297,
                336: 64,
                338: 39,
                340: 10,
            },
        ),
        callee_2: Account(storage={2: 1}),
        contract: Account(
            storage={
                0: 1,
                1: 1,
                5: 0xEBAF50DEBF10E08302FE4280C32DF010463CA297,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
