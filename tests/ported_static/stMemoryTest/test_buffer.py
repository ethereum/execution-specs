"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stMemoryTest/bufferFiller.yml
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
    ["state_tests/stMemoryTest/bufferFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            1,
            0,
            0,
            id="ok",
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
            id="ok",
        ),
        pytest.param(
            4,
            0,
            0,
            id="ok",
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
            id="ok",
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
            id="ok",
        ),
        pytest.param(
            17,
            0,
            0,
            id="ok",
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
            id="ok",
        ),
        pytest.param(
            20,
            0,
            0,
            id="ok",
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
            id="ok",
        ),
        pytest.param(
            32,
            0,
            0,
            id="ok",
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
            id="ok",
        ),
        pytest.param(
            35,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            36,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            37,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            38,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            39,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            40,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            41,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            42,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            43,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            44,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            45,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            46,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            47,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            48,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            49,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            50,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            51,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            52,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            53,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            54,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            55,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            56,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            57,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            58,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            59,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            60,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            61,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            62,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            63,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            64,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            65,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            66,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            67,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            68,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            69,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            70,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            71,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            72,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            73,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            74,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            75,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            76,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            77,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            78,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            79,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            80,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            81,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            82,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            83,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            84,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            85,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            86,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            87,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            88,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            89,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            90,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            91,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            92,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            93,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            94,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            95,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            96,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            97,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            98,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            99,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            100,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            101,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            102,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            103,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            104,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            105,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            106,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            107,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            108,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            109,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            110,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            111,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            112,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            113,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            114,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            115,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            116,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            117,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            118,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            119,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            120,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            121,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            122,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            123,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            124,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            125,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            126,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            127,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            128,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            129,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            130,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            131,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            132,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            133,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            134,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            135,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            136,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            137,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            138,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            139,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            140,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            141,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            142,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            143,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            144,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            145,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            146,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            147,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            148,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            149,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            150,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            151,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            152,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            153,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            154,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            155,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            156,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            157,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            158,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            159,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            160,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            161,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            162,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            163,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            164,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            165,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            166,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            167,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            168,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            169,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            170,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            171,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            172,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            173,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            174,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            175,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            176,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            177,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            178,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            179,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            180,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            181,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            182,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            183,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            184,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            185,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            186,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            187,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            188,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            189,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            190,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            191,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            192,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            193,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            194,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            195,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            196,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            197,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            198,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            199,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            200,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            201,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            202,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            203,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            204,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            205,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            206,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            207,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            208,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            209,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            210,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            211,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            212,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            213,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            214,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            215,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            216,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            217,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            218,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            219,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            220,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            221,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            222,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            223,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            224,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            225,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            226,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            227,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            228,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            229,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            230,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            231,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            232,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            233,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            234,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            235,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            236,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            237,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            238,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            239,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            240,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            241,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            242,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            243,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            244,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            245,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            246,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            247,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            248,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            249,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            250,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            251,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            252,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            253,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            254,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            255,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            256,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            257,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            258,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            259,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            260,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            261,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            262,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            263,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            264,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            265,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            266,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            267,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            268,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            269,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            270,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            271,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            272,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            273,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            274,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            275,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            276,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            277,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            278,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            279,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            280,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            281,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            282,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            283,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            284,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            285,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            286,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            287,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            288,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            289,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            290,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            291,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            292,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            293,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            294,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            295,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            296,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            297,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            298,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            299,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            300,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            301,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            302,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            303,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            304,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            305,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            306,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            307,
            0,
            0,
            id="ok",
        ),
        pytest.param(
            308,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            309,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            310,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            311,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            312,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            313,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            314,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            315,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            316,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            317,
            0,
            0,
            id="fail",
        ),
        pytest.param(
            318,
            0,
            0,
            id="ok-f3",
        ),
        pytest.param(
            319,
            0,
            0,
            id="ok-f3",
        ),
        pytest.param(
            320,
            0,
            0,
            id="fail-f3",
        ),
        pytest.param(
            321,
            0,
            0,
            id="ok-f3",
        ),
        pytest.param(
            322,
            0,
            0,
            id="ok-f3",
        ),
        pytest.param(
            323,
            0,
            0,
            id="fail-f3",
        ),
        pytest.param(
            324,
            0,
            0,
            id="fail-f3",
        ),
        pytest.param(
            325,
            0,
            0,
            id="fail-f3",
        ),
        pytest.param(
            326,
            0,
            0,
            id="fail-f3",
        ),
        pytest.param(
            327,
            0,
            0,
            id="fail-f3",
        ),
        pytest.param(
            328,
            0,
            0,
            id="fail-f3",
        ),
        pytest.param(
            329,
            0,
            0,
            id="fail-f3",
        ),
        pytest.param(
            330,
            0,
            0,
            id="fail-f3",
        ),
        pytest.param(
            331,
            0,
            0,
            id="fail-f3",
        ),
        pytest.param(
            332,
            0,
            0,
            id="fail-f3",
        ),
        pytest.param(
            333,
            0,
            0,
            id="ff-valid",
        ),
        pytest.param(
            334,
            0,
            0,
            id="ff-zero",
        ),
        pytest.param(
            335,
            0,
            0,
            id="ff-zero",
        ),
        pytest.param(
            336,
            0,
            0,
            id="ff-valid",
        ),
        pytest.param(
            337,
            0,
            0,
            id="ff-zero",
        ),
        pytest.param(
            338,
            0,
            0,
            id="ff-zero",
        ),
        pytest.param(
            339,
            0,
            0,
            id="ff-zero",
        ),
        pytest.param(
            340,
            0,
            0,
            id="ff-zero",
        ),
        pytest.param(
            341,
            0,
            0,
            id="ff-zero",
        ),
        pytest.param(
            342,
            0,
            0,
            id="ff-zero",
        ),
        pytest.param(
            343,
            0,
            0,
            id="ff-zero",
        ),
        pytest.param(
            344,
            0,
            0,
            id="ff-zero",
        ),
        pytest.param(
            345,
            0,
            0,
            id="ff-zero",
        ),
        pytest.param(
            346,
            0,
            0,
            id="ff-zero",
        ),
        pytest.param(
            347,
            0,
            0,
            id="ff-zero",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_buffer(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x000000000000000000000000000000000000C0DE)
    contract_1 = Address(0x000000000000000000000000000000000F30C0DE)
    contract_2 = Address(0x000000000000000000000000000000000FF0C0DE)
    contract_3 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
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

    # Source: lll
    # {
    #       (return 0 0x120)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0x120) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000C0DE),  # noqa: E501
    )
    # Source: lll
    # {
    #        ; We get length from the caller
    #        (def 'length $0)
    #        (def 'offset $0x20)
    #
    #        [[0]] 0    ; capricide
    #        (return offset length)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x0)
        + Op.RETURN(
            offset=Op.CALLDATALOAD(offset=0x20),
            size=Op.CALLDATALOAD(offset=0x0),
        )
        + Op.STOP,
        storage={0: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000F30C0DE),  # noqa: E501
    )
    # Source: lll
    # {
    #        ; We get length from the caller
    #        (def 'length $0)
    #        (def 'offset $0x20)
    #
    #        (revert offset length)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.REVERT(
            offset=Op.CALLDATALOAD(offset=0x20),
            size=Op.CALLDATALOAD(offset=0x0),
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000FF0C0DE),  # noqa: E501
    )
    # Source: lll
    # {
    #    (def 'opcode $4)
    #    (def 'bufferType $36)
    #    (def 'NOP 0)
    #
    #    ; Variables
    #    (def 'length     0x2020)
    #    (def 'offset     0x2040)
    #
    #    ; bufferTypes  0 is normal, 1 is length zero, 2 is negative length
    #    ; bufferType 3 is excessively long, for opcodes with bounds checking
    #    ; Add 0 for offset 0x100, 10 for offset 0x0
    #
    #    ; High offsets:
    #    ; 20 for 2^256-10
    #    ; 21 for 2^31-1
    #    ; 22 for 2^31
    #    ; 23 for 2^32-1
    #    ; 24 for 2^32
    #    ; 25 for 2^63-1
    #    ; 26 for 2^63
    #    ; 27 for 2^64-1
    #    ; 28 for 2^64
    #    (if (= bufferType 0) {
    #            [length] 10
    #            [offset] 0x100
    #      } NOP)
    #    (if (= bufferType 1) {
    #            [length] 0
    #            [offset] 0x100
    # ... (113 more lines)
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=Op.PUSH2[0x11],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x0),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x1F])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0xA)
        + Op.MSTORE(offset=0x2040, value=0x100)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x31],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x3F])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(offset=0x2040, value=0x100)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x51],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x2),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x62])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=Op.SUB(0x0, 0xA))
        + Op.MSTORE(offset=0x2040, value=0x100)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x74],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x3),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0x83])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x1000)
        + Op.MSTORE(offset=0x2040, value=0x100)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0x95],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0xA),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xA2])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0xA)
        + Op.MSTORE(offset=0x2040, value=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xB4],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0xB),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xC1])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(offset=0x2040, value=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xD3],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0xC),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=Op.PUSH2[0xE3])
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=Op.SUB(0x0, 0xA))
        + Op.MSTORE(offset=0x2040, value=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=Op.PUSH2[0xF5],
            condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0xD),
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x103)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x1000)
        + Op.MSTORE(offset=0x2040, value=0x0)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x115, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x14)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x125)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x5)
        + Op.MSTORE(offset=0x2040, value=Op.SUB(0x0, 0xA))
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x137, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x15)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x147)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x5)
        + Op.MSTORE(offset=0x2040, value=0x7FFFFFFF)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x159, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x16)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x169)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x5)
        + Op.MSTORE(offset=0x2040, value=0x80000000)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x17B, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x17)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x18B)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x5)
        + Op.MSTORE(offset=0x2040, value=0xFFFFFFFF)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x19D, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x18)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1AE)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x5)
        + Op.MSTORE(offset=0x2040, value=0x100000000)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1C0, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x19)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1D4)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x5)
        + Op.MSTORE(offset=0x2040, value=0x7FFFFFFFFFFFFFFF)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1E6, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1A)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x1FA)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x5)
        + Op.MSTORE(offset=0x2040, value=0x8000000000000000)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x20C, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1B)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x220)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x5)
        + Op.MSTORE(offset=0x2040, value=0xFFFFFFFFFFFFFFFF)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x232, condition=Op.EQ(Op.CALLDATALOAD(offset=0x24), 0x1C)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x247)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x2020, value=0x5)
        + Op.MSTORE(offset=0x2040, value=0x10000000000000000)
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x258, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x20)
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x262)
        + Op.JUMPDEST
        + Op.SHA3(offset=Op.MLOAD(offset=0x2040), size=Op.MLOAD(offset=0x2020))
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=0x275, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x37)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x281)
        + Op.JUMPDEST
        + Op.CALLDATACOPY(
            dest_offset=Op.MLOAD(offset=0x2040),
            offset=0x0,
            size=Op.MLOAD(offset=0x2020),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x293, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x39)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x29F)
        + Op.JUMPDEST
        + Op.CODECOPY(
            dest_offset=Op.MLOAD(offset=0x2040),
            offset=0x0,
            size=Op.MLOAD(offset=0x2020),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x2B1, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3C)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x2C0)
        + Op.JUMPDEST
        + Op.EXTCODECOPY(
            address=0xC0DE,
            dest_offset=Op.MLOAD(offset=0x2040),
            offset=0x0,
            size=Op.MLOAD(offset=0x2020),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x2D2, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x3E)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x2DE)
        + Op.JUMPDEST
        + Op.RETURNDATACOPY(
            dest_offset=Op.MLOAD(offset=0x2040),
            offset=0x0,
            size=Op.MLOAD(offset=0x2020),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x2F0, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA0)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x2FA)
        + Op.JUMPDEST
        + Op.LOG0(offset=Op.MLOAD(offset=0x2040), size=Op.MLOAD(offset=0x2020))
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x30C, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA1)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x318)
        + Op.JUMPDEST
        + Op.LOG1(
            offset=Op.MLOAD(offset=0x2040),
            size=Op.MLOAD(offset=0x2020),
            topic_1=0x1,
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x32A, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA2)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x338)
        + Op.JUMPDEST
        + Op.LOG2(
            offset=Op.MLOAD(offset=0x2040),
            size=Op.MLOAD(offset=0x2020),
            topic_1=0x1,
            topic_2=0x2,
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x34A, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA3)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x35A)
        + Op.JUMPDEST
        + Op.LOG3(
            offset=Op.MLOAD(offset=0x2040),
            size=Op.MLOAD(offset=0x2020),
            topic_1=0x1,
            topic_2=0x2,
            topic_3=0x3,
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x36C, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xA4)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x37E)
        + Op.JUMPDEST
        + Op.LOG4(
            offset=Op.MLOAD(offset=0x2040),
            size=Op.MLOAD(offset=0x2020),
            topic_1=0x1,
            topic_2=0x2,
            topic_3=0x3,
            topic_4=0x4,
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x38F, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF0)
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x39B)
        + Op.JUMPDEST
        + Op.CREATE(
            value=0x0,
            offset=Op.MLOAD(offset=0x2040),
            size=Op.MLOAD(offset=0x2020),
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=0x3AD, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF1)
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x3C3)
        + Op.JUMPDEST
        + Op.CALL(
            gas=0x1000,
            address=0xC0DE,
            value=0x0,
            args_offset=Op.MLOAD(offset=0x2040),
            args_size=Op.MLOAD(offset=0x2020),
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=0x3D6, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x1F1)
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x3EC)
        + Op.JUMPDEST
        + Op.CALL(
            gas=0x1000,
            address=0xC0DE,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=Op.MLOAD(offset=0x2040),
            ret_size=Op.MLOAD(offset=0x2020),
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=0x3FE, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF2)
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x414)
        + Op.JUMPDEST
        + Op.CALLCODE(
            gas=0x1000,
            address=0xC0DE,
            value=0x0,
            args_offset=Op.MLOAD(offset=0x2040),
            args_size=Op.MLOAD(offset=0x2020),
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=0x427, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x1F2)
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x43D)
        + Op.JUMPDEST
        + Op.CALLCODE(
            gas=0x1000,
            address=0xC0DE,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=Op.MLOAD(offset=0x2040),
            ret_size=Op.MLOAD(offset=0x2020),
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=0x44F, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF4)
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x464)
        + Op.JUMPDEST
        + Op.DELEGATECALL(
            gas=0x100000,
            address=0xC0DE,
            args_offset=Op.MLOAD(offset=0x2040),
            args_size=Op.MLOAD(offset=0x2020),
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=0x477, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x1F4)
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x48C)
        + Op.JUMPDEST
        + Op.DELEGATECALL(
            gas=0x100000,
            address=0xC0DE,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=Op.MLOAD(offset=0x2040),
            ret_size=Op.MLOAD(offset=0x2020),
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=0x49E, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF5)
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x4AD)
        + Op.JUMPDEST
        + Op.CREATE2(
            value=0x0,
            offset=Op.MLOAD(offset=0x2040),
            size=Op.MLOAD(offset=0x2020),
            salt=0x5A17,
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=0x4BF, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xFA)
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x4D4)
        + Op.JUMPDEST
        + Op.STATICCALL(
            gas=0x100000,
            address=0xC0DE,
            args_offset=Op.MLOAD(offset=0x2040),
            args_size=Op.MLOAD(offset=0x2020),
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=0x4E7, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x1FA)
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x4FC)
        + Op.JUMPDEST
        + Op.STATICCALL(
            gas=0x100000,
            address=0xC0DE,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=Op.MLOAD(offset=0x2040),
            ret_size=Op.MLOAD(offset=0x2020),
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=0x510, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x13E)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x530)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALL(
                gas=0x1000,
                address=0xC0DE,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x100,
                ret_size=0x100,
            )
        )
        + Op.RETURNDATACOPY(
            dest_offset=Op.MLOAD(offset=0x2040),
            offset=0x0,
            size=Op.MLOAD(offset=0x2020),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x541, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xF3)
        )
        + Op.PUSH1[0x0]
        + Op.JUMP(pc=0x557)
        + Op.JUMPDEST
        + Op.CALL(
            gas=0x100000,
            address=0xF30C0DE,
            value=0x0,
            args_offset=0x2020,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.JUMPDEST
        + Op.POP
        + Op.JUMPI(
            pc=0x56A, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0xFF)
        )
        + Op.POP(0x0)
        + Op.JUMP(pc=0x585)
        + Op.JUMPDEST
        + Op.POP(
            Op.CALL(
                gas=0x100000,
                address=0xFF0C0DE,
                value=0x0,
                args_offset=0x2020,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x100, value=0x0)
        + Op.STOP,
        storage={256: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [
                    0,
                    1,
                    3,
                    4,
                    6,
                    16,
                    17,
                    19,
                    20,
                    31,
                    32,
                    34,
                    35,
                    46,
                    47,
                    49,
                    50,
                    62,
                    65,
                    76,
                    77,
                    79,
                    80,
                    93,
                    94,
                    96,
                    97,
                    108,
                    109,
                    111,
                    112,
                    123,
                    124,
                    126,
                    127,
                    138,
                    139,
                    141,
                    142,
                    153,
                    154,
                    156,
                    157,
                    168,
                    169,
                    171,
                    172,
                    183,
                    184,
                    186,
                    187,
                    198,
                    199,
                    201,
                    202,
                    213,
                    214,
                    216,
                    217,
                    228,
                    229,
                    231,
                    232,
                    243,
                    244,
                    246,
                    247,
                    258,
                    259,
                    261,
                    262,
                    273,
                    274,
                    276,
                    277,
                    288,
                    289,
                    291,
                    292,
                    303,
                    304,
                    306,
                    307,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={256: 0})},
        },
        {
            "indexes": {
                "data": [
                    2,
                    5,
                    7,
                    8,
                    9,
                    10,
                    11,
                    12,
                    13,
                    14,
                    15,
                    18,
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
                    33,
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
                    48,
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
                    63,
                    64,
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
                    78,
                    81,
                    82,
                    83,
                    84,
                    85,
                    86,
                    87,
                    88,
                    89,
                    90,
                    91,
                    92,
                    95,
                    98,
                    99,
                    100,
                    101,
                    102,
                    103,
                    104,
                    105,
                    106,
                    107,
                    110,
                    113,
                    114,
                    115,
                    116,
                    117,
                    118,
                    119,
                    120,
                    121,
                    122,
                    125,
                    128,
                    129,
                    130,
                    131,
                    132,
                    133,
                    134,
                    135,
                    136,
                    137,
                    140,
                    143,
                    144,
                    145,
                    146,
                    147,
                    148,
                    149,
                    150,
                    151,
                    152,
                    155,
                    158,
                    159,
                    160,
                    161,
                    162,
                    163,
                    164,
                    165,
                    166,
                    167,
                    170,
                    173,
                    174,
                    175,
                    176,
                    177,
                    178,
                    179,
                    180,
                    181,
                    182,
                    185,
                    188,
                    189,
                    190,
                    191,
                    192,
                    193,
                    194,
                    195,
                    196,
                    197,
                    200,
                    203,
                    204,
                    205,
                    206,
                    207,
                    208,
                    209,
                    210,
                    211,
                    212,
                    215,
                    218,
                    219,
                    220,
                    221,
                    222,
                    223,
                    224,
                    225,
                    226,
                    227,
                    230,
                    233,
                    234,
                    235,
                    236,
                    237,
                    238,
                    239,
                    240,
                    241,
                    242,
                    245,
                    248,
                    249,
                    250,
                    251,
                    252,
                    253,
                    254,
                    255,
                    256,
                    257,
                    260,
                    263,
                    264,
                    265,
                    266,
                    267,
                    268,
                    269,
                    270,
                    271,
                    272,
                    275,
                    278,
                    279,
                    280,
                    281,
                    282,
                    283,
                    284,
                    285,
                    286,
                    287,
                    290,
                    293,
                    294,
                    295,
                    296,
                    297,
                    298,
                    299,
                    300,
                    301,
                    302,
                    305,
                    308,
                    309,
                    310,
                    311,
                    312,
                    313,
                    314,
                    315,
                    316,
                    317,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={256: 24743})},
        },
        {
            "indexes": {"data": [318, 319, 321, 322], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_1: Account(storage={0: 0})},
        },
        {
            "indexes": {
                "data": [
                    320,
                    323,
                    324,
                    325,
                    326,
                    327,
                    328,
                    329,
                    330,
                    331,
                    332,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_1: Account(storage={0: 24743})},
        },
        {
            "indexes": {"data": [333, 336], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={0: 10})},
        },
        {
            "indexes": {
                "data": [
                    334,
                    335,
                    337,
                    338,
                    339,
                    340,
                    341,
                    342,
                    343,
                    344,
                    345,
                    346,
                    347,
                ],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={0: 0})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("1a8451e6") + Hash(0x20) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0xD),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0x20) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0x37) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0x39) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0x3C) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0x3E) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0x3),
        Bytes("1a8451e6") + Hash(0x13E) + Hash(0xD),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0xA0) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0xA1) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0xA2) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0xA3) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0xA4) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0xF0) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0xF1) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0x1F1) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0xF2) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0x1F2) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0xF4) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0x1F4) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0xF5) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0xFA) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0x1FA) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0xF3) + Hash(0x1C),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0x0),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0x1),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0x2),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0xA),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0xB),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0xC),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0x14),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0x15),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0x16),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0x17),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0x18),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0x19),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0x1A),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0x1B),
        Bytes("1a8451e6") + Hash(0xFF) + Hash(0x1C),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_3,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
