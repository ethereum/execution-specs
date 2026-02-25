"""
Ported from:
tests/static/state_tests/stPreCompiledContracts2/CALLCODEEcrecoverV_prefixedf0Filler.json

contract code:
    push32 0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c
    push1 0x00
    mstore
    push1 0x00
    calldataload
    push1 0x20
    mstore
    push32 0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f
    push1 0x40
    mstore
    push32 0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549
    push1 0x60
    mstore
    push1 0x20
    push1 0x80
    push1 0x80
    push1 0x00
    push1 0x00
    push1 0x01
    push3 0x0493e0
    ... (18 more instructions)
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stPreCompiledContracts2/CALLCODEEcrecoverV_prefixedf0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000000000000000000000000000000000000000f01c",
        "00000000000000000000000000000000f000000000000000000000000000001c",
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_callcode_ecrecover_v_prefixedf0(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0xebcdd28b5479dbde3e8317ebac82a6e019e256e4")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0x1312d00,
        nonce=0,
        code=(
        Op.PUSH32[0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x20]
        + Op.MSTORE
        + Op.PUSH32[0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f]
        + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH32[0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549]
        + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x80]
        + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH3[0x493e0] + Op.CALLCODE + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0xa0]
        + Op.PUSH1[0x2] + Op.EXP + Op.PUSH1[0x80] + Op.MLOAD + Op.MOD + Op.PUSH1[0x0]
        + Op.SSTORE + Op.PUSH1[0x0] + Op.SLOAD + Op.ORIGIN + Op.EQ + Op.PUSH1[0x1]
        + Op.SSTORE + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=3652240,
        gas_price=10,
        nonce=0,
        value=100000,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
