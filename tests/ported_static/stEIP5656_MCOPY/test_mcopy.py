"""
MCOPY memory copy test cases

Ported from:
state_tests/Cancun/stEIP5656_MCOPY/MCOPYFiller.yml
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
    "000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000001f000000000000000000000000000000000000000000000000000000000000001f0000000000000000000000000000000000000000000000000000000000000000",
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002",
    "00000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000001f",
    "00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001f",
    "000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000002",
    "000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002",
    "0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001f0000000000000000000000000000000000000000000000000000000000000001",
    "0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001f0000000000000000000000000000000000000000000000000000000000000021",
    "000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000021",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000020",
    "000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000001",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020",
    "000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000210000000000000000000000000000000000000000000000000000000000000001",
    "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001",
    "000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000033",
]
TX_GAS = [1000000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/Cancun/stEIP5656_MCOPY/MCOPYFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="forward_size0_0",
        ),
        pytest.param(
            1, 0, 0,
            id="forward_size0_1",
        ),
        pytest.param(
            2, 0, 0,
            id="backward_size0_0",
        ),
        pytest.param(
            3, 0, 0,
            id="backward_size0_1",
        ),
        pytest.param(
            4, 0, 0,
            id="inplace_size0_0",
        ),
        pytest.param(
            5, 0, 0,
            id="inplace_size0_1",
        ),
        pytest.param(
            6, 0, 0,
            id="forward_overlapped_0",
        ),
        pytest.param(
            7, 0, 0,
            id="forward_overlapped_1",
        ),
        pytest.param(
            8, 0, 0,
            id="forward_disjoint_0",
        ),
        pytest.param(
            9, 0, 0,
            id="forward_disjoint_1",
        ),
        pytest.param(
            10, 0, 0,
            id="forward_adjacent_0",
        ),
        pytest.param(
            11, 0, 0,
            id="forward_adjacent_1",
        ),
        pytest.param(
            12, 0, 0,
            id="backward_overlapped_0",
        ),
        pytest.param(
            13, 0, 0,
            id="backward_overlapped_1",
        ),
        pytest.param(
            14, 0, 0,
            id="backward_disjoint_0",
        ),
        pytest.param(
            15, 0, 0,
            id="backward_disjoint_1",
        ),
        pytest.param(
            16, 0, 0,
            id="backward_adjacent_0",
        ),
        pytest.param(
            17, 0, 0,
            id="backward_adjacent_1",
        ),
        pytest.param(
            18, 0, 0,
            id="inplace_0",
        ),
        pytest.param(
            19, 0, 0,
            id="inplace_1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_mcopy(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """MCOPY memory copy test cases"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xf79127a3004abde26a4cbd80c428cb10f829fa11b54d36e7b326f4f4a5927acf
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1687174231,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: yul
    # cancun {
    #   // Fill memory at [0-96] (3x32) with the pattern of unique bytes.
    #   mstore( 0, 0xa0a1a2a3a4a5a6a7a8a9aAaBaCaDaEaFb0b1b2b3b4b5b6b7b8b9bAbBbCbDbEbF)
    #   mstore(32, 0xc0c1c2c3c4c5c6c7c8c9cAcBcCcDcEcFd0d1d2d3d4d5d6d7d8d9dAdBdCdDdEdF)
    #   mstore(64, 0xe0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFf0f1f2f3f4f5f6f7f8f9fAfBfCfDfEfF)
    # 
    #   // MCOPY using parameters from CALLDATA.
    #   mcopy(calldataload(0), calldataload(32), calldataload(64))
    # 
    #   // Dump memory at [0-96] to 3 storage slots.
    #   sstore(0, mload( 0))
    #   sstore(1, mload(32))
    #   sstore(2, mload(64))
    # }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=Op.PUSH0, value=0xa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf)
        + Op.MSTORE(offset=0x20, value=0xc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf)
        + Op.MSTORE(offset=0x40, value=0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff)
        + Op.MCOPY(dest_offset=Op.CALLDATALOAD(offset=Op.PUSH0), offset=Op.CALLDATALOAD(offset=0x20), size=Op.CALLDATALOAD(offset=0x40))
        + Op.SSTORE(key=Op.PUSH0, value=Op.MLOAD(offset=Op.PUSH0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x40)) + Op.STOP,
        nonce=1,
        address=Address("0xbfd584ec9dc8fbadcea812c707e1765b4df8fa6c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3b9aca00)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0, 1, 2, 3, 4, 5, 18, 19], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0xa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf,
            1: 0xc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf,
            2: 0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff,
        },
            ),
    },
        },
        {
            "indexes": {'data': [6], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0xa0a0a1a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf,
            1: 0xc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf,
            2: 0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff,
        },
            ),
    },
        },
        {
            "indexes": {'data': [7], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0xa0a1a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbe,
            1: 0xbfc1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf,
            2: 0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff,
        },
            ),
    },
        },
        {
            "indexes": {'data': [8], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0xa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf,
            1: 0xa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbedf,
            2: 0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff,
        },
            ),
    },
        },
        {
            "indexes": {'data': [9], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0xa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf,
            1: 0xa1a2c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf,
            2: 0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff,
        },
            ),
    },
        },
        {
            "indexes": {'data': [10], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0xa0a1a0a1a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf,
            1: 0xc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf,
            2: 0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff,
        },
            ),
    },
        },
        {
            "indexes": {'data': [11], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0xa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf,
            1: 0xbfc1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf,
            2: 0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff,
        },
            ),
    },
        },
        {
            "indexes": {'data': [12], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0xbfc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcddde,
            1: 0xdfc1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf,
            2: 0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff,
        },
            ),
    },
        },
        {
            "indexes": {'data': [13], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0xa0a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebfc0,
            1: 0xc1c2c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf,
            2: 0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff,
        },
            ),
    },
        },
        {
            "indexes": {'data': [14], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0xc1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedfe0,
            1: 0xc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf,
            2: 0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff,
        },
            ),
    },
        },
        {
            "indexes": {'data': [15], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0xa0a1c1a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf,
            1: 0xc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf,
            2: 0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff,
        },
            ),
    },
        },
        {
            "indexes": {'data': [16], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0xc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf,
            1: 0xc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf,
            2: 0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff,
        },
            ),
    },
        },
        {
            "indexes": {'data': [17], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        target: Account(
                storage={
            0: 0xa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebf,
            1: 0xc1c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d9dadbdcdddedf,
            2: 0xe0e1e2e3e4e5e6e7e8e9eaebecedeeeff0f1f2f3f4f5f6f7f8f9fafbfcfdfeff,
        },
            ),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
