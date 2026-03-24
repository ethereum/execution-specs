"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmIOandFlowOperations/codecopyFiller.yml
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
        "tests/static/state_tests/VMTests/vmIOandFlowOperations/codecopyFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        0: 0x6040600060003960005160005560205160015500000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        0: 0x6010600F600E600D600C600B600A600960086007600660056004600360026001,  # noqa: E501
                        1: 0x101010101010101010101010101016101005260206000600039604060206020,  # noqa: E501
                        2: 0x3960005160005560205160015560405160025500000000000000000000000000,  # noqa: E501
                    }
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        0: 0x6110006000600039600051600055602051600155000000000000000000000000  # noqa: E501
                    }
                )
            },
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {},
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            {
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        0: 0x3860FF5560FF5460006000396160A76000556160A76001556160A76002556000,  # noqa: E501
                        1: 0x5160005560205160015560405160025560605160035560805160045560A05160,  # noqa: E501
                        2: 0x5550061DEADFF60FF546000F360AA60BB60CC60DD60EE60FFF4000000000000,  # noqa: E501
                        255: 91,
                    }
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2", "case3", "case4"],
)
@pytest.mark.pre_alloc_mutable
def test_codecopy(
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
        code=(
            Op.CODECOPY(dest_offset=0x0, offset=0x0, size=0x40)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.CODECOPY(dest_offset=0x0, offset=0x0, size=Op.SUB(0x0, 0x1))
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.CODECOPY(dest_offset=0x0, offset=0x0, size=0x1000)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x100,
                value=Op.ADD(
                    Op.ADD(
                        Op.ADD(
                            Op.ADD(
                                Op.ADD(
                                    Op.ADD(
                                        Op.ADD(
                                            Op.ADD(
                                                Op.ADD(
                                                    Op.ADD(
                                                        Op.ADD(
                                                            Op.ADD(
                                                                Op.ADD(
                                                                    Op.ADD(
                                                                        Op.ADD(
                                                                            0x1,  # noqa: E501
                                                                            0x2,  # noqa: E501
                                                                        ),
                                                                        0x3,
                                                                    ),
                                                                    0x4,
                                                                ),
                                                                0x5,
                                                            ),
                                                            0x6,
                                                        ),
                                                        0x7,
                                                    ),
                                                    0x8,
                                                ),
                                                0x9,
                                            ),
                                            0xA,
                                        ),
                                        0xB,
                                    ),
                                    0xC,
                                ),
                                0xD,
                            ),
                            0xE,
                        ),
                        0xF,
                    ),
                    0x10,
                ),
            )
            + Op.CODECOPY(dest_offset=0x0, offset=0x0, size=0x20)
            + Op.CODECOPY(dest_offset=0x20, offset=0x20, size=0x40)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x40))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0xFF, value=Op.CODESIZE)
            + Op.CODECOPY(dest_offset=0x0, offset=0x0, size=Op.SLOAD(key=0xFF))
            + Op.SSTORE(key=0x0, value=0x60A7)
            + Op.SSTORE(key=0x1, value=0x60A7)
            + Op.SSTORE(key=0x2, value=0x60A7)
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x40))
            + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x60))
            + Op.SSTORE(key=0x4, value=Op.MLOAD(offset=0x80))
            + Op.SSTORE(key=0x5, value=Op.MLOAD(offset=0xA0))
            + Op.STOP
            + Op.SELFDESTRUCT(address=0xDEAD)
            + Op.RETURN(offset=0x0, size=Op.SLOAD(key=0xFF))
            + Op.DELEGATECALL(
                gas=0xFF,
                address=0xEE,
                args_offset=0xDD,
                args_size=0xCC,
                ret_offset=0xBB,
                ret_size=0xAA,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
    # {
    #     (delegatecall 0xffffff (+ 0x1000 $4) 0 0 0 0)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.DELEGATECALL(
                gas=0xFFFFFF,
                address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
