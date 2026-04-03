"""
Check balance in blackbox, just fill the balance consumed.

Ported from:
state_tests/stStaticCall/static_CheckCallCostOOGFiller.json
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
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_CheckCallCostOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_check_call_cost_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Check balance in blackbox, just fill the balance consumed."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x3327048BBC0B8C348A6352BE62994144E64B8FF2CEC68D9FF4CA4E911ECD5D22
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0x5AF3107A4000)
    # Source: lll
    # { (STATICCALL 100 <contract:0x2000000000000000000000000000000000000000> 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x64,
            address=0xEBE7ED7A6E995C9843A6DF04E332981EBB2772E0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xB59292B3A630476ADBC4A3643C0815B682A5009A),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 1 1) (KECCAK256 0x00 0x2fffff) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1)
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.STOP,
        nonce=0,
        address=Address(0xEBE7ED7A6E995C9843A6DF04E332981EBB2772E0),  # noqa: E501
    )

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [22000, 1000000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
