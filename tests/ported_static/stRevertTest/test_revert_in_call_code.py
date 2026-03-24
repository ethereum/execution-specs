"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertInCallCodeFiller.json
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
    ["tests/static/state_tests/stRevertTest/RevertInCallCodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_revert_in_call_code(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xA2333EEF5630066B928DEA5FD85A239F511B5B067D1441EE7AC290D0122B917B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x2232)
            + Op.REVERT(offset=0x0, size=0x20)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x26bc42b8191ccb142cb8cbc3490bd3bdce465591"),  # noqa: E501
    )
    # Source: LLL
    # { [[ 0 ]] (CALLCODE 50000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 1000 0 64 0 64 ) [[ 1 ]] (RETURNDATASIZE) (RETURNDATACOPY 64 0 32) [[ 2 ]] (MLOAD 64) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0xC350,
                    address=0x26BC42B8191CCB142CB8CBC3490BD3BDCE465591,
                    value=0x3E8,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
            + Op.RETURNDATACOPY(dest_offset=0x40, offset=0x0, size=0x20)
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x40))
            + Op.STOP
        ),
        balance=1000,
        nonce=0,
        address=Address("0x5e1d76d7badbad41710e47410dba9226c255d229"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5F5E100)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=105044,
    )

    post = {
        contract: Account(storage={1: 32, 2: 8754}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
