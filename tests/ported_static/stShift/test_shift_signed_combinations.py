"""
Https://github.com/ethereum/tests/issues/564.

Ported from:
state_tests/stShift/shiftSignedCombinationsFiller.yml
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stShift/shiftSignedCombinationsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_shift_signed_combinations(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Https://github."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # {
    #   (def 'sstore_n 0)
    #   (MSTORE sstore_n 0x0ff)
    #
    #   ;; Number of the first args
    #   (def 'counter_i 32)
    #   (def 'counter_i_max 6)
    #
    #   ;; Number of the second args
    #   (def 'counter_j 64)
    #   (def 'counter_j_max 14)
    #
    #   ;; Set of the first args
    #   (def 'data_istart 10100)
    #   (MSTORE (ADD data_istart (MUL 32 0)) 0x0000000000000000000000000000000000000000000000000000000000000080)  # noqa: E501
    #   (MSTORE (ADD data_istart (MUL 32 1)) 0x0000000000000000000000000000000000000000000000000000000000008000)  # noqa: E501
    #   (MSTORE (ADD data_istart (MUL 32 2)) 0x0000000000000000000000000000000000000000000000000000000080000000)  # noqa: E501
    #   (MSTORE (ADD data_istart (MUL 32 3)) 0x0000000000000000000000000000000000000000000000008000000000000000)  # noqa: E501
    #   (MSTORE (ADD data_istart (MUL 32 4)) 0x0000000000000000000000000000000080000000000000000000000000000000)  # noqa: E501
    #   (MSTORE (ADD data_istart (MUL 32 5)) 0x8000000000000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #
    #   ;; Set of the second args
    #   (def 'data_jstart 20100)
    #   (MSTORE (ADD data_jstart (MUL 32 0)) 0x0000000000000000000000000000000000000000000000000000000000000000)  # noqa: E501
    #   (MSTORE (ADD data_jstart (MUL 32 1)) 0x0000000000000000000000000000000000000000000000000000000000000001)  # noqa: E501
    #   (MSTORE (ADD data_jstart (MUL 32 2)) 0x0000000000000000000000000000000000000000000000000000000000000002)  # noqa: E501
    #   (MSTORE (ADD data_istart (MUL 32 3)) 0x0000000000000000000000000000000000000000000000000000000000000005)  # noqa: E501
    #   (MSTORE (ADD data_jstart (MUL 32 4)) 0x00000000000000000000000000000000000000000000000000000000000000fe)  # noqa: E501
    #   (MSTORE (ADD data_jstart (MUL 32 5)) 0x00000000000000000000000000000000000000000000000000000000000000ff)  # noqa: E501
    #   (MSTORE (ADD data_jstart (MUL 32 6)) 0x0000000000000000000000000000000000000000000000000000000000000100)  # noqa: E501
    # ... (99 more lines)
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0xFF)
        + Op.MSTORE(offset=Op.ADD(0x2774, Op.MUL(0x20, 0x0)), value=0x80)
        + Op.MSTORE(offset=Op.ADD(0x2774, Op.MUL(0x20, 0x1)), value=0x8000)
        + Op.MSTORE(offset=Op.ADD(0x2774, Op.MUL(0x20, 0x2)), value=0x80000000)
        + Op.MSTORE(
            offset=Op.ADD(0x2774, Op.MUL(0x20, 0x3)), value=0x8000000000000000
        )
        + Op.MSTORE(
            offset=Op.ADD(0x2774, Op.MUL(0x20, 0x4)),
            value=0x80000000000000000000000000000000,
        )
        + Op.MSTORE(
            offset=Op.ADD(0x2774, Op.MUL(0x20, 0x5)),
            value=0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.MSTORE(offset=Op.ADD(0x4E84, Op.MUL(0x20, 0x0)), value=0x0)
        + Op.MSTORE(offset=Op.ADD(0x4E84, Op.MUL(0x20, 0x1)), value=0x1)
        + Op.MSTORE(offset=Op.ADD(0x4E84, Op.MUL(0x20, 0x2)), value=0x2)
        + Op.MSTORE(offset=Op.ADD(0x2774, Op.MUL(0x20, 0x3)), value=0x5)
        + Op.MSTORE(offset=Op.ADD(0x4E84, Op.MUL(0x20, 0x4)), value=0xFE)
        + Op.MSTORE(offset=Op.ADD(0x4E84, Op.MUL(0x20, 0x5)), value=0xFF)
        + Op.MSTORE(offset=Op.ADD(0x4E84, Op.MUL(0x20, 0x6)), value=0x100)
        + Op.MSTORE(offset=Op.ADD(0x4E84, Op.MUL(0x20, 0x7)), value=0x101)
        + Op.MSTORE(
            offset=Op.ADD(0x4E84, Op.MUL(0x20, 0x8)),
            value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        )
        + Op.MSTORE(
            offset=Op.ADD(0x4E84, Op.MUL(0x20, 0x9)),
            value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
        )
        + Op.MSTORE(
            offset=Op.ADD(0x4E84, Op.MUL(0x20, 0xA)),
            value=0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.MSTORE(
            offset=Op.ADD(0x4E84, Op.MUL(0x20, 0xB)),
            value=0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.MSTORE(
            offset=Op.ADD(0x4E84, Op.MUL(0x20, 0xC)),
            value=0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
        )
        + Op.MSTORE(
            offset=Op.ADD(0x4E84, Op.MUL(0x20, 0xD)),
            value=0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
        )
        + Op.MSTORE(offset=0x20, value=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x40D, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x20), 0x6))
        )
        + Op.MSTORE(offset=0x40, value=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x3FF, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x40), 0xE))
        )
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=0x1000001D)
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.JUMPI(
            pc=0x24C,
            condition=Op.EQ(
                Op.MLOAD(
                    offset=Op.ADD(0x2774, Op.MUL(0x20, Op.MLOAD(offset=0x20)))
                ),
                0x0,
            ),
        )
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0),
            value=Op.MLOAD(
                offset=Op.ADD(0x2774, Op.MUL(0x20, Op.MLOAD(offset=0x20)))
            ),
        )
        + Op.JUMP(pc=0x253)
        + Op.JUMPDEST
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=0x80)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.JUMPI(
            pc=0x282,
            condition=Op.EQ(
                Op.MLOAD(
                    offset=Op.ADD(0x4E84, Op.MUL(0x20, Op.MLOAD(offset=0x40)))
                ),
                0x0,
            ),
        )
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0),
            value=Op.MLOAD(
                offset=Op.ADD(0x4E84, Op.MUL(0x20, Op.MLOAD(offset=0x40)))
            ),
        )
        + Op.JUMP(pc=0x289)
        + Op.JUMPDEST
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=0x80)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0),
            value=Op.SAR(
                Op.MLOAD(
                    offset=Op.ADD(0x2774, Op.MUL(0x20, Op.MLOAD(offset=0x20)))
                ),
                Op.MLOAD(
                    offset=Op.ADD(0x4E84, Op.MUL(0x20, Op.MLOAD(offset=0x40)))
                ),
            ),
        )
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=0x1000001B)
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.JUMPI(
            pc=0x2EE,
            condition=Op.EQ(
                Op.MLOAD(
                    offset=Op.ADD(0x2774, Op.MUL(0x20, Op.MLOAD(offset=0x20)))
                ),
                0x0,
            ),
        )
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0),
            value=Op.MLOAD(
                offset=Op.ADD(0x2774, Op.MUL(0x20, Op.MLOAD(offset=0x20)))
            ),
        )
        + Op.JUMP(pc=0x2F5)
        + Op.JUMPDEST
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=0x80)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.JUMPI(
            pc=0x324,
            condition=Op.EQ(
                Op.MLOAD(
                    offset=Op.ADD(0x4E84, Op.MUL(0x20, Op.MLOAD(offset=0x40)))
                ),
                0x0,
            ),
        )
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0),
            value=Op.MLOAD(
                offset=Op.ADD(0x4E84, Op.MUL(0x20, Op.MLOAD(offset=0x40)))
            ),
        )
        + Op.JUMP(pc=0x32B)
        + Op.JUMPDEST
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=0x80)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0),
            value=Op.SHL(
                Op.MLOAD(
                    offset=Op.ADD(0x2774, Op.MUL(0x20, Op.MLOAD(offset=0x20)))
                ),
                Op.MLOAD(
                    offset=Op.ADD(0x4E84, Op.MUL(0x20, Op.MLOAD(offset=0x40)))
                ),
            ),
        )
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=0x1000001C)
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.JUMPI(
            pc=0x390,
            condition=Op.EQ(
                Op.MLOAD(
                    offset=Op.ADD(0x2774, Op.MUL(0x20, Op.MLOAD(offset=0x20)))
                ),
                0x0,
            ),
        )
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0),
            value=Op.MLOAD(
                offset=Op.ADD(0x2774, Op.MUL(0x20, Op.MLOAD(offset=0x20)))
            ),
        )
        + Op.JUMP(pc=0x397)
        + Op.JUMPDEST
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=0x80)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.JUMPI(
            pc=0x3C6,
            condition=Op.EQ(
                Op.MLOAD(
                    offset=Op.ADD(0x4E84, Op.MUL(0x20, Op.MLOAD(offset=0x40)))
                ),
                0x0,
            ),
        )
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0),
            value=Op.MLOAD(
                offset=Op.ADD(0x4E84, Op.MUL(0x20, Op.MLOAD(offset=0x40)))
            ),
        )
        + Op.JUMP(pc=0x3CD)
        + Op.JUMPDEST
        + Op.SSTORE(key=Op.MLOAD(offset=0x0), value=0x80)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.MLOAD(offset=0x0)))
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0),
            value=Op.SHR(
                Op.MLOAD(
                    offset=Op.ADD(0x2774, Op.MUL(0x20, Op.MLOAD(offset=0x20)))
                ),
                Op.MLOAD(
                    offset=Op.ADD(0x4E84, Op.MUL(0x20, Op.MLOAD(offset=0x40)))
                ),
            ),
        )
        + Op.MSTORE(offset=0x40, value=Op.ADD(0x1, Op.MLOAD(offset=0x40)))
        + Op.JUMP(pc=0x200)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x20, value=Op.ADD(0x1, Op.MLOAD(offset=0x20)))
        + Op.JUMP(pc=0x1EF)
        + Op.JUMPDEST
        + Op.STOP * 2,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x6C08B7236EE4784E5499B9A576902679D8F863D5),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=80000000,
        value=1,
    )

    post = {
        target: Account(
            storage={
                256: 0x1000001D,
                257: 128,
                258: 128,
                260: 0x1000001B,
                261: 128,
                262: 128,
                264: 0x1000001C,
                265: 128,
                266: 128,
                268: 0x1000001D,
                269: 128,
                270: 1,
                272: 0x1000001B,
                273: 128,
                274: 1,
                275: 0x100000000000000000000000000000000,
                276: 0x1000001C,
                277: 128,
                278: 1,
                280: 0x1000001D,
                281: 128,
                282: 2,
                284: 0x1000001B,
                285: 128,
                286: 2,
                287: 0x200000000000000000000000000000000,
                288: 0x1000001C,
                289: 128,
                290: 2,
                292: 0x1000001D,
                293: 128,
                294: 128,
                296: 0x1000001B,
                297: 128,
                298: 128,
                300: 0x1000001C,
                301: 128,
                302: 128,
                304: 0x1000001D,
                305: 128,
                306: 254,
                308: 0x1000001B,
                309: 128,
                310: 254,
                311: 0xFE00000000000000000000000000000000,
                312: 0x1000001C,
                313: 128,
                314: 254,
                316: 0x1000001D,
                317: 128,
                318: 255,
                320: 0x1000001B,
                321: 128,
                322: 255,
                323: 0xFF00000000000000000000000000000000,
                324: 0x1000001C,
                325: 128,
                326: 255,
                328: 0x1000001D,
                329: 128,
                330: 256,
                332: 0x1000001B,
                333: 128,
                334: 256,
                335: 0x10000000000000000000000000000000000,
                336: 0x1000001C,
                337: 128,
                338: 256,
                340: 0x1000001D,
                341: 128,
                342: 257,
                344: 0x1000001B,
                345: 128,
                346: 257,
                347: 0x10100000000000000000000000000000000,
                348: 0x1000001C,
                349: 128,
                350: 257,
                352: 0x1000001D,
                353: 128,
                354: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                355: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                356: 0x1000001B,
                357: 128,
                358: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                359: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000000,  # noqa: E501
                360: 0x1000001C,
                361: 128,
                362: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                363: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                364: 0x1000001D,
                365: 128,
                366: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                367: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                368: 0x1000001B,
                369: 128,
                370: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                371: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE00000000000000000000000000000000,  # noqa: E501
                372: 0x1000001C,
                373: 128,
                374: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                375: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                376: 0x1000001D,
                377: 128,
                378: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                379: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF80000000000000000000000000000000,  # noqa: E501
                380: 0x1000001B,
                381: 128,
                382: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                384: 0x1000001C,
                385: 128,
                386: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                387: 0x80000000000000000000000000000000,
                388: 0x1000001D,
                389: 128,
                390: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                391: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFA0000000000000000000000000000000,  # noqa: E501
                392: 0x1000001B,
                393: 128,
                394: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                396: 0x1000001C,
                397: 128,
                398: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                399: 0xA0000000000000000000000000000000,
                400: 0x1000001D,
                401: 128,
                402: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                403: 0x55555555555555555555555555555555,
                404: 0x1000001B,
                405: 128,
                406: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                407: 0x5555555555555555555555555555555500000000000000000000000000000000,  # noqa: E501
                408: 0x1000001C,
                409: 128,
                410: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                411: 0x55555555555555555555555555555555,
                412: 0x1000001D,
                413: 128,
                414: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                415: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                416: 0x1000001B,
                417: 128,
                418: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                419: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA00000000000000000000000000000000,  # noqa: E501
                420: 0x1000001C,
                421: 128,
                422: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                423: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,
                424: 0x1000001D,
                425: 32768,
                426: 128,
                428: 0x1000001B,
                429: 32768,
                430: 128,
                432: 0x1000001C,
                433: 32768,
                434: 128,
                436: 0x1000001D,
                437: 32768,
                438: 1,
                440: 0x1000001B,
                441: 32768,
                442: 1,
                444: 0x1000001C,
                445: 32768,
                446: 1,
                448: 0x1000001D,
                449: 32768,
                450: 2,
                452: 0x1000001B,
                453: 32768,
                454: 2,
                456: 0x1000001C,
                457: 32768,
                458: 2,
                460: 0x1000001D,
                461: 32768,
                462: 128,
                464: 0x1000001B,
                465: 32768,
                466: 128,
                468: 0x1000001C,
                469: 32768,
                470: 128,
                472: 0x1000001D,
                473: 32768,
                474: 254,
                476: 0x1000001B,
                477: 32768,
                478: 254,
                480: 0x1000001C,
                481: 32768,
                482: 254,
                484: 0x1000001D,
                485: 32768,
                486: 255,
                488: 0x1000001B,
                489: 32768,
                490: 255,
                492: 0x1000001C,
                493: 32768,
                494: 255,
                496: 0x1000001D,
                497: 32768,
                498: 256,
                500: 0x1000001B,
                501: 32768,
                502: 256,
                504: 0x1000001C,
                505: 32768,
                506: 256,
                508: 0x1000001D,
                509: 32768,
                510: 257,
                512: 0x1000001B,
                513: 32768,
                514: 257,
                516: 0x1000001C,
                517: 32768,
                518: 257,
                520: 0x1000001D,
                521: 32768,
                522: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                523: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                524: 0x1000001B,
                525: 32768,
                526: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                528: 0x1000001C,
                529: 32768,
                530: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                532: 0x1000001D,
                533: 32768,
                534: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                535: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                536: 0x1000001B,
                537: 32768,
                538: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                540: 0x1000001C,
                541: 32768,
                542: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                544: 0x1000001D,
                545: 32768,
                546: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                547: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                548: 0x1000001B,
                549: 32768,
                550: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                552: 0x1000001C,
                553: 32768,
                554: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                556: 0x1000001D,
                557: 32768,
                558: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                559: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                560: 0x1000001B,
                561: 32768,
                562: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                564: 0x1000001C,
                565: 32768,
                566: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                568: 0x1000001D,
                569: 32768,
                570: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                572: 0x1000001B,
                573: 32768,
                574: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                576: 0x1000001C,
                577: 32768,
                578: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                580: 0x1000001D,
                581: 32768,
                582: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                583: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                584: 0x1000001B,
                585: 32768,
                586: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                588: 0x1000001C,
                589: 32768,
                590: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                592: 0x1000001D,
                593: 0x80000000,
                594: 128,
                596: 0x1000001B,
                597: 0x80000000,
                598: 128,
                600: 0x1000001C,
                601: 0x80000000,
                602: 128,
                604: 0x1000001D,
                605: 0x80000000,
                606: 1,
                608: 0x1000001B,
                609: 0x80000000,
                610: 1,
                612: 0x1000001C,
                613: 0x80000000,
                614: 1,
                616: 0x1000001D,
                617: 0x80000000,
                618: 2,
                620: 0x1000001B,
                621: 0x80000000,
                622: 2,
                624: 0x1000001C,
                625: 0x80000000,
                626: 2,
                628: 0x1000001D,
                629: 0x80000000,
                630: 128,
                632: 0x1000001B,
                633: 0x80000000,
                634: 128,
                636: 0x1000001C,
                637: 0x80000000,
                638: 128,
                640: 0x1000001D,
                641: 0x80000000,
                642: 254,
                644: 0x1000001B,
                645: 0x80000000,
                646: 254,
                648: 0x1000001C,
                649: 0x80000000,
                650: 254,
                652: 0x1000001D,
                653: 0x80000000,
                654: 255,
                656: 0x1000001B,
                657: 0x80000000,
                658: 255,
                660: 0x1000001C,
                661: 0x80000000,
                662: 255,
                664: 0x1000001D,
                665: 0x80000000,
                666: 256,
                668: 0x1000001B,
                669: 0x80000000,
                670: 256,
                672: 0x1000001C,
                673: 0x80000000,
                674: 256,
                676: 0x1000001D,
                677: 0x80000000,
                678: 257,
                680: 0x1000001B,
                681: 0x80000000,
                682: 257,
                684: 0x1000001C,
                685: 0x80000000,
                686: 257,
                688: 0x1000001D,
                689: 0x80000000,
                690: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                691: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                692: 0x1000001B,
                693: 0x80000000,
                694: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                696: 0x1000001C,
                697: 0x80000000,
                698: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                700: 0x1000001D,
                701: 0x80000000,
                702: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                703: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                704: 0x1000001B,
                705: 0x80000000,
                706: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                708: 0x1000001C,
                709: 0x80000000,
                710: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                712: 0x1000001D,
                713: 0x80000000,
                714: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                715: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                716: 0x1000001B,
                717: 0x80000000,
                718: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                720: 0x1000001C,
                721: 0x80000000,
                722: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                724: 0x1000001D,
                725: 0x80000000,
                726: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                727: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                728: 0x1000001B,
                729: 0x80000000,
                730: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                732: 0x1000001C,
                733: 0x80000000,
                734: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                736: 0x1000001D,
                737: 0x80000000,
                738: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                740: 0x1000001B,
                741: 0x80000000,
                742: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                744: 0x1000001C,
                745: 0x80000000,
                746: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                748: 0x1000001D,
                749: 0x80000000,
                750: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                751: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                752: 0x1000001B,
                753: 0x80000000,
                754: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                756: 0x1000001C,
                757: 0x80000000,
                758: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                760: 0x1000001D,
                761: 5,
                762: 128,
                764: 0x1000001B,
                765: 5,
                766: 128,
                768: 0x1000001C,
                769: 5,
                770: 128,
                772: 0x1000001D,
                773: 5,
                774: 1,
                776: 0x1000001B,
                777: 5,
                778: 1,
                779: 32,
                780: 0x1000001C,
                781: 5,
                782: 1,
                784: 0x1000001D,
                785: 5,
                786: 2,
                788: 0x1000001B,
                789: 5,
                790: 2,
                791: 64,
                792: 0x1000001C,
                793: 5,
                794: 2,
                796: 0x1000001D,
                797: 5,
                798: 128,
                800: 0x1000001B,
                801: 5,
                802: 128,
                804: 0x1000001C,
                805: 5,
                806: 128,
                808: 0x1000001D,
                809: 5,
                810: 254,
                811: 7,
                812: 0x1000001B,
                813: 5,
                814: 254,
                815: 8128,
                816: 0x1000001C,
                817: 5,
                818: 254,
                819: 7,
                820: 0x1000001D,
                821: 5,
                822: 255,
                823: 7,
                824: 0x1000001B,
                825: 5,
                826: 255,
                827: 8160,
                828: 0x1000001C,
                829: 5,
                830: 255,
                831: 7,
                832: 0x1000001D,
                833: 5,
                834: 256,
                835: 8,
                836: 0x1000001B,
                837: 5,
                838: 256,
                839: 8192,
                840: 0x1000001C,
                841: 5,
                842: 256,
                843: 8,
                844: 0x1000001D,
                845: 5,
                846: 257,
                847: 8,
                848: 0x1000001B,
                849: 5,
                850: 257,
                851: 8224,
                852: 0x1000001C,
                853: 5,
                854: 257,
                855: 8,
                856: 0x1000001D,
                857: 5,
                858: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                859: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                860: 0x1000001B,
                861: 5,
                862: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                863: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE0,  # noqa: E501
                864: 0x1000001C,
                865: 5,
                866: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                867: 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                868: 0x1000001D,
                869: 5,
                870: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                871: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                872: 0x1000001B,
                873: 5,
                874: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                875: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFC0,  # noqa: E501
                876: 0x1000001C,
                877: 5,
                878: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                879: 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                880: 0x1000001D,
                881: 5,
                882: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                883: 0xFC00000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                884: 0x1000001B,
                885: 5,
                886: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                888: 0x1000001C,
                889: 5,
                890: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                891: 0x400000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                892: 0x1000001D,
                893: 5,
                894: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                895: 0xFD00000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                896: 0x1000001B,
                897: 5,
                898: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                900: 0x1000001C,
                901: 5,
                902: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                903: 0x500000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                904: 0x1000001D,
                905: 5,
                906: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                907: 0x2AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                908: 0x1000001B,
                909: 5,
                910: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                911: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA0,  # noqa: E501
                912: 0x1000001C,
                913: 5,
                914: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                915: 0x2AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                916: 0x1000001D,
                917: 5,
                918: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                919: 0xFD55555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                920: 0x1000001B,
                921: 5,
                922: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                923: 0x5555555555555555555555555555555555555555555555555555555555555540,  # noqa: E501
                924: 0x1000001C,
                925: 5,
                926: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                927: 0x555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                928: 0x1000001D,
                929: 0x80000000000000000000000000000000,
                930: 128,
                932: 0x1000001B,
                933: 0x80000000000000000000000000000000,
                934: 128,
                936: 0x1000001C,
                937: 0x80000000000000000000000000000000,
                938: 128,
                940: 0x1000001D,
                941: 0x80000000000000000000000000000000,
                942: 1,
                944: 0x1000001B,
                945: 0x80000000000000000000000000000000,
                946: 1,
                948: 0x1000001C,
                949: 0x80000000000000000000000000000000,
                950: 1,
                952: 0x1000001D,
                953: 0x80000000000000000000000000000000,
                954: 2,
                956: 0x1000001B,
                957: 0x80000000000000000000000000000000,
                958: 2,
                960: 0x1000001C,
                961: 0x80000000000000000000000000000000,
                962: 2,
                964: 0x1000001D,
                965: 0x80000000000000000000000000000000,
                966: 128,
                968: 0x1000001B,
                969: 0x80000000000000000000000000000000,
                970: 128,
                972: 0x1000001C,
                973: 0x80000000000000000000000000000000,
                974: 128,
                976: 0x1000001D,
                977: 0x80000000000000000000000000000000,
                978: 254,
                980: 0x1000001B,
                981: 0x80000000000000000000000000000000,
                982: 254,
                984: 0x1000001C,
                985: 0x80000000000000000000000000000000,
                986: 254,
                988: 0x1000001D,
                989: 0x80000000000000000000000000000000,
                990: 255,
                992: 0x1000001B,
                993: 0x80000000000000000000000000000000,
                994: 255,
                996: 0x1000001C,
                997: 0x80000000000000000000000000000000,
                998: 255,
                1000: 0x1000001D,
                1001: 0x80000000000000000000000000000000,
                1002: 256,
                1004: 0x1000001B,
                1005: 0x80000000000000000000000000000000,
                1006: 256,
                1008: 0x1000001C,
                1009: 0x80000000000000000000000000000000,
                1010: 256,
                1012: 0x1000001D,
                1013: 0x80000000000000000000000000000000,
                1014: 257,
                1016: 0x1000001B,
                1017: 0x80000000000000000000000000000000,
                1018: 257,
                1020: 0x1000001C,
                1021: 0x80000000000000000000000000000000,
                1022: 257,
                1024: 0x1000001D,
                1025: 0x80000000000000000000000000000000,
                1026: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1027: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1028: 0x1000001B,
                1029: 0x80000000000000000000000000000000,
                1030: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1032: 0x1000001C,
                1033: 0x80000000000000000000000000000000,
                1034: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1036: 0x1000001D,
                1037: 0x80000000000000000000000000000000,
                1038: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                1039: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1040: 0x1000001B,
                1041: 0x80000000000000000000000000000000,
                1042: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                1044: 0x1000001C,
                1045: 0x80000000000000000000000000000000,
                1046: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                1048: 0x1000001D,
                1049: 0x80000000000000000000000000000000,
                1050: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1051: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1052: 0x1000001B,
                1053: 0x80000000000000000000000000000000,
                1054: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1056: 0x1000001C,
                1057: 0x80000000000000000000000000000000,
                1058: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1060: 0x1000001D,
                1061: 0x80000000000000000000000000000000,
                1062: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1063: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1064: 0x1000001B,
                1065: 0x80000000000000000000000000000000,
                1066: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1068: 0x1000001C,
                1069: 0x80000000000000000000000000000000,
                1070: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1072: 0x1000001D,
                1073: 0x80000000000000000000000000000000,
                1074: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                1076: 0x1000001B,
                1077: 0x80000000000000000000000000000000,
                1078: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                1080: 0x1000001C,
                1081: 0x80000000000000000000000000000000,
                1082: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                1084: 0x1000001D,
                1085: 0x80000000000000000000000000000000,
                1086: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                1087: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1088: 0x1000001B,
                1089: 0x80000000000000000000000000000000,
                1090: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                1092: 0x1000001C,
                1093: 0x80000000000000000000000000000000,
                1094: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                1096: 0x1000001D,
                1097: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1098: 128,
                1100: 0x1000001B,
                1101: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1102: 128,
                1104: 0x1000001C,
                1105: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1106: 128,
                1108: 0x1000001D,
                1109: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1110: 1,
                1112: 0x1000001B,
                1113: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1114: 1,
                1116: 0x1000001C,
                1117: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1118: 1,
                1120: 0x1000001D,
                1121: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1122: 2,
                1124: 0x1000001B,
                1125: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1126: 2,
                1128: 0x1000001C,
                1129: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1130: 2,
                1132: 0x1000001D,
                1133: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1134: 128,
                1136: 0x1000001B,
                1137: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1138: 128,
                1140: 0x1000001C,
                1141: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1142: 128,
                1144: 0x1000001D,
                1145: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1146: 254,
                1148: 0x1000001B,
                1149: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1150: 254,
                1152: 0x1000001C,
                1153: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1154: 254,
                1156: 0x1000001D,
                1157: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1158: 255,
                1160: 0x1000001B,
                1161: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1162: 255,
                1164: 0x1000001C,
                1165: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1166: 255,
                1168: 0x1000001D,
                1169: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1170: 256,
                1172: 0x1000001B,
                1173: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1174: 256,
                1176: 0x1000001C,
                1177: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1178: 256,
                1180: 0x1000001D,
                1181: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1182: 257,
                1184: 0x1000001B,
                1185: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1186: 257,
                1188: 0x1000001C,
                1189: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1190: 257,
                1192: 0x1000001D,
                1193: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1194: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1195: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1196: 0x1000001B,
                1197: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1198: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1200: 0x1000001C,
                1201: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1202: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1204: 0x1000001D,
                1205: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1206: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                1207: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1208: 0x1000001B,
                1209: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1210: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                1212: 0x1000001C,
                1213: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1214: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,  # noqa: E501
                1216: 0x1000001D,
                1217: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1218: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1219: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1220: 0x1000001B,
                1221: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1222: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1224: 0x1000001C,
                1225: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1226: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1228: 0x1000001D,
                1229: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1230: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1231: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1232: 0x1000001B,
                1233: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1234: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1236: 0x1000001C,
                1237: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1238: 0xA000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1240: 0x1000001D,
                1241: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1242: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                1244: 0x1000001B,
                1245: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1246: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                1248: 0x1000001C,
                1249: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1250: 0x5555555555555555555555555555555555555555555555555555555555555555,  # noqa: E501
                1252: 0x1000001D,
                1253: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1254: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                1255: 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                1256: 0x1000001B,
                1257: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1258: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
                1260: 0x1000001C,
                1261: 0x8000000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                1262: 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA,  # noqa: E501
            },
            balance=0xDE0B6B3A7640001,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
