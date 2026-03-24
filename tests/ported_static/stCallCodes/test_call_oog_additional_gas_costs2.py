"""
call(oog during init) ->  code.

Ported from:
tests/static/state_tests/stCallCodes/call_OOG_additionalGasCosts2Filler.json
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
        "tests/static/state_tests/stCallCodes/call_OOG_additionalGasCosts2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_oog_additional_gas_costs2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Call(oog during init) ->  code."""
    coinbase = Address("0xeb201d2887816e041f6e807e804f64f3a7a226fe")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.PUSH1[0x0],
        nonce=0,
        address=Address("0x89cd1cb7ad11c6949bec0c8c7533dc073960c54f"),  # noqa: E501
    )
    # Source: LLL
    # { [[0]] (CALL 6000 <contract:0x1000000000000000000000000000000000000001> 1 0 64 0 64 ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x1770,
                    address=0x89CD1CB7AD11C6949BEC0C8C7533DC073960C54F,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        storage={0x0: 0x2},
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xc1f36f15e971b13f8178b8c0c5c4f5e6b1b2b2c3"),  # noqa: E501
    )
    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=30000,
    )

    post = {
        contract: Account(storage={0: 2}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
