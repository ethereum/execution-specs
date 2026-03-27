"""
Test_random_statetest307.

Ported from:
state_tests/stRandom/randomStatetest307Filler.json
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
    ["state_tests/stRandom/randomStatetest307Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest307(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest307."""
    coinbase = Address("0x945304eb96065b2a98b57a48a06ae28d285a71b5")
    contract_0 = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b5547f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000000000000000000000000000000000000000c3507f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000000000000000000000000000000000000000000037f055  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5]
        + Op.PUSH32[0xC350]
        + Op.SLOAD(key=Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5])
        + Op.PUSH32[0xC350]
        + Op.CALLDATACOPY(
            dest_offset=Op.PUSH32[0x0],
            offset=Op.PUSH32[0x0],
            size=Op.PUSH32[0xC350],
        )
        + Op.CREATE
        + Op.SSTORE,
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
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
        address=Address("0x945304eb96065b2a98b57a48a06ae28d285a71b5"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=bytes.fromhex(
            "7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b5547f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000000000000000000000000000000000000000c3507f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000000000000000000000000000000000000000000037f0"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x4ACA7F0D,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(storage={}, nonce=0),
        Address(
            "0x62c01474f089b07dae603491675dc5b5748f7049"
        ): Account.NONEXISTENT,
        Address(
            "0x91ed00a0a906270d466af043c4e111dadca970a3"
        ): Account.NONEXISTENT,
        coinbase: Account(storage={}, nonce=0),
        Address(
            "0xd2571607e241ecf590ed94b12d87c94babe36db6"
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
