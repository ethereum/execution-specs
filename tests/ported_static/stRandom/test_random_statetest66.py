"""
test_random_statetest66

Ported from:
state_tests/stRandom/randomStatetest66Filler.json
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
    ["state_tests/stRandom/randomStatetest66Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest66(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_random_statetest66"""
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
    # 0x457fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff417fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe097f000000000000000000000001000000000000000000000000000000000000000055
    contract_0 = pre.deploy_contract(
        code=Op.GASLIMIT
        + Op.PUSH32[0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff]
        + Op.COINBASE
        + Op.SSTORE(key=Op.PUSH32[0x10000000000000000000000000000000000000000], value=Op.MULMOD(0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe, Op.PUSH32[0x945304eb96065b2a98b57a48a06ae28d285a71b5], 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)),  # noqa: E501
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
        data=bytes.fromhex("457fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff417fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b57ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe097f0000000000000000000000010000000000000000000000000000000000000000"),  # noqa: E501
        gas_limit=100000,
        value=0x2f5660ce,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(
                storage={
            0x10000000000000000000000000000000000000000: 0xffffffffffffffffffffffff6bacfb1469f9a4d5674a85b75f951d72d7a58e4a,
        },
                nonce=0,
            ),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
