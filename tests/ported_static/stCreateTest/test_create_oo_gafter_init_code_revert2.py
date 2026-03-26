"""
Calls a contract that runs CREATE which deploy a code. then after deployment and exiting from CREATE a REVERT is called. check the REVERT data in this case equal to RETURN value of CREATE. CREATE fails due to the deployment cost.

Ported from:
state_tests/stCreateTest/CreateOOGafterInitCodeRevert2Filler.json
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
    "000000000000000000000000c94f5374fce5edbc8e2a8697c15331677e6ebf0b",
    "000000000000000000000000d94f5374fce5edbc8e2a8697c15331677e6ebf0b",
]
TX_GAS = [175000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateOOGafterInitCodeRevert2Filler.json"],
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_oo_gafter_init_code_revert2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Calls a contract that runs CREATE which deploy a code."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x1000000000000000000000000000000000000000")
    contract_1 = Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_2 = Address("0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_3 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
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
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_0 = pre.deploy_contract(
        code=Op.CALL(gas=Op.GAS, address=Op.CALLDATALOAD(offset=0x0), value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0)
        + Op.STOP,
        balance=0xe8d4a51000,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # { (CALL 33000 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0 32) [[ 1 ]] (MLOAD 0) }
    contract_1 = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x80e8, address=0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x20))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0)) + Op.STOP,
        storage={1: 255},
        nonce=0,
        address=Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: lll
    # { (CALL 23000 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0 32) [[ 1 ]] (MLOAD 0) }
    contract_2 = pre.deploy_contract(
        code=Op.POP(Op.CALL(gas=0x59d8, address=0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x20))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0)) + Op.STOP,
        storage={1: 255},
        nonce=0,
        address=Address("0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 0x6460016001556000526005601bf3) (CREATE 0 18 14) (REVERT 0 32) }
    contract_3 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x6460016001556000526005601bf3)
        + Op.POP(Op.CREATE(value=0x0, offset=0x12, size=0xe))
        + Op.REVERT(offset=0x0, size=0x20) + Op.STOP,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_1: Account(storage={1: 0x6460016001556000526005601bf3}),
        Address("0xf1ecf98489fa9ed60a664fc4998db699cfa39d40"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': 1, 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_2: Account(storage={1: 0}),
        Address("0xf1ecf98489fa9ed60a664fc4998db699cfa39d40"): Account.NONEXISTENT,  # noqa: E501
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
