"""
Invokes failing CREATE (because initcode fails) and checks.

if the create address is considered warm in the follow up call as required by
EIP-2929.
Addresses taken from https://toolkit.abdk.consulting/ethereum#contract-address

Written primarily by Paweł Bylica (@chfast). Somewhat modified by Ori (@qbzzt)

Ported from:
state_tests/stCreateTest/CreateAddressWarmAfterFailFiller.yml
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
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateAddressWarmAfterFailFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="create-contructor-revert-v0",
        ),
        pytest.param(
            0,
            0,
            1,
            id="create-contructor-revert-v1",
        ),
        pytest.param(
            1,
            0,
            0,
            id="create2-contructor-revert-v0",
        ),
        pytest.param(
            1,
            0,
            1,
            id="create2-contructor-revert-v1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="create-code-too-big-v0",
        ),
        pytest.param(
            2,
            0,
            1,
            id="create-code-too-big-v1",
        ),
        pytest.param(
            3,
            0,
            0,
            id="create2-code-too-big-v0",
        ),
        pytest.param(
            3,
            0,
            1,
            id="create2-code-too-big-v1",
        ),
        pytest.param(
            4,
            0,
            0,
            id="create-invalid-opcode-v0",
        ),
        pytest.param(
            4,
            0,
            1,
            id="create-invalid-opcode-v1",
        ),
        pytest.param(
            5,
            0,
            0,
            id="create2-invalid-opcode-v0",
        ),
        pytest.param(
            5,
            0,
            1,
            id="create2-invalid-opcode-v1",
        ),
        pytest.param(
            6,
            0,
            0,
            id="create-oog-constructor-v0",
        ),
        pytest.param(
            6,
            0,
            1,
            id="create-oog-constructor-v1",
        ),
        pytest.param(
            7,
            0,
            0,
            id="create-oog-post-constr-v0",
        ),
        pytest.param(
            7,
            0,
            1,
            id="create-oog-post-constr-v1",
        ),
        pytest.param(
            8,
            0,
            0,
            id="create2-oog-constructor-v0",
        ),
        pytest.param(
            8,
            0,
            1,
            id="create2-oog-constructor-v1",
        ),
        pytest.param(
            9,
            0,
            0,
            id="create2-oog-post-constr-v0",
        ),
        pytest.param(
            9,
            0,
            1,
            id="create2-oog-post-constr-v1",
        ),
        pytest.param(
            10,
            0,
            0,
            id="create-high-nonce-v0",
        ),
        pytest.param(
            10,
            0,
            1,
            id="create-high-nonce-v1",
        ),
        pytest.param(
            11,
            0,
            0,
            id="create-0xef-v0",
        ),
        pytest.param(
            11,
            0,
            1,
            id="create-0xef-v1",
        ),
        pytest.param(
            12,
            0,
            0,
            id="create2-0xef-v0",
        ),
        pytest.param(
            12,
            0,
            1,
            id="create2-0xef-v1",
        ),
        pytest.param(
            13,
            0,
            0,
            id="create-ok-v0",
        ),
        pytest.param(
            13,
            0,
            1,
            id="create-ok-v1",
        ),
        pytest.param(
            14,
            0,
            0,
            id="create2-ok-v0",
        ),
        pytest.param(
            14,
            0,
            1,
            id="create2-ok-v1",
        ),
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
    """
    Invokes failing CREATE (because initcode fails) and checks
    if the...
    """
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x00000000000000000000000000000000000C0DEC)
    contract_1 = Address(0x00000000000000000000000000000000C0DE1006)
    contract_2 = Address(0x00000000000000000000000000000020C0DE1006)
    contract_3 = Address(0x00000000000000000000000000000000C0DEFFFF)
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

    pre[sender] = Account(balance=0xE8D4A51001)
    # Source: yul
    # london
    #   object "C" {
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
    # ... (173 more lines)
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex(
            "6004356000906002600390600493600593600c90600d96600e90600f9863dead60a7865563dead60a7875563dead60a7885563dead60a7825563dead60a7895563dead60a7855563dead60a7815563dead60a7835563dead60a78a5573d4e7ae083132925a4927c1f5816238ba17b82a00938060001461044c5780600a1461040e57806001146103dc5780600b146103a357806002146103715780600c1461033257806003146102f757806004146102bb578060051461027f5780600d146102435780600e1461020657806006146101d4578060101461019b5780600714610169576011146100ed57600080fd5b60009788808080809b9a819b9a829b73f7fef4b66b1570a057d7d5cec5c58846befa5b5c92615a1760058061049488398680f590555b5a825583808080348782f190555a81540390555a8755349082f190555a81540390555a825583808080348782f190555a81540390555a8755349082f190555a8154039055005b5060009788808080809b9a819b9a829b6000805160206104998339815191529260058061049487398580f09055610123565b5060009788808080809b9a819b9a829b73562d97e3e4d6d3c6e791ea64bb73d820871aa2199284600a8061048a83398180f59055610123565b5060009788808080809b9a819b9a829b60008051602061049983398151915292600a8061048a87398580f09055610123565b5060009788808080809b9a819b9a829b73d70df326038a3c7ca8fac785a99162bfe75ccc469284808080806420c0de100662010000f19055610123565b5060009788808080809b9a819b9a829b73d70df326038a3c7ca8fac785a99162bfe75ccc469284808080806420c0de1006617000f19055610123565b5060009788808080809b9a819b9a829b73b2050fc27ab6d6d42dc0ce6f7c0bf9481a4c3fc392848080808063c0deffff62010000f19055610123565b5060009788808080809b9a819b9a829b73a5a6a95fd9554f15ab6986a57519092be209512592848080808063c0de100662010000f19055610123565b5060009788808080809b9a819b9a829b73a5a6a95fd9554f15ab6986a57519092be209512592848080808063c0de1006617000f19055610123565b5060009788808080809b9a819b9a829b73a13d43586820e5d97a3fd1960625d537c86dc4e79284600665fe60106000f360d01b82528180f59055610123565b5060009788808080809b9a819b9a829b6000805160206104998339815191529260018061048987398580f09055610123565b5060009788808080809b9a819b9a829b73014001fdbede82315f4b8c2a7d45e980a8a4a12e928460068061048383398180f59055610123565b5060009788808080809b9a819b9a829b6000805160206104998339815191529260068061048387398580f09055610123565b5060009788808080809b9a819b9a829b7343255ee039968e0254887fc8c7172736983d878c928460056460006000fd60d81b82528180f59055610123565b5060009788808080809b9a819b9a829b6000805160206104998339815191529260048061047f87398580f0905561012356fe600080fd6160016000f3fe60ef60005360106000f360016000f3000000000000000000000000d4e7ae083132925a4927c1f5816238ba17b82a65"  # noqa: E501
        ),
        balance=4096,
        nonce=0,
        address=Address(0x00000000000000000000000000000000000C0DEC),  # noqa: E501
    )
    # Source: yul
    # berlin
    #   object "C" {
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
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.CODECOPY(dest_offset=0x0, offset=0x12, size=0x6)
        + Op.SSTORE(
            key=0x0, value=Op.CREATE(value=Op.DUP1, offset=0x0, size=0x6)
        )
        + Op.STOP
        + Op.INVALID
        + Op.RETURN(offset=0x0, size=0x6000),
        balance=4096,
        nonce=1,
        address=Address(0x00000000000000000000000000000000C0DE1006),  # noqa: E501
    )
    # Source: yul
    # berlin
    #   object "C" {
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
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.CODECOPY(dest_offset=0x0, offset=0x13, size=0x6)
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE2(
                value=Op.DUP1, offset=Op.DUP2, size=0x6, salt=0x0
            ),
        )
        + Op.STOP
        + Op.INVALID
        + Op.RETURN(offset=0x0, size=0x6000),
        balance=4096,
        nonce=1,
        address=Address(0x00000000000000000000000000000020C0DE1006),  # noqa: E501
    )
    # Source: yul
    # berlin
    #   object "C" {
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
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.CODECOPY(dest_offset=0x0, offset=0x12, size=0x5)
        + Op.SSTORE(
            key=0x0, value=Op.CREATE(value=Op.DUP1, offset=0x0, size=0x5)
        )
        + Op.STOP
        + Op.INVALID
        + Op.RETURN(offset=0x0, size=0x20),
        balance=4096,
        nonce=18446744073709551615,
        address=Address(0x00000000000000000000000000000000C0DEFFFF),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 2, 11, 4], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                compute_create_address(
                    address=contract_0, nonce=0
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [0, 2, 11, 4], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                compute_create_address(address=contract_0, nonce=0): Account(
                    code=b"", balance=2, nonce=0
                ),
                Address(0xD4E7AE083132925A4927C1F5816238BA17B82A00): Account(
                    code=b"", balance=2, nonce=0
                ),
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                compute_create_address(
                    address=contract_0, nonce=0
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                Address(0x43255EE039968E0254887FC8C7172736983D878C): Account(
                    code=b"", balance=2, nonce=0
                ),
                Address(0xD4E7AE083132925A4927C1F5816238BA17B82A00): Account(
                    code=b"", balance=2, nonce=0
                ),
            },
        },
        {
            "indexes": {"data": [12], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                    0x562D97E3E4D6D3C6E791EA64BB73D820871AA219
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [12], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                Address(0x562D97E3E4D6D3C6E791EA64BB73D820871AA219): Account(
                    code=b"", balance=2, nonce=0
                ),
                Address(0xD4E7AE083132925A4927C1F5816238BA17B82A00): Account(
                    code=b"", balance=2, nonce=0
                ),
            },
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                    0x014001FDBEDE82315F4B8C2A7D45E980A8A4A12E
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                Address(0x014001FDBEDE82315F4B8C2A7D45E980A8A4A12E): Account(
                    code=b"", balance=2, nonce=0
                ),
                Address(0xD4E7AE083132925A4927C1F5816238BA17B82A00): Account(
                    code=b"", balance=2, nonce=0
                ),
            },
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                    0xA13D43586820E5D97A3FD1960625D537C86DC4E7
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                Address(0xA13D43586820E5D97A3FD1960625D537C86DC4E7): Account(
                    code=b"", balance=2, nonce=0
                ),
                Address(0xD4E7AE083132925A4927C1F5816238BA17B82A00): Account(
                    code=b"", balance=2, nonce=0
                ),
            },
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                Address(
                    0xB2050FC27AB6D6D42DC0CE6F7C0BF9481A4C3FC3
                ): Account.NONEXISTENT,
                Address(
                    0xD4E7AE083132925A4927C1F5816238BA17B82A00
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                Address(0xD4E7AE083132925A4927C1F5816238BA17B82A00): Account(
                    code=b"", balance=2, nonce=0
                ),
                Address(0xB2050FC27AB6D6D42DC0CE6F7C0BF9481A4C3FC3): Account(
                    code=b"", balance=2, nonce=0
                ),
            },
        },
        {
            "indexes": {"data": [8, 9, 6, 7], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                compute_create_address(
                    address=contract_0, nonce=0
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [8, 9, 6, 7], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                Address(0xD4E7AE083132925A4927C1F5816238BA17B82A00): Account(
                    code=b"", balance=2, nonce=0
                ),
            },
        },
        {
            "indexes": {"data": [13], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                compute_create_address(address=contract_0, nonce=0): Account(
                    code=bytes.fromhex("00")
                ),
            },
        },
        {
            "indexes": {"data": [13], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                compute_create_address(address=contract_0, nonce=0): Account(
                    code=bytes.fromhex("00"), balance=2, nonce=1
                ),
                Address(0xD4E7AE083132925A4927C1F5816238BA17B82A00): Account(
                    code=b"", balance=2, nonce=0
                ),
            },
        },
        {
            "indexes": {"data": [14], "gas": -1, "value": [0]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                Address(0xF7FEF4B66B1570A057D7D5CEC5C58846BEFA5B5C): Account(
                    code=bytes.fromhex("00"), nonce=1
                ),
            },
        },
        {
            "indexes": {"data": [14], "gas": -1, "value": [1]},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
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
                Address(0xF7FEF4B66B1570A057D7D5CEC5C58846BEFA5B5C): Account(
                    code=bytes.fromhex("00"), balance=2, nonce=1
                ),
                Address(0xD4E7AE083132925A4927C1F5816238BA17B82A00): Account(
                    code=b"", balance=2, nonce=0
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("52c3fd24") + Hash(0x0),
        Bytes("52c3fd24") + Hash(0xA),
        Bytes("52c3fd24") + Hash(0x1),
        Bytes("52c3fd24") + Hash(0xB),
        Bytes("52c3fd24") + Hash(0x2),
        Bytes("52c3fd24") + Hash(0xC),
        Bytes("52c3fd24") + Hash(0x3),
        Bytes("52c3fd24") + Hash(0x4),
        Bytes("52c3fd24") + Hash(0xD),
        Bytes("52c3fd24") + Hash(0xE),
        Bytes("52c3fd24") + Hash(0x5),
        Bytes("52c3fd24") + Hash(0x6),
        Bytes("52c3fd24") + Hash(0x10),
        Bytes("52c3fd24") + Hash(0x7),
        Bytes("52c3fd24") + Hash(0x11),
    ]
    tx_gas = [16777216]
    tx_value = [0, 1]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
