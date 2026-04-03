"""
Test_random_statetest368.

Ported from:
state_tests/stRandom/randomStatetest368Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest368Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest368(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_random_statetest368."""
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
    # 0x7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000007ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe097f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b54206f06d870339356057907760005155  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex(
            "7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000007ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe097f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b54206f06d870339356057907760005155"  # noqa: E501
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
            "7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7f00000000000000000000000000000000000000000000000000000000000000007ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe7f000000000000000000000000ffffffffffffffffffffffffffffffffffffffff7ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe097f00000000000000000000000000000000000000000000000000000000000000007f000000000000000000000000945304eb96065b2a98b57a48a06ae28d285a71b54206f06d8703393560579077"  # noqa: E501
        ),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
        value=0x43AC3494,
    )

    post = {
        contract_0: Account(storage={}, nonce=1),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
        compute_create_address(address=contract_0, nonce=0): Account(
            storage={}, code=b"", balance=1000, nonce=1
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
