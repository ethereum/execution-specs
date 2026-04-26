"""
Test: this test checks that the returndata buffer is changed when a...

Ported from:
state_tests/stRevertTest/RevertOpcodeInCallsOnNonEmptyReturnDataFiller.json
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
    [
        "state_tests/stRevertTest/RevertOpcodeInCallsOnNonEmptyReturnDataFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0",
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2-g0",
        ),
        pytest.param(
            2,
            1,
            0,
            id="d2-g1",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3-g0",
        ),
        pytest.param(
            3,
            1,
            0,
            id="d3-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_in_calls_on_non_empty_return_data(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test: tis test checks that the returndata buffer is changed when a..."""
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
    # { [[1]] 12 (REVERT 0 1) [[3]] 13 }
    addr_6 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0xC)
        + Op.REVERT(offset=0x0, size=0x1)
        + Op.SSTORE(key=0x3, value=0xD)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B),  # noqa: E501
    )
    # Source: lll
    # { [1] 12 (RETURN 0 64) }
    addr_7 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0xC)
        + Op.RETURN(offset=0x0, size=0x40)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0x127EAF7E31D691A8393B7A2F84A6E94372190C01),  # noqa: E501
    )
    # Source: lll
    # { (CALL 0 <contract:0xffff5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[0]] (DELEGATECALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0) [[2]] (RETURNDATASIZE) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x0,
                address=0x127EAF7E31D691A8393B7A2F84A6E94372190C01,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.DELEGATECALL(
                gas=0xC350,
                address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=Op.RETURNDATASIZE)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0xF20CCAF271BEAA36E7CF4C9CED2867FAC9558F14),  # noqa: E501
    )
    # Source: lll
    # { (CALL 0 <contract:0xffff5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[0]] (CALLCODE 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] (RETURNDATASIZE) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x0,
                address=0x127EAF7E31D691A8393B7A2F84A6E94372190C01,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0xC350,
                address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=Op.RETURNDATASIZE)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0xC9DA6CD8413F64323F12CD44C99671F280F15E1C),  # noqa: E501
    )
    # Source: lll
    # { (CALL 0 <contract:0xffff5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[4]] (CALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[5]] (RETURNDATASIZE) }  # noqa: E501
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x0,
                address=0x127EAF7E31D691A8393B7A2F84A6E94372190C01,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(
            key=0x4,
            value=Op.CALL(
                gas=0xC350,
                address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x5, value=Op.RETURNDATASIZE)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0xEA519C47889074E6378B0D83747F2C3EA0B9CBC9),  # noqa: E501
    )
    # Source: lll
    # { (CALL 0 <contract:0xffff5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[0]] (CALL 50000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] (RETURNDATASIZE) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x0,
                address=0x127EAF7E31D691A8393B7A2F84A6E94372190C01,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0xC350,
                address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=Op.RETURNDATASIZE)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0xE73611B5B479B30C93AC377AEB3BFB199764F3C3),  # noqa: E501
    )
    # Source: lll
    # { (CALL 0 <contract:0xffff5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[10]] (CALL 260000 (CALLDATALOAD 0) 0 0 0 0 0)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x0,
                address=0x127EAF7E31D691A8393B7A2F84A6E94372190C01,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(
            key=0xA,
            value=Op.CALL(
                gas=0x3F7A0,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        storage={10: 255},
        balance=1,
        nonce=0,
        address=Address(0x172A8F572404293AA810685DFDC6F740C300CC4B),  # noqa: E501
    )
    # Source: lll
    # { (CALL 0 <contract:0xffff5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[0]] (CALL 100000 <contract:0xb3305374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[2]] (RETURNDATASIZE) }  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALL(
                gas=0x0,
                address=0x127EAF7E31D691A8393B7A2F84A6E94372190C01,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x186A0,
                address=0xEA519C47889074E6378B0D83747F2C3EA0B9CBC9,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=Op.RETURNDATASIZE)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0x6BACDFA8216DBB2A09819F8739E57AE3574C9FFF),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                target: Account(storage={10: 1}),
                addr: Account(storage={2: 1}, nonce=0),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                addr: Account(storage={}),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                target: Account(storage={10: 1}),
                addr_2: Account(storage={2: 1}, nonce=0),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                addr_2: Account(storage={}),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                target: Account(storage={10: 1}),
                addr_3: Account(storage={2: 1}, nonce=0),
            },
        },
        {
            "indexes": {"data": 2, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                addr_3: Account(storage={}),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                target: Account(storage={10: 1}),
                addr_4: Account(storage={0: 1}, nonce=0),
                addr_5: Account(storage={5: 1}, nonce=0),
            },
        },
        {
            "indexes": {"data": 3, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_6: Account(storage={}),
                target: Account(storage={10: 255}),
                addr_4: Account(storage={0: 0}, nonce=0),
                addr_5: Account(storage={5: 0}, nonce=0),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
        Hash(addr_4, left_padding=True),
    ]
    tx_gas = [860000, 28000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
