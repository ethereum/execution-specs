"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertOpcodeCallsFiller.json
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
    ["tests/static/state_tests/stRevertTest/RevertOpcodeCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, expected_post",
    [
        (
            "000000000000000000000000ceb48d108c874b5b014acdd1a2466d65a3d01de6",
            460000,
            {
                Address("0x1ada72179309fd8a562e308928e38763a543ed6c"): Account(
                    storage={10: 1}
                ),
                Address("0xceb48d108c874b5b014acdd1a2466d65a3d01de6"): Account(
                    storage={2: 14}
                ),
            },
        ),
        (
            "000000000000000000000000ceb48d108c874b5b014acdd1a2466d65a3d01de6",
            83622,
            {},
        ),
        (
            "000000000000000000000000737f82ed94146e759790d925492df5a8ced35885",
            460000,
            {
                Address("0x1ada72179309fd8a562e308928e38763a543ed6c"): Account(
                    storage={10: 1}
                ),
                Address("0x737f82ed94146e759790d925492df5a8ced35885"): Account(
                    storage={2: 14}
                ),
            },
        ),
        (
            "000000000000000000000000737f82ed94146e759790d925492df5a8ced35885",
            83622,
            {},
        ),
        (
            "0000000000000000000000006b8268ac8921e6a6e59a4b1d51a76f4e807e17af",
            460000,
            {
                Address("0x1ada72179309fd8a562e308928e38763a543ed6c"): Account(
                    storage={10: 1}
                ),
                Address("0x6b8268ac8921e6a6e59a4b1d51a76f4e807e17af"): Account(
                    storage={2: 14}
                ),
            },
        ),
        (
            "0000000000000000000000006b8268ac8921e6a6e59a4b1d51a76f4e807e17af",
            83622,
            {},
        ),
        (
            "000000000000000000000000bf3fc188d9c8d699ffa12f0369e3b2bcf8428f7c",
            460000,
            {
                Address("0x1ada72179309fd8a562e308928e38763a543ed6c"): Account(
                    storage={10: 1}
                ),
                Address("0x652761b88018ea027f6f27e456fe55c2dc5d6a91"): Account(
                    storage={5: 14}
                ),
                Address("0xbf3fc188d9c8d699ffa12f0369e3b2bcf8428f7c"): Account(
                    storage={0: 1, 2: 14}
                ),
            },
        ),
        (
            "000000000000000000000000bf3fc188d9c8d699ffa12f0369e3b2bcf8428f7c",
            83622,
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_calls(
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

    # Source: LLL
    # {  [[10]] (CALL 260000 (CALLDATALOAD 0) 0 0 0 0 0)}
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0xA,
                value=Op.CALL(
                    gas=0x3F7A0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x1ada72179309fd8a562e308928e38763a543ed6c"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x4,
                value=Op.CALL(
                    gas=0xC350,
                    address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x5, value=0xE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x652761b88018ea027f6f27e456fe55c2dc5d6a91"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=0xE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x6b8268ac8921e6a6e59a4b1d51a76f4e807e17af"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0xC350,
                    address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=0xE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x737f82ed94146e759790d925492df5a8ced35885"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0xC)
            + Op.REVERT(offset=0x0, size=0x1)
            + Op.SSTORE(key=0x3, value=0xD)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x186A0,
                    address=0x652761B88018EA027F6F27E456FE55C2DC5D6A91,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=0xE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0xbf3fc188d9c8d699ffa12f0369e3b2bcf8428f7c"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0xC350,
                    address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=0xE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0xceb48d108c874b5b014acdd1a2466d65a3d01de6"),  # noqa: E501
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
