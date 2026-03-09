"""
CALL precompiles during init code of CREATE2 contract.

Ported from:
tests/static/state_tests/stCreate2/create2callPrecompilesFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stCreate2/create2callPrecompilesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "6000609b80601360003960006000f5500000fe7f18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c600052601c6020527f73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f6040527feeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549606052602060806080600060006001620493e0f160025560a060020a6080510660005560005432146001550000",  # noqa: E501
            {
                Address("0xf68e26002db0f9ca9b54367c57c25e474c581622"): Account(
                    storage={
                        0: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        1: 1,
                        2: 1,
                    }
                )
            },
        ),
        (
            "6000602480601360003960006000f5500000fe64f34578907f6005526020600060256000600060026101f4f16002556000516000550000",  # noqa: E501
            {
                Address("0x3b9ea59b92545beb727022289665cf38fa462bae"): Account(
                    storage={
                        0: 0xCB39B3BDE22925B2F931111130C774761D8895E0E08437C9B396C1E97D10F34D,  # noqa: E501
                        2: 1,
                    }
                )
            },
        ),
        (
            "6000601b80601360003960006000f5500000fe602060006000600060006003610258f16002556000516000550000",  # noqa: E501
            {
                Address("0x7525f19e2970539fd2897357777a4c275175bcf5"): Account(
                    storage={
                        0: 0x9C1185A5C5E9FC54612808977EE8F548B2258D31,
                        2: 1,
                    }
                )
            },
        ),
        (
            "6000602480601360003960006000f5500000fe64f34578907f6000526020600060256000600060046101f4f16002556000516000550000",  # noqa: E501
            {
                Address("0x0ee431db7c48fc10a9a56c909bfefa87661442fb"): Account(
                    storage={0: 0xF34578907F, 2: 1}
                )
            },
        ),
        (
            "6000609680601360003960006000f5500000fe6001600052602060205260206040527f03fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc6060527f2efffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc6080527f2f0000000000000000000000000000000000000000000000000000000000000060965260206103e860976000600060055af26001556103e8516002550000",  # noqa: E501
            {
                Address("0xbbd394930b408da783ee071ced240ece997bc8b2"): Account(
                    storage={
                        1: 1,
                        2: 0x162EAD82CADEFAEAF6E9283248FDF2F2845F6396F6F17C4D5A39F820B6F6B5F9,  # noqa: E501
                    }
                )
            },
        ),
        (
            "6000602280601360003960006000f5500000fe600160005260206000610100600060006006620927c0f16002556000516000550000",  # noqa: E501
            {
                Address("0x2e3ec33a50ed32c2fcbef07a1bab8643db4dc670"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "600060b780601360003960006000f5500000fe7f0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd26000527f16da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba6020527f1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2866040527f0217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d46060526000600060806000600073addf5374fce5edbc8e2a8697c15331677e6ebf0b6207a120f2500000",  # noqa: E501
            {
                Address("0xaa0ab87aa0e27e22e21671040c11f3537cdc7b3e"): Account(
                    storage={
                        0: 1,
                        1: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
                        2: 0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,  # noqa: E501
                    }
                )
            },
        ),
        (
            "600060c680601360003960006000f5500000fe7f1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2866000527f0217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d4602052600060405260006060527f1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2866080527f0217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d460a052600160c0526000600060e06000600073b94f5374fce5edbc8e2a8697c15331677e6ebf0b6207a120f2500000",  # noqa: E501
            {
                Address("0xab7cf4e4980432e892fa512ec2b9e8532c23ac15"): Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
                        11: 0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
                        20: 0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
                        21: 0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
                    }
                )
            },
        ),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2call_precompiles(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """CALL precompiles during init code of CREATE2 contract."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # {(MSTORE 0 (CALLDATALOAD 0)) (MSTORE 32 (CALLDATALOAD 32)) (MSTORE 64 (CALLDATALOAD 64)) (MSTORE 96 (CALLDATALOAD 96)) [[0]](CALLCODE 500000 6 0 0 128 200 64)  [[1]] (MLOAD 200)  [[2]] (MLOAD 232) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
            + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x20))
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x40))
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x60))
            + Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0x7A120,
                    address=0x6,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x80,
                    ret_offset=0xC8,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0xC8))
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0xE8))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xaddf5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: LLL
    # {(MSTORE 0 (CALLDATALOAD 0)) (MSTORE 32 (CALLDATALOAD 32)) (MSTORE 64 (CALLDATALOAD 64)) (MSTORE 96 (CALLDATALOAD 96))  (MSTORE 128 (CALLDATALOAD 128)) (MSTORE 160 (CALLDATALOAD 160)) (MSTORE 192 (CALLDATALOAD 192)) [[0]](CALLCODE 500000 6 0 0 128 300 64)  [[1]](CALLCODE 500000 7 0 128 96 400 64) [[10]] (MLOAD 300)  [[11]] (MLOAD 332) [[20]] (MLOAD 400)  [[21]] (MLOAD 432) [[2]] (EQ (SLOAD 10) (SLOAD 20)) [[3]] (EQ (SLOAD 11) (SLOAD 21))}  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
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
                key=0x2,
                value=Op.EQ(Op.SLOAD(key=0xA), Op.SLOAD(key=0x14)),
            )
            + Op.SSTORE(
                key=0x3,
                value=Op.EQ(Op.SLOAD(key=0xB), Op.SLOAD(key=0x15)),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data,
        gas_limit=15000000,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stCreate2/create2callPrecompilesFiller.json"],
)
@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "6000609b80601360003960006000f5500000fe7f18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c600052601c6020527f73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f6040527feeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549606052602060806080600060006001620493e0f160025560a060020a6080510660005560005432146001550000",  # noqa: E501
            {
                Address("0xf68e26002db0f9ca9b54367c57c25e474c581622"): Account(
                    storage={
                        0: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        1: 1,
                        2: 1,
                    }
                )
            },
        ),
        (
            "6000602480601360003960006000f5500000fe64f34578907f6005526020600060256000600060026101f4f16002556000516000550000",  # noqa: E501
            {
                Address("0x3b9ea59b92545beb727022289665cf38fa462bae"): Account(
                    storage={
                        0: 0xCB39B3BDE22925B2F931111130C774761D8895E0E08437C9B396C1E97D10F34D,  # noqa: E501
                        2: 1,
                    }
                )
            },
        ),
        (
            "6000601b80601360003960006000f5500000fe602060006000600060006003610258f16002556000516000550000",  # noqa: E501
            {
                Address("0x7525f19e2970539fd2897357777a4c275175bcf5"): Account(
                    storage={
                        0: 0x9C1185A5C5E9FC54612808977EE8F548B2258D31,
                        2: 1,
                    }
                )
            },
        ),
        (
            "6000602480601360003960006000f5500000fe64f34578907f6000526020600060256000600060046101f4f16002556000516000550000",  # noqa: E501
            {
                Address("0x0ee431db7c48fc10a9a56c909bfefa87661442fb"): Account(
                    storage={0: 0xF34578907F, 2: 1}
                )
            },
        ),
        (
            "6000609680601360003960006000f5500000fe6001600052602060205260206040527f03fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc6060527f2efffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc6080527f2f0000000000000000000000000000000000000000000000000000000000000060965260206103e860976000600060055af26001556103e8516002550000",  # noqa: E501
            {
                Address("0xbbd394930b408da783ee071ced240ece997bc8b2"): Account(
                    storage={
                        1: 1,
                        2: 0x162EAD82CADEFAEAF6E9283248FDF2F2845F6396F6F17C4D5A39F820B6F6B5F9,  # noqa: E501
                    }
                )
            },
        ),
        (
            "6000602280601360003960006000f5500000fe600160005260206000610100600060006006620927c0f16002556000516000550000",  # noqa: E501
            {
                Address("0x2e3ec33a50ed32c2fcbef07a1bab8643db4dc670"): Account(
                    storage={0: 1}
                )
            },
        ),
        (
            "600060b780601360003960006000f5500000fe7f0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd26000527f16da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba6020527f1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2866040527f0217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d46060526000600060806000600073addf5374fce5edbc8e2a8697c15331677e6ebf0b6207a120f2500000",  # noqa: E501
            {
                Address("0xaa0ab87aa0e27e22e21671040c11f3537cdc7b3e"): Account(
                    storage={
                        0: 1,
                        1: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
                        2: 0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,  # noqa: E501
                    }
                )
            },
        ),
        (
            "600060c680601360003960006000f5500000fe7f1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2866000527f0217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d4602052600060405260006060527f1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2866080527f0217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d460a052600160c0526000600060e06000600073b94f5374fce5edbc8e2a8697c15331677e6ebf0b6207a120f2500000",  # noqa: E501
            {
                Address("0xab7cf4e4980432e892fa512ec2b9e8532c23ac15"): Account(
                    storage={
                        0: 1,
                        1: 1,
                        2: 1,
                        3: 1,
                        10: 0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
                        11: 0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
                        20: 0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
                        21: 0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
                    }
                )
            },
        ),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2call_precompiles_from_osaka(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """CALL precompiles during init code of CREATE2 contract."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # {(MSTORE 0 (CALLDATALOAD 0)) (MSTORE 32 (CALLDATALOAD 32)) (MSTORE 64 (CALLDATALOAD 64)) (MSTORE 96 (CALLDATALOAD 96)) [[0]](CALLCODE 500000 6 0 0 128 200 64)  [[1]] (MLOAD 200)  [[2]] (MLOAD 232) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
            + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x20))
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x40))
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x60))
            + Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0x7A120,
                    address=0x6,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x80,
                    ret_offset=0xC8,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0xC8))
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0xE8))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xaddf5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: LLL
    # {(MSTORE 0 (CALLDATALOAD 0)) (MSTORE 32 (CALLDATALOAD 32)) (MSTORE 64 (CALLDATALOAD 64)) (MSTORE 96 (CALLDATALOAD 96))  (MSTORE 128 (CALLDATALOAD 128)) (MSTORE 160 (CALLDATALOAD 160)) (MSTORE 192 (CALLDATALOAD 192)) [[0]](CALLCODE 500000 6 0 0 128 300 64)  [[1]](CALLCODE 500000 7 0 128 96 400 64) [[10]] (MLOAD 300)  [[11]] (MLOAD 332) [[20]] (MLOAD 400)  [[21]] (MLOAD 432) [[2]] (EQ (SLOAD 10) (SLOAD 20)) [[3]] (EQ (SLOAD 11) (SLOAD 21))}  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
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
                key=0x2,
                value=Op.EQ(Op.SLOAD(key=0xA), Op.SLOAD(key=0x14)),
            )
            + Op.SSTORE(
                key=0x3,
                value=Op.EQ(Op.SLOAD(key=0xB), Op.SLOAD(key=0x15)),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data,
        gas_limit=15000000,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
