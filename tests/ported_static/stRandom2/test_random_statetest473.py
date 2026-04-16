"""
Test_random_statetest473.

Ported from:
state_tests/stRandom2/randomStatetest473Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
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
    ["state_tests/stRandom2/randomStatetest473Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest473(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest473."""
    coinbase = Address(0x945304EB96065B2A98B57A48A06AE28D285A71B5)
    contract_0 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
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
        nonce=0,
        address=Address(0x945304EB96065B2A98B57A48A06AE28D285A71B5),  # noqa: E501
    )
    # Source: raw
    # 0x7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff317f000000000000000000000000000000000000000000000000000000000000c3507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000017ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b59102095560005155  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.BALANCE(
            address=Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        )
        + Op.PUSH32[0xC350]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
        ]
        + Op.PUSH32[0x1]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5]
        + Op.SWAP2
        + Op.SSTORE(key=Op.MULMOD, value=Op.MUL)
        + Op.MLOAD(offset=0x0)
        + Op.SSTORE,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(
            "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff317f000000000000000000000000000000000000000000000000000000000000c3507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000017ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b5910209"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x4467CA41,
    )

    post = {
        contract_0: Account(
            storage={
                0xFFFFFFFFFFFFFFFFFFFFFFFF6BACFB1469F9A4D5674A85B75F951D72D7A58E4A: 50000,  # noqa: E501
            },
            nonce=0,
        ),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
