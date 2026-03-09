"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_Call50000_identity2Filler.json
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
        "tests/static/state_tests/stStaticCall/static_Call50000_identity2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "000000000000000000000000cfb4c99d22928822feffa77a1a6de64042e48dd3",
            {
                Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"): Account(
                    storage={0: 1, 1: 1}
                ),
                Address("0xcfb4c99d22928822feffa77a1a6de64042e48dd3"): Account(
                    storage={1: 50000, 2: 42}
                ),
            },
        ),
        (
            "000000000000000000000000b02bd8691a1a4f5fd4432b5b17c68dde3013fc35",
            {
                Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call50000_identity2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=8925000000,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x2A)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x30,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.MSTORE(
                offset=0x0,
                value=Op.STATICCALL(
                    gas=0x61C,
                    address=0x4,
                    args_offset=0x0,
                    args_size=0xC350,
                    ret_offset=0x1,
                    ret_size=0xC350,
                ),
            )
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x5)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x20, value=Op.MLOAD(offset=0x80))
            + Op.MSTORE(offset=0x40, value=Op.MLOAD(offset=0x1))
            + Op.STOP
        ),
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0xb02bd8691a1a4f5fd4432b5b17c68dde3013fc35"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=Op.CALLVALUE,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x2A)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x30,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0x61C,
                    address=0x4,
                    args_offset=0x0,
                    args_size=0xC350,
                    ret_offset=0x1,
                    ret_size=0xC350,
                ),
            )
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x5)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x1))
            + Op.STOP
        ),
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0xcfb4c99d22928822feffa77a1a6de64042e48dd3"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=882500000,
        value=10,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
