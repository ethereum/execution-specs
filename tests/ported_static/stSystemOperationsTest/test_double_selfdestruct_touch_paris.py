"""
A single contract can execute SELFDESTRUCT multiple times using by...

multiple times. The second and later SELFDESTRUCTs have little effect but can
touch some new beneficiary addresses.

Ported from:
state_tests/stSystemOperationsTest/doubleSelfdestructTouch_ParisFiller.yml
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stSystemOperationsTest/doubleSelfdestructTouch_ParisFiller.yml"  # noqa: E501
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
            id="-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="-v1",
        ),
        pytest.param(
            0,
            0,
            2,
            id="-v2",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_double_selfdestruct_touch_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """A single contract can execute SELFDESTRUCT multiple times using by..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    empty_account_1 = Address(0x68FA59E127B7526718EB0A4E113DF5793628CB91)
    empty_account_2 = Address(0x76FAE819612A29489A1A43208613D8F8557B8898)
    sender = EOA(
        key=0xE92C121432830128CA66D3D8C4E6D8D96CC4BEFA7C612D28415082EB3C8339C5
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=999,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre[sender] = Account(balance=0x5F5E102)
    pre[empty_account_1] = Account(balance=10)
    pre[empty_account_2] = Account(balance=10)
    # Source: yul
    # berlin
    # {
    #   let index := add(sload(0), 1)
    #   sstore(0, index)
    #   selfdestruct(sload(index))
    # }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.ADD(Op.SLOAD(key=0x0), 0x1)
        + Op.SSTORE(key=0x0, value=Op.DUP1)
        + Op.SELFDESTRUCT(address=Op.SLOAD),
        storage={0: 0, 1: empty_account_1, 2: empty_account_2},
        nonce=0,
        address=Address(0x29E4504A3D2A0E0AE0EBBBEFEDD4570639B3EBEE),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   let v0 := callvalue()
    #   let v1 := shr(1, v0)
    #   let r1 := call(70000, <contract:0x000000000000000000000000000000000000dead>, v1, 0, 0, 0, 0)  # noqa: E501
    #   let v2 := sub(v0, v1)
    #   let r2 := call(70000, <contract:0x000000000000000000000000000000000000dead>, v2, 0, 0, 0, 0)  # noqa: E501
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.DUP1 * 3
        + Op.CALLVALUE
        + Op.SHR(0x1, Op.DUP1)
        + Op.SWAP1
        + Op.POP(
            Op.CALL(
                gas=0x11170,
                address=0x29E4504A3D2A0E0AE0EBBBEFEDD4570639B3EBEE,
                value=Op.DUP6,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=Op.DUP3,
            )
        )
        + Op.SUB
        + Op.PUSH20[0x29E4504A3D2A0E0AE0EBBBEFEDD4570639B3EBEE]
        + Op.PUSH3[0x11170]
        + Op.CALL
        + Op.STOP,
        nonce=0,
        address=Address(0x8EC7465877D3957084DC907C0F6D8F2911A17A52),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": -1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                target: Account(storage={}, balance=0, nonce=0),
                empty_account_1: Account(balance=10),
                empty_account_2: Account(balance=10),
            },
        },
        {
            "indexes": {"data": -1, "gas": -1, "value": 1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                target: Account(storage={}, balance=0, nonce=0),
                empty_account_1: Account(balance=10),
                empty_account_2: Account(balance=11, nonce=0),
            },
        },
        {
            "indexes": {"data": -1, "gas": -1, "value": 2},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                target: Account(storage={}, balance=0, nonce=0),
                empty_account_1: Account(balance=11, nonce=0),
                empty_account_2: Account(balance=11, nonce=0),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [10000000]
    tx_value = [0, 1, 2]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
