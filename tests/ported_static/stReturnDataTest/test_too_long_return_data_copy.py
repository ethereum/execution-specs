"""
Ori Pomerantz   qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stReturnDataTest/tooLongReturnDataCopyFiller.yml
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
    [
        "tests/static/state_tests/stReturnDataTest/tooLongReturnDataCopyFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000001000000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000009000000000000000000000000000000000000000000000000000000000000000800000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000800000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000001000000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000020000000000000000000000000000000000000000000000000000000000000001000000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000011000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000010000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000090000000000000000000000000000000000000000000000000000000000000008000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000008000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000010000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000010000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000100000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001100000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f9000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 24743}
                )
            },
        ),
        (
            "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000800000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 57005}
                )
            },
        ),
        (
            "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000008000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
            {
                Address("0xa6e4f86617d6ab14d857f9115c2ab9f2787157ba"): Account(
                    storage={0: 16}
                ),
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 57005}
                ),
            },
        ),
        (
            "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
            {
                Address("0xa6e4f86617d6ab14d857f9115c2ab9f2787157ba"): Account(
                    storage={0: 16}
                ),
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 57005}
                ),
            },
        ),
        (
            "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
            {
                Address("0xa6e4f86617d6ab14d857f9115c2ab9f2787157ba"): Account(
                    storage={0: 16}
                ),
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 57005}
                ),
            },
        ),
        (
            "917694f9000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000080000000000000000000000000000000000000000000000000000000000000008000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
            {
                Address("0xa6e4f86617d6ab14d857f9115c2ab9f2787157ba"): Account(
                    storage={0: 16}
                ),
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 57005}
                ),
            },
        ),
        (
            "917694f900000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 57005}
                )
            },
        ),
        (
            "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000800000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 57005}
                )
            },
        ),
        (
            "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001000000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 57005}
                )
            },
        ),
        (
            "917694f900000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000f00000000000000000000000023eef957bcfb3738417aee7fdf4294cf110d7881",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 57005}
                )
            },
        ),
        (
            "917694f9000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a6e4f86617d6ab14d857f9115c2ab9f2787157ba",  # noqa: E501
            {
                Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"): Account(
                    storage={0: 57005}
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
        "case8",
        "case9",
        "case10",
        "case11",
        "case12",
        "case13",
        "case14",
        "case15",
        "case16",
        "case17",
        "case18",
        "case19",
        "case20",
        "case21",
        "case22",
        "case23",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_too_long_return_data_copy(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Ori Pomerantz   qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x04DC42D61413D4DED993826AC4D6ED7A4A970C60335D2B285C60A4274E792FF1
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4503599627370496,
    )

    pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.MSTORE(
                offset=0x0,
                value=0x1F1E1D1C1B1A191817161514131211100F0E0D0C0B0A090807060504030201FF,  # noqa: E501
            )
            + Op.SSTORE(key=0x0, value=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.REVERT
        ),
        address=Address("0x23eef957bcfb3738417aee7fdf4294cf110d7881"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000, nonce=1)
    pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x0)
            + Op.MSTORE(
                offset=0x0,
                value=0x1F1E1D1C1B1A191817161514131211100F0E0D0C0B0A090807060504030201FF,  # noqa: E501
            )
            + Op.SSTORE(key=0x0, value=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.RETURN
        ),
        address=Address("0xa6e4f86617d6ab14d857f9115c2ab9f2787157ba"),  # noqa: E501
    )
    # Source: Yul
    # {
    #    let lengthReturned := calldataload(0x04)
    #    let offsetCopied   := calldataload(0x24)
    #    let lengthCopied   := calldataload(0x44)
    #    let contract       := calldataload(0x64)
    #    mstore(0, lengthReturned)
    #
    #    // The length of the buffer to be returned is part of the calldata
    #    // for this contract. However, it is necessary to send it to the
    #    // contract we're calling (either <contract:0x000000000000000000000000000000000000c0de> or <contract:0x0000000000000000000000000000000000000bad>) so it will know  # noqa: E501
    #    // what size of buffer to return to us
    #    let retVal := call(gas(), contract, 0,
    #       0, 0x20,    // input buffer with lengthReturned
    #       0, 0x100)    // output buffer
    #
    #    // Copy the return data (which fails if
    #    // offsetCopied+lengthCopied > lengthReturned)
    #    returndatacopy(0x100, offsetCopied, lengthCopied)
    #
    #
    #    // Show that other copies of excess length work (otherwise
    #    // the goat will never die)
    #    extcodecopy(<contract:0x000000000000000000000000000000000000c0de>, 0,0, add(0x20,extcodesize(<contract:0x000000000000000000000000000000000000c0de>)))  # noqa: E501
    #    calldatacopy(0,0, add(0x20,calldatasize()))
    #    codecopy(0,0, add(0x20,codesize()))
    #
    #
    #    // If we get here, kill the goat to show success
    #    sstore(0, 0xDEAD)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.CALLDATALOAD(offset=0x4)
            + Op.CALLDATALOAD(offset=0x24)
            + Op.PUSH2[0x100]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x20]
            + Op.DUP2
            + Op.DUP1
            + Op.CALLDATALOAD(offset=0x44)
            + Op.SWAP7
            + Op.CALLDATALOAD(offset=0x64)
            + Op.SWAP1
            + Op.DUP3
            + Op.MSTORE
            + Op.GAS
            + Op.POP(Op.CALL)
            + Op.PUSH2[0x100]
            + Op.RETURNDATACOPY
            + Op.EXTCODECOPY(
                address=0xA6E4F86617D6AB14D857F9115C2AB9F2787157BA,
                dest_offset=Op.DUP1,
                offset=0x0,
                size=Op.ADD(
                    0x20,
                    Op.EXTCODESIZE(
                        address=0xA6E4F86617D6AB14D857F9115C2AB9F2787157BA,
                    ),
                ),
            )
            + Op.CALLDATACOPY(
                dest_offset=Op.DUP1,
                offset=0x0,
                size=Op.ADD(0x20, Op.CALLDATASIZE),
            )
            + Op.CODECOPY(
                dest_offset=Op.DUP1,
                offset=0x0,
                size=Op.ADD(0x20, Op.CODESIZE),
            )
            + Op.SSTORE(key=0x0, value=0xDEAD)
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xDE0B6B3A7640000,
        address=Address("0xe4592ed5b9c3a9302d66798e39bfb7dfd44fafc1"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        gas_price=100,
        nonce=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
