"""
Ported from:
tests/static/state_tests/stExtCodeHash/extCodeHashPrecompilesFiller.yml

contract code:
    push1 0x14
    push1 0x00
    push1 0x0c
    calldatacopy
    push1 0x00
    mload
    extcodehash
    push1 0x00
    sstore
    push1 0x00
    mload
    extcodesize
    push1 0x01
    sstore
    stop
"""

import pytest
from execution_testing import (
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashPrecompilesFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "095e7baea6a6c7c4c2dfeb977efac326af552d87",
        "0000000000000000000000000000000000000001",
        "0000000000000000000000000000000000000002",
        "0000000000000000000000000000000000000003",
        "0000000000000000000000000000000000000004",
        "0000000000000000000000000000000000000005",
        "0000000000000000000000000000000000000006",
        "0000000000000000000000000000000000000007",
        "0000000000000000000000000000000000000008",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8'],
)
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_precompiles(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x14] + Op.PUSH1[0x0] + Op.PUSH1[0xc] + Op.CALLDATACOPY
        + Op.PUSH1[0x0] + Op.MLOAD + Op.EXTCODEHASH + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH1[0x0] + Op.MLOAD + Op.EXTCODESIZE + Op.PUSH1[0x1] + Op.SSTORE
        + Op.STOP
    ),
        storage={0x0: 0xab, 0x1: 0xab},
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
