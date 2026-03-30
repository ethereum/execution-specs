"""
Call -> call -> code oog.

Ported from:
state_tests/stCallCodes/callcall_00_OOGE_valueTransferFiller.json
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
    ["state_tests/stCallCodes/callcall_00_OOGE_valueTransferFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcall_00_ooge_value_transfer(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Call -> call -> code oog ."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
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

    # Source: lll
    # {  [[ 0 ]] (CALL 800000 <contract:0x1000000000000000000000000000000000000001> 20 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0xC3500,
                address=0xA781AD010268E97D590D07E5B442975243B2F05B,
                value=0x14,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xB06C4FF2E2503BB892CC3C9237A1AE465A759616),  # noqa: E501
    )
    # Source: lll
    # { [[ 1 ]] (CALL 600000 <contract:0x1000000000000000000000000000000000000002> 10 0 64 0 64 )  [[11]] 1}  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0x927C0,
                address=0x766B2CF0691F51029181FC511395B7AB71353A88,
                value=0xA,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0xB, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xA781AD010268E97D590D07E5B442975243B2F05B),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 2 1) (KECCAK256 0x00 0x2fffff) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x2, value=0x1)
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.STOP,
        nonce=0,
        address=Address(0x766B2CF0691F51029181FC511395B7AB71353A88),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
    )

    post = {
        target: Account(storage={0: 1}),
        addr: Account(storage={11: 1}),
        addr_2: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
