"""
Sstore 1 -> {calltype} -> change to {0, 1, 2} |-> {calltype} -> {non,...

Ported from:
state_tests/stTimeConsuming/sstore_combinations_initial11_2_ParisFiller.json
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
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stTimeConsuming/sstore_combinations_initial11_2_ParisFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7",
        ),
        pytest.param(
            8,
            0,
            0,
            id="d8",
        ),
        pytest.param(
            9,
            0,
            0,
            id="d9",
        ),
        pytest.param(
            10,
            0,
            0,
            id="d10",
        ),
        pytest.param(
            11,
            0,
            0,
            id="d11",
        ),
        pytest.param(
            12,
            0,
            0,
            id="d12",
        ),
        pytest.param(
            13,
            0,
            0,
            id="d13",
        ),
        pytest.param(
            14,
            0,
            0,
            id="d14",
        ),
        pytest.param(
            15,
            0,
            0,
            id="d15",
        ),
        pytest.param(
            16,
            0,
            0,
            id="d16",
        ),
        pytest.param(
            17,
            0,
            0,
            id="d17",
        ),
        pytest.param(
            18,
            0,
            0,
            id="d18",
        ),
        pytest.param(
            19,
            0,
            0,
            id="d19",
        ),
        pytest.param(
            20,
            0,
            0,
            id="d20",
        ),
        pytest.param(
            21,
            0,
            0,
            id="d21",
        ),
        pytest.param(
            22,
            0,
            0,
            id="d22",
        ),
        pytest.param(
            23,
            0,
            0,
            id="d23",
        ),
        pytest.param(
            24,
            0,
            0,
            id="d24",
        ),
        pytest.param(
            25,
            0,
            0,
            id="d25",
        ),
        pytest.param(
            26,
            0,
            0,
            id="d26",
        ),
        pytest.param(
            27,
            0,
            0,
            id="d27",
        ),
        pytest.param(
            28,
            0,
            0,
            id="d28",
        ),
        pytest.param(
            29,
            0,
            0,
            id="d29",
        ),
        pytest.param(
            30,
            0,
            0,
            id="d30",
        ),
        pytest.param(
            31,
            0,
            0,
            id="d31",
        ),
        pytest.param(
            32,
            0,
            0,
            id="d32",
        ),
        pytest.param(
            33,
            0,
            0,
            id="d33",
        ),
        pytest.param(
            34,
            0,
            0,
            id="d34",
        ),
        pytest.param(
            35,
            0,
            0,
            id="d35",
        ),
        pytest.param(
            36,
            0,
            0,
            id="d36",
        ),
        pytest.param(
            37,
            0,
            0,
            id="d37",
        ),
        pytest.param(
            38,
            0,
            0,
            id="d38",
        ),
        pytest.param(
            39,
            0,
            0,
            id="d39",
        ),
        pytest.param(
            40,
            0,
            0,
            id="d40",
        ),
        pytest.param(
            41,
            0,
            0,
            id="d41",
        ),
        pytest.param(
            42,
            0,
            0,
            id="d42",
        ),
        pytest.param(
            43,
            0,
            0,
            id="d43",
        ),
        pytest.param(
            44,
            0,
            0,
            id="d44",
        ),
        pytest.param(
            45,
            0,
            0,
            id="d45",
        ),
        pytest.param(
            46,
            0,
            0,
            id="d46",
        ),
        pytest.param(
            47,
            0,
            0,
            id="d47",
        ),
        pytest.param(
            48,
            0,
            0,
            id="d48",
        ),
        pytest.param(
            49,
            0,
            0,
            id="d49",
        ),
        pytest.param(
            50,
            0,
            0,
            id="d50",
        ),
        pytest.param(
            51,
            0,
            0,
            id="d51",
        ),
        pytest.param(
            52,
            0,
            0,
            id="d52",
        ),
        pytest.param(
            53,
            0,
            0,
            id="d53",
        ),
        pytest.param(
            54,
            0,
            0,
            id="d54",
        ),
        pytest.param(
            55,
            0,
            0,
            id="d55",
        ),
        pytest.param(
            56,
            0,
            0,
            id="d56",
        ),
        pytest.param(
            57,
            0,
            0,
            id="d57",
        ),
        pytest.param(
            58,
            0,
            0,
            id="d58",
        ),
        pytest.param(
            59,
            0,
            0,
            id="d59",
        ),
        pytest.param(
            60,
            0,
            0,
            id="d60",
        ),
        pytest.param(
            61,
            0,
            0,
            id="d61",
        ),
        pytest.param(
            62,
            0,
            0,
            id="d62",
        ),
        pytest.param(
            63,
            0,
            0,
            id="d63",
        ),
        pytest.param(
            64,
            0,
            0,
            id="d64",
        ),
        pytest.param(
            65,
            0,
            0,
            id="d65",
        ),
        pytest.param(
            66,
            0,
            0,
            id="d66",
        ),
        pytest.param(
            67,
            0,
            0,
            id="d67",
        ),
        pytest.param(
            68,
            0,
            0,
            id="d68",
        ),
        pytest.param(
            69,
            0,
            0,
            id="d69",
        ),
        pytest.param(
            70,
            0,
            0,
            id="d70",
        ),
        pytest.param(
            71,
            0,
            0,
            id="d71",
        ),
        pytest.param(
            72,
            0,
            0,
            id="d72",
        ),
        pytest.param(
            73,
            0,
            0,
            id="d73",
        ),
        pytest.param(
            74,
            0,
            0,
            id="d74",
        ),
        pytest.param(
            75,
            0,
            0,
            id="d75",
        ),
        pytest.param(
            76,
            0,
            0,
            id="d76",
        ),
        pytest.param(
            77,
            0,
            0,
            id="d77",
        ),
        pytest.param(
            78,
            0,
            0,
            id="d78",
        ),
        pytest.param(
            79,
            0,
            0,
            id="d79",
        ),
        pytest.param(
            80,
            0,
            0,
            id="d80",
        ),
        pytest.param(
            81,
            0,
            0,
            id="d81",
        ),
        pytest.param(
            82,
            0,
            0,
            id="d82",
        ),
        pytest.param(
            83,
            0,
            0,
            id="d83",
        ),
        pytest.param(
            84,
            0,
            0,
            id="d84",
        ),
        pytest.param(
            85,
            0,
            0,
            id="d85",
        ),
        pytest.param(
            86,
            0,
            0,
            id="d86",
        ),
        pytest.param(
            87,
            0,
            0,
            id="d87",
        ),
        pytest.param(
            88,
            0,
            0,
            id="d88",
        ),
        pytest.param(
            89,
            0,
            0,
            id="d89",
        ),
        pytest.param(
            90,
            0,
            0,
            id="d90",
        ),
        pytest.param(
            91,
            0,
            0,
            id="d91",
        ),
        pytest.param(
            92,
            0,
            0,
            id="d92",
        ),
        pytest.param(
            93,
            0,
            0,
            id="d93",
        ),
        pytest.param(
            94,
            0,
            0,
            id="d94",
        ),
        pytest.param(
            95,
            0,
            0,
            id="d95",
        ),
        pytest.param(
            96,
            0,
            0,
            id="d96",
        ),
        pytest.param(
            97,
            0,
            0,
            id="d97",
        ),
        pytest.param(
            98,
            0,
            0,
            id="d98",
        ),
        pytest.param(
            99,
            0,
            0,
            id="d99",
        ),
        pytest.param(
            100,
            0,
            0,
            id="d100",
        ),
        pytest.param(
            101,
            0,
            0,
            id="d101",
        ),
        pytest.param(
            102,
            0,
            0,
            id="d102",
        ),
        pytest.param(
            103,
            0,
            0,
            id="d103",
        ),
        pytest.param(
            104,
            0,
            0,
            id="d104",
        ),
        pytest.param(
            105,
            0,
            0,
            id="d105",
        ),
        pytest.param(
            106,
            0,
            0,
            id="d106",
        ),
        pytest.param(
            107,
            0,
            0,
            id="d107",
        ),
        pytest.param(
            108,
            0,
            0,
            id="d108",
        ),
        pytest.param(
            109,
            0,
            0,
            id="d109",
        ),
        pytest.param(
            110,
            0,
            0,
            id="d110",
        ),
        pytest.param(
            111,
            0,
            0,
            id="d111",
        ),
        pytest.param(
            112,
            0,
            0,
            id="d112",
        ),
        pytest.param(
            113,
            0,
            0,
            id="d113",
        ),
        pytest.param(
            114,
            0,
            0,
            id="d114",
        ),
        pytest.param(
            115,
            0,
            0,
            id="d115",
        ),
        pytest.param(
            116,
            0,
            0,
            id="d116",
        ),
        pytest.param(
            117,
            0,
            0,
            id="d117",
        ),
        pytest.param(
            118,
            0,
            0,
            id="d118",
        ),
        pytest.param(
            119,
            0,
            0,
            id="d119",
        ),
        pytest.param(
            120,
            0,
            0,
            id="d120",
        ),
        pytest.param(
            121,
            0,
            0,
            id="d121",
        ),
        pytest.param(
            122,
            0,
            0,
            id="d122",
        ),
        pytest.param(
            123,
            0,
            0,
            id="d123",
        ),
        pytest.param(
            124,
            0,
            0,
            id="d124",
        ),
        pytest.param(
            125,
            0,
            0,
            id="d125",
        ),
        pytest.param(
            126,
            0,
            0,
            id="d126",
        ),
        pytest.param(
            127,
            0,
            0,
            id="d127",
        ),
        pytest.param(
            128,
            0,
            0,
            id="d128",
        ),
        pytest.param(
            129,
            0,
            0,
            id="d129",
        ),
        pytest.param(
            130,
            0,
            0,
            id="d130",
        ),
        pytest.param(
            131,
            0,
            0,
            id="d131",
        ),
        pytest.param(
            132,
            0,
            0,
            id="d132",
        ),
        pytest.param(
            133,
            0,
            0,
            id="d133",
        ),
        pytest.param(
            134,
            0,
            0,
            id="d134",
        ),
        pytest.param(
            135,
            0,
            0,
            id="d135",
        ),
        pytest.param(
            136,
            0,
            0,
            id="d136",
        ),
        pytest.param(
            137,
            0,
            0,
            id="d137",
        ),
        pytest.param(
            138,
            0,
            0,
            id="d138",
        ),
        pytest.param(
            139,
            0,
            0,
            id="d139",
        ),
        pytest.param(
            140,
            0,
            0,
            id="d140",
        ),
        pytest.param(
            141,
            0,
            0,
            id="d141",
        ),
        pytest.param(
            142,
            0,
            0,
            id="d142",
        ),
        pytest.param(
            143,
            0,
            0,
            id="d143",
        ),
        pytest.param(
            144,
            0,
            0,
            id="d144",
        ),
        pytest.param(
            145,
            0,
            0,
            id="d145",
        ),
        pytest.param(
            146,
            0,
            0,
            id="d146",
        ),
        pytest.param(
            147,
            0,
            0,
            id="d147",
        ),
        pytest.param(
            148,
            0,
            0,
            id="d148",
        ),
        pytest.param(
            149,
            0,
            0,
            id="d149",
        ),
        pytest.param(
            150,
            0,
            0,
            id="d150",
        ),
        pytest.param(
            151,
            0,
            0,
            id="d151",
        ),
        pytest.param(
            152,
            0,
            0,
            id="d152",
        ),
        pytest.param(
            153,
            0,
            0,
            id="d153",
        ),
        pytest.param(
            154,
            0,
            0,
            id="d154",
        ),
        pytest.param(
            155,
            0,
            0,
            id="d155",
        ),
        pytest.param(
            156,
            0,
            0,
            id="d156",
        ),
        pytest.param(
            157,
            0,
            0,
            id="d157",
        ),
        pytest.param(
            158,
            0,
            0,
            id="d158",
        ),
        pytest.param(
            159,
            0,
            0,
            id="d159",
        ),
        pytest.param(
            160,
            0,
            0,
            id="d160",
        ),
        pytest.param(
            161,
            0,
            0,
            id="d161",
        ),
        pytest.param(
            162,
            0,
            0,
            id="d162",
        ),
        pytest.param(
            163,
            0,
            0,
            id="d163",
        ),
        pytest.param(
            164,
            0,
            0,
            id="d164",
        ),
        pytest.param(
            165,
            0,
            0,
            id="d165",
        ),
        pytest.param(
            166,
            0,
            0,
            id="d166",
        ),
        pytest.param(
            167,
            0,
            0,
            id="d167",
        ),
        pytest.param(
            168,
            0,
            0,
            id="d168",
        ),
        pytest.param(
            169,
            0,
            0,
            id="d169",
        ),
        pytest.param(
            170,
            0,
            0,
            id="d170",
        ),
        pytest.param(
            171,
            0,
            0,
            id="d171",
        ),
        pytest.param(
            172,
            0,
            0,
            id="d172",
        ),
        pytest.param(
            173,
            0,
            0,
            id="d173",
        ),
        pytest.param(
            174,
            0,
            0,
            id="d174",
        ),
        pytest.param(
            175,
            0,
            0,
            id="d175",
        ),
        pytest.param(
            176,
            0,
            0,
            id="d176",
        ),
        pytest.param(
            177,
            0,
            0,
            id="d177",
        ),
        pytest.param(
            178,
            0,
            0,
            id="d178",
        ),
        pytest.param(
            179,
            0,
            0,
            id="d179",
        ),
        pytest.param(
            180,
            0,
            0,
            id="d180",
        ),
        pytest.param(
            181,
            0,
            0,
            id="d181",
        ),
        pytest.param(
            182,
            0,
            0,
            id="d182",
        ),
        pytest.param(
            183,
            0,
            0,
            id="d183",
        ),
        pytest.param(
            184,
            0,
            0,
            id="d184",
        ),
        pytest.param(
            185,
            0,
            0,
            id="d185",
        ),
        pytest.param(
            186,
            0,
            0,
            id="d186",
        ),
        pytest.param(
            187,
            0,
            0,
            id="d187",
        ),
        pytest.param(
            188,
            0,
            0,
            id="d188",
        ),
        pytest.param(
            189,
            0,
            0,
            id="d189",
        ),
        pytest.param(
            190,
            0,
            0,
            id="d190",
        ),
        pytest.param(
            191,
            0,
            0,
            id="d191",
        ),
        pytest.param(
            192,
            0,
            0,
            id="d192",
        ),
        pytest.param(
            193,
            0,
            0,
            id="d193",
        ),
        pytest.param(
            194,
            0,
            0,
            id="d194",
        ),
        pytest.param(
            195,
            0,
            0,
            id="d195",
        ),
        pytest.param(
            196,
            0,
            0,
            id="d196",
        ),
        pytest.param(
            197,
            0,
            0,
            id="d197",
        ),
        pytest.param(
            198,
            0,
            0,
            id="d198",
        ),
        pytest.param(
            199,
            0,
            0,
            id="d199",
        ),
        pytest.param(
            200,
            0,
            0,
            id="d200",
        ),
        pytest.param(
            201,
            0,
            0,
            id="d201",
        ),
        pytest.param(
            202,
            0,
            0,
            id="d202",
        ),
        pytest.param(
            203,
            0,
            0,
            id="d203",
        ),
        pytest.param(
            204,
            0,
            0,
            id="d204",
        ),
        pytest.param(
            205,
            0,
            0,
            id="d205",
        ),
        pytest.param(
            206,
            0,
            0,
            id="d206",
        ),
        pytest.param(
            207,
            0,
            0,
            id="d207",
        ),
        pytest.param(
            208,
            0,
            0,
            id="d208",
        ),
        pytest.param(
            209,
            0,
            0,
            id="d209",
        ),
        pytest.param(
            210,
            0,
            0,
            id="d210",
        ),
        pytest.param(
            211,
            0,
            0,
            id="d211",
        ),
        pytest.param(
            212,
            0,
            0,
            id="d212",
        ),
        pytest.param(
            213,
            0,
            0,
            id="d213",
        ),
        pytest.param(
            214,
            0,
            0,
            id="d214",
        ),
        pytest.param(
            215,
            0,
            0,
            id="d215",
        ),
        pytest.param(
            216,
            0,
            0,
            id="d216",
        ),
        pytest.param(
            217,
            0,
            0,
            id="d217",
        ),
        pytest.param(
            218,
            0,
            0,
            id="d218",
        ),
        pytest.param(
            219,
            0,
            0,
            id="d219",
        ),
        pytest.param(
            220,
            0,
            0,
            id="d220",
        ),
        pytest.param(
            221,
            0,
            0,
            id="d221",
        ),
        pytest.param(
            222,
            0,
            0,
            id="d222",
        ),
        pytest.param(
            223,
            0,
            0,
            id="d223",
        ),
        pytest.param(
            224,
            0,
            0,
            id="d224",
        ),
        pytest.param(
            225,
            0,
            0,
            id="d225",
        ),
        pytest.param(
            226,
            0,
            0,
            id="d226",
        ),
        pytest.param(
            227,
            0,
            0,
            id="d227",
        ),
        pytest.param(
            228,
            0,
            0,
            id="d228",
        ),
        pytest.param(
            229,
            0,
            0,
            id="d229",
        ),
        pytest.param(
            230,
            0,
            0,
            id="d230",
        ),
        pytest.param(
            231,
            0,
            0,
            id="d231",
        ),
        pytest.param(
            232,
            0,
            0,
            id="d232",
        ),
        pytest.param(
            233,
            0,
            0,
            id="d233",
        ),
        pytest.param(
            234,
            0,
            0,
            id="d234",
        ),
        pytest.param(
            235,
            0,
            0,
            id="d235",
        ),
        pytest.param(
            236,
            0,
            0,
            id="d236",
        ),
        pytest.param(
            237,
            0,
            0,
            id="d237",
        ),
        pytest.param(
            238,
            0,
            0,
            id="d238",
        ),
        pytest.param(
            239,
            0,
            0,
            id="d239",
        ),
        pytest.param(
            240,
            0,
            0,
            id="d240",
        ),
        pytest.param(
            241,
            0,
            0,
            id="d241",
        ),
        pytest.param(
            242,
            0,
            0,
            id="d242",
        ),
        pytest.param(
            243,
            0,
            0,
            id="d243",
        ),
        pytest.param(
            244,
            0,
            0,
            id="d244",
        ),
        pytest.param(
            245,
            0,
            0,
            id="d245",
        ),
        pytest.param(
            246,
            0,
            0,
            id="d246",
        ),
        pytest.param(
            247,
            0,
            0,
            id="d247",
        ),
        pytest.param(
            248,
            0,
            0,
            id="d248",
        ),
        pytest.param(
            249,
            0,
            0,
            id="d249",
        ),
        pytest.param(
            250,
            0,
            0,
            id="d250",
        ),
        pytest.param(
            251,
            0,
            0,
            id="d251",
        ),
        pytest.param(
            252,
            0,
            0,
            id="d252",
        ),
        pytest.param(
            253,
            0,
            0,
            id="d253",
        ),
        pytest.param(
            254,
            0,
            0,
            id="d254",
        ),
        pytest.param(
            255,
            0,
            0,
            id="d255",
        ),
        pytest.param(
            256,
            0,
            0,
            id="d256",
        ),
        pytest.param(
            257,
            0,
            0,
            id="d257",
        ),
        pytest.param(
            258,
            0,
            0,
            id="d258",
        ),
        pytest.param(
            259,
            0,
            0,
            id="d259",
        ),
        pytest.param(
            260,
            0,
            0,
            id="d260",
        ),
        pytest.param(
            261,
            0,
            0,
            id="d261",
        ),
        pytest.param(
            262,
            0,
            0,
            id="d262",
        ),
        pytest.param(
            263,
            0,
            0,
            id="d263",
        ),
        pytest.param(
            264,
            0,
            0,
            id="d264",
        ),
        pytest.param(
            265,
            0,
            0,
            id="d265",
        ),
        pytest.param(
            266,
            0,
            0,
            id="d266",
        ),
        pytest.param(
            267,
            0,
            0,
            id="d267",
        ),
        pytest.param(
            268,
            0,
            0,
            id="d268",
        ),
        pytest.param(
            269,
            0,
            0,
            id="d269",
        ),
        pytest.param(
            270,
            0,
            0,
            id="d270",
        ),
        pytest.param(
            271,
            0,
            0,
            id="d271",
        ),
        pytest.param(
            272,
            0,
            0,
            id="d272",
        ),
        pytest.param(
            273,
            0,
            0,
            id="d273",
        ),
        pytest.param(
            274,
            0,
            0,
            id="d274",
        ),
        pytest.param(
            275,
            0,
            0,
            id="d275",
        ),
        pytest.param(
            276,
            0,
            0,
            id="d276",
        ),
        pytest.param(
            277,
            0,
            0,
            id="d277",
        ),
        pytest.param(
            278,
            0,
            0,
            id="d278",
        ),
        pytest.param(
            279,
            0,
            0,
            id="d279",
        ),
        pytest.param(
            280,
            0,
            0,
            id="d280",
        ),
        pytest.param(
            281,
            0,
            0,
            id="d281",
        ),
        pytest.param(
            282,
            0,
            0,
            id="d282",
        ),
        pytest.param(
            283,
            0,
            0,
            id="d283",
        ),
        pytest.param(
            284,
            0,
            0,
            id="d284",
        ),
        pytest.param(
            285,
            0,
            0,
            id="d285",
        ),
        pytest.param(
            286,
            0,
            0,
            id="d286",
        ),
        pytest.param(
            287,
            0,
            0,
            id="d287",
        ),
        pytest.param(
            288,
            0,
            0,
            id="d288",
        ),
        pytest.param(
            289,
            0,
            0,
            id="d289",
        ),
        pytest.param(
            290,
            0,
            0,
            id="d290",
        ),
        pytest.param(
            291,
            0,
            0,
            id="d291",
        ),
        pytest.param(
            292,
            0,
            0,
            id="d292",
        ),
        pytest.param(
            293,
            0,
            0,
            id="d293",
        ),
        pytest.param(
            294,
            0,
            0,
            id="d294",
        ),
        pytest.param(
            295,
            0,
            0,
            id="d295",
        ),
        pytest.param(
            296,
            0,
            0,
            id="d296",
        ),
        pytest.param(
            297,
            0,
            0,
            id="d297",
        ),
        pytest.param(
            298,
            0,
            0,
            id="d298",
        ),
        pytest.param(
            299,
            0,
            0,
            id="d299",
        ),
        pytest.param(
            300,
            0,
            0,
            id="d300",
        ),
        pytest.param(
            301,
            0,
            0,
            id="d301",
        ),
        pytest.param(
            302,
            0,
            0,
            id="d302",
        ),
        pytest.param(
            303,
            0,
            0,
            id="d303",
        ),
        pytest.param(
            304,
            0,
            0,
            id="d304",
        ),
        pytest.param(
            305,
            0,
            0,
            id="d305",
        ),
        pytest.param(
            306,
            0,
            0,
            id="d306",
        ),
        pytest.param(
            307,
            0,
            0,
            id="d307",
        ),
        pytest.param(
            308,
            0,
            0,
            id="d308",
        ),
        pytest.param(
            309,
            0,
            0,
            id="d309",
        ),
        pytest.param(
            310,
            0,
            0,
            id="d310",
        ),
        pytest.param(
            311,
            0,
            0,
            id="d311",
        ),
        pytest.param(
            312,
            0,
            0,
            id="d312",
        ),
        pytest.param(
            313,
            0,
            0,
            id="d313",
        ),
        pytest.param(
            314,
            0,
            0,
            id="d314",
        ),
        pytest.param(
            315,
            0,
            0,
            id="d315",
        ),
        pytest.param(
            316,
            0,
            0,
            id="d316",
        ),
        pytest.param(
            317,
            0,
            0,
            id="d317",
        ),
        pytest.param(
            318,
            0,
            0,
            id="d318",
        ),
        pytest.param(
            319,
            0,
            0,
            id="d319",
        ),
        pytest.param(
            320,
            0,
            0,
            id="d320",
        ),
        pytest.param(
            321,
            0,
            0,
            id="d321",
        ),
        pytest.param(
            322,
            0,
            0,
            id="d322",
        ),
        pytest.param(
            323,
            0,
            0,
            id="d323",
        ),
        pytest.param(
            324,
            0,
            0,
            id="d324",
        ),
        pytest.param(
            325,
            0,
            0,
            id="d325",
        ),
        pytest.param(
            326,
            0,
            0,
            id="d326",
        ),
        pytest.param(
            327,
            0,
            0,
            id="d327",
        ),
        pytest.param(
            328,
            0,
            0,
            id="d328",
        ),
        pytest.param(
            329,
            0,
            0,
            id="d329",
        ),
        pytest.param(
            330,
            0,
            0,
            id="d330",
        ),
        pytest.param(
            331,
            0,
            0,
            id="d331",
        ),
        pytest.param(
            332,
            0,
            0,
            id="d332",
        ),
        pytest.param(
            333,
            0,
            0,
            id="d333",
        ),
        pytest.param(
            334,
            0,
            0,
            id="d334",
        ),
        pytest.param(
            335,
            0,
            0,
            id="d335",
        ),
        pytest.param(
            336,
            0,
            0,
            id="d336",
        ),
        pytest.param(
            337,
            0,
            0,
            id="d337",
        ),
        pytest.param(
            338,
            0,
            0,
            id="d338",
        ),
        pytest.param(
            339,
            0,
            0,
            id="d339",
        ),
        pytest.param(
            340,
            0,
            0,
            id="d340",
        ),
        pytest.param(
            341,
            0,
            0,
            id="d341",
        ),
        pytest.param(
            342,
            0,
            0,
            id="d342",
        ),
        pytest.param(
            343,
            0,
            0,
            id="d343",
        ),
        pytest.param(
            344,
            0,
            0,
            id="d344",
        ),
        pytest.param(
            345,
            0,
            0,
            id="d345",
        ),
        pytest.param(
            346,
            0,
            0,
            id="d346",
        ),
        pytest.param(
            347,
            0,
            0,
            id="d347",
        ),
        pytest.param(
            348,
            0,
            0,
            id="d348",
        ),
        pytest.param(
            349,
            0,
            0,
            id="d349",
        ),
        pytest.param(
            350,
            0,
            0,
            id="d350",
        ),
        pytest.param(
            351,
            0,
            0,
            id="d351",
        ),
        pytest.param(
            352,
            0,
            0,
            id="d352",
        ),
        pytest.param(
            353,
            0,
            0,
            id="d353",
        ),
        pytest.param(
            354,
            0,
            0,
            id="d354",
        ),
        pytest.param(
            355,
            0,
            0,
            id="d355",
        ),
        pytest.param(
            356,
            0,
            0,
            id="d356",
        ),
        pytest.param(
            357,
            0,
            0,
            id="d357",
        ),
        pytest.param(
            358,
            0,
            0,
            id="d358",
        ),
        pytest.param(
            359,
            0,
            0,
            id="d359",
        ),
        pytest.param(
            360,
            0,
            0,
            id="d360",
        ),
        pytest.param(
            361,
            0,
            0,
            id="d361",
        ),
        pytest.param(
            362,
            0,
            0,
            id="d362",
        ),
        pytest.param(
            363,
            0,
            0,
            id="d363",
        ),
        pytest.param(
            364,
            0,
            0,
            id="d364",
        ),
        pytest.param(
            365,
            0,
            0,
            id="d365",
        ),
        pytest.param(
            366,
            0,
            0,
            id="d366",
        ),
        pytest.param(
            367,
            0,
            0,
            id="d367",
        ),
        pytest.param(
            368,
            0,
            0,
            id="d368",
        ),
        pytest.param(
            369,
            0,
            0,
            id="d369",
        ),
        pytest.param(
            370,
            0,
            0,
            id="d370",
        ),
        pytest.param(
            371,
            0,
            0,
            id="d371",
        ),
        pytest.param(
            372,
            0,
            0,
            id="d372",
        ),
        pytest.param(
            373,
            0,
            0,
            id="d373",
        ),
        pytest.param(
            374,
            0,
            0,
            id="d374",
        ),
        pytest.param(
            375,
            0,
            0,
            id="d375",
        ),
        pytest.param(
            376,
            0,
            0,
            id="d376",
        ),
        pytest.param(
            377,
            0,
            0,
            id="d377",
        ),
        pytest.param(
            378,
            0,
            0,
            id="d378",
        ),
        pytest.param(
            379,
            0,
            0,
            id="d379",
        ),
        pytest.param(
            380,
            0,
            0,
            id="d380",
        ),
        pytest.param(
            381,
            0,
            0,
            id="d381",
        ),
        pytest.param(
            382,
            0,
            0,
            id="d382",
        ),
        pytest.param(
            383,
            0,
            0,
            id="d383",
        ),
        pytest.param(
            384,
            0,
            0,
            id="d384",
        ),
        pytest.param(
            385,
            0,
            0,
            id="d385",
        ),
        pytest.param(
            386,
            0,
            0,
            id="d386",
        ),
        pytest.param(
            387,
            0,
            0,
            id="d387",
        ),
        pytest.param(
            388,
            0,
            0,
            id="d388",
        ),
        pytest.param(
            389,
            0,
            0,
            id="d389",
        ),
        pytest.param(
            390,
            0,
            0,
            id="d390",
        ),
        pytest.param(
            391,
            0,
            0,
            id="d391",
        ),
        pytest.param(
            392,
            0,
            0,
            id="d392",
        ),
        pytest.param(
            393,
            0,
            0,
            id="d393",
        ),
        pytest.param(
            394,
            0,
            0,
            id="d394",
        ),
        pytest.param(
            395,
            0,
            0,
            id="d395",
        ),
        pytest.param(
            396,
            0,
            0,
            id="d396",
        ),
        pytest.param(
            397,
            0,
            0,
            id="d397",
        ),
        pytest.param(
            398,
            0,
            0,
            id="d398",
        ),
        pytest.param(
            399,
            0,
            0,
            id="d399",
        ),
        pytest.param(
            400,
            0,
            0,
            id="d400",
        ),
        pytest.param(
            401,
            0,
            0,
            id="d401",
        ),
        pytest.param(
            402,
            0,
            0,
            id="d402",
        ),
        pytest.param(
            403,
            0,
            0,
            id="d403",
        ),
        pytest.param(
            404,
            0,
            0,
            id="d404",
        ),
        pytest.param(
            405,
            0,
            0,
            id="d405",
        ),
        pytest.param(
            406,
            0,
            0,
            id="d406",
        ),
        pytest.param(
            407,
            0,
            0,
            id="d407",
        ),
        pytest.param(
            408,
            0,
            0,
            id="d408",
        ),
        pytest.param(
            409,
            0,
            0,
            id="d409",
        ),
        pytest.param(
            410,
            0,
            0,
            id="d410",
        ),
        pytest.param(
            411,
            0,
            0,
            id="d411",
        ),
        pytest.param(
            412,
            0,
            0,
            id="d412",
        ),
        pytest.param(
            413,
            0,
            0,
            id="d413",
        ),
        pytest.param(
            414,
            0,
            0,
            id="d414",
        ),
        pytest.param(
            415,
            0,
            0,
            id="d415",
        ),
        pytest.param(
            416,
            0,
            0,
            id="d416",
        ),
        pytest.param(
            417,
            0,
            0,
            id="d417",
        ),
        pytest.param(
            418,
            0,
            0,
            id="d418",
        ),
        pytest.param(
            419,
            0,
            0,
            id="d419",
        ),
        pytest.param(
            420,
            0,
            0,
            id="d420",
        ),
        pytest.param(
            421,
            0,
            0,
            id="d421",
        ),
        pytest.param(
            422,
            0,
            0,
            id="d422",
        ),
        pytest.param(
            423,
            0,
            0,
            id="d423",
        ),
        pytest.param(
            424,
            0,
            0,
            id="d424",
        ),
        pytest.param(
            425,
            0,
            0,
            id="d425",
        ),
        pytest.param(
            426,
            0,
            0,
            id="d426",
        ),
        pytest.param(
            427,
            0,
            0,
            id="d427",
        ),
        pytest.param(
            428,
            0,
            0,
            id="d428",
        ),
        pytest.param(
            429,
            0,
            0,
            id="d429",
        ),
        pytest.param(
            430,
            0,
            0,
            id="d430",
        ),
        pytest.param(
            431,
            0,
            0,
            id="d431",
        ),
        pytest.param(
            432,
            0,
            0,
            id="d432",
        ),
        pytest.param(
            433,
            0,
            0,
            id="d433",
        ),
        pytest.param(
            434,
            0,
            0,
            id="d434",
        ),
        pytest.param(
            435,
            0,
            0,
            id="d435",
        ),
        pytest.param(
            436,
            0,
            0,
            id="d436",
        ),
        pytest.param(
            437,
            0,
            0,
            id="d437",
        ),
        pytest.param(
            438,
            0,
            0,
            id="d438",
        ),
        pytest.param(
            439,
            0,
            0,
            id="d439",
        ),
        pytest.param(
            440,
            0,
            0,
            id="d440",
        ),
        pytest.param(
            441,
            0,
            0,
            id="d441",
        ),
        pytest.param(
            442,
            0,
            0,
            id="d442",
        ),
        pytest.param(
            443,
            0,
            0,
            id="d443",
        ),
        pytest.param(
            444,
            0,
            0,
            id="d444",
        ),
        pytest.param(
            445,
            0,
            0,
            id="d445",
        ),
        pytest.param(
            446,
            0,
            0,
            id="d446",
        ),
        pytest.param(
            447,
            0,
            0,
            id="d447",
        ),
        pytest.param(
            448,
            0,
            0,
            id="d448",
        ),
        pytest.param(
            449,
            0,
            0,
            id="d449",
        ),
        pytest.param(
            450,
            0,
            0,
            id="d450",
        ),
        pytest.param(
            451,
            0,
            0,
            id="d451",
        ),
        pytest.param(
            452,
            0,
            0,
            id="d452",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_sstore_combinations_initial11_2_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Sstore 1 -> {calltype} -> change to {0, 1, 2} |-> {calltype} ->..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB000000000000000000000000000000000000000)
    contract_1 = Address(0xB100000000000000000000000000000000000000)
    contract_2 = Address(0xB200000000000000000000000000000000000000)
    contract_3 = Address(0x1000000000000000000000000000000000000000)
    contract_4 = Address(0x2000000000000000000000000000000000000000)
    contract_5 = Address(0x3000000000000000000000000000000000000000)
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

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { [[0]] 0  [[1]] 1  [[2]] 2 }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x0)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x2, value=0x2)
        + Op.STOP,
        nonce=0,
        address=Address(0xB000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { [[0]] 0  [[1]] 1  [[2]] 2 }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x0)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x2, value=0x2)
        + Op.STOP,
        storage={0: 1, 1: 1, 2: 1},
        nonce=0,
        address=Address(0xB100000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { [[0]] 0  [[1]] 1  [[2]] 2 }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x0)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x2, value=0x2)
        + Op.STOP,
        storage={0: 2, 1: 2, 2: 2},
        nonce=0,
        address=Address(0xB200000000000000000000000000000000000000),  # noqa: E501
    )
    pre[contract_3] = Account(balance=10, storage={0: 1, 1: 1, 2: 1})
    # Source: lll
    # { [[1]] 1 [[1]] 0 [[2]] 1 [[2]] 0 [[3]] 1 [[3]] 0 [[4]] 1 [[4]] 0 [[5]] 1 [[5]] 0 [[6]] 1 [[6]] 0 [[7]] 1 [[7]] 0 [[8]] 1 [[8]] 0 [[9]] 1 [[9]] 0 [[10]] 1 [[10]] 0 [[11]] 1 [[11]] 0 [[12]] 1 [[12]] 0 [[13]] 1 [[13]] 0 [[14]] 1 [[14]] 0 [[15]] 1 [[15]] 0 [[16]] 1 [[16]] 0  [[1]] 1 }  # noqa: E501
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x1, value=0x0)
        + Op.SSTORE(key=0x2, value=0x1)
        + Op.SSTORE(key=0x2, value=0x0)
        + Op.SSTORE(key=0x3, value=0x1)
        + Op.SSTORE(key=0x3, value=0x0)
        + Op.SSTORE(key=0x4, value=0x1)
        + Op.SSTORE(key=0x4, value=0x0)
        + Op.SSTORE(key=0x5, value=0x1)
        + Op.SSTORE(key=0x5, value=0x0)
        + Op.SSTORE(key=0x6, value=0x1)
        + Op.SSTORE(key=0x6, value=0x0)
        + Op.SSTORE(key=0x7, value=0x1)
        + Op.SSTORE(key=0x7, value=0x0)
        + Op.SSTORE(key=0x8, value=0x1)
        + Op.SSTORE(key=0x8, value=0x0)
        + Op.SSTORE(key=0x9, value=0x1)
        + Op.SSTORE(key=0x9, value=0x0)
        + Op.SSTORE(key=0xA, value=0x1)
        + Op.SSTORE(key=0xA, value=0x0)
        + Op.SSTORE(key=0xB, value=0x1)
        + Op.SSTORE(key=0xB, value=0x0)
        + Op.SSTORE(key=0xC, value=0x1)
        + Op.SSTORE(key=0xC, value=0x0)
        + Op.SSTORE(key=0xD, value=0x1)
        + Op.SSTORE(key=0xD, value=0x0)
        + Op.SSTORE(key=0xE, value=0x1)
        + Op.SSTORE(key=0xE, value=0x0)
        + Op.SSTORE(key=0xF, value=0x1)
        + Op.SSTORE(key=0xF, value=0x0)
        + Op.SSTORE(key=0x10, value=0x1)
        + Op.SSTORE(key=0x10, value=0x0)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x2000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (REVERT 0 32) }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.REVERT(offset=0x0, size=0x20) + Op.STOP,
        storage={0: 2, 1: 2, 2: 2},
        nonce=0,
        address=Address(0x3000000000000000000000000000000000000000),  # noqa: E501
    )

    tx_data = [
        Op.MSTORE(offset=0x64, value=0x4FC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4FD)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4FE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4FF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x500)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x501)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x502)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x503)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x504)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x505)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x506)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x507)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x508)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x509)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x50A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x50B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x50C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x50D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x50E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x50F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x510)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x511)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x512)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x513)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x514)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x515)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x516)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x517)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x518)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x519)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x51A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x51B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x51C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x51D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x51E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x51F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x520)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x521)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x522)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x523)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x524)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x525)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x526)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x527)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x528)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x529)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x52A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x52B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x52C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x52D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x52E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x52F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x530)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x531)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x532)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x533)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x534)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x535)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x536)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x537)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x538)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x539)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x53A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x53B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x53C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x53D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x53E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x53F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x540)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x541)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x542)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x543)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x544)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x545)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x546)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x547)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x548)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x549)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x54A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x54B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x54C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x54D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x54E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x54F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x550)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x551)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x552)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x553)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x554)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x555)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x556)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x557)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x558)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x559)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x55A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x55B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x55C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x55D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x55E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x55F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x560)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x561)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x562)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x563)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x564)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x565)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x566)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x567)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x568)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x569)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x56A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x56B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x56C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x56D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x56E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x56F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x570)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x571)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x572)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x573)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x574)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x575)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x576)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x577)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x578)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x579)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x57A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x57B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x57C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x57D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x57E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x57F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x580)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x581)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x582)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x583)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x584)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x585)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x586)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x587)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x588)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x589)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x58A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x58B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x58C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x58D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x58E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x58F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x590)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x591)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x592)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x593)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x594)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x595)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x596)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x597)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x598)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x599)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x59A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x59B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x59C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x59D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x59E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x59F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5A0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5A1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5A2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5A3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5A4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5A5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5A6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5A7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5A8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5A9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5AA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5AB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5AC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5AD)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5AE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5AF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5B0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5B1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5B2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5B3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5B4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5B5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5B6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5B7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5B8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5B9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5BA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5BB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5BC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5BD)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5BE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5BF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5C0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5C1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5C2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5C3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5C4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5C5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5C6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5C7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5C8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5C9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5CA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5CB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5CC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5CD)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5CE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5CF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5D0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5D1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5D2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5D3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5D4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5D5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5D6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5D7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5D8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5D9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5DA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5DB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5DC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5DD)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5DE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5DF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5E0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5E1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5E2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5E3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5E4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5E5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5E6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5E7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5E8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5E9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5EA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5EB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5EC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5ED)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5EE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5EF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5F0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5F1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5F2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5F3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5F4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5F5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5F6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5F7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5F8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5F9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5FA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5FB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5FC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5FD)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5FE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x5FF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x600)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x601)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x602)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x603)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x604)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x605)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x606)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x607)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x608)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x609)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x60A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x60B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x60C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x60D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x60E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x60F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x610)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x611)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x612)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x613)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x614)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x615)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x616)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x617)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x618)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x619)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x61A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x61B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x61C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x61D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x61E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x61F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x620)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x621)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x622)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x623)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x624)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x625)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x626)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x627)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x628)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x629)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x62A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x62B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x62C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x62D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x62E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x62F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x630)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x631)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x632)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x633)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x634)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x635)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x636)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x637)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x638)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x639)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x63A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x63B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x63C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x63D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x63E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x63F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x640)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x641)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x642)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x643)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x644)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x645)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x646)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x647)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x648)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x649)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x64A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x64B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x64C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x64D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x64E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x64F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x650)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x651)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x652)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x653)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x654)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x655)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x656)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x657)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x658)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x659)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x65A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x65B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x65C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x65D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x65E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x65F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x660)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x661)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x662)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x663)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x664)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x665)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x666)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x667)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x668)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x669)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x66A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x66B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x66C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x66D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x66E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x66F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x670)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x671)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x672)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x673)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x674)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x675)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x676)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x677)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x678)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x679)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x67A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x67B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x67C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x67D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x67E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x67F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x680)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x681)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x682)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x683)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x684)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x685)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x686)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x687)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x688)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x689)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x68A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x68B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x68C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x68D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x68E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x68F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x690)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x691)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x692)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x693)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x694)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x695)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x696)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x697)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x698)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x699)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x69A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x69B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x69C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x69D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x69E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x69F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6A0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6A1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6A2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6A3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6A4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6A5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6A6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6A7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6A8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6A9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6AA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6AB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6AC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6AD)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6AE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6AF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6B0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6B1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6B2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6B3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6B4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6B5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6B6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6B7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6B8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6B9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6BA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6BB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6BC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6BD)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6BE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6BF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x6C0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
    ]
    tx_gas = [2000000]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        contract_4: Account(storage={1: 1}),
        compute_create_address(address=sender, nonce=0): Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
