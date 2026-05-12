"""
Call -> call -> (call -> code) suicide.

Ported from:
state_tests/stCallCodes/callcallcall_000_SuicideEndFiller.json

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
    ["state_tests/stCallCodes/callcallcall_000_SuicideEndFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcall_000_suicide_end(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Call -> call -> (call -> code) suicide."""
    # EIP-8037 inner-CALL gas bumps: original values restored for
    # pre-EIP-8037 forks; bumped values cover the per-storage state-
    # gas spill into regular gas on Amsterdam.
    outer_call_gas = 150000
    middle_call_gas = 100000
    inner_call_gas = 50000
    if fork.is_eip_enabled(8037):
        outer_call_gas = 1000000
        middle_call_gas = 800000
        inner_call_gas = 100000

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
    # {  (SSTORE 3 1)  }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        balance=0x2540BE400,
        nonce=0,
        address=Address(0xCB6497F0337B6CD0F7239A8819295EC7D1DAFD34),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (CALL 150000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=outer_call_gas,
                address=0x77B749FFFF7EC61D31C79ED104F230A7959B2879,
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
        address=Address(0x4353E77718BE108D4C149D88B34CACEDA42C5C66),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.CALL(
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
        address=Address(0x77B749FFFF7EC61D31C79ED104F230A7959B2879),  # noqa: E501
    )
    # Source: lll
    # {  [[ 2 ]] (CALL 50000 <contract:0x1000000000000000000000000000000000000003> 0 0 64 0 64 ) (SELFDESTRUCT <contract:0x1000000000000000000000000000000000000001>) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=inner_call_gas,
                address=0xCB6497F0337B6CD0F7239A8819295EC7D1DAFD34,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SELFDESTRUCT(address=0x77B749FFFF7EC61D31C79ED104F230A7959B2879)
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
        addr: Account(balance=0x4A817C800),
        addr_3: Account(storage={3: 1}, balance=0x2540BE400),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
