"""
Test_call_ecrecover_overflow.

Ported from:
state_tests/stPreCompiledContracts2/CallEcrecover_OverflowFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
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
    ["state_tests/stPreCompiledContracts2/CallEcrecover_OverflowFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            1,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            2,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            3,
            0,
            0,
            id="pass01",
        ),
        pytest.param(
            4,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            5,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            6,
            0,
            0,
            id="pass02",
        ),
        pytest.param(
            7,
            0,
            0,
            id="pass03",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_call_ecrecover_overflow(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_call_ecrecover_overflow."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    # Source: yul
    # berlin
    # {
    #  // Copy Hash, V, R, S values
    #  calldatacopy(0x00, 0x04, 0x80)
    #
    #  // Call the EC Recover Precompile
    #  sstore(0, call(3000, 1, 0, 0, 0x80, 0x80, 0x20))
    #  sstore(1, mload(0x80))
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATACOPY(dest_offset=0x0, offset=0x4, size=0x80)
        + Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0xBB8,
                address=0x1,
                value=Op.DUP1,
                args_offset=0x0,
                args_size=Op.DUP1,
                ret_offset=0x80,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
        + Op.STOP,
        nonce=0,
        address=Address(0xDB8963071FEAE3B63E19D9D7AF8EE89A92E99356),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 1, 2, 4, 5], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 1, 1: 0})},
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 1,
                        1: 0x2182DA748249A933BF737586B80212DF19B8F829,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 1,
                        1: 0x1B85AC3C9B09DE43659C5D04A2D9C75457D9ABF4,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 1,
                        1: 0xD0277C8A3ECCD462A313FC60161BAC36B16E8699,
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("917694f9")
        + Hash(
            0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C
        )
        + Hash(0x1C)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
        )
        + Hash(
            0x1FFFD310AC743F371DE3B9F7F9CB56C0B28AD43601B4AB949F53FAA07BD2C804
        ),
        Bytes("917694f9")
        + Hash(
            0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C
        )
        + Hash(0x1C)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364142
        )
        + Hash(
            0x1FFFD310AC743F371DE3B9F7F9CB56C0B28AD43601B4AB949F53FAA07BD2C804
        ),
        Bytes("917694f9")
        + Hash(
            0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C
        )
        + Hash(0x1C)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364140
        )
        + Hash(
            0xEFFFD310AC743F371DE3B9F7F9CB56C0B28AD43601B4AB949F53FAA07BD2C804
        ),
        Bytes("917694f9")
        + Hash(
            0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C
        )
        + Hash(0x1C)
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD036413F
        )
        + Hash(
            0xEFFFD310AC743F371DE3B9F7F9CB56C0B28AD43601B4AB949F53FAA07BD2C804
        ),
        Bytes("917694f9")
        + Hash(
            0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C
        )
        + Hash(0x1C)
        + Hash(
            0x48B55BFA915AC795C431978D8A6A992B628D557DA5FF759B307D495A36649353
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
        ),
        Bytes("917694f9")
        + Hash(
            0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C
        )
        + Hash(0x1C)
        + Hash(
            0x48B55BFA915AC795C431978D8A6A992B628D557DA5FF759B307D495A36649353
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364142
        ),
        Bytes("917694f9")
        + Hash(
            0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C
        )
        + Hash(0x1C)
        + Hash(
            0x48B55BFA915AC795C431978D8A6A992B628D557DA5FF759B307D495A36649353
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364140
        ),
        Bytes("917694f9")
        + Hash(
            0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C
        )
        + Hash(0x1C)
        + Hash(
            0x48B55BFA915AC795C431978D8A6A992B628D557DA5FF759B307D495A36649353
        )
        + Hash(
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD036413F
        ),
    ]
    tx_gas = [100000]
    tx_value = [100000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
