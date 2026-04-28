"""
CALL to ECREC precompile with input that has a valid signature...

Ported from:
state_tests/stPreCompiledContracts2/CallEcrecoverUnrecoverableKeyFiller.json
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
    [
        "state_tests/stPreCompiledContracts2/CallEcrecoverUnrecoverableKeyFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ecrecover_unrecoverable_key(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALL to ECREC precompile with input that has a valid signature..."""
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
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: lll
    # { (MSTORE 0 0xa8b53bdf3306a35a7103ab5504a0c9b492295564b6202b1942a84ef300107281) (MSTORE 32 0x000000000000000000000000000000000000000000000000000000000000001b) (MSTORE 64 0x3078356531653033663533636531386237373263636230303933666637316633) (MSTORE 96 0x6635336635633735623734646362333161383561613862383839326234653862) (MSTORE 128 0x1122334455667788991011121314151617181920212223242526272829303132) (CALL 300000 1 0 0 128 128 32) (SSTORE 0 (MLOAD 128)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0xA8B53BDF3306A35A7103AB5504A0C9B492295564B6202B1942A84EF300107281,  # noqa: E501
        )
        + Op.MSTORE(offset=0x20, value=0x1B)
        + Op.MSTORE(
            offset=0x40,
            value=0x3078356531653033663533636531386237373263636230303933666637316633,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x60,
            value=0x6635336635633735623734646362333161383561613862383839326234653862,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x80,
            value=0x1122334455667788991011121314151617181920212223242526272829303132,  # noqa: E501
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=0x1,
                value=0x0,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x80,
                ret_size=0x20,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x80))
        + Op.STOP,
        balance=0x1312D00,
        nonce=0,
        address=Address(0x85C44D846ED50AC9E384C1B575FD96F3EDF5751F),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3652240,
        value=0x186A0,
    )

    post = {
        target: Account(
            storage={
                0: 0x1122334455667788991011121314151617181920212223242526272829303132,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
