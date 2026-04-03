"""
Test_static_zero_value_suicide_oog_revert.

Ported from:
state_tests/stStaticCall/static_ZeroValue_SUICIDE_OOGRevertFiller.json
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
    ["state_tests/stStaticCall/static_ZeroValue_SUICIDE_OOGRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_zero_value_suicide_oog_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_zero_value_suicide_oog_revert."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { (STATICCALL 100000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) (KECCAK256 0x00 0x2fffff) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.STATICCALL(
                gas=0x186A0,
                address=0xDA2EB5512889130C4AF686A291B08665B889CB22,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.STOP,
        nonce=0,
        address=Address(0xCBECD26BEBBAEDDEF56FCE1849F78096332B11AB),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>)  }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0xDA2EB5512889130C4AF686A291B08665B889CB22
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xDA2EB5512889130C4AF686A291B08665B889CB22),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1000000,
    )

    post = {
        sender: Account(nonce=1),
        target: Account(storage={}),
        addr: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
