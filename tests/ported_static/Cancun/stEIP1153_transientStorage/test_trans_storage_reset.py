"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/Cancun/stEIP1153_transientStorage
transStorageResetFiller.yml
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
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f1f100",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f1f1fd",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f1f1fe",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f100",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f1fd",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f1fe",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f100",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f1fd",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f1fe",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f400",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f4fd",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f4fe",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f200",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f2fd",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f4f2fe",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f400",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f4fd",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f4fe",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f200",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f2fd",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f2f2fe",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f10000",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f100fd",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f100fe",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f40000",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f400fd",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f400fe",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f20000",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f200fd",  # noqa: E501
    "d6c2107a0000000000000000000000009f075370ef41d4cd90151e731e33836e6f521669000000000000000000000000d1f046b080a87137c61a14bb81c2b6bbcec170840000000000000000000000000000000000000000000000000000000000f200fe",  # noqa: E501
]

TX_GAS = [16777216]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/Cancun/stEIP1153_transientStorage/transStorageResetFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(2, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(0, 0, 0, id="case2"),
        pytest.param(23, 0, 0, id="case3"),
        pytest.param(22, 0, 0, id="case4"),
        pytest.param(21, 0, 0, id="case5"),
        pytest.param(8, 0, 0, id="case6"),
        pytest.param(7, 0, 0, id="case7"),
        pytest.param(6, 0, 0, id="case8"),
        pytest.param(20, 0, 0, id="case9"),
        pytest.param(19, 0, 0, id="case10"),
        pytest.param(18, 0, 0, id="case11"),
        pytest.param(17, 0, 0, id="case12"),
        pytest.param(16, 0, 0, id="case13"),
        pytest.param(15, 0, 0, id="case14"),
        pytest.param(29, 0, 0, id="case15"),
        pytest.param(28, 0, 0, id="case16"),
        pytest.param(27, 0, 0, id="case17"),
        pytest.param(5, 0, 0, id="case18"),
        pytest.param(4, 0, 0, id="case19"),
        pytest.param(3, 0, 0, id="case20"),
        pytest.param(14, 0, 0, id="case21"),
        pytest.param(13, 0, 0, id="case22"),
        pytest.param(12, 0, 0, id="case23"),
        pytest.param(11, 0, 0, id="case24"),
        pytest.param(10, 0, 0, id="case25"),
        pytest.param(9, 0, 0, id="case26"),
        pytest.param(26, 0, 0, id="case27"),
        pytest.param(25, 0, 0, id="case28"),
        pytest.param(24, 0, 0, id="case29"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_trans_storage_reset(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x48DC5A9F099CAAAA557742CA3A990A94BE45B9969126A1BC74E5E8BE5A2B5B47
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: Yul
    # {
    #   let reverter := calldataload(4)
    #   let dead     := calldataload(36)
    #   let param := calldataload(68)
    #   sstore(0, reverter)
    #   mstore(0, reverter)
    #   mstore(32, dead)
    #   mstore(64, param)
    #   sstore(1, call(gas(), reverter, 0, 0, 96, 0, 0))
    # }
    contract = pre.deploy_contract(
        code=(
            Op.PUSH0
            + Op.DUP1
            + Op.PUSH1[0x60]
            + Op.DUP2
            + Op.DUP1
            + Op.CALLDATALOAD(offset=0x4)
            + Op.CALLDATALOAD(offset=0x24)
            + Op.CALLDATALOAD(offset=0x44)
            + Op.SWAP1
            + Op.SSTORE(key=Op.DUP5, value=Op.DUP3)
            + Op.MSTORE(offset=Op.DUP5, value=Op.DUP3)
            + Op.PUSH1[0x20]
            + Op.MSTORE
            + Op.PUSH1[0x40]
            + Op.MSTORE
            + Op.GAS
            + Op.SSTORE(key=0x1, value=Op.CALL)
            + Op.STOP
        ),
        address=Address("0x1679c7439ef325a99a6afc54a8f7894c3da35b16"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    callee = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=Op.PUSH0)
            + Op.CALLDATALOAD(offset=0x20)
            + Op.SWAP1
            + Op.PUSH0
            + Op.MSTORE
            + Op.MSTORE(offset=0x20, value=Op.DUP1)
            + Op.BYTE(0x1D, Op.CALLDATALOAD(offset=0x40))
            + Op.SWAP1
            + Op.PUSH1[0x19]
            + Op.PUSH0
            + Op.JUMP(pc=0xA8)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x39, condition=Op.ISZERO)
            + Op.PUSH2[0x60A7]
            + Op.PUSH1[0x27]
            + Op.PUSH0
            + Op.JUMP(pc=0xA8)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x2D, condition=Op.EQ)
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x37]
            + Op.PUSH2[0xBEEF]
            + Op.PUSH0
            + Op.JUMP(pc=0xAC)
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x43]
            + Op.PUSH2[0x60A7]
            + Op.PUSH0
            + Op.JUMP(pc=0xAC)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x40))
            + Op.PUSH0
            + Op.SWAP2
            + Op.DIV(Op.GAS, 0x2)
            + Op.SWAP1
            + Op.JUMPI(pc=0x96, condition=Op.EQ(0xF1, Op.DUP1))
            + Op.JUMPI(pc=0x84, condition=Op.EQ(0xF2, Op.DUP1))
            + Op.PUSH1[0xF4]
            + Op.JUMPI(pc=0x74, condition=Op.EQ)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x1, value=Op.DUP3)
            + Op.PUSH1[0x70]
            + Op.PUSH0
            + Op.JUMP(pc=0xA8)
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.SSTORE
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.DUP1
            + Op.SWAP4
            + Op.POP
            + Op.DUP1
            + Op.SWAP3
            + Op.PUSH1[0x60]
            + Op.SWAP3
            + Op.DELEGATECALL
            + Op.PUSH0
            + Op.DUP1
            + Op.JUMP(pc=0x65)
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH0
            + Op.DUP1
            + Op.DUP1
            + Op.SWAP5
            + Op.POP
            + Op.DUP1
            + Op.SWAP4
            + Op.PUSH1[0x60]
            + Op.SWAP4
            + Op.CALLCODE
            + Op.PUSH0
            + Op.DUP1
            + Op.JUMP(pc=0x65)
            + Op.JUMPDEST
            + Op.POP
            + Op.PUSH0
            + Op.DUP1
            + Op.DUP1
            + Op.SWAP5
            + Op.POP
            + Op.DUP1
            + Op.SWAP4
            + Op.PUSH1[0x60]
            + Op.SWAP4
            + Op.CALL
            + Op.PUSH0
            + Op.DUP1
            + Op.JUMP(pc=0x65)
            + Op.JUMPDEST
            + Op.TLOAD
            + Op.SWAP1
            + Op.JUMP
            + Op.JUMPDEST
            + Op.TSTORE
            + Op.JUMP
        ),
        storage={0x1: 0x60A7},
        address=Address("0x9f075370ef41d4cd90151e731e33836e6f521669"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=Op.PUSH0)
            + Op.CALLDATALOAD(offset=0x20)
            + Op.MSTORE(offset=Op.PUSH0, value=Op.DUP2)
            + Op.PUSH1[0x20]
            + Op.MSTORE
            + Op.BYTE(0x1E, Op.CALLDATALOAD(offset=0x40))
            + Op.BYTE(0x1F, Op.CALLDATALOAD(offset=0x40))
            + Op.SWAP2
            + Op.PUSH2[0x7E57]
            + Op.SWAP2
            + Op.SWAP1
            + Op.JUMPI(pc=0x91, condition=Op.EQ(0xF1, Op.DUP2))
            + Op.JUMPI(pc=0x80, condition=Op.EQ(0xF2, Op.DUP2))
            + Op.JUMPI(pc=0x70, condition=Op.EQ(0xF4, Op.DUP2))
            + Op.POP
            + Op.JUMPI(pc=0x60, condition=Op.ISZERO)
            + Op.JUMPDEST
            + Op.PUSH1[0x10]
            + Op.SSTORE
            + Op.JUMPI(pc=0x5E, condition=Op.ISZERO(Op.DUP1))
            + Op.JUMPI(pc=0x5A, condition=Op.EQ(0xFD, Op.DUP1))
            + Op.JUMPI(pc=0x58, condition=Op.EQ(0xFE, Op.DUP1))
            + Op.PUSH1[0xFF]
            + Op.JUMPI(pc=0x55, condition=Op.EQ)
            + Op.STOP
            + Op.JUMPDEST
            + Op.SELFDESTRUCT(address=Op.PUSH0)
            + Op.JUMPDEST
            + Op.INVALID
            + Op.JUMPDEST
            + Op.REVERT(offset=Op.DUP1, size=Op.PUSH0)
            + Op.JUMPDEST
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x6C]
            + Op.PUSH4[0xBAD0BEEF]
            + Op.PUSH0
            + Op.JUMP(pc=0xA2)
            + Op.JUMPDEST
            + Op.JUMP(pc=0x37)
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.DUP1
            + Op.SWAP4
            + Op.POP
            + Op.DUP1
            + Op.SWAP3
            + Op.POP
            + Op.PUSH1[0x40]
            + Op.SWAP2
            + Op.GAS
            + Op.DELEGATECALL
            + Op.JUMP(pc=0x37)
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.DUP1
            + Op.DUP1
            + Op.SWAP5
            + Op.POP
            + Op.DUP1
            + Op.SWAP4
            + Op.POP
            + Op.PUSH1[0x40]
            + Op.SWAP3
            + Op.GAS
            + Op.CALLCODE
            + Op.JUMP(pc=0x37)
            + Op.JUMPDEST
            + Op.PUSH0
            + Op.DUP1
            + Op.DUP1
            + Op.SWAP5
            + Op.POP
            + Op.DUP1
            + Op.SWAP4
            + Op.POP
            + Op.PUSH1[0x40]
            + Op.SWAP3
            + Op.GAS
            + Op.CALL
            + Op.JUMP(pc=0x37)
            + Op.JUMPDEST
            + Op.TSTORE
            + Op.JUMP
        ),
        storage={0x10: 0x60A7},
        address=Address("0xd1f046b080a87137c61a14bb81c2b6bbcec17084"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 48879, 1: 1},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 1},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 23, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 22, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 21, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743, 1: 1},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 32343},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 8, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 48879, 1: 1, 16: 1},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 20, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 19, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 18, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 48879, 1: 1, 16: 1},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 17, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 16, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 15, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 48879, 1: 1, 16: 1},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 29, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 28, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 27, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 0xBAD0BEEF, 1: 1, 16: 32343},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 48879, 1: 1, 16: 1},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 14, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 13, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 12, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 48879, 1: 1, 16: 1},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 11, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 10, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 9, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 48879, 1: 1, 16: 1},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 26, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 25, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 24743},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 24, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={
                        0: 0x9F075370EF41D4CD90151E731E33836E6F521669,
                        1: 1,
                    },
                    code=bytes.fromhex(
                        "5f8060608180600435602435604435908284558284526020526040525af160015500"  # noqa: E501
                    ),
                ),
                callee: Account(
                    storage={0: 0xBAD0BEEF, 1: 1, 16: 32343},
                    code=bytes.fromhex(
                        "5f35602035905f5280602052604035601d1a9060195f60a8565b156039576160a760275f60a8565b14602d57005b603761beef5f60ac565b005b60436160a75f60ac565b6040356040525f9160025a04908060f1146096578060f21460845760f4146074575b8260015560705f60a8565b5f55005b5f8093508092606092f45f806065565b505f808094508093606093f25f806065565b505f808094508093606093f15f806065565b5c90565b5d56"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    storage={16: 24743},
                    code=bytes.fromhex(
                        "5f35602035815f52602052604035601e1a604035601f1a91617e5791908160f1146091578160f2146080578160f41460705750156060575b6010558015605e578060fd14605a578060fe1460585760ff14605557005b5fff5bfe5b5f80fd5b005b606c63bad0beef5f60a2565b6037565b5f8093508092506040915af46037565b5f808094508093506040925af26037565b5f808094508093506040925af16037565b5d56"  # noqa: E501
                    ),
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
        nonce=1,
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
