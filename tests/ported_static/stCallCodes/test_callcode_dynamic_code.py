"""
callcode to a contract that is being created in the same transaction

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
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "0000000000000000000000001000000000000000000000000000000000000000",
    "0000000000000000000000002000000000000000000000000000000000000000",
    "0000000000000000000000003000000000000000000000000000000000000000",
    "0000000000000000000000004000000000000000000000000000000000000000",
]
TX_GAS = [1000000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCallCodes/callcodeDynamicCodeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0",
        ),
        pytest.param(
            1, 0, 0,
            id="d1",
        ),
        pytest.param(
            2, 0, 0,
            id="d2",
        ),
        pytest.param(
            3, 0, 0,
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
    """callcode to a contract that is being created in the same transaction"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x1100000000000000000000000000000000000000")
    contract_1 = Address("0x1000000000000000000000000000000000000000")
    contract_2 = Address("0x2000000000000000000000000000000000000000")
    contract_3 = Address("0x3000000000000000000000000000000000000000")
    contract_4 = Address("0x4000000000000000000000000000000000000000")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: lll
    # { (CALL 800000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_0 = pre.deploy_contract(
        code=Op.CALL(gas=0xc3500, address=Op.CALLDATALOAD(offset=0x0), value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0x1100000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # {(seq [[10]] (CREATE 0 0 (lll(seq  (RETURN 0 (lll(seq [[0]] 1  [[20]] (ADDRESS) [[21]] (ORIGIN) [[22]] (CALLER)   )0) )  )0)   )  [[11]] (CALLCODE 100000 (SLOAD 10) 0 0 64 0 64)                   )}
    contract_1 = pre.deploy_contract(
        code=Op.PUSH1[0x1f]
        + Op.CODECOPY(dest_offset=0x0, offset=0x27, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.SSTORE(key=0xa, value=Op.CREATE)
        + Op.SSTORE(key=0xb, value=Op.CALLCODE(gas=0x186a0, address=Op.SLOAD(key=0xa), value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP + Op.INVALID + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x0, offset=0xd, size=Op.DUP1) + Op.PUSH1[0x0]
        + Op.RETURN + Op.STOP + Op.INVALID + Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=0x14, value=Op.ADDRESS)
        + Op.SSTORE(key=0x15, value=Op.ORIGIN)
        + Op.SSTORE(key=0x16, value=Op.CALLER) + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # {(seq [[10]] (CREATE2 0 0 (lll(seq  (RETURN 0 (lll(seq [[0]] 1  [[20]] (ADDRESS) [[21]] (ORIGIN) [[22]] (CALLER)  )0) )  )0)  0 )  [[11]] (CALLCODE 100000 (SLOAD 10) 0 0 64 0 64)                   )}
    contract_2 = pre.deploy_contract(
        code=Op.PUSH1[0x0] + Op.PUSH1[0x1f]
        + Op.CODECOPY(dest_offset=0x0, offset=0x29, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.SSTORE(key=0xa, value=Op.CREATE2)
        + Op.SSTORE(key=0xb, value=Op.CALLCODE(gas=0x186a0, address=Op.SLOAD(key=0xa), value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP + Op.INVALID + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x0, offset=0xd, size=Op.DUP1) + Op.PUSH1[0x0]
        + Op.RETURN + Op.STOP + Op.INVALID + Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=0x14, value=Op.ADDRESS)
        + Op.SSTORE(key=0x15, value=Op.ORIGIN)
        + Op.SSTORE(key=0x16, value=Op.CALLER) + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address("0x2000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # {(seq (CREATE 0 0 (lll(seq       [[10]] (CREATE 0 0 (lll(seq  (RETURN 0 (lll(seq [[0]] 1  [[20]] (ADDRESS)  [[21]] (ORIGIN) [[22]] (CALLER)  )0) )  )0)   )  [[11]] (CALLCODE 100000 (SLOAD 10) 0 0 64 0 64)            )0))       )}
    contract_3 = pre.deploy_contract(
        code=Op.PUSH1[0x46] + Op.CODECOPY(dest_offset=0x0, offset=0xf, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.CREATE + Op.STOP + Op.INVALID + Op.PUSH1[0x1f]
        + Op.CODECOPY(dest_offset=0x0, offset=0x27, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.SSTORE(key=0xa, value=Op.CREATE)
        + Op.SSTORE(key=0xb, value=Op.CALLCODE(gas=0x186a0, address=Op.SLOAD(key=0xa), value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP + Op.INVALID + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x0, offset=0xd, size=Op.DUP1) + Op.PUSH1[0x0]
        + Op.RETURN + Op.STOP + Op.INVALID + Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=0x14, value=Op.ADDRESS)
        + Op.SSTORE(key=0x15, value=Op.ORIGIN)
        + Op.SSTORE(key=0x16, value=Op.CALLER) + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address("0x3000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # {(seq (CREATE 0 0 (lll(seq       [[10]] (CREATE2 0 0 (lll(seq  (RETURN 0 (lll(seq [[0]] 1  [[20]] (ADDRESS)  [[21]] (ORIGIN) [[22]] (CALLER)  )0) )  )0)  0 )  [[11]] (CALLCODE 100000 (SLOAD 10) 0 0 64 0 64)            )0))       )}
    contract_4 = pre.deploy_contract(
        code=Op.PUSH1[0x48] + Op.CODECOPY(dest_offset=0x0, offset=0xf, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.CREATE + Op.STOP + Op.INVALID + Op.PUSH1[0x0]
        + Op.PUSH1[0x1f]
        + Op.CODECOPY(dest_offset=0x0, offset=0x29, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2 + Op.SSTORE(key=0xa, value=Op.CREATE2)
        + Op.SSTORE(key=0xb, value=Op.CALLCODE(gas=0x186a0, address=Op.SLOAD(key=0xa), value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP + Op.INVALID + Op.PUSH1[0x12]
        + Op.CODECOPY(dest_offset=0x0, offset=0xd, size=Op.DUP1) + Op.PUSH1[0x0]
        + Op.RETURN + Op.STOP + Op.INVALID + Op.SSTORE(key=0x0, value=0x1)
        + Op.SSTORE(key=0x14, value=Op.ADDRESS)
        + Op.SSTORE(key=0x15, value=Op.ORIGIN)
        + Op.SSTORE(key=0x16, value=Op.CALLER) + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address("0x4000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2386f26fc10000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_1: Account(
                storage={
            0: 1,
            10: 0x13136008b64ff592819b2fa6d43f2835c452020e,
            11: 1,
            20: 0x1000000000000000000000000000000000000000,
            21: 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b,
            22: 0x1000000000000000000000000000000000000000,
        },
            ),
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_2: Account(
                storage={
            0: 1,
            10: 0x2d39fad743351d4cf3f4717907d3dda5e0a689a7,
            11: 1,
            20: 0x2000000000000000000000000000000000000000,
            21: 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b,
            22: 0x2000000000000000000000000000000000000000,
        },
            ),
    },
        },
        {
            "indexes": {'data': 2, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0x4b86c4ed99b87f0f396bc0c76885453c343916ed"): Account(
                storage={
            0: 1,
            10: 0xbf1676be6038ab86d66e00824c2e3577858040f6,
            11: 1,
            20: 0x4b86c4ed99b87f0f396bc0c76885453c343916ed,
            21: 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b,
            22: 0x4b86c4ed99b87f0f396bc0c76885453c343916ed,
        },
                code=b"",
                balance=0,
                nonce=2,
            ),
    },
        },
        {
            "indexes": {'data': 3, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        Address("0xa51c188504a60578914fcae68f7a1f0dcbb856a9"): Account(
                storage={
            0: 1,
            10: 0xf2d6bf688fae45da62ab2dd4f36945bc924cc61,
            11: 1,
            20: 0xa51c188504a60578914fcae68f7a1f0dcbb856a9,
            21: 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b,
            22: 0xa51c188504a60578914fcae68f7a1f0dcbb856a9,
        },
                code=b"",
                balance=0,
                nonce=2,
            ),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
