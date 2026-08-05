"""
Verify a CALLCODE -> CALLCODE -> (DELEGATECALL + SELFDESTRUCT) chain:
every store lands in the outermost target's storage and the SELFDESTRUCT
(running in the target's context) destroys the target.

Ported from:
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_SuicideEndFiller.json

@manually-enhanced: Do not overwrite. The three call budgets are derived
bottom-up from the fork (each frame pays its stores' state gas from its
own grant under EIP-8037), and the target's post code is coupled to the
composed bytecode (the gas operand varies by fork).
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_SuicideEndFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcallcode_001_suicide_end(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Chained callcode stores land in the target; it self-destructs."""
    # Derived bottom-up call budgets: with a zero state-gas reservoir
    # each frame pays its stores' state gas from its own grant, so every
    # level's budget covers its callee plus its own work with margin.
    store_cost = Op.SSTORE(
        key=0x3, value=0x1, key_warm=False, original_value=0, new_value=1
    ).gas_cost(fork)
    inner_call_gas = store_cost + 5_000
    middle_call_gas = inner_call_gas + 2 * store_cost + 30_000
    outer_call_gas = middle_call_gas + store_cost + 30_000

    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  (SSTORE 3 1) }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0x73B954EBC05BB0FF4A0F6A13A054D50AD1584099),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (CALLCODE 150000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    target_code = (
        Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=outer_call_gas,
                address=0xEAF8C2AE0D01A880CEA4E1AA88DEF5EDD153D57B,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP
    )
    target = pre.deploy_contract(  # noqa: F841
        code=target_code,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xA74CA10B765DCDA3B60687F73F2881E2A56EDA64),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (CALLCODE 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=middle_call_gas,
                address=0xAC521409E2FA9526BFE6B827805783D2E307C4CE,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0xEAF8C2AE0D01A880CEA4E1AA88DEF5EDD153D57B),  # noqa: E501
    )
    # Source: lll
    # {  [[ 2 ]] (DELEGATECALL 50000 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (SELFDESTRUCT <contract:0x1000000000000000000000000000000000000001>) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.DELEGATECALL(
                gas=inner_call_gas,
                address=0x73B954EBC05BB0FF4A0F6A13A054D50AD1584099,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SELFDESTRUCT(address=0xEAF8C2AE0D01A880CEA4E1AA88DEF5EDD153D57B)
        + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0xAC521409E2FA9526BFE6B827805783D2E307C4CE),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {
        target: Account(
            storage={0: 1, 1: 1, 2: 1, 3: 1},
            # Coupled to the deployed bytecode (the gas operand varies
            # by fork), proving SELFDESTRUCT in a CALLCODE context kills
            # nothing here.
            code=target_code,
            balance=0,
            nonce=0,
        ),
        addr: Account(storage={1: 0, 3: 0}),
        addr_2: Account(storage={0: 0, 2: 0}),
        addr_3: Account(storage={3: 0}),
        sender: Account(storage={1: 0, 2: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
