"""
Test_random_statetest274.

Ported from:
state_tests/stRandom/randomStatetest274Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest274Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest274(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest274."""
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
    # 0x7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffffa405457f00000000000000000000000100000000000000000000000000000000000000007f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>88015a9a0542a13a051497514215  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.LOG4
        + Op.SDIV
        + Op.GASLIMIT
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.ADD(Op.DUP9, Op.PUSH32[coinbase])
        + Op.GAS
        + Op.SWAP11
        + Op.SDIV
        + Op.TIMESTAMP
        + Op.LOG1
        + Op.EQ(Op.SDIV, Op.GASPRICE)
        + Op.SWAP8
        + Op.MLOAD
        + Op.ISZERO(Op.TIMESTAMP),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
            + Op.LOG4
            + Op.SDIV
            + Op.GASLIMIT
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.ADD(Op.DUP9, Op.PUSH32[coinbase])
            + Op.GAS
            + Op.SWAP11
            + Op.SDIV
            + Op.TIMESTAMP
            + Op.LOG1
            + Op.EQ(Op.SDIV, Op.GASPRICE)
            + Op.SWAP8
            + Op.MLOAD
            + Op.ISZERO(Op.TIMESTAMP)
        ),
        gas_limit=100000,
        value=0xB6A01E0,
    )

    post = {
        target: Account(storage={}, balance=0, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
