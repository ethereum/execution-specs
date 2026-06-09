"""
Test_codesize_oog_invalid_size.

Ported from:
state_tests/stCodeSizeLimit/codesizeOOGInvalidSizeFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCodeSizeLimit/codesizeOOGInvalidSizeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_before("EIP7954")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_codesize_oog_invalid_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_codesize_oog_invalid_size."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=20000000,
    )

    # Return sizes are fork.max_code_size() + 13 and + 1 so CREATE
    # always overflows the code-size limit. On pre-7954 forks this
    # yields the original 0x600D / 0x6001 (max_code_size = 0x6000);
    # on Amsterdam+ it scales with the raised limit.
    max_code_size = fork.max_code_size()
    size_d0 = max_code_size + 13
    size_d1 = max_code_size + 1
    tx_data = [
        Op.CODECOPY(dest_offset=0x0, offset=0xD, size=size_d0)
        + Op.RETURN(offset=0x0, size=size_d0),
        Op.CODECOPY(dest_offset=0x0, offset=0xD, size=size_d1)
        + Op.RETURN(offset=0x0, size=size_d1),
    ]
    tx_gas = [15000000]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
