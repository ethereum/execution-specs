"""
RevertOpcodeCreate for CREATE2.

Ported from:
tests/static/state_tests/stCreate2/RevertOpcodeCreateFiller.json
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
    ["tests/static/state_tests/stCreate2/RevertOpcodeCreateFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, expected_post",
    [
        (
            460000,
            {
                Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"): Account(
                    storage={0: 12}
                )
            },
        ),
        (70000, {}),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_create(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """RevertOpcodeCreate for CREATE2."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: LLL
    # { (MSTORE 0 0x600160005560016000fd6011600155 ) [[1]](CREATE2 1 17 15 0) [[0]] 12 }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x600160005560016000FD6011600155)
            + Op.SSTORE(
                key=0x1,
                value=Op.CREATE2(value=0x1, offset=0x11, size=0xF, salt=0x0),
            )
            + Op.SSTORE(key=0x0, value=0xC)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("600160005560016000fe6011600155"),
        gas_limit=tx_gas_limit,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
