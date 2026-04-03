"""
Test_jump_to_push.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/jumpToPushFiller.yml
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
    ["state_tests/VMTests/vmIOandFlowOperations/jumpToPushFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            1,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            2,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            3,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            4,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            5,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            6,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            7,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            8,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            9,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            10,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            11,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            12,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            13,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            14,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            15,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            16,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            17,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            18,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            19,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            20,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            21,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            22,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            23,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            24,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            25,
            0,
            0,
            id="jump-ok",
        ),
        pytest.param(
            26,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            27,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            28,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            29,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            30,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            31,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            32,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            33,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            34,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            35,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            36,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            37,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            38,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            39,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            40,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            41,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            42,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            43,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            44,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            45,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            46,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            47,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            48,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            49,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            50,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            51,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            52,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            53,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            54,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            55,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            56,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            57,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            58,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            59,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            60,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            61,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            62,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            63,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            64,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            65,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            66,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            67,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            68,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            69,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            70,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            71,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            72,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            73,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            74,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            75,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            76,
            0,
            0,
            id="jump-fail",
        ),
        pytest.param(
            77,
            0,
            0,
            id="jump-fail",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_jump_to_push(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_jump_to_push."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x000000000000000000000000000000000000001A)
    contract_1 = Address(0x000000000000000000000000000000000000001B)
    contract_2 = Address(0x000000000000000000000000000000000000002A)
    contract_3 = Address(0x000000000000000000000000000000000000002B)
    contract_4 = Address(0x000000000000000000000000000000000000002C)
    contract_5 = Address(0x000000000000000000000000000000000000003A)
    contract_6 = Address(0x000000000000000000000000000000000000003B)
    contract_7 = Address(0x000000000000000000000000000000000000003C)
    contract_8 = Address(0x000000000000000000000000000000000000004A)
    contract_9 = Address(0x000000000000000000000000000000000000004B)
    contract_10 = Address(0x000000000000000000000000000000000000004C)
    contract_11 = Address(0x000000000000000000000000000000000000005A)
    contract_12 = Address(0x000000000000000000000000000000000000005B)
    contract_13 = Address(0x000000000000000000000000000000000000005C)
    contract_14 = Address(0x000000000000000000000000000000000000006A)
    contract_15 = Address(0x000000000000000000000000000000000000006B)
    contract_16 = Address(0x000000000000000000000000000000000000006C)
    contract_17 = Address(0x000000000000000000000000000000000000007A)
    contract_18 = Address(0x000000000000000000000000000000000000007B)
    contract_19 = Address(0x000000000000000000000000000000000000007C)
    contract_20 = Address(0x000000000000000000000000000000000000008A)
    contract_21 = Address(0x000000000000000000000000000000000000008B)
    contract_22 = Address(0x000000000000000000000000000000000000008C)
    contract_23 = Address(0x000000000000000000000000000000000000009A)
    contract_24 = Address(0x000000000000000000000000000000000000009B)
    contract_25 = Address(0x000000000000000000000000000000000000009C)
    contract_26 = Address(0x00000000000000000000000000000000000000AA)
    contract_27 = Address(0x00000000000000000000000000000000000000AB)
    contract_28 = Address(0x00000000000000000000000000000000000000AC)
    contract_29 = Address(0x00000000000000000000000000000000000000BA)
    contract_30 = Address(0x00000000000000000000000000000000000000BB)
    contract_31 = Address(0x00000000000000000000000000000000000000BC)
    contract_32 = Address(0x00000000000000000000000000000000000000CA)
    contract_33 = Address(0x00000000000000000000000000000000000000CB)
    contract_34 = Address(0x00000000000000000000000000000000000000CC)
    contract_35 = Address(0x00000000000000000000000000000000000000DA)
    contract_36 = Address(0x00000000000000000000000000000000000000DB)
    contract_37 = Address(0x00000000000000000000000000000000000000DC)
    contract_38 = Address(0x00000000000000000000000000000000000000EA)
    contract_39 = Address(0x00000000000000000000000000000000000000EB)
    contract_40 = Address(0x00000000000000000000000000000000000000EC)
    contract_41 = Address(0x00000000000000000000000000000000000000FA)
    contract_42 = Address(0x00000000000000000000000000000000000000FB)
    contract_43 = Address(0x00000000000000000000000000000000000000FC)
    contract_44 = Address(0x000000000000000000000000000000000000010A)
    contract_45 = Address(0x000000000000000000000000000000000000010B)
    contract_46 = Address(0x000000000000000000000000000000000000010C)
    contract_47 = Address(0x000000000000000000000000000000000000011A)
    contract_48 = Address(0x000000000000000000000000000000000000011B)
    contract_49 = Address(0x000000000000000000000000000000000000011C)
    contract_50 = Address(0x000000000000000000000000000000000000012A)
    contract_51 = Address(0x000000000000000000000000000000000000012B)
    contract_52 = Address(0x000000000000000000000000000000000000012C)
    contract_53 = Address(0x000000000000000000000000000000000000013A)
    contract_54 = Address(0x000000000000000000000000000000000000013B)
    contract_55 = Address(0x000000000000000000000000000000000000013C)
    contract_56 = Address(0x000000000000000000000000000000000000014A)
    contract_57 = Address(0x000000000000000000000000000000000000014B)
    contract_58 = Address(0x000000000000000000000000000000000000014C)
    contract_59 = Address(0x000000000000000000000000000000000000015A)
    contract_60 = Address(0x000000000000000000000000000000000000015B)
    contract_61 = Address(0x000000000000000000000000000000000000015C)
    contract_62 = Address(0x000000000000000000000000000000000000016A)
    contract_63 = Address(0x000000000000000000000000000000000000016B)
    contract_64 = Address(0x000000000000000000000000000000000000016C)
    contract_65 = Address(0x000000000000000000000000000000000000017A)
    contract_66 = Address(0x000000000000000000000000000000000000017B)
    contract_67 = Address(0x000000000000000000000000000000000000017C)
    contract_68 = Address(0x000000000000000000000000000000000000018A)
    contract_69 = Address(0x000000000000000000000000000000000000018B)
    contract_70 = Address(0x000000000000000000000000000000000000018C)
    contract_71 = Address(0x000000000000000000000000000000000000019A)
    contract_72 = Address(0x000000000000000000000000000000000000019B)
    contract_73 = Address(0x000000000000000000000000000000000000019C)
    contract_74 = Address(0x00000000000000000000000000000000000001AA)
    contract_75 = Address(0x00000000000000000000000000000000000001AB)
    contract_76 = Address(0x00000000000000000000000000000000000001AC)
    contract_77 = Address(0x00000000000000000000000000000000000001BA)
    contract_78 = Address(0x00000000000000000000000000000000000001BB)
    contract_79 = Address(0x00000000000000000000000000000000000001BC)
    contract_80 = Address(0x00000000000000000000000000000000000001CA)
    contract_81 = Address(0x00000000000000000000000000000000000001CB)
    contract_82 = Address(0x00000000000000000000000000000000000001CC)
    contract_83 = Address(0x00000000000000000000000000000000000001DA)
    contract_84 = Address(0x00000000000000000000000000000000000001DB)
    contract_85 = Address(0x00000000000000000000000000000000000001DC)
    contract_86 = Address(0x00000000000000000000000000000000000001EA)
    contract_87 = Address(0x00000000000000000000000000000000000001EB)
    contract_88 = Address(0x00000000000000000000000000000000000001EC)
    contract_89 = Address(0x00000000000000000000000000000000000001FA)
    contract_90 = Address(0x00000000000000000000000000000000000001FB)
    contract_91 = Address(0x00000000000000000000000000000000000001FC)
    contract_92 = Address(0x000000000000000000000000000000000000020A)
    contract_93 = Address(0x000000000000000000000000000000000000020B)
    contract_94 = Address(0x000000000000000000000000000000000000020C)
    contract_95 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw
    # 0x6001600055600A56605B5B
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0xA)
        + Op.PUSH1[0x5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000001A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956605B5B
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH1[0x5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000001B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600B56615B5B5B
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0xB)
        + Op.PUSH2[0x5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000002A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956615B5B5B
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH2[0x5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000002B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600A56615B5B5B
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0xA)
        + Op.PUSH2[0x5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000002C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600C56625B5B5B5B
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0xC)
        + Op.PUSH3[0x5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000003A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956625B5B5B5B
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH3[0x5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000003B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600B56625B5B5B5B
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0xB)
        + Op.PUSH3[0x5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000003C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600D56635B5B5B5B5B
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0xD)
        + Op.PUSH4[0x5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000004A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956635B5B5B5B5B
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH4[0x5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000004B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600C56635B5B5B5B5B
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0xC)
        + Op.PUSH4[0x5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000004C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600E56645B5B5B5B5B5B
    contract_11 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0xE)
        + Op.PUSH5[0x5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000005A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956645B5B5B5B5B5B
    contract_12 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH5[0x5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000005B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600D56645B5B5B5B5B5B
    contract_13 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0xD)
        + Op.PUSH5[0x5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000005C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600F56655B5B5B5B5B5B5B
    contract_14 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0xF)
        + Op.PUSH6[0x5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000006A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956655B5B5B5B5B5B5B
    contract_15 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH6[0x5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000006B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600E56655B5B5B5B5B5B5B
    contract_16 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0xE)
        + Op.PUSH6[0x5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000006C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601056665B5B5B5B5B5B5B5B
    contract_17 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x10)
        + Op.PUSH7[0x5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000007A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956665B5B5B5B5B5B5B5B
    contract_18 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH7[0x5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000007B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600F56665B5B5B5B5B5B5B5B
    contract_19 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0xF)
        + Op.PUSH7[0x5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000007C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601156675B5B5B5B5B5B5B5B5B
    contract_20 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x11)
        + Op.PUSH8[0x5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000008A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956675B5B5B5B5B5B5B5B5B
    contract_21 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH8[0x5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000008B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601056675B5B5B5B5B5B5B5B5B
    contract_22 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x10)
        + Op.PUSH8[0x5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000008C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601256685B5B5B5B5B5B5B5B5B5B
    contract_23 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x12)
        + Op.PUSH9[0x5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000009A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956685B5B5B5B5B5B5B5B5B5B
    contract_24 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH9[0x5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000009B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601156685B5B5B5B5B5B5B5B5B5B
    contract_25 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x11)
        + Op.PUSH9[0x5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000009C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601356695B5B5B5B5B5B5B5B5B5B5B
    contract_26 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x13)
        + Op.PUSH10[0x5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000AA),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956695B5B5B5B5B5B5B5B5B5B5B
    contract_27 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH10[0x5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000AB),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601256695B5B5B5B5B5B5B5B5B5B5B
    contract_28 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x12)
        + Op.PUSH10[0x5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000AC),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556014566A5B5B5B5B5B5B5B5B5B5B5B5B
    contract_29 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x14)
        + Op.PUSH11[0x5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000BA),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556009566A5B5B5B5B5B5B5B5B5B5B5B5B
    contract_30 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH11[0x5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000BB),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556013566A5B5B5B5B5B5B5B5B5B5B5B5B
    contract_31 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x13)
        + Op.PUSH11[0x5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000BC),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556015566B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_32 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x15)
        + Op.PUSH12[0x5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000CA),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556009566B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_33 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH12[0x5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000CB),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556014566B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_34 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x14)
        + Op.PUSH12[0x5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000CC),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556016566C5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_35 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x16)
        + Op.PUSH13[0x5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000DA),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556009566C5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_36 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH13[0x5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000DB),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556015566C5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_37 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x15)
        + Op.PUSH13[0x5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000DC),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556017566D5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_38 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x17)
        + Op.PUSH14[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000EA),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556009566D5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_39 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH14[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000EB),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556016566D5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_40 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x16)
        + Op.PUSH14[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000EC),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556018566E5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_41 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x18)
        + Op.PUSH15[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000FA),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556009566E5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_42 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH15[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000FB),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556017566E5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_43 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x17)
        + Op.PUSH15[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000000FC),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556019566F5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_44 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x19)
        + Op.PUSH16[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000010A),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556009566F5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_45 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH16[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000010B),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556018566F5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_46 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x18)
        + Op.PUSH16[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000010C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601A56705B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_47 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x1A)
        + Op.PUSH17[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000011A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956705B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_48 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH17[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000011B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601956705B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_49 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x19)
        + Op.PUSH17[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000011C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601B56715B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_50 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x1B)
        + Op.PUSH18[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000012A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956715B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_51 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH18[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000012B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601A56715B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_52 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x1A)
        + Op.PUSH18[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000012C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601C56725B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_53 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x1C)
        + Op.PUSH19[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000013A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956725B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_54 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH19[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000013B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601B56725B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_55 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x1B)
        + Op.PUSH19[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000013C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601D56735B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_56 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x1D)
        + Op.PUSH20[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000014A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956735B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_57 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH20[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000014B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601C56735B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_58 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x1C)
        + Op.PUSH20[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000014C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601E56745B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_59 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x1E)
        + Op.PUSH21[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000015A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956745B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_60 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH21[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000015B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601D56745B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_61 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x1D)
        + Op.PUSH21[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000015C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601F56755B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_62 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x1F)
        + Op.PUSH22[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000016A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956755B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_63 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH22[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000016B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601E56755B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_64 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x1E)
        + Op.PUSH22[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000016C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055602056765B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_65 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x20)
        + Op.PUSH23[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000017A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956765B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_66 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH23[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000017B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055601F56765B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_67 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x1F)
        + Op.PUSH23[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000017C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055602156775B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_68 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x21)
        + Op.PUSH24[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000018A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956775B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_69 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH24[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000018B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055602056775B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_70 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x20)
        + Op.PUSH24[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000018C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055602256785B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_71 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x22)
        + Op.PUSH25[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000019A),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956785B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_72 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH25[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000019B),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055602156785B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
    contract_73 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x21)
        + Op.PUSH25[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000019C),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055602356795B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_74 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x23)
        + Op.PUSH26[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001AA),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055600956795B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_75 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH26[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001AB),  # noqa: E501
    )
    # Source: raw
    # 0x6001600055602256795B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_76 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x22)
        + Op.PUSH26[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001AC),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556024567A5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_77 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x24)
        + Op.PUSH27[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001BA),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556009567A5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_78 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH27[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001BB),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556023567A5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_79 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x23)
        + Op.PUSH27[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001BC),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556025567B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_80 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x25)
        + Op.PUSH28[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001CA),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556009567B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_81 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH28[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001CB),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556024567B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_82 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x24)
        + Op.PUSH28[0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001CC),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556026567C5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_83 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x26)
        + Op.PUSH29[
            0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
        ]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001DA),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556009567C5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_84 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH29[
            0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
        ]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001DB),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556025567C5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_85 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x25)
        + Op.PUSH29[
            0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
        ]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001DC),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556027567D5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_86 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x27)
        + Op.PUSH30[
            0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
        ]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001EA),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556009567D5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_87 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH30[
            0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
        ]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001EB),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556026567D5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_88 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x26)
        + Op.PUSH30[
            0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
        ]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001EC),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556028567E5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_89 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x28)
        + Op.PUSH31[
            0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
        ]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001FA),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556009567E5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_90 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH31[
            0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
        ]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001FB),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556027567E5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_91 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x27)
        + Op.PUSH31[
            0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
        ]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000001FC),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556029567F5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_92 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x29)
        + Op.PUSH32[
            0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
        ]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000020A),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556009567F5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_93 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x9)
        + Op.PUSH32[
            0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
        ]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000020B),  # noqa: E501
    )
    # Source: raw
    # 0x60016000556028567F5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B  # noqa: E501
    contract_94 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x1)
        + Op.JUMP(pc=0x28)
        + Op.PUSH32[
            0x5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B5B
        ]
        + Op.JUMPDEST,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000020C),  # noqa: E501
    )
    # Source: yul
    # berlin {
    #   let addr := calldataload(4)
    #   pop(delegatecall(sub(gas(), 5000), addr, 0, 0, 0, 0))
    # }
    contract_95 = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=Op.SUB(Op.GAS, 0x1388),
            address=Op.CALLDATALOAD(offset=0x4),
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        storage={0: 0},
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [
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
                    36,
                    37,
                    38,
                    39,
                    40,
                    41,
                    42,
                    43,
                    44,
                    45,
                    46,
                    47,
                    48,
                    49,
                    50,
                    51,
                    52,
                    53,
                    54,
                    55,
                    56,
                    57,
                    58,
                    59,
                    60,
                    61,
                    62,
                    63,
                    64,
                    65,
                    66,
                    67,
                    68,
                    69,
                    70,
                    71,
                    72,
                    73,
                    74,
                    75,
                    76,
                    77,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_95: Account(storage={0: 0})},
        },
        {
            "indexes": {
                "data": [
                    0,
                    1,
                    2,
                    3,
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
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_95: Account(storage={0: 1})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(contract_0, left_padding=True),
        Bytes("693c6139") + Hash(contract_2, left_padding=True),
        Bytes("693c6139") + Hash(contract_5, left_padding=True),
        Bytes("693c6139") + Hash(contract_8, left_padding=True),
        Bytes("693c6139") + Hash(contract_11, left_padding=True),
        Bytes("693c6139") + Hash(contract_14, left_padding=True),
        Bytes("693c6139") + Hash(contract_17, left_padding=True),
        Bytes("693c6139") + Hash(contract_20, left_padding=True),
        Bytes("693c6139") + Hash(contract_23, left_padding=True),
        Bytes("693c6139") + Hash(contract_26, left_padding=True),
        Bytes("693c6139") + Hash(contract_29, left_padding=True),
        Bytes("693c6139") + Hash(contract_32, left_padding=True),
        Bytes("693c6139") + Hash(contract_35, left_padding=True),
        Bytes("693c6139") + Hash(contract_38, left_padding=True),
        Bytes("693c6139") + Hash(contract_41, left_padding=True),
        Bytes("693c6139") + Hash(contract_44, left_padding=True),
        Bytes("693c6139") + Hash(contract_47, left_padding=True),
        Bytes("693c6139") + Hash(contract_50, left_padding=True),
        Bytes("693c6139") + Hash(contract_53, left_padding=True),
        Bytes("693c6139") + Hash(contract_56, left_padding=True),
        Bytes("693c6139") + Hash(contract_59, left_padding=True),
        Bytes("693c6139") + Hash(contract_62, left_padding=True),
        Bytes("693c6139") + Hash(contract_65, left_padding=True),
        Bytes("693c6139") + Hash(contract_68, left_padding=True),
        Bytes("693c6139") + Hash(contract_71, left_padding=True),
        Bytes("693c6139") + Hash(contract_92, left_padding=True),
        Bytes("693c6139") + Hash(0x1C),
        Bytes("693c6139") + Hash(contract_4, left_padding=True),
        Bytes("693c6139") + Hash(contract_7, left_padding=True),
        Bytes("693c6139") + Hash(contract_10, left_padding=True),
        Bytes("693c6139") + Hash(contract_13, left_padding=True),
        Bytes("693c6139") + Hash(contract_16, left_padding=True),
        Bytes("693c6139") + Hash(contract_19, left_padding=True),
        Bytes("693c6139") + Hash(contract_22, left_padding=True),
        Bytes("693c6139") + Hash(contract_25, left_padding=True),
        Bytes("693c6139") + Hash(contract_28, left_padding=True),
        Bytes("693c6139") + Hash(contract_31, left_padding=True),
        Bytes("693c6139") + Hash(contract_34, left_padding=True),
        Bytes("693c6139") + Hash(contract_37, left_padding=True),
        Bytes("693c6139") + Hash(contract_40, left_padding=True),
        Bytes("693c6139") + Hash(contract_43, left_padding=True),
        Bytes("693c6139") + Hash(contract_46, left_padding=True),
        Bytes("693c6139") + Hash(contract_49, left_padding=True),
        Bytes("693c6139") + Hash(contract_52, left_padding=True),
        Bytes("693c6139") + Hash(contract_55, left_padding=True),
        Bytes("693c6139") + Hash(contract_58, left_padding=True),
        Bytes("693c6139") + Hash(contract_61, left_padding=True),
        Bytes("693c6139") + Hash(contract_64, left_padding=True),
        Bytes("693c6139") + Hash(contract_67, left_padding=True),
        Bytes("693c6139") + Hash(contract_70, left_padding=True),
        Bytes("693c6139") + Hash(contract_73, left_padding=True),
        Bytes("693c6139") + Hash(contract_94, left_padding=True),
        Bytes("693c6139") + Hash(0x1C),
        Bytes("693c6139") + Hash(contract_4, left_padding=True),
        Bytes("693c6139") + Hash(contract_7, left_padding=True),
        Bytes("693c6139") + Hash(contract_10, left_padding=True),
        Bytes("693c6139") + Hash(contract_13, left_padding=True),
        Bytes("693c6139") + Hash(contract_16, left_padding=True),
        Bytes("693c6139") + Hash(contract_19, left_padding=True),
        Bytes("693c6139") + Hash(contract_22, left_padding=True),
        Bytes("693c6139") + Hash(contract_25, left_padding=True),
        Bytes("693c6139") + Hash(contract_28, left_padding=True),
        Bytes("693c6139") + Hash(contract_31, left_padding=True),
        Bytes("693c6139") + Hash(contract_34, left_padding=True),
        Bytes("693c6139") + Hash(contract_37, left_padding=True),
        Bytes("693c6139") + Hash(contract_40, left_padding=True),
        Bytes("693c6139") + Hash(contract_43, left_padding=True),
        Bytes("693c6139") + Hash(contract_46, left_padding=True),
        Bytes("693c6139") + Hash(contract_49, left_padding=True),
        Bytes("693c6139") + Hash(contract_52, left_padding=True),
        Bytes("693c6139") + Hash(contract_55, left_padding=True),
        Bytes("693c6139") + Hash(contract_58, left_padding=True),
        Bytes("693c6139") + Hash(contract_61, left_padding=True),
        Bytes("693c6139") + Hash(contract_64, left_padding=True),
        Bytes("693c6139") + Hash(contract_67, left_padding=True),
        Bytes("693c6139") + Hash(contract_70, left_padding=True),
        Bytes("693c6139") + Hash(contract_73, left_padding=True),
        Bytes("693c6139") + Hash(contract_94, left_padding=True),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_95,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
