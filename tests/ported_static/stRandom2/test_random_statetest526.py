"""
Test_random_statetest526.

Ported from:
state_tests/stRandom2/randomStatetest526Filler.json

@manually-enhanced: Do not overwrite. tx `gas_limit` has been removed.
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
    ["state_tests/stRandom2/randomStatetest526Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest526(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest526."""
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
    # 0x7f00000000000000000000000100000000000000000000000000000000000000007f00000000000000000000000100000000000000000000000000000000000000007f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b5417e7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b5419e01950777810975058c746f5560005155  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.PUSH32[0x10000000000000000000000000000000000000000] * 2
        + Op.PUSH32[0x0]
        + Op.PUSH32[coinbase]
        + Op.COINBASE
        + Op.SSTORE(
            key=0xB5419E01950777810975058C746F55600051,
            value=0x7F000000000000000000000000945304EB96065B2A98B57A48A06AE28D285A,  # noqa: E501
        ),
    )

    env = Environment(fee_recipient=coinbase, prev_randao=0x20000)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=(
            Op.PUSH32[0x10000000000000000000000000000000000000000] * 2
            + Op.PUSH32[0x0]
            + Op.PUSH32[coinbase]
            + Op.COINBASE
            + Bytes("7e7f000000000000000000000000")
            + coinbase
            + Bytes("419e01950777810975058c746f")
        ),
        value=0x3AA8C462,
    )

    post = {
        contract_0: Account(
            storage={
                0xB5419E01950777810975058C746F55600051: 0x7F000000000000000000000000945304EB96065B2A98B57A48A06AE28D285A,  # noqa: E501
            },
            nonce=1,
        ),
        coinbase: Account(storage={}, nonce=1),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
