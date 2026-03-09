"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest267Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest267Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest267(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x945304eb96065b2a98b57a48a06ae28d285a71b5")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.PREVRANDAO
            + Op.PUSH32[0xC350]
            + Op.PUSH32[
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE  # noqa: E501
            ]
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5]
            + Op.PUSH32[0x0]
            + Op.SSTORE(
                key=0xB5A132776D398E3B7C14686A07346F600051,
                value=0x7F000000000000000000000000945304EB96065B2A98B57A48A06AE28D285A,  # noqa: E501
            )
        ),
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x9,
                condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLDATALOAD(offset=0x20),
            )
        ),
        balance=46,
        nonce=0,
        address=coinbase,  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "447f000000000000000000000000000000000000000000000000000000000000c3507fff"  # noqa: E501
            "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f00000000"  # noqa: E501
            "000000000000000100000000000000000000000000000000000000007f00000000000000"  # noqa: E501
            "0000000000945304eb96065b2a98b57a48a06ae28d285a71b57f00000000000000000000"  # noqa: E501
            "000000000000000000000000000000000000000000007e7f000000000000000000000000"  # noqa: E501
            "945304eb96065b2a98b57a48a06ae28d285a71b5a132776d398e3b7c14686a07346f"  # noqa: E501
        ),
        gas_limit=100000,
        value=256968366,
    )

    post = {
        contract: Account(
            storage={
                0xB5A132776D398E3B7C14686A07346F600051: 0x7F000000000000000000000000945304EB96065B2A98B57A48A06AE28D285A,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
