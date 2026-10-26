"""
Test_random_statetest368.

Ported from:
state_tests/stRandom/randomStatetest368Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest368Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest368(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_random_statetest368."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x6000355415600957005b60203560003555
    coinbase = pre.deploy_contract(
        code=Op.JUMPI(
            pc=0x9,
            condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(
            key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)
        ),
        balance=46,
    )
    # Source: raw
    # 0x7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000007ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe097f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b54206f06d870339356057907760005155  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=(
            Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[0x0]
            + Op.CREATE(
                value=Op.MOD(Op.TIMESTAMP, Op.PUSH32[coinbase]),
                offset=Op.PUSH32[0x0],
                size=Op.MULMOD(
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
                    Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF],
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
                ),
            )
            + bytes.fromhex("6d870339356057907760005155")
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=(
            Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.PUSH32[0x0]
            + Op.CREATE(
                value=Op.MOD(Op.TIMESTAMP, Op.PUSH32[coinbase]),
                offset=Op.PUSH32[0x0],
                size=Op.MULMOD(
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
                    Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF],
                    0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE,
                ),
            )
            + Bytes("6d8703393560579077")
        ),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
        value=0x43AC3494,
    )

    post = {
        contract_0: Account(storage={}, nonce=2),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
        compute_create_address(address=contract_0, nonce=1): Account(
            storage={}, code=b"", balance=1000, nonce=1
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
