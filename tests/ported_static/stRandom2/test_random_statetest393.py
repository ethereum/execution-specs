"""
Test_random_statetest393.

Ported from:
state_tests/stRandom2/randomStatetest393Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom2/randomStatetest393Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest393(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest393."""
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
    # 0x7f00000000000000000000000100000000000000000000000000000000000000007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000<contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5>7f000000000000000000000000000000000000000000000000000000000000c3507ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff20b39838f628b96846cff0455  # noqa: E501
    target = pre.deploy_contract(
        code=(
            Op.SIGNEXTEND(
                Op.CALLCODE(
                    gas=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    address=Op.PUSH32[0xC350],
                    value=Op.PUSH32[coinbase],
                    args_offset=Op.PUSH32[
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                    ],
                    args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    ret_offset=Op.PUSH32[coinbase],
                    ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ),
                Op.PUSH32[0x10000000000000000000000000000000000000000],
            )
            + Op.CODECOPY
            + Op.DUP4
            + Op.DUP16
            + Op.PUSH3[0x8B9684]
            + bytes.fromhex("6cff0455")
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=(
            Op.SIGNEXTEND(
                Op.CALLCODE(
                    gas=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    address=Op.PUSH32[0xC350],
                    value=Op.PUSH32[coinbase],
                    args_offset=Op.PUSH32[
                        0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
                    ],
                    args_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    ret_offset=Op.PUSH32[coinbase],
                    ret_size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                ),
                Op.PUSH32[0x10000000000000000000000000000000000000000],
            )
            + Op.CODECOPY
            + Op.DUP4
            + Op.DUP16
            + Op.PUSH3[0x8B9684]
            + Bytes("6cff04")
        ),
        gas_limit=100000,
        value=0x1D3BBA19,
    )

    post = {
        target: Account(storage={}, balance=0, nonce=1),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
