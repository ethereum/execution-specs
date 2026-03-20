"""
Calls a contract that runs CREATE which deploy a code. then after...

Ported from:
tests/static/state_tests/stCreateTest/CreateOOGafterInitCodeRevert2Filler.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

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
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCreateTest/CreateOOGafterInitCodeRevert2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
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
    """Calls a contract that runs CREATE which deploy a code. then after..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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

    # Source: LLL
    # { (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xE8D4A51000,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: LLL
    # { (MSTORE 0 0x6460016001556000526005601bf3) (CREATE 0 18 14) (REVERT 0 32) }  # noqa: E501
    callee = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x6460016001556000526005601BF3)
            + Op.POP(Op.CREATE(value=0x0, offset=0x12, size=0xE))
            + Op.REVERT(offset=0x0, size=0x20)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: LLL
    # { (CALL 33000 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0 32) [[ 1 ]] (MLOAD 0) }  # noqa: E501
    callee_1 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x80E8,
                    address=0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x1: 0xFF},
        nonce=0,
        address=Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: LLL
    # { (CALL 23000 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0 32) [[ 1 ]] (MLOAD 0) }  # noqa: E501
    callee_2 = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x59D8,
                    address=0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x1: 0xFF},
        nonce=0,
        address=Address("0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex("600060006000600060006000355af100")
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "6d6460016001556000526005601bf3600052600e60126000f05060206000fd00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={1: 0x6460016001556000526005601BF3},
                    code=bytes.fromhex(
                        "6020600060006000600073b94f5374fce5edbc8e2a8697c15331677e6ebf0b6180e8f15060005160015500"  # noqa: E501
                    ),
                ),
                callee_2: Account(
                    storage={1: 255},
                    code=bytes.fromhex(
                        "6020600060006000600073b94f5374fce5edbc8e2a8697c15331677e6ebf0b6159d8f15060005160015500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex("600060006000600060006000355af100")
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "6d6460016001556000526005601bf3600052600e60126000f05060206000fd00"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={1: 255},
                    code=bytes.fromhex(
                        "6020600060006000600073b94f5374fce5edbc8e2a8697c15331677e6ebf0b6180e8f15060005160015500"  # noqa: E501
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "6020600060006000600073b94f5374fce5edbc8e2a8697c15331677e6ebf0b6159d8f15060005160015500"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
