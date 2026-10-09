"""
Test_random_statetest352.

Ported from:
state_tests/stRandom/randomStatetest352Filler.json
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
    ["state_tests/stRandom/randomStatetest352Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest352(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest352."""
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
    # 0x7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f00000000000000000000000000000000000000000000000000000000000000003a457f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>13428284f28a980b4539a39d1408  # noqa: E501
    target = pre.deploy_contract(
        code=Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.PUSH32[0x0]
        + Op.GASPRICE
        + Op.CALLCODE(
            gas=Op.DUP5,
            address=Op.DUP3,
            value=Op.TIMESTAMP,
            args_offset=Op.SGT(
                Op.PUSH32[coinbase],
                Op.PUSH32[0x0],
            ),
            args_size=Op.PUSH32[coinbase],
            ret_offset=Op.PUSH32[0xC350],
            ret_size=Op.GASLIMIT,
        )
        + Op.DUP11
        + Op.SWAP9
        + Op.SIGNEXTEND
        + Op.GASLIMIT
        + Op.CODECOPY
        + Op.LOG3
        + Op.SWAP14
        + Op.EQ
        + Op.ADDMOD,
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
            ]
            + Op.PUSH32[0x0]
            + Op.GASPRICE
            + Op.CALLCODE(
                gas=Op.DUP5,
                address=Op.DUP3,
                value=Op.TIMESTAMP,
                args_offset=Op.SGT(Op.PUSH32[coinbase], Op.PUSH32[0x0]),
                args_size=Op.PUSH32[coinbase],
                ret_offset=Op.PUSH32[0xC350],
                ret_size=Op.GASLIMIT,
            )
            + Op.DUP11
            + Op.SWAP9
            + Op.SIGNEXTEND
            + Op.GASLIMIT
            + Op.CODECOPY
            + Op.LOG3
            + Op.SWAP14
            + Op.EQ
            + Op.ADDMOD
        ),
        gas_limit=100000,
        value=0x14EB9AE,
    )

    post = {
        target: Account(storage={}, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
