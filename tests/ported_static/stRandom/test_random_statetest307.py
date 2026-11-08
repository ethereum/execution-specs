"""
Test_random_statetest307.

Ported from:
state_tests/stRandom/randomStatetest307Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest307Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest307(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest307."""
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
    # 0x7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b5547f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000000000000000000000000000000000000000c3507f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000000000000000000000000000000000000000000037f055  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.PUSH32[coinbase]
        + Op.PUSH32[0xC350]
        + Op.SLOAD(key=Op.PUSH32[coinbase])
        + Op.PUSH32[0xC350]
        + Op.CALLDATACOPY(
            dest_offset=Op.PUSH32[0x0],
            offset=Op.PUSH32[0x0],
            size=Op.PUSH32[0xC350],
        )
        + Op.CREATE
        + Op.SSTORE,
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=(
            Op.PUSH32[coinbase]
            + Op.PUSH32[0xC350]
            + Op.SLOAD(key=Op.PUSH32[coinbase])
            + Op.PUSH32[0xC350]
            + Op.CALLDATACOPY(
                dest_offset=Op.PUSH32[0x0],
                offset=Op.PUSH32[0x0],
                size=Op.PUSH32[0xC350],
            )
            + Op.CREATE
        ),
        gas_limit=100000,
        value=0x4ACA7F0D,
    )

    post = {
        contract_0: Account(storage={}, nonce=1),
        compute_create_address(
            address=compute_create_address(address=contract_0, nonce=1),
            nonce=0,
        ): Account.NONEXISTENT,
        compute_create_address(
            address=compute_create_address(address=contract_0, nonce=1),
            nonce=1,
        ): Account.NONEXISTENT,
        coinbase: Account(storage={}, nonce=1),
        compute_create_address(
            address=contract_0, nonce=1
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
