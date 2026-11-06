"""
Test_random_statetest246.

Ported from:
state_tests/stRandom/randomStatetest246Filler.json
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
    ["state_tests/stRandom/randomStatetest246Filler.json"],
)
@pytest.mark.valid_from("Cancun")
def test_random_statetest246(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest246."""
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: raw
    # 0x434241314441434293170955
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.NUMBER
        + Op.TIMESTAMP
        + Op.BALANCE(address=Op.COINBASE)
        + Op.PREVRANDAO
        + Op.COINBASE
        + Op.NUMBER
        + Op.TIMESTAMP
        + Op.SWAP4
        + Op.SSTORE(key=Op.MULMOD, value=Op.OR),
        balance=0xDE0B6B3A7640000,
    )
    # Source: raw
    # 0x6000355415600957005b60203560003555
    coinbase = pre.deploy_contract(  # noqa: F841
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

    env = Environment(
        fee_recipient=coinbase,
        prev_randao=0x20000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes("42"),
        gas_limit=400000,
        value=0x186A0,
    )

    post = {
        contract_0: Account(
            storage={(46 | 1) * int.from_bytes(coinbase) % 0x20000: 1000}
        ),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
