"""
Test_revert_opcode_return.

Ported from:
state_tests/stRevertTest/RevertOpcodeReturnFiller.json
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
    "0000000000000000000000001963fd2c717f5b4b9fa3d6baf38d66241e1ec005",
    "000000000000000000000000745e52346d8549444323699e9fc383ae89bdd24f",
    "00000000000000000000000050eaca0a040ac6242d0c01cc1ff82f5b95cc10e4",
    "000000000000000000000000f933d2374d5875de033a8ed9d9c1ce5dea25c78b",
    "000000000000000000000000e5b2dfe7f932f2d5eaa7c8fb2e1e9a8b6a846fd7",
    "000000000000000000000000858f82bbfd84fc9eb91291458511df77311dbd0d",
]
TX_GAS = [800000, 80000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stRevertTest/RevertOpcodeReturnFiller.json"],
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
        pytest.param(
            4,
            0,
            0,
            id="d4-g0",
        ),
        pytest.param(
            4,
            1,
            0,
            id="d4-g1",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5-g0",
        ),
        pytest.param(
            5,
            1,
            0,
            id="d5-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_return(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_revert_opcode_return."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
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

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { [[1]](CALL 150000 (CALLDATALOAD 0) 0 0 0 0 32) [[2]] (MLOAD 0) }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0x249F0,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        nonce=0,
        address=Address("0x1fc98371f1a058f1a6042e30a141aa8bb67dd1bc"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x72657665727465642064617461) (MSTORE 0 0x726576657274206d657373616765) (REVERT 0 32) }  # noqa: E501
    addr_0xa100000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
        + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
        + Op.REVERT(offset=0x0, size=0x20)
        + Op.STOP,
        nonce=0,
        address=Address("0x1963fd2c717f5b4b9fa3d6baf38d66241e1ec005"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x72657665727465642064617461) (MSTORE 0 0x726576657274206d657373616765) (REVERT 0 0) }  # noqa: E501
    addr_0xa200000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
        + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
        + Op.REVERT(offset=0x0, size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0x745e52346d8549444323699e9fc383ae89bdd24f"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x72657665727465642064617461) (MSTORE 0 0x726576657274206d657373616765) (REVERT 0 0xfffffffffffffffffffffffffffff) }  # noqa: E501
    addr_0xa300000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
        + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
        + Op.REVERT(offset=0x0, size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.STOP,
        nonce=0,
        address=Address("0x50eaca0a040ac6242d0c01cc1ff82f5b95cc10e4"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x72657665727465642064617461) (MSTORE 0 0x726576657274206d657373616765) (REVERT 0x0100 0x00) }  # noqa: E501
    addr_0xa400000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
        + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
        + Op.REVERT(offset=0x100, size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0xf933d2374d5875de033a8ed9d9c1ce5dea25c78b"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x72657665727465642064617461) (MSTORE 0 0x726576657274206d657373616765) (REVERT 0x01 0x00) }  # noqa: E501
    addr_0xa500000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
        + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
        + Op.REVERT(offset=0x1, size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0xe5b2dfe7f932f2d5eaa7c8fb2e1e9a8b6a846fd7"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x72657665727465642064617461) (MSTORE 0 0x726576657274206d657373616765) (REVERT 0xfffffffffffffffffffffffffffff 0x00) }  # noqa: E501
    addr_0xa600000000000000000000000000000000000000 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
        + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
        + Op.REVERT(offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0x858f82bbfd84fc9eb91291458511df77311dbd0d"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                target: Account(
                    storage={1: 0, 2: 0x726576657274206D657373616765}
                ),
                addr_0xa100000000000000000000000000000000000000: Account(
                    storage={}
                ),
            },
        },
        {
            "indexes": {"data": [1, 2, 3, 4, 5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                target: Account(storage={1: 0, 2: 0}),
                addr_0xa100000000000000000000000000000000000000: Account(
                    storage={}
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
