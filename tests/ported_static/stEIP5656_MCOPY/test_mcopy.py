"""
MCOPY memory copy test cases.

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
    ["state_tests/Cancun/stEIP5656_MCOPY/MCOPYFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="forward_size0_0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="forward_size0_1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="backward_size0_0",
        ),
        pytest.param(
            3,
            0,
            0,
            id="backward_size0_1",
        ),
        pytest.param(
            4,
            0,
            0,
            id="inplace_size0_0",
        ),
        pytest.param(
            5,
            0,
            0,
            id="inplace_size0_1",
        ),
        pytest.param(
            6,
            0,
            0,
            id="forward_overlapped_0",
        ),
        pytest.param(
            7,
            0,
            0,
            id="forward_overlapped_1",
        ),
        pytest.param(
            8,
            0,
            0,
            id="forward_disjoint_0",
        ),
        pytest.param(
            9,
            0,
            0,
            id="forward_disjoint_1",
        ),
        pytest.param(
            10,
            0,
            0,
            id="forward_adjacent_0",
        ),
        pytest.param(
            11,
            0,
            0,
            id="forward_adjacent_1",
        ),
        pytest.param(
            12,
            0,
            0,
            id="backward_overlapped_0",
        ),
        pytest.param(
            13,
            0,
            0,
            id="backward_overlapped_1",
        ),
        pytest.param(
            14,
            0,
            0,
            id="backward_disjoint_0",
        ),
        pytest.param(
            15,
            0,
            0,
            id="backward_disjoint_1",
        ),
        pytest.param(
            16,
            0,
            0,
            id="backward_adjacent_0",
        ),
        pytest.param(
            17,
            0,
            0,
            id="backward_adjacent_1",
        ),
        pytest.param(
            18,
            0,
            0,
            id="inplace_0",
        ),
        pytest.param(
            19,
            0,
            0,
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
    """MCOPY memory copy test cases."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1687174231,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: yul
    # cancun {
    #   // Fill memory at [0-96] (3x32) with the pattern of unique bytes.
    #   mstore( 0, 0xa0a1a2a3a4a5a6a7a8a9aAaBaCaDaEaFb0b1b2b3b4b5b6b7b8b9bAbBbCbDbEbF)  # noqa: E501
    #   mstore(32, 0xc0c1c2c3c4c5c6c7c8c9cAcBcCcDcEcFd0d1d2d3d4d5d6d7d8d9dAdBdCdDdEdF)  # noqa: E501
    #   mstore(64, 0xe0e1e2e3e4e5e6e7e8e9eAeBeCeDeEeFf0f1f2f3f4f5f6f7f8f9fAfBfCfDfEfF)  # noqa: E501
    #
    #   // MCOPY using parameters from CALLDATA.
    #   mcopy(calldataload(0), calldataload(32), calldataload(64))
    #
    #   // Dump memory at [0-96] to 3 storage slots.
    #   sstore(0, mload( 0))
    #   sstore(1, mload(32))
    #   sstore(2, mload(64))
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=Op.PUSH0,
            value=0xA0A1A2A3A4A5A6A7A8A9AAABACADAEAFB0B1B2B3B4B5B6B7B8B9BABBBCBDBEBF,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0xC0C1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x40,
            value=0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
        )
        + Op.MCOPY(
            dest_offset=Op.CALLDATALOAD(offset=Op.PUSH0),
            offset=Op.CALLDATALOAD(offset=0x20),
            size=Op.CALLDATALOAD(offset=0x40),
        )
        + Op.SSTORE(key=Op.PUSH0, value=Op.MLOAD(offset=Op.PUSH0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x40))
        + Op.STOP,
        nonce=1,
        address=Address(0xBFD584EC9DC8FBADCEA812C707E1765B4DF8FA6C),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)

    expect_entries_: list[dict] = [
        {
            "indexes": {
                "data": [0, 1, 2, 3, 4, 5, 18, 19],
                "gas": -1,
                "value": -1,
            },
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xA0A1A2A3A4A5A6A7A8A9AAABACADAEAFB0B1B2B3B4B5B6B7B8B9BABBBCBDBEBF,  # noqa: E501
                        1: 0xC0C1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
                        2: 0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [6], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xA0A0A1A3A4A5A6A7A8A9AAABACADAEAFB0B1B2B3B4B5B6B7B8B9BABBBCBDBEBF,  # noqa: E501
                        1: 0xC0C1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
                        2: 0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [7], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xA0A1A1A2A3A4A5A6A7A8A9AAABACADAEAFB0B1B2B3B4B5B6B7B8B9BABBBCBDBE,  # noqa: E501
                        1: 0xBFC1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
                        2: 0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [8], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xA0A1A2A3A4A5A6A7A8A9AAABACADAEAFB0B1B2B3B4B5B6B7B8B9BABBBCBDBEBF,  # noqa: E501
                        1: 0xA0A1A2A3A4A5A6A7A8A9AAABACADAEAFB0B1B2B3B4B5B6B7B8B9BABBBCBDBEDF,  # noqa: E501
                        2: 0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [9], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xA0A1A2A3A4A5A6A7A8A9AAABACADAEAFB0B1B2B3B4B5B6B7B8B9BABBBCBDBEBF,  # noqa: E501
                        1: 0xA1A2C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
                        2: 0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [10], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xA0A1A0A1A4A5A6A7A8A9AAABACADAEAFB0B1B2B3B4B5B6B7B8B9BABBBCBDBEBF,  # noqa: E501
                        1: 0xC0C1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
                        2: 0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [11], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xA0A1A2A3A4A5A6A7A8A9AAABACADAEAFB0B1B2B3B4B5B6B7B8B9BABBBCBDBEBF,  # noqa: E501
                        1: 0xBFC1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
                        2: 0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [12], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xBFC0C1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDE,  # noqa: E501
                        1: 0xDFC1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
                        2: 0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [13], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xA0A2A3A4A5A6A7A8A9AAABACADAEAFB0B1B2B3B4B5B6B7B8B9BABBBCBDBEBFC0,  # noqa: E501
                        1: 0xC1C2C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
                        2: 0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [14], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xC1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDFE0,  # noqa: E501
                        1: 0xC0C1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
                        2: 0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [15], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xA0A1C1A3A4A5A6A7A8A9AAABACADAEAFB0B1B2B3B4B5B6B7B8B9BABBBCBDBEBF,  # noqa: E501
                        1: 0xC0C1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
                        2: 0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [16], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xC0C1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
                        1: 0xC0C1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
                        2: 0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [17], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(
                    storage={
                        0: 0xA0A1A2A3A4A5A6A7A8A9AAABACADAEAFB0B1B2B3B4B5B6B7B8B9BABBBCBDBEBF,  # noqa: E501
                        1: 0xC1C1C2C3C4C5C6C7C8C9CACBCCCDCECFD0D1D2D3D4D5D6D7D8D9DADBDCDDDEDF,  # noqa: E501
                        2: 0xE0E1E2E3E4E5E6E7E8E9EAEBECEDEEEFF0F1F2F3F4F5F6F7F8F9FAFBFCFDFEFF,  # noqa: E501
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(0x2) + Hash(0x0) + Hash(0x0),
        Hash(0x20) + Hash(0x1) + Hash(0x0),
        Hash(0x0) + Hash(0x1) + Hash(0x0),
        Hash(0x20) + Hash(0x21) + Hash(0x0),
        Hash(0x0) + Hash(0x0) + Hash(0x0),
        Hash(0x1F) + Hash(0x1F) + Hash(0x0),
        Hash(0x1) + Hash(0x0) + Hash(0x2),
        Hash(0x2) + Hash(0x1) + Hash(0x1F),
        Hash(0x20) + Hash(0x0) + Hash(0x1F),
        Hash(0x20) + Hash(0x1) + Hash(0x2),
        Hash(0x2) + Hash(0x0) + Hash(0x2),
        Hash(0x20) + Hash(0x1F) + Hash(0x1),
        Hash(0x0) + Hash(0x1F) + Hash(0x21),
        Hash(0x1) + Hash(0x2) + Hash(0x21),
        Hash(0x0) + Hash(0x21) + Hash(0x20),
        Hash(0x2) + Hash(0x21) + Hash(0x1),
        Hash(0x0) + Hash(0x20) + Hash(0x20),
        Hash(0x20) + Hash(0x21) + Hash(0x1),
        Hash(0x0) + Hash(0x0) + Hash(0x1),
        Hash(0x2) + Hash(0x2) + Hash(0x33),
    ]
    tx_gas = [1000000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
