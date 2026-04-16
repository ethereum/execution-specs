"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stPreCompiledContracts2/ecrecoverWeirdVFiller.yml
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
    ["state_tests/stPreCompiledContracts2/ecrecoverWeirdVFiller.yml"],
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
            id="good",
        ),
        pytest.param(
            2,
            0,
            0,
            id="good",
        ),
        pytest.param(
            3,
            0,
            0,
            id="good",
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
            id="fail",
        ),
        pytest.param(
            7,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            8,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            9,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            10,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            11,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            12,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            13,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            14,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            15,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            16,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            17,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            18,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            19,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            20,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            21,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            22,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            23,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            24,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            25,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            26,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            27,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            28,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            29,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            30,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            31,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            32,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            33,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            34,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            35,
            0,
            0,
            id="fail",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_ecrecover_weird_v(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0xEB201D2887816E041F6E807E804F64F3A7A226FE)
    sender = EOA(
        key=0xDE0C95357363DA5C1C5A73BD7C2781CA5C9FECC1014103B5E1D1E990AE8208EC
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)
    # Source: yul
    # berlin
    # {
    #    let ecRecoverAddr := 1
    #
    #    // Call ecRecover
    #
    #    // Not the most efficient code, but it is more readable to see what each parameter means  # noqa: E501
    #    mstore(0x00, calldataload(0x04))    // msgHash
    #    mstore(0x20, calldataload(0x24))    // v
    #    mstore(0x40, calldataload(0x44))    // r
    #    mstore(0x60, calldataload(0x64))    // s
    #    let res := staticcall(gas(), ecRecoverAddr, 0, 0x80, 0x100, 0x100)
    #
    #    // write results
    #    sstore(0, res)
    #    sstore(1, mload(0x100))
    #    sstore(2, mload(0x120))
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH2[0x100]
        + Op.DUP1
        + Op.PUSH1[0x80]
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x1]
        + Op.MSTORE(offset=Op.DUP3, value=Op.CALLDATALOAD(offset=0x4))
        + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x24))
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x44))
        + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x64))
        + Op.GAS
        + Op.SSTORE(key=0x0, value=Op.STATICCALL)
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x100))
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x120))
        + Op.STOP,
        storage={0: 24743, 1: 24743, 2: 24743},
        nonce=1,
        address=Address(0x9121BB12ADE6BF12796E6007B21A204E05B1BD49),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [
                    0,
                    4,
                    5,
                    6,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    16,
                    17,
                    18,
                    19,
                    20,
                    21,
                    22,
                    23,
                    24,
                    25,
                    26,
                    27,
                    28,
                    29,
                    30,
                    31,
                    32,
                    33,
                    34,
                    35,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 1, 1: 0, 2: 0})},
        },
        {
            "indexes": {"data": [1, 2, 3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 1,
                        1: 0xB957B0DA344F6A17F0081D63BE7345A860E5B7A2,
                        2: 0,
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("917694f9")
        + Hash(0x7E57)
        + Hash(0x7E57)
        + Hash(0x7E57)
        + Hash(0x7E57),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x1B)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x1C)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(
            0xDEAF0DEAD0600D0F00D00000000000000060A70000000000000F0AD0BAD0BEEF
        )
        + Hash(0x1B)
        + Hash(
            0x8A41A35DFD03F28615DC64B7754457691C66BD73F630C7423280282FA431A5BE
        )
        + Hash(
            0x2D40DECF11713D564FA2DF10DEA5EB2ADF45455ED309B4C8CC6853E2498323F5
        ),
        Bytes("917694f9")
        + Hash(
            0xDAF5A779AE972F972197303D7B574746C7EF83EADAC0F2791AD23DB92E4C8E53
        )
        + Hash(0x25)
        + Hash(
            0x28EF61340BD939BC2195FE537567866003E1A15D3C71FF63E1590620AA636276
        )
        + Hash(
            0x67CBE9D8997F761AECB703304B3800CCF555C9F3DC64214B297FB1966A3B6D83
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x25)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x26)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x2F)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x30)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x39)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x3A)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x4D)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x4E)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x23)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x24)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0xEB)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0xEC)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x0)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x1)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x2)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x3)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x4)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x5)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x6)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x7)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x8)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0xFF)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x100)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x10FF)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x1100)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x100FF)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x10100)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0x123456FF)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0x12345700)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
        Bytes("917694f9")
        + Hash(0x0)
        + Hash(0xDEADBEEF00FF)
        + Hash(
            0xCE354E1B07BA96E325AA4851999F07AABCB4471E49F0A0DAAFED98CAAB963F03
        )
        + Hash(
            0x79D9F3993CDD509F1BFBA63DBD23DBDFF879FB95203A5049F348A95CE8249F3B
        ),
        Bytes("917694f9")
        + Hash(0x1)
        + Hash(0xDEADBEEF0100)
        + Hash(
            0x541C4CE1565A646DDDE26E1B483A88A6500CE15BD24622492F05CDD18B97161D
        )
        + Hash(
            0x1827E364C15CFA61DAB02339904B1E542F3939C6E8D6367D352026E71FFD6AF5
        ),
    ]
    tx_gas = [16777216]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
