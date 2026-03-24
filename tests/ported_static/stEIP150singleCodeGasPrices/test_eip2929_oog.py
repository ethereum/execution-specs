"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP150singleCodeGasPrices/eip2929OOGFiller.yml
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
        "tests/static/state_tests/stEIP150singleCodeGasPrices/eip2929OOGFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000010fa00000000000000000000000000000000000000000000000000000000000006d6",  # noqa: E501
            {},
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000105500000000000000000000000000000000000000000000000000000000000055f0",  # noqa: E501
            {},
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000103100000000000000000000000000000000000000000000000000000000000007d0",  # noqa: E501
            {},
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000103b00000000000000000000000000000000000000000000000000000000000009c4",  # noqa: E501
            {},
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000103c00000000000000000000000000000000000000000000000000000000000009c4",  # noqa: E501
            {},
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000103f00000000000000000000000000000000000000000000000000000000000009c4",  # noqa: E501
            {},
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000010f100000000000000000000000000000000000000000000000000000000000006d6",  # noqa: E501
            {},
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000010f200000000000000000000000000000000000000000000000000000000000006d6",  # noqa: E501
            {},
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000010f400000000000000000000000000000000000000000000000000000000000006d6",  # noqa: E501
            {},
        ),
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000105400000000000000000000000000000000000000000000000000000000000007d0",  # noqa: E501
            {},
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_eip2929_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
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
        gas_limit=100000000,
    )

    pre.deploy_contract(
        code=Op.BALANCE(address=0xACC7) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000001031"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    (extcodesize 0x1031)
    # }
    pre.deploy_contract(
        code=Op.EXTCODESIZE(address=0x1031) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x000000000000000000000000000000000000103b"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    (extcodecopy 0x1031 0 0 0x20)
    # }
    pre.deploy_contract(
        code=(
            Op.EXTCODECOPY(
                address=0x1031,
                dest_offset=0x0,
                offset=0x0,
                size=0x20,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x000000000000000000000000000000000000103c"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    (extcodehash 0x1031)
    # }
    pre.deploy_contract(
        code=Op.EXTCODEHASH(address=0x1031) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x000000000000000000000000000000000000103f"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.SLOAD(key=0x0) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000001054"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x60A7) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x0000000000000000000000000000000000001055"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    (call 0x06A5 0xACC7 0 0 0 0 0)
    # }
    pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0x6A5,
                address=0xACC7,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000010f1"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    (callcode 0x06A5 0xACC7 0 0 0 0 0)
    # }
    pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0x6A5,
                address=0xACC7,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000010f2"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    (delegatecall 0x06A5 0xACC7 0 0 0 0)
    # }
    pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=0x6A5,
                address=0xACC7,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000010f4"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    (staticcall 0x06A5 0xACC7 0 0 0 0)
    # }
    pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0x6A5,
                address=0xACC7,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x00000000000000000000000000000000000010fa"),  # noqa: E501
    )
    # Source: LLL
    # {
    #    (return 0 0)
    # }
    pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0x0) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0x000000000000000000000000000000000000acc7"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    # Source: LLL
    # {
    #    (def 'addr     $4)     ; the address to call
    #    (def 'callGas $36)     ; the amount of gas to give it
    #
    #    [[0]] (call callGas addr 0 0 0 0 0)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.CALLDATALOAD(offset=0x24),
                    address=Op.CALLDATALOAD(offset=0x4),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        nonce=1,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
