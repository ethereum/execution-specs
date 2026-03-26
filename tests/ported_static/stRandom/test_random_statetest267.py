"""
test_random_statetest267

Ported from:
state_tests/stRandom/randomStatetest267Filler.json
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
    ["state_tests/stRandom/randomStatetest267Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest267(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_random_statetest267"""
    coinbase = Address("0x945304eb96065b2a98b57a48a06ae28d285a71b5")
    contract_0 = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
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
    # 0x447f000000000000000000000000000000000000000000000000000000000000c3507ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f00000000000000000000000100000000000000000000000000000000000000007f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f00000000000000000000000000000000000000000000000000000000000000007e7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b5a132776d398e3b7c14686a07346f60005155
    contract_0 = pre.deploy_contract(
        code=Op.PREVRANDAO + Op.PUSH32[0xc350]
        + Op.PUSH32[0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe]
        + Op.PUSH32[0x10000000000000000000000000000000000000000]
        + Op.PUSH32[0x945304eb96065b2a98b57a48a06ae28d285a71b5] + Op.PUSH32[0x0]
        + Op.SSTORE(key=0xb5a132776d398e3b7c14686a07346f600051, value=0x7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a),  # noqa: E501
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    # Source: raw
    # 0x6000355415600957005b60203560003555
    coinbase = pre.deploy_contract(
        code=Op.JUMPI(pc=0x9, condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))))  # noqa: E501
        + Op.STOP + Op.JUMPDEST
        + Op.SSTORE(key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)),  # noqa: E501
        balance=46,
        nonce=0,
        address=Address("0x945304eb96065b2a98b57a48a06ae28d285a71b5"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=bytes.fromhex("447f000000000000000000000000000000000000000000000000000000000000c3507ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f00000000000000000000000100000000000000000000000000000000000000007f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57f00000000000000000000000000000000000000000000000000000000000000007e7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b5a132776d398e3b7c14686a07346f"),  # noqa: E501
        gas_limit=100000,
        value=0xf5106ae,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(
                storage={
            0xb5a132776d398e3b7c14686a07346f600051: 0x7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a,
        },
                nonce=0,
            ),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
