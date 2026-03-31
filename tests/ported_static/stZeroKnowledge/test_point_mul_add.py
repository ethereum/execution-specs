"""
Test_point_mul_add.

Ported from:
state_tests/stZeroKnowledge/pointMulAddFiller.json
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
    ["state_tests/stZeroKnowledge/pointMulAddFiller.json"],
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
            0,
            2,
            0,
            id="d0-g2",
        ),
        pytest.param(
            0,
            3,
            0,
            id="d0-g3",
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
            1,
            2,
            0,
            id="d1-g2",
        ),
        pytest.param(
            1,
            3,
            0,
            id="d1-g3",
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
            2,
            2,
            0,
            id="d2-g2",
        ),
        pytest.param(
            2,
            3,
            0,
            id="d2-g3",
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
            3,
            2,
            0,
            id="d3-g2",
        ),
        pytest.param(
            3,
            3,
            0,
            id="d3-g3",
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
            4,
            2,
            0,
            id="d4-g2",
        ),
        pytest.param(
            4,
            3,
            0,
            id="d4-g3",
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
        pytest.param(
            5,
            2,
            0,
            id="d5-g2",
        ),
        pytest.param(
            5,
            3,
            0,
            id="d5-g3",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6-g0",
        ),
        pytest.param(
            6,
            1,
            0,
            id="d6-g1",
        ),
        pytest.param(
            6,
            2,
            0,
            id="d6-g2",
        ),
        pytest.param(
            6,
            3,
            0,
            id="d6-g3",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7-g0",
        ),
        pytest.param(
            7,
            1,
            0,
            id="d7-g1",
        ),
        pytest.param(
            7,
            2,
            0,
            id="d7-g2",
        ),
        pytest.param(
            7,
            3,
            0,
            id="d7-g3",
        ),
        pytest.param(
            8,
            0,
            0,
            id="d8-g0",
        ),
        pytest.param(
            8,
            1,
            0,
            id="d8-g1",
        ),
        pytest.param(
            8,
            2,
            0,
            id="d8-g2",
        ),
        pytest.param(
            8,
            3,
            0,
            id="d8-g3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_point_mul_add(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_point_mul_add."""
    coinbase = Address(0x68795C4AA09D6F4ED3E5DEDDF8C2AD3049A601DA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4012015,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)
    # Source: lll
    # {(MSTORE 0 (CALLDATALOAD 0)) (MSTORE 32 (CALLDATALOAD 32)) (MSTORE 64 (CALLDATALOAD 64)) (MSTORE 96 (CALLDATALOAD 96))  (MSTORE 128 (CALLDATALOAD 128)) (MSTORE 160 (CALLDATALOAD 160)) (MSTORE 192 (CALLDATALOAD 192)) [[0]](CALLCODE 500000 6 0 0 128 300 64)  [[1]](CALLCODE 500000 7 0 128 96 400 64) [[10]] (MLOAD 300)  [[11]] (MLOAD 332) [[20]] (MLOAD 400)  [[21]] (MLOAD 432) [[2]] (EQ (SLOAD 10) (SLOAD 20)) [[3]] (EQ (SLOAD 11) (SLOAD 21))}  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x20))
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x40))
        + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x60))
        + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x80))
        + Op.MSTORE(offset=0xA0, value=Op.CALLDATALOAD(offset=0xA0))
        + Op.MSTORE(offset=0xC0, value=Op.CALLDATALOAD(offset=0xC0))
        + Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x7A120,
                address=0x6,
                value=0x0,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x12C,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=0x7A120,
                address=0x7,
                value=0x0,
                args_offset=0x80,
                args_size=0x60,
                ret_offset=0x190,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0xA, value=Op.MLOAD(offset=0x12C))
        + Op.SSTORE(key=0xB, value=Op.MLOAD(offset=0x14C))
        + Op.SSTORE(key=0x14, value=Op.MLOAD(offset=0x190))
        + Op.SSTORE(key=0x15, value=Op.MLOAD(offset=0x1B0))
        + Op.SSTORE(
            key=0x2, value=Op.EQ(Op.SLOAD(key=0xA), Op.SLOAD(key=0x14))
        )
        + Op.SSTORE(
            key=0x3, value=Op.EQ(Op.SLOAD(key=0xB), Op.SLOAD(key=0x15))
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
                        11: 0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
                        20: 0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
                        21: 0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [1], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
                        11: 0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,  # noqa: E501
                        20: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
                        21: 0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [2], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 1, 1: 1, 2: 1, 3: 1})},
        },
        {
            "indexes": {"data": [3], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x255E468453D7636CC1563E43F7521755F95E6C56043C7321B4AE04E772945FB0,  # noqa: E501
                        11: 0x225C5F1623620FD84BFBAB2D861A9D1E570F7727C540F403085998EBAF407C4,  # noqa: E501
                        20: 0x255E468453D7636CC1563E43F7521755F95E6C56043C7321B4AE04E772945FB0,  # noqa: E501
                        21: 0x225C5F1623620FD84BFBAB2D861A9D1E570F7727C540F403085998EBAF407C4,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [4], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
                        11: 0x2EDDCB59A6517E86BFBE35C9691479FFFC6E0580000CA2706C983FF7AFCB1DB8,  # noqa: E501
                        20: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
                        21: 0x2EDDCB59A6517E86BFBE35C9691479FFFC6E0580000CA2706C983FF7AFCB1DB8,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [5], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x255E468453D7636CC1563E43F7521755F95E6C56043C7321B4AE04E772945FB0,  # noqa: E501
                        11: 0x225C5F1623620FD84BFBAB2D861A9D1E570F7727C540F403085998EBAF407C4,  # noqa: E501
                        20: 0x255E468453D7636CC1563E43F7521755F95E6C56043C7321B4AE04E772945FB0,  # noqa: E501
                        21: 0x225C5F1623620FD84BFBAB2D861A9D1E570F7727C540F403085998EBAF407C4,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [6], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
                        11: 0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
                        20: 0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
                        21: 0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [7], "gas": [0, 3], "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 1,
                        1: 1,
                        10: 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD3,  # noqa: E501
                        11: 0x15ED738C0E0A7C92E7845F96B2AE9C0A68A6A449E3538FC7FF3EBF7A5A18A2C4,  # noqa: E501
                        20: 1,
                        21: 0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [8], "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 1, 1: 1, 2: 1, 3: 1})},
        },
        {
            "indexes": {"data": -1, "gas": [1, 2], "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={})},
        },
        {
            "indexes": {"data": [0, 1, 3, 4, 5, 6], "gas": [3], "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={})},
        },
        {
            "indexes": {"data": [8, 2], "gas": [3], "value": -1},
            "network": [">=Cancun"],
            "result": {contract_0: Account(storage={0: 1, 1: 1, 2: 1, 3: 1})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(0xF25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2)
        + Hash(
            0x16DA2F5CB6BE7A0AA72C440C53C9BBDFEC6C36C7D515536431B3A865468ACBBA
        )
        + Hash(
            0xF25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2
        )
        + Hash(
            0x16DA2F5CB6BE7A0AA72C440C53C9BBDFEC6C36C7D515536431B3A865468ACBBA
        )
        + Hash(
            0xF25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2
        )
        + Hash(
            0x16DA2F5CB6BE7A0AA72C440C53C9BBDFEC6C36C7D515536431B3A865468ACBBA
        )
        + Hash(0x2),
        Hash(
            0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286
        )
        + Hash(
            0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4
        )
        + Hash(
            0xF25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2
        )
        + Hash(
            0x16DA2F5CB6BE7A0AA72C440C53C9BBDFEC6C36C7D515536431B3A865468ACBBA
        )
        + Hash(
            0xF25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2
        )
        + Hash(
            0x16DA2F5CB6BE7A0AA72C440C53C9BBDFEC6C36C7D515536431B3A865468ACBBA
        )
        + Hash(0x3),
        Hash(
            0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49
        )
        + Hash(
            0x2EDDCB59A6517E86BFBE35C9691479FFFC6E0580000CA2706C983FF7AFCB1DB8
        )
        + Hash(
            0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49
        )
        + Hash(
            0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F
        )
        + Hash(
            0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49
        )
        + Hash(
            0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F
        )
        + Hash(0x0),
        Hash(
            0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49
        )
        + Hash(
            0x2EDDCB59A6517E86BFBE35C9691479FFFC6E0580000CA2706C983FF7AFCB1DB8
        )
        + Hash(
            0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49
        )
        + Hash(
            0x2EDDCB59A6517E86BFBE35C9691479FFFC6E0580000CA2706C983FF7AFCB1DB8
        )
        + Hash(
            0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49
        )
        + Hash(
            0x2EDDCB59A6517E86BFBE35C9691479FFFC6E0580000CA2706C983FF7AFCB1DB8
        )
        + Hash(0x2),
        Hash(
            0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49
        )
        + Hash(
            0x2EDDCB59A6517E86BFBE35C9691479FFFC6E0580000CA2706C983FF7AFCB1DB8
        )
        + Hash(0x0)
        + Hash(0x0)
        + Hash(
            0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49
        )
        + Hash(
            0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F
        )
        + Hash(
            0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593F0000000
        ),
        Hash(
            0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49
        )
        + Hash(
            0x2EDDCB59A6517E86BFBE35C9691479FFFC6E0580000CA2706C983FF7AFCB1DB8
        )
        + Hash(
            0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49
        )
        + Hash(
            0x2EDDCB59A6517E86BFBE35C9691479FFFC6E0580000CA2706C983FF7AFCB1DB8
        )
        + Hash(
            0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49
        )
        + Hash(
            0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F
        )
        + Hash(
            0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593EFFFFFFF
        ),
        Hash(
            0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286
        )
        + Hash(
            0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4
        )
        + Hash(0x0)
        + Hash(0x0)
        + Hash(
            0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286
        )
        + Hash(
            0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4
        )
        + Hash(0x1),
        Hash(0x1)
        + Hash(0x2)
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x1)
        + Hash(0x2)
        + Hash(
            0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593F0000000
        ),
        Hash(0x1)
        + Hash(0x2)
        + Hash(0x1)
        + Hash(
            0x30644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD45
        )
        + Hash(0x1)
        + Hash(0x2)
        + Hash(0x0),
    ]
    tx_gas = [2000000, 90000, 110000, 192000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
