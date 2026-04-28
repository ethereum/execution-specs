"""
Test_static_revert_depth2.

Ported from:
state_tests/stStaticCall/static_RevertDepth2Filler.json
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_RevertDepth2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_revert_depth2(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_revert_depth2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { (MSTORE 1 1) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (STATICCALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0) (KECCAK256 0x00 0x2fffff) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.STATICCALL(
                gas=0xC350,
                address=addr_2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {  (STATICCALL 50000 <contract:0xc000000000000000000000000000000000000000> 0 0 0 0) (MSTORE 1 1) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.STATICCALL(
                gas=0xC350,
                address=addr_2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x1, value=0x1)
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { [[0]] (ADD 1 (SLOAD 0)) [[1]] (STATICCALL 150000 <contract:0xb000000000000000000000000000000000000000> 0 0 0 0) [[2]] (STATICCALL 150000 <contract:0xd000000000000000000000000000000000000000> 0 0 0 0)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
        + Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x249F0,
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.STATICCALL(
                gas=0x249F0,
                address=addr_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1706850,
    )

    post = {
        target: Account(storage={0: 1, 1: 1, 2: 0}),
        addr: Account(storage={0: 0, 1: 0}),
        addr_2: Account(storage={0: 0}),
        addr_3: Account(storage={0: 0, 1: 0, 2: 0}),
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
