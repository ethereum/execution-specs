"""
Test_random_statetest372.

Ported from:
state_tests/stRandom/randomStatetest372Filler.json
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
    ["state_tests/stRandom/randomStatetest372Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest372(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest372."""
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
    # 0x7f00000000000000000000000000000000000000000000000000000000000000017ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f00000000000000000000000100000000000000000000000000000000000000007f00000000000000000000000100000000000000000000000000000000000000007f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f0000000000000000000000000000000000000000000000000000000000000001180860005155  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH32[0x1]
        + Op.PUSH32[
            0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE
        ]
        + Op.PUSH32[0x10000000000000000000000000000000000000000] * 2
        + Op.SSTORE(
            key=Op.MLOAD(offset=0x0),
            value=Op.ADDMOD(
                Op.XOR(
                    Op.PUSH32[0x1],
                    Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5],
                ),
                Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5],
                Op.PUSH32[0x945304EB96065B2A98B57A48A06AE28D285A71B5],
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
            "7f00000000000000000000000000000000000000000000000000000000000000017ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f00000000000000000000000100000000000000000000000000000000000000007f00000000000000000000000100000000000000000000000000000000000000007f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f00000000000000000000000000000000000000000000000000000000000000011808"  # noqa: E501
        ),
        gas_limit=100000,
        value=0x6D4BEA09,
    )

    post = {
        contract_0: Account(
            storage={0: 0x945304EB96065B2A98B57A48A06AE28D285A71B4},
            nonce=0,
        ),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
