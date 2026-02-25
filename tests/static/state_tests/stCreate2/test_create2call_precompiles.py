"""
CALL precompiles during init code of CREATE2 contract 

Ported from:
tests/static/state_tests/stCreate2/create2callPrecompilesFiller.json

contract code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x20
    calldataload
    push1 0x20
    mstore
    push1 0x40
    calldataload
    push1 0x40
    mstore
    push1 0x60
    calldataload
    push1 0x60
    mstore
    push1 0x40
    push1 0xc8
    push1 0x80
    push1 0x00
    ... (15 more instructions)

callee_1 code:
    push1 0x00
    calldataload
    push1 0x00
    mstore
    push1 0x20
    calldataload
    push1 0x20
    mstore
    push1 0x40
    calldataload
    push1 0x40
    mstore
    push1 0x60
    calldataload
    push1 0x60
    mstore
    push1 0x80
    calldataload
    push1 0x80
    mstore
    ... (59 more instructions)
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
    ["tests/static/state_tests/stCreate2/create2callPrecompilesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "6000609b80601360003960006000f5500000fe7f18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c600052601c6020527f73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f6040527feeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549606052602060806080600060006001620493e0f160025560a060020a6080510660005560005432146001550000",
        "6000602480601360003960006000f5500000fe64f34578907f6005526020600060256000600060026101f4f16002556000516000550000",
        "6000601b80601360003960006000f5500000fe602060006000600060006003610258f16002556000516000550000",
        "6000602480601360003960006000f5500000fe64f34578907f6000526020600060256000600060046101f4f16002556000516000550000",
        "6000609680601360003960006000f5500000fe6001600052602060205260206040527f03fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc6060527f2efffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc6080527f2f0000000000000000000000000000000000000000000000000000000000000060965260206103e860976000600060055af26001556103e8516002550000",
        "6000602280601360003960006000f5500000fe600160005260206000610100600060006006620927c0f16002556000516000550000",
        "600060b780601360003960006000f5500000fe7f0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd26000527f16da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba6020527f1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2866040527f0217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d46060526000600060806000600073addf5374fce5edbc8e2a8697c15331677e6ebf0b6207a120f2500000",
        "600060c680601360003960006000f5500000fe7f1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2866000527f0217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d4602052600060405260006060527f1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2866080527f0217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d460a052600160c0526000600060e06000600073b94f5374fce5edbc8e2a8697c15331677e6ebf0b6207a120f2500000",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7'],
)
@pytest.mark.pre_alloc_mutable
def test_create2call_precompiles(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """CALL precompiles during init code of CREATE2 contract ."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xaddf5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee_1 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000000,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.CALLDATALOAD + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.CALLDATALOAD + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x60]
        + Op.CALLDATALOAD + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.PUSH1[0xc8] + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x6] + Op.PUSH3[0x7a120] + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0xc8] + Op.MLOAD + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0xe8]
        + Op.MLOAD + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.CALLDATALOAD + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.CALLDATALOAD + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x60]
        + Op.CALLDATALOAD + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x80]
        + Op.CALLDATALOAD + Op.PUSH1[0x80] + Op.MSTORE + Op.PUSH1[0xa0]
        + Op.CALLDATALOAD + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH1[0xc0]
        + Op.CALLDATALOAD + Op.PUSH1[0xc0] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.PUSH2[0x12c] + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x6] + Op.PUSH3[0x7a120] + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x40] + Op.PUSH2[0x190] + Op.PUSH1[0x60] + Op.PUSH1[0x80]
        + Op.PUSH1[0x0] + Op.PUSH1[0x7] + Op.PUSH3[0x7a120] + Op.CALLCODE
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH2[0x12c] + Op.MLOAD + Op.PUSH1[0xa]
        + Op.SSTORE + Op.PUSH2[0x14c] + Op.MLOAD + Op.PUSH1[0xb] + Op.SSTORE
        + Op.PUSH2[0x190] + Op.MLOAD + Op.PUSH1[0x14] + Op.SSTORE + Op.PUSH2[0x1b0]
        + Op.MLOAD + Op.PUSH1[0x15] + Op.SSTORE + Op.PUSH1[0x14] + Op.SLOAD
        + Op.PUSH1[0xa] + Op.SLOAD + Op.EQ + Op.PUSH1[0x2] + Op.SSTORE
        + Op.PUSH1[0x15] + Op.SLOAD + Op.PUSH1[0xb] + Op.SLOAD + Op.EQ + Op.PUSH1[0x3]
        + Op.SSTORE + Op.STOP
    ),
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=None,
        data=tx_data,
        gas_limit=15000000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
