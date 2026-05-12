"""
CALLCODE -> CALLCODE -> (CALL -> code) (suicide).

Ported from:
state_tests/stCallCodes/callcodecallcodecall_110_SuicideEndFiller.json

@manually-enhanced: Do not overwrite. The hardcoded inner-CALL gas
values (50k / 100k / 150k) were tuned to the pre-EIP-8037 gas budget.
On Amsterdam each SSTORE in the innermost callee adds per-storage
state-gas (32 * COST_PER_STATE_BYTE) that spills back into regular
gas when the reservoir is empty, OoG'ing the inner CALL before its
SSTORE marker fires. Bump fork-conditionally on EIP-8037 only; pre-
EIP-8037 forks keep the original values.

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
    ["state_tests/stCallCodes/callcodecallcodecall_110_SuicideEndFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcodecall_110_suicide_end(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """CALLCODE -> CALLCODE -> (CALL -> code) (suicide) ."""
    # EIP-8037 inner-CALL gas bumps: original values restored for
    # pre-EIP-8037 forks; bumped values cover the per-storage state-
    # gas spill into regular gas on Amsterdam.
    outer_call_gas = 0x249F0
    middle_call_gas = 0x186A0
    inner_call_gas = 0xC350
    if fork.is_eip_enabled(8037):
        outer_call_gas = 0xF4240
        middle_call_gas = 0xC3500
        inner_call_gas = 0x186A0

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
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
        + Op.STOP,
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
                address=0xD957E143AD2C011BC6A2B142795F1A9BA70D0680,
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
    # {  [[ 2 ]] (CALL 50000 <contract:0x1000000000000000000000000000000000000003> 0 0 64 0 64 ) (SELFDESTRUCT <contract:0x1000000000000000000000000000000000000001>) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=inner_call_gas,
                address=0x73B954EBC05BB0FF4A0F6A13A054D50AD1584099,
                value=0x0,
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
        address=Address(0xD957E143AD2C011BC6A2B142795F1A9BA70D0680),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {
        addr: Account(balance=0xDE0B6B5FB6FE400),
        addr_3: Account(storage={3: 1}, balance=0x2540BE400),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
