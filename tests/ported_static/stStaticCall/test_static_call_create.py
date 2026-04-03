"""
Test_static_call_create.

Ported from:
state_tests/stStaticCall/static_callCreateFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callCreateFiller.json"],
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
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call_create."""
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
    # {  [[ 0 ]] (STATICCALL 300000 (CALLDATALOAD 0) 0 0 0 0) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x493E0,
                address=Op.CALLDATALOAD(offset=0x0),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xE49F04B30026F23E9E04493C44ECE7CFEC9224CA),  # noqa: E501
    )
    # Source: lll
    # {  (CALL 150000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0 0) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0x249F0,
            address=0x29D4D72A31D1B141B2067D1D4193BDF12FCDDC41,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xF5C27325E6C5769B6569971CD81E01570FD30EF1),  # noqa: E501
    )
    # Source: lll
    # {  (DELEGATECALL 150000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=0x249F0,
            address=0x29D4D72A31D1B141B2067D1D4193BDF12FCDDC41,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xB4AA7CC91D100EDDC01F22CA32F643BB0F1C91CC),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 150000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x249F0,
            address=0x29D4D72A31D1B141B2067D1D4193BDF12FCDDC41,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xF9ECFE0635FEFB5AD44418F97D7FCAF210EBD5AA),  # noqa: E501
    )
    # Source: lll
    # {  (CREATE 0 1 1) }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.CREATE(value=0x0, offset=0x1, size=0x1) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x29D4D72A31D1B141B2067D1D4193BDF12FCDDC41),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 2, 3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 1})},
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_4, left_padding=True),
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
    ]
    tx_gas = [1000000]
    tx_value = [100000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
