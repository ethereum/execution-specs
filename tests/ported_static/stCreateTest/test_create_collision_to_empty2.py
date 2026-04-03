"""
Data0 - create collision to empty, data1 - to empty but nonce, data2 -...

Ported from:
state_tests/stCreateTest/CreateCollisionToEmpty2Filler.json
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
    ["state_tests/stCreateTest/CreateCollisionToEmpty2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0-g0-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="d0-g0-v1",
        ),
        pytest.param(
            0,
            1,
            0,
            id="d0-g1-v0",
        ),
        pytest.param(
            0,
            1,
            1,
            id="d0-g1-v1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1-g0-v0",
        ),
        pytest.param(
            1,
            0,
            1,
            id="d1-g0-v1",
        ),
        pytest.param(
            1,
            1,
            0,
            id="d1-g1-v0",
        ),
        pytest.param(
            1,
            1,
            1,
            id="d1-g1-v1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2-g0-v0",
        ),
        pytest.param(
            2,
            0,
            1,
            id="d2-g0-v1",
        ),
        pytest.param(
            2,
            1,
            0,
            id="d2-g1-v0",
        ),
        pytest.param(
            2,
            1,
            1,
            id="d2-g1-v1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_collision_to_empty2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Data0 - create collision to empty, data1 - to empty but nonce,..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x1A00000000000000000000000000000000000000)
    contract_1 = Address(0x1000000000000000000000000000000000000000)
    contract_2 = Address(0x2000000000000000000000000000000000000000)
    contract_3 = Address(0x3000000000000000000000000000000000000000)
    contract_4 = Address(0x13136008B64FF592819B2FA6D43F2835C452020E)
    contract_5 = Address(0x0BF4C804E0579073BAF54EC4EC37CD04F3455C65)
    contract_6 = Address(0x4B86C4ED99B87F0F396BC0C76885453C343916ED)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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
    # { (CALL 80000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0x13880,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x1A00000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 0x6001600155) [[1]] (CREATE 0 27 5) }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x6001600155)
        + Op.SSTORE(key=0x1, value=Op.CREATE(value=0x0, offset=0x1B, size=0x5))
        + Op.STOP,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 0x6001600155) [[1]] (CREATE 0 27 5) }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x6001600155)
        + Op.SSTORE(key=0x1, value=Op.CREATE(value=0x0, offset=0x1B, size=0x5))
        + Op.STOP,
        nonce=0,
        address=Address(0x2000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 0x6001600155) [[1]] (CREATE 0 27 5) }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x6001600155)
        + Op.SSTORE(key=0x1, value=Op.CREATE(value=0x0, offset=0x1B, size=0x5))
        + Op.STOP,
        nonce=0,
        address=Address(0x3000000000000000000000000000000000000000),  # noqa: E501
    )
    pre[contract_4] = Account(balance=10)
    pre[contract_5] = Account(balance=0, nonce=2)
    # Source: raw
    # 0x1122334455
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex("1122334455"),
        nonce=0,
        address=Address(0x4B86C4ED99B87F0F396BC0C76885453C343916ED),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_1: Account(storage={}, nonce=0),
                contract_4: Account(storage={}, code=b"", balance=10, nonce=0),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_1: Account(
                    storage={1: 0x13136008B64FF592819B2FA6D43F2835C452020E},
                    nonce=1,
                ),
                contract_4: Account(
                    storage={1: 1}, code=b"", balance=10, nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [1, 2], "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_2: Account(storage={1: 0}, nonce=0),
                contract_5: Account(storage={}, code=b"", nonce=2),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_2: Account(storage={1: 0}, nonce=0),
                contract_5: Account(storage={}, code=b"", nonce=2),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_3: Account(storage={1: 0}, nonce=0),
                contract_6: Account(
                    storage={},
                    code=bytes.fromhex("1122334455"),
                    nonce=0,
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(contract_1, left_padding=True),
        Hash(contract_2, left_padding=True),
        Hash(contract_3, left_padding=True),
    ]
    tx_gas = [600000, 54000]
    tx_value = [0, 1]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
