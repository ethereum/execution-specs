"""
Callcode happen to a contract that is dynamically created from within...

Ported from:
state_tests/stCallCodes/callcodeDynamicCode2SelfCallFiller.json
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
    ["state_tests/stCallCodes/callcodeDynamicCode2SelfCallFiller.json"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_callcode_dynamic_code2_self_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Callcode happen to a contract that is dynamically created from..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x1100000000000000000000000000000000000000)
    contract_1 = Address(0xA000000000000000000000000000000000000000)
    contract_2 = Address(0x1000000000000000000000000000000000000000)
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

    pre[sender] = Account(balance=0x2386F26FC10000)
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
    # {  (MSTORE 0 0x604060006040600060007313136008b64ff592819b2fa6d43f2835c452020e62) (MSTORE 32 0x0186a0f2600b5533600c55000000000000000000000000000000000000000000)  (CREATE 1 0 64) }  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x604060006040600060007313136008B64FF592819B2FA6D43F2835C452020E62,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0x186A0F2600B5533600C55000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.CREATE(value=0x1, offset=0x0, size=0x40)
        + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address(0xA000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # {(seq [[10]] (CREATE 0 0 (lll(seq  [[122]] (CALLCODE 100000 0x13136008b64ff592819b2fa6d43f2835c452020e 0 0 64 0 64)  (RETURN 0 (lll(seq [[0]] 1  [[20]] (ADDRESS) [[21]] (ORIGIN) [[22]] (CALLER)   )0) )  )0)   )  [[11]] (CALLCODE 100000 (SLOAD 10) 0 0 64 0 64)                   )}  # noqa: E501
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x46]
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
        + Op.SSTORE(
            key=0x7A,
            value=Op.CALLCODE(
                gas=0x186A0,
                address=0x13136008B64FF592819B2FA6D43F2835C452020E,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x0, offset=0x34, size=Op.DUP1)
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

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=contract_1, nonce=0): Account(
                    storage={11: 1, 12: contract_1}, balance=1
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
                        10: compute_create_address(
                            address=contract_2, nonce=0
                        ),
                        11: 1,
                        20: contract_2,
                        21: sender,
                        22: contract_2,
                    },
                    nonce=1,
                ),
                compute_create_address(address=contract_2, nonce=0): Account(
                    storage={122: 1}, nonce=1
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(contract_1, left_padding=True),
        Hash(contract_2, left_padding=True),
    ]
    tx_gas = [1453081]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
