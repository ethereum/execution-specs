"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/VMTests/vmTests/randomFiller.yml
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
    ["tests/static/state_tests/VMTests/vmTests/randomFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
            {},
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {},
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {},
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000003",  # noqa: E501
            {},
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000004",  # noqa: E501
            {},
        ),
        (
            "693c61390000000000000000000000000000000000000000000000000000000000000005",  # noqa: E501
            {},
        ),
    ],
    ids=["case0", "case1", "case2", "case3", "case4", "case5"],
)
@pytest.mark.pre_alloc_mutable
def test_random(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xF3630C36A29EC9AF814AE38E4D48056A3368BB1435C5C2B3289763E4C77A3DF0
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
        code=bytes.fromhex("4040459143404144809759886d608f"),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x15adfb805be4f3ee3e5c535abc860890a3a2a6c9"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.BLOCKHASH + Op.COINBASE,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x2e3b99613a2e74ebb0cd62d7b9eb38bad240cec6"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.BLOCKHASH
            + Op.BLOCKHASH(block_number=Op.GASLIMIT)
            + Op.COINBASE
            + Op.GASLIMIT
            + Op.GASLIMIT
            + Op.CODECOPY(
                dest_offset=Op.CALLVALUE,
                offset=Op.COINBASE,
                size=Op.PREVRANDAO,
            )
            + Op.SELFDESTRUCT(address=Op.DUP8)
            + Op.CALLDATACOPY
            + Op.CALLDATALOAD
            + Op.SSTORE(key=Op.ADDRESS, value=Op.DIV)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x3412d3ebac3fcacfb451708aef7cc8e5bf1e5261"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x10000000000000)
    pre.deploy_contract(
        code=(
            Op.NUMBER
            + Op.NUMBER
            + Op.TIMESTAMP
            + Op.PREVRANDAO
            + Op.TIMESTAMP
            + Op.PREVRANDAO
            + Op.GASLIMIT
            + Op.GASLIMIT
            + Op.SWAP8
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x66b8dba513dc25f967ef7e84306616c0071cccae"),  # noqa: E501
    )
    # Source: LLL
    # {
    #     (call (gas) (+ 0x1000 $4) 0 0 0 0 0)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=Op.GAS,
                address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xa83db56c7ce68c06129b80c7be0d0f5e0869d536"),  # noqa: E501
    )
    pre.deploy_contract(
        code=bytes.fromhex("65424555"),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xacd000f275b1a28d0c3b7dee7f114c4d28fb1636"),  # noqa: E501
    )
    pre.deploy_contract(
        code=bytes.fromhex("7745414245403745f31387900a8d55"),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xdfe69e96fb3aafde261565670b1fea29869c6950"),  # noqa: E501
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
