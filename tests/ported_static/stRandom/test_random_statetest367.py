"""
Test_random_statetest367.

Ported from:
state_tests/stRandom/randomStatetest367Filler.json
"""

import pytest
from execution_testing import (
    EOA,
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
    ["state_tests/stRandom/randomStatetest367Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest367(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest367."""
    coinbase = Address(0x945304EB96065B2A98B57A48A06AE28D285A71B5)
    contract_0 = Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87)
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

    # Source: raw
    # 0x7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f0000000000000000000000000000000000000000000000000000000000000000447f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b5447f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b51905810a6c7a5959339f3342838b5560005155  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5]
        + Op.PUSH32[0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF]
        + Op.PUSH32[0x0]
        + Op.PREVRANDAO
        + Op.PUSH32[0xC350]
        + Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5]
        + Op.SSTORE(
            key=0x7A5959339F3342838B55600051,
            value=Op.EXP(
                Op.DUP2,
                Op.SDIV(
                    Op.NOT(
                        Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5]
                    ),
                    Op.PREVRANDAO,
                ),
            ),
        ),
        nonce=0,
        address=Address(0x095E7BAEA6A6C7C4C2DFEB977EFAC326AF552D87),  # noqa: E501
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
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(
            "7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f0000000000000000000000000000000000000000000000000000000000000000447f000000000000000000000000000000000000000000000000000000000000c3507f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b5447f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b51905810a6c7a5959339f3342838b"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x2BC3D730,
    )

    post = {
        contract_0: Account(
            storage={
                0x7A5959339F3342838B55600051: 0x880AD67C991058B3847EC9F491F7A8D6ECBB1DFF5C2326E7E8E9EB560CA29ECD,  # noqa: E501
            },
            nonce=0,
        ),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
