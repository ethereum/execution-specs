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
        address=Address(0x1FC98371F1A058F1A6042E30A141AA8BB67DD1BC),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x72657665727465642064617461) (MSTORE 0 0x726576657274206d657373616765) (REVERT 0 32) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
        + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
        + Op.REVERT(offset=0x0, size=0x20)
        + Op.STOP,
        nonce=0,
        address=Address(0x1963FD2C717F5B4B9FA3D6BAF38D66241E1EC005),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x72657665727465642064617461) (MSTORE 0 0x726576657274206d657373616765) (REVERT 0 0) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
        + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
        + Op.REVERT(offset=0x0, size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address(0x745E52346D8549444323699E9FC383AE89BDD24F),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x72657665727465642064617461) (MSTORE 0 0x726576657274206d657373616765) (REVERT 0 0xfffffffffffffffffffffffffffff) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
        + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
        + Op.REVERT(offset=0x0, size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.STOP,
        nonce=0,
        address=Address(0x50EACA0A040AC6242D0C01CC1FF82F5B95CC10E4),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x72657665727465642064617461) (MSTORE 0 0x726576657274206d657373616765) (REVERT 0x0100 0x00) }  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
        + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
        + Op.REVERT(offset=0x100, size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address(0xF933D2374D5875DE033A8ED9D9C1CE5DEA25C78B),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x72657665727465642064617461) (MSTORE 0 0x726576657274206d657373616765) (REVERT 0x01 0x00) }  # noqa: E501
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
        + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
        + Op.REVERT(offset=0x1, size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address(0xE5B2DFE7F932F2D5EAA7C8FB2E1E9A8B6A846FD7),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 0x72657665727465642064617461) (MSTORE 0 0x726576657274206d657373616765) (REVERT 0xfffffffffffffffffffffffffffff 0x00) }  # noqa: E501
    addr_6 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
        + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
        + Op.REVERT(offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address(0x858F82BBFD84FC9EB91291458511DF77311DBD0D),  # noqa: E501
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
                addr: Account(storage={}),
            },
        },
        {
            "indexes": {"data": [1, 2, 3, 4, 5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                target: Account(storage={1: 0, 2: 0}),
                addr: Account(storage={}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
        Hash(addr_4, left_padding=True),
        Hash(addr_5, left_padding=True),
        Hash(addr_6, left_padding=True),
    ]
    tx_gas = [800000, 80000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
