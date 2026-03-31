"""
Callcode to a contract that is being created in the same transaction.

Ported from:
state_tests/stCallCodes/callcodeDynamicCodeFiller.json
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
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCallCodes/callcodeDynamicCodeFiller.json"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_callcode_dynamic_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Callcode to a contract that is being created in the same transaction."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x1100000000000000000000000000000000000000)
    contract_1 = Address(0x1000000000000000000000000000000000000000)
    contract_2 = Address(0x2000000000000000000000000000000000000000)
    contract_3 = Address(0x3000000000000000000000000000000000000000)
    contract_4 = Address(0x4000000000000000000000000000000000000000)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { (CALL 800000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0xC3500,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x1100000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # {(seq [[10]] (CREATE 0 0 (lll(seq  (RETURN 0 (lll(seq [[0]] 1  [[20]] (ADDRESS) [[21]] (ORIGIN) [[22]] (CALLER)   )0) )  )0)   )  [[11]] (CALLCODE 100000 (SLOAD 10) 0 0 64 0 64)                   )}  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x1F]
        + Op.CODECOPY(dest_offset=0x0, offset=0x27, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.SSTORE(key=0xA, value=Op.CREATE)
        + Op.SSTORE(
            key=0xB,
            value=Op.CALLCODE(
                gas=0x186A0,
                address=Op.SLOAD(key=0xA),
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP
        + Op.INVALID
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x0, offset=0xD, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=0x14, value=Op.ADDRESS)
        + Op.SSTORE(key=0x15, value=Op.ORIGIN)
        + Op.SSTORE(key=0x16, value=Op.CALLER)
        + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # {(seq [[10]] (CREATE2 0 0 (lll(seq  (RETURN 0 (lll(seq [[0]] 1  [[20]] (ADDRESS) [[21]] (ORIGIN) [[22]] (CALLER)  )0) )  )0)  0 )  [[11]] (CALLCODE 100000 (SLOAD 10) 0 0 64 0 64)                   )}  # noqa: E501
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0x1F]
        + Op.CODECOPY(dest_offset=0x0, offset=0x29, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.SSTORE(key=0xA, value=Op.CREATE2)
        + Op.SSTORE(
            key=0xB,
            value=Op.CALLCODE(
                gas=0x186A0,
                address=Op.SLOAD(key=0xA),
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP
        + Op.INVALID
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x0, offset=0xD, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=0x14, value=Op.ADDRESS)
        + Op.SSTORE(key=0x15, value=Op.ORIGIN)
        + Op.SSTORE(key=0x16, value=Op.CALLER)
        + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address(0x2000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # {(seq (CREATE 0 0 (lll(seq       [[10]] (CREATE 0 0 (lll(seq  (RETURN 0 (lll(seq [[0]] 1  [[20]] (ADDRESS)  [[21]] (ORIGIN) [[22]] (CALLER)  )0) )  )0)   )  [[11]] (CALLCODE 100000 (SLOAD 10) 0 0 64 0 64)            )0))       )}  # noqa: E501
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x46]
        + Op.CODECOPY(dest_offset=0x0, offset=0xF, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.CREATE
        + Op.STOP
        + Op.INVALID
        + Op.PUSH1[0x1F]
        + Op.CODECOPY(dest_offset=0x0, offset=0x27, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.SSTORE(key=0xA, value=Op.CREATE)
        + Op.SSTORE(
            key=0xB,
            value=Op.CALLCODE(
                gas=0x186A0,
                address=Op.SLOAD(key=0xA),
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP
        + Op.INVALID
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x0, offset=0xD, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=0x14, value=Op.ADDRESS)
        + Op.SSTORE(key=0x15, value=Op.ORIGIN)
        + Op.SSTORE(key=0x16, value=Op.CALLER)
        + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address(0x3000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # {(seq (CREATE 0 0 (lll(seq       [[10]] (CREATE2 0 0 (lll(seq  (RETURN 0 (lll(seq [[0]] 1  [[20]] (ADDRESS)  [[21]] (ORIGIN) [[22]] (CALLER)  )0) )  )0)  0 )  [[11]] (CALLCODE 100000 (SLOAD 10) 0 0 64 0 64)            )0))       )}  # noqa: E501
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x48]
        + Op.CODECOPY(dest_offset=0x0, offset=0xF, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.CREATE
        + Op.STOP
        + Op.INVALID
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x1F]
        + Op.CODECOPY(dest_offset=0x0, offset=0x29, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.SSTORE(key=0xA, value=Op.CREATE2)
        + Op.SSTORE(
            key=0xB,
            value=Op.CALLCODE(
                gas=0x186A0,
                address=Op.SLOAD(key=0xA),
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP
        + Op.INVALID
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x0, offset=0xD, size=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.STOP
        + Op.INVALID
        + Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=0x14, value=Op.ADDRESS)
        + Op.SSTORE(key=0x15, value=Op.ORIGIN)
        + Op.SSTORE(key=0x16, value=Op.CALLER)
        + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address(0x4000000000000000000000000000000000000000),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2386F26FC10000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_1: Account(
                    storage={
                        0: 1,
                        10: 0x13136008B64FF592819B2FA6D43F2835C452020E,
                        11: 1,
                        20: 0x1000000000000000000000000000000000000000,
                        21: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        22: 0x1000000000000000000000000000000000000000,
                    },
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_2: Account(
                    storage={
                        0: 1,
                        10: 0x2D39FAD743351D4CF3F4717907D3DDA5E0A689A7,
                        11: 1,
                        20: 0x2000000000000000000000000000000000000000,
                        21: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        22: 0x2000000000000000000000000000000000000000,
                    },
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=contract_3, nonce=0): Account(
                    storage={
                        0: 1,
                        10: 0xBF1676BE6038AB86D66E00824C2E3577858040F6,
                        11: 1,
                        20: 0x4B86C4ED99B87F0F396BC0C76885453C343916ED,
                        21: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        22: 0x4B86C4ED99B87F0F396BC0C76885453C343916ED,
                    },
                    code=b"",
                    balance=0,
                    nonce=2,
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=contract_4, nonce=0): Account(
                    storage={
                        0: 1,
                        10: 0xF2D6BF688FAE45DA62AB2DD4F36945BC924CC61,
                        11: 1,
                        20: 0xA51C188504A60578914FCAE68F7A1F0DCBB856A9,
                        21: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        22: 0xA51C188504A60578914FCAE68F7A1F0DCBB856A9,
                    },
                    code=b"",
                    balance=0,
                    nonce=2,
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(contract_1, left_padding=True),
        Hash(contract_2, left_padding=True),
        Hash(contract_3, left_padding=True),
        Hash(contract_4, left_padding=True),
    ]
    tx_gas = [1000000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
