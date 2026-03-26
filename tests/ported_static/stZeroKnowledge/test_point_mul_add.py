"""
test_point_mul_add

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
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd216da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd216da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd216da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba0000000000000000000000000000000000000000000000000000000000000002",
    "1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2860217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d40f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd216da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd216da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba0000000000000000000000000000000000000000000000000000000000000003",
    "1f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c492eddcb59a6517e86bfbe35c9691479fffc6e0580000ca2706c983ff7afcb1db81f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c49018683193ae021a2f8920fed186cde5d9b1365116865281ccf884c1f28b1df8f1f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c49018683193ae021a2f8920fed186cde5d9b1365116865281ccf884c1f28b1df8f0000000000000000000000000000000000000000000000000000000000000000",
    "1f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c492eddcb59a6517e86bfbe35c9691479fffc6e0580000ca2706c983ff7afcb1db81f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c492eddcb59a6517e86bfbe35c9691479fffc6e0580000ca2706c983ff7afcb1db81f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c492eddcb59a6517e86bfbe35c9691479fffc6e0580000ca2706c983ff7afcb1db80000000000000000000000000000000000000000000000000000000000000002",
    "1f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c492eddcb59a6517e86bfbe35c9691479fffc6e0580000ca2706c983ff7afcb1db8000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c49018683193ae021a2f8920fed186cde5d9b1365116865281ccf884c1f28b1df8f30644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000",
    "1f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c492eddcb59a6517e86bfbe35c9691479fffc6e0580000ca2706c983ff7afcb1db81f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c492eddcb59a6517e86bfbe35c9691479fffc6e0580000ca2706c983ff7afcb1db81f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c49018683193ae021a2f8920fed186cde5d9b1365116865281ccf884c1f28b1df8f30644e72e131a029b85045b68181585d2833e84879b9709143e1f593efffffff",
    "1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2860217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d4000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2860217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d40000000000000000000000000000000000000000000000000000000000000001",
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000230644e72e131a029b85045b68181585d2833e84879b9709143e1f593f0000000",
    "00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000130644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd45000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000000",
]
TX_GAS = [2000000, 90000, 110000, 192000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stZeroKnowledge/pointMulAddFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="d0-g0",
        ),
        pytest.param(
            0, 1, 0,
            id="d0-g1",
        ),
        pytest.param(
            0, 2, 0,
            id="d0-g2",
        ),
        pytest.param(
            0, 3, 0,
            id="d0-g3",
        ),
        pytest.param(
            1, 0, 0,
            id="d1-g0",
        ),
        pytest.param(
            1, 1, 0,
            id="d1-g1",
        ),
        pytest.param(
            1, 2, 0,
            id="d1-g2",
        ),
        pytest.param(
            1, 3, 0,
            id="d1-g3",
        ),
        pytest.param(
            2, 0, 0,
            id="d2-g0",
        ),
        pytest.param(
            2, 1, 0,
            id="d2-g1",
        ),
        pytest.param(
            2, 2, 0,
            id="d2-g2",
        ),
        pytest.param(
            2, 3, 0,
            id="d2-g3",
        ),
        pytest.param(
            3, 0, 0,
            id="d3-g0",
        ),
        pytest.param(
            3, 1, 0,
            id="d3-g1",
        ),
        pytest.param(
            3, 2, 0,
            id="d3-g2",
        ),
        pytest.param(
            3, 3, 0,
            id="d3-g3",
        ),
        pytest.param(
            4, 0, 0,
            id="d4-g0",
        ),
        pytest.param(
            4, 1, 0,
            id="d4-g1",
        ),
        pytest.param(
            4, 2, 0,
            id="d4-g2",
        ),
        pytest.param(
            4, 3, 0,
            id="d4-g3",
        ),
        pytest.param(
            5, 0, 0,
            id="d5-g0",
        ),
        pytest.param(
            5, 1, 0,
            id="d5-g1",
        ),
        pytest.param(
            5, 2, 0,
            id="d5-g2",
        ),
        pytest.param(
            5, 3, 0,
            id="d5-g3",
        ),
        pytest.param(
            6, 0, 0,
            id="d6-g0",
        ),
        pytest.param(
            6, 1, 0,
            id="d6-g1",
        ),
        pytest.param(
            6, 2, 0,
            id="d6-g2",
        ),
        pytest.param(
            6, 3, 0,
            id="d6-g3",
        ),
        pytest.param(
            7, 0, 0,
            id="d7-g0",
        ),
        pytest.param(
            7, 1, 0,
            id="d7-g1",
        ),
        pytest.param(
            7, 2, 0,
            id="d7-g2",
        ),
        pytest.param(
            7, 3, 0,
            id="d7-g3",
        ),
        pytest.param(
            8, 0, 0,
            id="d8-g0",
        ),
        pytest.param(
            8, 1, 0,
            id="d8-g1",
        ),
        pytest.param(
            8, 2, 0,
            id="d8-g2",
        ),
        pytest.param(
            8, 3, 0,
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
    """test_point_mul_add"""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    contract_0 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=4012015,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)
    # Source: lll
    # {(MSTORE 0 (CALLDATALOAD 0)) (MSTORE 32 (CALLDATALOAD 32)) (MSTORE 64 (CALLDATALOAD 64)) (MSTORE 96 (CALLDATALOAD 96))  (MSTORE 128 (CALLDATALOAD 128)) (MSTORE 160 (CALLDATALOAD 160)) (MSTORE 192 (CALLDATALOAD 192)) [[0]](CALLCODE 500000 6 0 0 128 300 64)  [[1]](CALLCODE 500000 7 0 128 96 400 64) [[10]] (MLOAD 300)  [[11]] (MLOAD 332) [[20]] (MLOAD 400)  [[21]] (MLOAD 432) [[2]] (EQ (SLOAD 10) (SLOAD 20)) [[3]] (EQ (SLOAD 11) (SLOAD 21))}
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x20))
        + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x40))
        + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x60))
        + Op.MSTORE(offset=0x80, value=Op.CALLDATALOAD(offset=0x80))
        + Op.MSTORE(offset=0xa0, value=Op.CALLDATALOAD(offset=0xa0))
        + Op.MSTORE(offset=0xc0, value=Op.CALLDATALOAD(offset=0xc0))
        + Op.SSTORE(key=0x0, value=Op.CALLCODE(gas=0x7a120, address=0x6, value=0x0, args_offset=0x0, args_size=0x80, ret_offset=0x12c, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0x1, value=Op.CALLCODE(gas=0x7a120, address=0x7, value=0x0, args_offset=0x80, args_size=0x60, ret_offset=0x190, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0xa, value=Op.MLOAD(offset=0x12c))
        + Op.SSTORE(key=0xb, value=Op.MLOAD(offset=0x14c))
        + Op.SSTORE(key=0x14, value=Op.MLOAD(offset=0x190))
        + Op.SSTORE(key=0x15, value=Op.MLOAD(offset=0x1b0))
        + Op.SSTORE(key=0x2, value=Op.EQ(Op.SLOAD(key=0xa), Op.SLOAD(key=0x14)))  # noqa: E501
        + Op.SSTORE(key=0x3, value=Op.EQ(Op.SLOAD(key=0xb), Op.SLOAD(key=0x15)))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0], 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(
                storage={
            0: 1,
            1: 1,
            2: 1,
            3: 1,
            10: 0x1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc286,
            11: 0x217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d4,
            20: 0x1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc286,
            21: 0x217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d4,
        },
            ),
    },
        },
        {
            "indexes": {'data': [1], 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(
                storage={
            0: 1,
            1: 1,
            2: 1,
            3: 1,
            10: 0x1f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c49,
            11: 0x18683193ae021a2f8920fed186cde5d9b1365116865281ccf884c1f28b1df8f,
            20: 0x1f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c49,
            21: 0x18683193ae021a2f8920fed186cde5d9b1365116865281ccf884c1f28b1df8f,
        },
            ),
    },
        },
        {
            "indexes": {'data': [2], 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_0: Account(storage={0: 1, 1: 1, 2: 1, 3: 1})},
        },
        {
            "indexes": {'data': [3], 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(
                storage={
            0: 1,
            1: 1,
            2: 1,
            3: 1,
            10: 0x255e468453d7636cc1563e43f7521755f95e6c56043c7321b4ae04e772945fb0,
            11: 0x225c5f1623620fd84bfbab2d861a9d1e570f7727c540f403085998ebaf407c4,
            20: 0x255e468453d7636cc1563e43f7521755f95e6c56043c7321b4ae04e772945fb0,
            21: 0x225c5f1623620fd84bfbab2d861a9d1e570f7727c540f403085998ebaf407c4,
        },
            ),
    },
        },
        {
            "indexes": {'data': [4], 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(
                storage={
            0: 1,
            1: 1,
            2: 1,
            3: 1,
            10: 0x1f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c49,
            11: 0x2eddcb59a6517e86bfbe35c9691479fffc6e0580000ca2706c983ff7afcb1db8,
            20: 0x1f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c49,
            21: 0x2eddcb59a6517e86bfbe35c9691479fffc6e0580000ca2706c983ff7afcb1db8,
        },
            ),
    },
        },
        {
            "indexes": {'data': [5], 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(
                storage={
            0: 1,
            1: 1,
            2: 1,
            3: 1,
            10: 0x255e468453d7636cc1563e43f7521755f95e6c56043c7321b4ae04e772945fb0,
            11: 0x225c5f1623620fd84bfbab2d861a9d1e570f7727c540f403085998ebaf407c4,
            20: 0x255e468453d7636cc1563e43f7521755f95e6c56043c7321b4ae04e772945fb0,
            21: 0x225c5f1623620fd84bfbab2d861a9d1e570f7727c540f403085998ebaf407c4,
        },
            ),
    },
        },
        {
            "indexes": {'data': [6], 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(
                storage={
            0: 1,
            1: 1,
            2: 1,
            3: 1,
            10: 0x1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc286,
            11: 0x217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d4,
            20: 0x1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc286,
            21: 0x217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d4,
        },
            ),
    },
        },
        {
            "indexes": {'data': [7], 'gas': [0, 3], 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(
                storage={
            0: 1,
            1: 1,
            10: 0x30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd3,
            11: 0x15ed738c0e0a7c92e7845f96b2ae9c0a68a6a449e3538fc7ff3ebf7a5a18a2c4,
            20: 1,
            21: 0x30644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd45,
        },
            ),
    },
        },
        {
            "indexes": {'data': [8], 'gas': 0, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_0: Account(storage={0: 1, 1: 1, 2: 1, 3: 1})},
        },
        {
            "indexes": {'data': -1, 'gas': [1, 2], 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_0: Account(storage={})},
        },
        {
            "indexes": {'data': [0, 1, 3, 4, 5, 6], 'gas': [3], 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_0: Account(storage={})},
        },
        {
            "indexes": {'data': [8, 2], 'gas': [3], 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_0: Account(storage={0: 1, 1: 1, 2: 1, 3: 1})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=1,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
