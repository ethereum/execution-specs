"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
tests/static/state_tests/stEIP2930/coinbaseT2Filler.yml

contract code:
    gas
    push1 0x00
    mstore
    push1 0x00
    dup1
    dup1
    dup1
    push3 0x0f4240
    push20 0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3
    gas
    call
    pop
    gas
    push1 0x20
    mstore
    push1 0x21
    push1 0x20
    mload
    push1 0x00
    mload
    ... (5 more instructions)
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stEIP2930/coinbaseT2Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_access_list",
    [
        [AccessList(address=Address("0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3"), storage_keys=[])],
        [AccessList(address=Address("0x000000000000000000000000000000000000ba5a"), storage_keys=[])],
    ],
    ids=['case0', 'case1'],
)
@pytest.mark.pre_alloc_mutable
def test_coinbase_t2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_access_list,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3")
    sender = Address("0x8dab845a8398167a1c204f0e79540d619be8b473")
    contract = Address("0x30873f83c35401e315e6e5994c012f1ee8119585")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=100,
        gas_limit=71794957647893862,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=1,
        code=(
        Op.GAS + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP1
        + Op.DUP1 + Op.PUSH3[0xf4240]
        + Op.PUSH20[0x7704d8a022a1ba8f3539fc82c7d7fb065abc0df3] + Op.GAS + Op.CALL
        + Op.POP + Op.GAS + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x21]
        + Op.PUSH1[0x20] + Op.MLOAD + Op.PUSH1[0x0] + Op.MLOAD + Op.SUB + Op.SUB
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)

    tx = Transaction(
        secret_key=Hash(
            "0xde0c95357363da5c1c5a73bd7c2781ca5c9fecc1014103b5e1d1e990ae8208ec"
        ),
        to=contract,
        data=bytes.fromhex("693c61390000000000000000000000000000000000000000000000000000000000000000"),
        gas_limit=16777216,
        max_fee_per_gas=10000,
        max_priority_fee_per_gas=100,
        nonce=1,
        value=0,
        access_list=tx_access_list,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
