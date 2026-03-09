"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest137Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest137Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest137(
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
            Op.ADDMOD(
                Op.PUSH32[0x0],
                Op.PUSH32[0x0],
                Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF],
            )
            + Op.PUSH32[0x10000000000000000000000000000000000000000]
            + Op.PUSH32[0x1]
            + Op.SSTORE(
                key=0xB5A130E86CA17390989355F092A255600051,
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
            "7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f0000"  # noqa: E501
            "0000000000000000000000000000000000000000000000000000000000007f0000000000"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000087f00000000000000"  # noqa: E501
            "000000000100000000000000000000000000000000000000007f00000000000000000000"  # noqa: E501
            "000000000000000000000000000000000000000000017e7f000000000000000000000000"  # noqa: E501
            "945304eb96065b2a98b57a48a06ae28d285a71b5a130e86ca17390989355f092a2"  # noqa: E501
        ),
        gas_limit=100000,
        value=866944487,
    )

    post = {
        contract: Account(
            storage={
                0xB5A130E86CA17390989355F092A255600051: 0x7F000000000000000000000000945304EB96065B2A98B57A48A06AE28D285A,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
