"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertOpcodeReturnFiller.json
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
    ["tests/static/state_tests/stRevertTest/RevertOpcodeReturnFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, expected_post",
    [
        (
            "0000000000000000000000001963fd2c717f5b4b9fa3d6baf38d66241e1ec005",
            800000,
            {
                Address("0x1fc98371f1a058f1a6042e30a141aa8bb67dd1bc"): Account(
                    storage={2: 0x726576657274206D657373616765}
                )
            },
        ),
        (
            "0000000000000000000000001963fd2c717f5b4b9fa3d6baf38d66241e1ec005",
            80000,
            {
                Address("0x1fc98371f1a058f1a6042e30a141aa8bb67dd1bc"): Account(
                    storage={2: 0x726576657274206D657373616765}
                )
            },
        ),
        (
            "000000000000000000000000745e52346d8549444323699e9fc383ae89bdd24f",
            800000,
            {},
        ),
        (
            "000000000000000000000000745e52346d8549444323699e9fc383ae89bdd24f",
            80000,
            {},
        ),
        (
            "00000000000000000000000050eaca0a040ac6242d0c01cc1ff82f5b95cc10e4",
            800000,
            {},
        ),
        (
            "00000000000000000000000050eaca0a040ac6242d0c01cc1ff82f5b95cc10e4",
            80000,
            {},
        ),
        (
            "000000000000000000000000f933d2374d5875de033a8ed9d9c1ce5dea25c78b",
            800000,
            {},
        ),
        (
            "000000000000000000000000f933d2374d5875de033a8ed9d9c1ce5dea25c78b",
            80000,
            {},
        ),
        (
            "000000000000000000000000e5b2dfe7f932f2d5eaa7c8fb2e1e9a8b6a846fd7",
            800000,
            {},
        ),
        (
            "000000000000000000000000e5b2dfe7f932f2d5eaa7c8fb2e1e9a8b6a846fd7",
            80000,
            {},
        ),
        (
            "000000000000000000000000858f82bbfd84fc9eb91291458511df77311dbd0d",
            800000,
            {},
        ),
        (
            "000000000000000000000000858f82bbfd84fc9eb91291458511df77311dbd0d",
            80000,
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
        "case10",
        "case11",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_return(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
            + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
            + Op.REVERT(offset=0x0, size=0x20)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1963fd2c717f5b4b9fa3d6baf38d66241e1ec005"),  # noqa: E501
    )
    # Source: LLL
    # { [[1]](CALL 150000 (CALLDATALOAD 0) 0 0 0 0 32) [[2]] (MLOAD 0) }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.CALL(
                    gas=0x249F0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1fc98371f1a058f1a6042e30a141aa8bb67dd1bc"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
            + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
            + Op.REVERT(offset=0x0, size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x50eaca0a040ac6242d0c01cc1ff82f5b95cc10e4"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
            + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
            + Op.REVERT(offset=0x0, size=0x0)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x745e52346d8549444323699e9fc383ae89bdd24f"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
            + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
            + Op.REVERT(offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, size=0x0)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x858f82bbfd84fc9eb91291458511df77311dbd0d"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
            + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
            + Op.REVERT(offset=0x1, size=0x0)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xe5b2dfe7f932f2d5eaa7c8fb2e1e9a8b6a846fd7"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=0x72657665727465642064617461)
            + Op.MSTORE(offset=0x0, value=0x726576657274206D657373616765)
            + Op.REVERT(offset=0x100, size=0x0)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xf933d2374d5875de033a8ed9d9c1ce5dea25c78b"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
