"""
Test_static_callcallcall_000_oogm_after.

Ported from:
state_tests/stStaticCall/static_callcallcall_000_OOGMAfterFiller.json
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
    ["state_tests/stStaticCall/static_callcallcall_000_OOGMAfterFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_callcallcall_000_oogm_after(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_callcallcall_000_oogm_after."""
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

    # Source: lll
    # {  [[ 0 ]] (STATICCALL 600150 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) [[ 111 ]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x92856,
                address=0x8FF16542095DE9F85F7C395D6D543D19B30D97D7,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x6F, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x03681C634A188409B5F9B8CA2382C1A1499D8A0D),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 400080 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (SSTORE 3 1)}  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x61AD0,
                address=0xC2234F6B4A777DB8DF1447C9C2D0C8CEE376DE76,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x3, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x8FF16542095DE9F85F7C395D6D543D19B30D97D7),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 120020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 32 1) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x1D4D4,
                address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xC2234F6B4A777DB8DF1447C9C2D0C8CEE376DE76),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0x335C5531B84765A7626E6E76688F18B81BE5259C),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=1720000,
    )

    post = {
        target: Account(storage={0: 0, 1: 0, 2: 0, 3: 0, 111: 1}),
        addr: Account(storage={1: 0, 2: 0, 3: 0}),
        addr_2: Account(storage={2: 0, 3: 0}),
        addr_3: Account(storage={3: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
