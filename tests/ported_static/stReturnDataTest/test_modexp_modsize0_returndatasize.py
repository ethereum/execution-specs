"""
Test_modexp_modsize0_returndatasize.

Ported from:
state_tests/stReturnDataTest/modexp_modsize0_returndatasizeFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
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
    ["state_tests/stReturnDataTest/modexp_modsize0_returndatasizeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
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
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_modsize0_returndatasize(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_modexp_modsize0_returndatasize."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    # Source: lll
    # { (CALLDATACOPY 0 0 (CALLDATASIZE)) [[1]] (CALLCODE (GAS) 5 0 0 (CALLDATASIZE) 1000 32) [[2]](MLOAD 1000) [[3]](RETURNDATASIZE) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=Op.CALLDATASIZE)
        + Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x5,
                value=0x0,
                args_offset=0x0,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x3E8,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x3E8))
        + Op.SSTORE(key=0x3, value=Op.RETURNDATASIZE)
        + Op.STOP,
        storage={3: 0xFFFFFFFF},
        nonce=0,
        address=Address(0x4263C26963E4C1DD1CB69C116009E749F9E4EEC2),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={1: 1, 2: 0, 3: 0})},
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={1: 1, 2: 0, 3: 1})},
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={1: 1, 2: 0, 3: 100})},
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={1: 1, 2: 0, 3: 256})},
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000101"  # noqa: E501
        ),
        Bytes(
            "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001010101"  # noqa: E501
        ),
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000064000000000000000000000000000000000000000000000000000000000000006400000000000000000000000000000000000000000000000000000000000000645442ddc2b70f66c1f6d2b296c0a875be7eddd0a80958cbc7425f1899ccf90511a5c318226e48ee23f130b44dc17a691ce66be5da18b85ed7943535b205aa125e9f59294a00f05155c23e97dac6b3a00b0c63c8411bf815fc183b420b4d9dc5f715040d5c60957f52d334b843197adec58c131c907cd96059fc5adce9dda351b5df3d666fcf3eb63c46851c1816e323f2119ebdf5ef35"  # noqa: E501
        ),
        Hash(0x100)
        + Hash(0x100)
        + Hash(0x100)
        + Hash(
            0xF536269E59ACDB356459B59F1EA6ACC924650F8F05DAE101A3B463D33342DCC6
        )
        + Hash(
            0x265D1BA9465FD0F1106B3F03A4AF0A0B553E8B6BA8682584BA19C3835430FF31
        )
        + Hash(
            0x904A717282064031BCF9185DD172DAD65305EE0E61D0C638B0A0EF0F4E51653
        )
        + Hash(
            0x996020C2723FAEA116881E25FB3D554DBC51B180052C981FC79CA93567EB6FF0
        )
        + Hash(
            0xE619DEEB2984AE3CA232523AA5BD21EA4F8CAA12CB8CD90DBAFB9BD6951DCAEF
        )
        + Hash(
            0xFC4A74D195F5341BC6C3D7217DF82597B84C4E1BBEF4F2CE8C32AEDBD99430F
        )
        + Hash(
            0x4E1A59B886C4CEB9BF7A00A415C207F3A4CCF95D5483642F95A9B240806C508C
        )
        + Hash(
            0x29BB48DE38C8E1229257D5D807229FB3708AD6AC619B133FD7C1FE3C375F90CE
        )
        + Hash(
            0x55689018465A8A3D7C08097D415C702E7F57FCD6DE6EA55CCA75C49B835C6C90
        )
        + Hash(
            0x172753948FBD5DEE5A74A422E3169D0CF5665FFC9198DC7F3FA502DA817F1C81
        )
        + Hash(
            0xAF0843EF5BEC2CA2E8F3E24A76AC7322DAB5A5BDA802B247F1CF5282936CD1CB
        )
        + Hash(
            0x115F40E71DB8D62B58C7D6C0AE7C78888987C22FF6AFAE345ADE859A9BEB127D
        ),
        Bytes(
            "0000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000f3f14010101"  # noqa: E501
        ),
    ]
    tx_gas = [10000000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
