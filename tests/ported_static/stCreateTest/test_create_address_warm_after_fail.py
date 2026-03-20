"""
Invokes failing CREATE (because initcode fails) and checks.

if the create address is considered warm in the follow up call as required by
EIP-2929.
Addresses taken from https://toolkit.abdk.consulting/ethereum#contract-address

Written primarily by Paweł Bylica (@chfast). Somewhat modified by Ori (@qbzzt)

Ported from:
tests/static/state_tests/stCreateTest/CreateAddressWarmAfterFailFiller.yml
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
    "52c3fd240000000000000000000000000000000000000000000000000000000000000000",
    "52c3fd24000000000000000000000000000000000000000000000000000000000000000a",
    "52c3fd240000000000000000000000000000000000000000000000000000000000000001",
    "52c3fd24000000000000000000000000000000000000000000000000000000000000000b",
    "52c3fd240000000000000000000000000000000000000000000000000000000000000002",
    "52c3fd24000000000000000000000000000000000000000000000000000000000000000c",
    "52c3fd240000000000000000000000000000000000000000000000000000000000000003",
    "52c3fd240000000000000000000000000000000000000000000000000000000000000004",
    "52c3fd24000000000000000000000000000000000000000000000000000000000000000d",
    "52c3fd24000000000000000000000000000000000000000000000000000000000000000e",
    "52c3fd240000000000000000000000000000000000000000000000000000000000000005",
    "52c3fd240000000000000000000000000000000000000000000000000000000000000006",
    "52c3fd240000000000000000000000000000000000000000000000000000000000000010",
    "52c3fd240000000000000000000000000000000000000000000000000000000000000007",
    "52c3fd240000000000000000000000000000000000000000000000000000000000000011",
]

TX_GAS = [16777216]

TX_VALUE = [0, 1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCreateTest/CreateAddressWarmAfterFailFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(11, 0, 0, id="case0"),
        pytest.param(11, 0, 1, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
        pytest.param(2, 0, 1, id="case3"),
        pytest.param(0, 0, 0, id="case4"),
        pytest.param(0, 0, 1, id="case5"),
        pytest.param(10, 0, 0, id="case6"),
        pytest.param(10, 0, 1, id="case7"),
        pytest.param(4, 0, 0, id="case8"),
        pytest.param(4, 0, 1, id="case9"),
        pytest.param(13, 0, 0, id="case10"),
        pytest.param(13, 0, 1, id="case11"),
        pytest.param(6, 0, 0, id="case12"),
        pytest.param(6, 0, 1, id="case13"),
        pytest.param(7, 0, 0, id="case14"),
        pytest.param(7, 0, 1, id="case15"),
        pytest.param(12, 0, 0, id="case16"),
        pytest.param(12, 0, 1, id="case17"),
        pytest.param(3, 0, 0, id="case18"),
        pytest.param(3, 0, 1, id="case19"),
        pytest.param(1, 0, 0, id="case20"),
        pytest.param(1, 0, 1, id="case21"),
        pytest.param(5, 0, 0, id="case22"),
        pytest.param(5, 0, 1, id="case23"),
        pytest.param(14, 0, 0, id="case24"),
        pytest.param(14, 0, 1, id="case25"),
        pytest.param(8, 0, 0, id="case26"),
        pytest.param(8, 0, 1, id="case27"),
        pytest.param(9, 0, 0, id="case28"),
        pytest.param(9, 0, 1, id="case29"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_address_warm_after_fail(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Invokes failing CREATE (because initcode fails) and checks."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=999,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    # Source: Yul
    # {
    #     code {
    #       let failType := calldataload(4)
    #       let initcode_size
    #
    #       // The return values of various actions. Done twice to see if there is a difference  # noqa: E501
    #       let create_1 := 0
    #       let call_created_1 := 2
    #       let call_created_2 := 3
    #       let call_empty_1 := 4
    #       let call_empty_2 := 5
    #
    #       // The costs of those operations
    #       let create_1_cost := 10
    #       let call_created_1_cost := 12
    #       let call_created_2_cost := 13
    #       let call_empty_1_cost := 14
    #       let call_empty_2_cost := 15
    #
    #       // Make the storage cells we use here are warm
    #       sstore(create_1, 0xdead60A7)
    #       sstore(call_created_1, 0xdead60A7)
    #       sstore(call_created_2, 0xdead60A7)
    #       sstore(call_empty_1, 0xdead60A7)
    #       sstore(call_empty_2, 0xdead60A7)
    #       sstore(call_created_1_cost, 0xdead60A7)
    #       sstore(call_created_2_cost, 0xdead60A7)
    #       sstore(call_empty_1_cost, 0xdead60A7)
    #       sstore(call_empty_2_cost, 0xdead60A7)
    #
    # ... (172 more lines)
    contract = pre.deploy_contract(
        code=bytes.fromhex(
            "6004356000906002600390600493600593600c90600d96600e90600f9863dead60a78655"  # noqa: E501
            "63dead60a7875563dead60a7885563dead60a7825563dead60a7895563dead60a7855563"  # noqa: E501
            "dead60a7815563dead60a7835563dead60a78a5573d4e7ae083132925a4927c1f5816238"  # noqa: E501
            "ba17b82a00938060001461044c5780600a1461040e57806001146103dc5780600b146103"  # noqa: E501
            "a357806002146103715780600c1461033257806003146102f757806004146102bb578060"  # noqa: E501
            "051461027f5780600d146102435780600e1461020657806006146101d457806010146101"  # noqa: E501
            "9b5780600714610169576011146100ed57600080fd5b60009788808080809b9a819b9a82"  # noqa: E501
            "9b73f7fef4b66b1570a057d7d5cec5c58846befa5b5c92615a1760058061049488398680"  # noqa: E501
            "f590555b5a825583808080348782f190555a81540390555a8755349082f190555a815403"  # noqa: E501
            "90555a825583808080348782f190555a81540390555a8755349082f190555a8154039055"  # noqa: E501
            "005b5060009788808080809b9a819b9a829b600080516020610499833981519152926005"  # noqa: E501
            "8061049487398580f09055610123565b5060009788808080809b9a819b9a829b73562d97"  # noqa: E501
            "e3e4d6d3c6e791ea64bb73d820871aa2199284600a8061048a83398180f5905561012356"  # noqa: E501
            "5b5060009788808080809b9a819b9a829b60008051602061049983398151915292600a80"  # noqa: E501
            "61048a87398580f09055610123565b5060009788808080809b9a819b9a829b73d70df326"  # noqa: E501
            "038a3c7ca8fac785a99162bfe75ccc469284808080806420c0de100662010000f1905561"  # noqa: E501
            "0123565b5060009788808080809b9a819b9a829b73d70df326038a3c7ca8fac785a99162"  # noqa: E501
            "bfe75ccc469284808080806420c0de1006617000f19055610123565b5060009788808080"  # noqa: E501
            "809b9a819b9a829b73b2050fc27ab6d6d42dc0ce6f7c0bf9481a4c3fc392848080808063"  # noqa: E501
            "c0deffff62010000f19055610123565b5060009788808080809b9a819b9a829b73a5a6a9"  # noqa: E501
            "5fd9554f15ab6986a57519092be209512592848080808063c0de100662010000f1905561"  # noqa: E501
            "0123565b5060009788808080809b9a819b9a829b73a5a6a95fd9554f15ab6986a5751909"  # noqa: E501
            "2be209512592848080808063c0de1006617000f19055610123565b506000978880808080"  # noqa: E501
            "9b9a819b9a829b73a13d43586820e5d97a3fd1960625d537c86dc4e79284600665fe6010"  # noqa: E501
            "6000f360d01b82528180f59055610123565b5060009788808080809b9a819b9a829b6000"  # noqa: E501
            "805160206104998339815191529260018061048987398580f09055610123565b50600097"  # noqa: E501
            "88808080809b9a819b9a829b73014001fdbede82315f4b8c2a7d45e980a8a4a12e928460"  # noqa: E501
            "068061048383398180f59055610123565b5060009788808080809b9a819b9a829b600080"  # noqa: E501
            "5160206104998339815191529260068061048387398580f09055610123565b5060009788"  # noqa: E501
            "808080809b9a819b9a829b7343255ee039968e0254887fc8c7172736983d878c92846005"  # noqa: E501
            "6460006000fd60d81b82528180f59055610123565b5060009788808080809b9a819b9a82"  # noqa: E501
            "9b6000805160206104998339815191529260048061047f87398580f0905561012356fe60"  # noqa: E501
            "0080fd6160016000f3fe60ef60005360106000f360016000f30000000000000000000000"  # noqa: E501
            "00d4e7ae083132925a4927c1f5816238ba17b82a65"
        ),
        balance=4096,
        nonce=0,
        address=Address("0x00000000000000000000000000000000000c0dec"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     code {
    #       datacopy(0, dataoffset("dummy"), datasize("dummy"))
    #       sstore(0, create(0, 0, datasize("dummy")))
    #       stop()
    #     }
    #     object "dummy" {
    #       code {
    #         return(0,0x6000)
    #     }
    #   }
    #  }
    pre.deploy_contract(
        code=(
            Op.CODECOPY(dest_offset=0x0, offset=0x12, size=0x6)
            + Op.SSTORE(
                key=0x0,
                value=Op.CREATE(value=Op.DUP1, offset=0x0, size=0x6),
            )
            + Op.STOP
            + Op.INVALID
            + Op.RETURN(offset=0x0, size=0x6000)
        ),
        balance=4096,
        address=Address("0x00000000000000000000000000000000c0de1006"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     code {
    #       datacopy(0, dataoffset("dummy"), datasize("dummy"))
    #       sstore(0, create(0, 0, datasize("dummy")))
    #       stop()
    #     }
    #     object "dummy" {
    #       code {
    #         return(0,0x20)
    #     }
    #   }
    #  }
    pre.deploy_contract(
        code=(
            Op.CODECOPY(dest_offset=0x0, offset=0x12, size=0x5)
            + Op.SSTORE(
                key=0x0,
                value=Op.CREATE(value=Op.DUP1, offset=0x0, size=0x5),
            )
            + Op.STOP
            + Op.INVALID
            + Op.RETURN(offset=0x0, size=0x20)
        ),
        balance=4096,
        nonce=18446744073709551615,
        address=Address("0x00000000000000000000000000000000c0deffff"),  # noqa: E501
    )
    # Source: Yul
    # {
    #     code {
    #       datacopy(0, dataoffset("dummy"), datasize("dummy"))
    #       sstore(0, create2(0, 0, datasize("dummy"), 0))
    #       stop()
    #     }
    #     object "dummy" {
    #       code {
    #         return(0,0x6000)
    #     }
    #   }
    #  }
    pre.deploy_contract(
        code=(
            Op.CODECOPY(dest_offset=0x0, offset=0x13, size=0x6)
            + Op.SSTORE(
                key=0x0,
                value=Op.CREATE2(
                    value=Op.DUP1,
                    offset=Op.DUP2,
                    size=0x6,
                    salt=0x0,
                ),
            )
            + Op.STOP
            + Op.INVALID
            + Op.RETURN(offset=0x0, size=0x6000)
        ),
        balance=4096,
        address=Address("0x00000000000000000000000000000020c0de1006"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51001)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 2, 11, 4], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 328,
                        13: 316,
                        14: 2828,
                        15: 316,
                    },
                    nonce=1,
                ),
                sender: Account(nonce=1),
                Address(
                    "0xd4e7ae083132925a4927c1f5816238ba17b82a65"
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [0, 2, 11, 4], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 32028,
                        13: 7016,
                        14: 34528,
                        15: 7016,
                    },
                    nonce=1,
                ),
                sender: Account(nonce=1),
                Address("0xd4e7ae083132925a4927c1f5816238ba17b82a00"): Account(
                    nonce=0, balance=2, code=b""
                ),
                Address("0xd4e7ae083132925a4927c1f5816238ba17b82a65"): Account(
                    nonce=0, balance=2, code=b""
                ),
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 328,
                        13: 316,
                        14: 2828,
                        15: 316,
                    },
                    nonce=1,
                ),
                sender: Account(nonce=1),
                Address(
                    "0xd4e7ae083132925a4927c1f5816238ba17b82a65"
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 32028,
                        13: 7016,
                        14: 34528,
                        15: 7016,
                    },
                    nonce=1,
                ),
                Address("0x43255ee039968e0254887fc8c7172736983d878c"): Account(
                    nonce=0, balance=2, code=b""
                ),
                sender: Account(nonce=1),
                Address("0xd4e7ae083132925a4927c1f5816238ba17b82a00"): Account(
                    nonce=0, balance=2, code=b""
                ),
            },
        },
        {
            "indexes": {"data": [12], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 328,
                        13: 316,
                        14: 2828,
                        15: 316,
                    },
                    nonce=1,
                ),
                Address(
                    "0x562d97e3e4d6d3c6e791ea64bb73d820871aa219"
                ): Account.NONEXISTENT,
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": [12], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 32028,
                        13: 7016,
                        14: 34528,
                        15: 7016,
                    },
                    nonce=1,
                ),
                Address("0x562d97e3e4d6d3c6e791ea64bb73d820871aa219"): Account(
                    nonce=0, balance=2, code=b""
                ),
                sender: Account(nonce=1),
                Address("0xd4e7ae083132925a4927c1f5816238ba17b82a00"): Account(
                    nonce=0, balance=2, code=b""
                ),
            },
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 328,
                        13: 316,
                        14: 2828,
                        15: 316,
                    },
                    nonce=1,
                ),
                Address(
                    "0x014001fdbede82315f4b8c2a7d45e980a8a4a12e"
                ): Account.NONEXISTENT,
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 32028,
                        13: 7016,
                        14: 34528,
                        15: 7016,
                    },
                    nonce=1,
                ),
                Address("0x014001fdbede82315f4b8c2a7d45e980a8a4a12e"): Account(
                    nonce=0, balance=2, code=b""
                ),
                sender: Account(nonce=1),
                Address("0xd4e7ae083132925a4927c1f5816238ba17b82a00"): Account(
                    nonce=0, balance=2, code=b""
                ),
            },
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 328,
                        13: 316,
                        14: 2828,
                        15: 316,
                    },
                    nonce=1,
                ),
                Address(
                    "0xa13d43586820e5d97a3fd1960625d537c86dc4e7"
                ): Account.NONEXISTENT,
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 32028,
                        13: 7016,
                        14: 34528,
                        15: 7016,
                    },
                    nonce=1,
                ),
                Address("0xa13d43586820e5d97a3fd1960625d537c86dc4e7"): Account(
                    nonce=0, balance=2, code=b""
                ),
                sender: Account(nonce=1),
                Address("0xd4e7ae083132925a4927c1f5816238ba17b82a00"): Account(
                    nonce=0, balance=2, code=b""
                ),
            },
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 1,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 2828,
                        13: 316,
                        14: 2828,
                        15: 316,
                    },
                    nonce=0,
                ),
                sender: Account(nonce=1),
                Address(
                    "0xb2050fc27ab6d6d42dc0ce6f7c0bf9481a4c3fc3"
                ): Account.NONEXISTENT,
                Address(
                    "0xd4e7ae083132925a4927c1f5816238ba17b82a00"
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 1,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 34528,
                        13: 7016,
                        14: 34528,
                        15: 7016,
                    },
                    nonce=0,
                ),
                sender: Account(nonce=1),
                Address("0xb2050fc27ab6d6d42dc0ce6f7c0bf9481a4c3fc3"): Account(
                    nonce=0, balance=2, code=b""
                ),
                Address("0xd4e7ae083132925a4927c1f5816238ba17b82a00"): Account(
                    nonce=0, balance=2, code=b""
                ),
            },
        },
        {
            "indexes": {"data": [8, 9, 6, 7], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 2828,
                        13: 316,
                        14: 2828,
                        15: 316,
                    },
                    nonce=0,
                ),
                sender: Account(nonce=1),
                Address(
                    "0xd4e7ae083132925a4927c1f5816238ba17b82a65"
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [8, 9, 6, 7], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 34528,
                        13: 7016,
                        14: 34528,
                        15: 7016,
                    },
                    nonce=0,
                ),
                sender: Account(nonce=1),
                Address("0xd4e7ae083132925a4927c1f5816238ba17b82a00"): Account(
                    nonce=0, balance=2, code=b""
                ),
            },
        },
        {
            "indexes": {"data": [13], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0xD4E7AE083132925A4927C1F5816238BA17B82A65,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 328,
                        13: 316,
                        14: 2828,
                        15: 316,
                    },
                    nonce=1,
                ),
                sender: Account(nonce=1),
                Address("0xd4e7ae083132925a4927c1f5816238ba17b82a65"): Account(
                    code=bytes.fromhex("00")
                ),
            },
        },
        {
            "indexes": {"data": [13], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0xD4E7AE083132925A4927C1F5816238BA17B82A65,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 7028,
                        13: 7016,
                        14: 34528,
                        15: 7016,
                    },
                    nonce=1,
                ),
                sender: Account(nonce=1),
                Address("0xd4e7ae083132925a4927c1f5816238ba17b82a00"): Account(
                    nonce=0, balance=2, code=b""
                ),
                Address("0xd4e7ae083132925a4927c1f5816238ba17b82a65"): Account(
                    nonce=1, balance=2, code=bytes.fromhex("00")
                ),
            },
        },
        {
            "indexes": {"data": [14], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0xF7FEF4B66B1570A057D7D5CEC5C58846BEFA5B5C,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 328,
                        13: 316,
                        14: 2828,
                        15: 316,
                    },
                    nonce=1,
                ),
                sender: Account(nonce=1),
                Address("0xf7fef4b66b1570a057d7d5cec5c58846befa5b5c"): Account(
                    nonce=1, code=bytes.fromhex("00")
                ),
            },
        },
        {
            "indexes": {"data": [14], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0xF7FEF4B66B1570A057D7D5CEC5C58846BEFA5B5C,
                        2: 1,
                        3: 1,
                        4: 1,
                        5: 1,
                        12: 7028,
                        13: 7016,
                        14: 34528,
                        15: 7016,
                    },
                    nonce=1,
                ),
                sender: Account(nonce=1),
                Address("0xd4e7ae083132925a4927c1f5816238ba17b82a00"): Account(
                    nonce=0, balance=2, code=b""
                ),
                Address("0xf7fef4b66b1570a057d7d5cec5c58846befa5b5c"): Account(
                    nonce=1, balance=2, code=bytes.fromhex("00")
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
