"""
Ported from:
tests/static/state_tests/stRevertTest/RevertSubCallStorageOOGFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRevertTest/RevertSubCallStorageOOGFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, tx_value",
    [
        (81000, 0),
        (81000, 1),
        (181000, 0),
        (181000, 1),
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_revert_sub_call_storage_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0xdfa0378009e95c6b0e668db83477627c9b1e5d01")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=1,
        nonce=0,
        code=bytes.fromhex(
        "60606040526000357c010000000000000000000000000000000000000000000000000000"
        "0000900463ffffffff168063b28175c4146046578063c0406226146052575b6000565b34"
        "60005760506076565b005b34600057605c6081565b604051808215151515815260200191"
        "505060405180910390f35b600c6000819055505b565b600060896076565b600d60018190"
        "5550600e600281905550600190505b905600a165627a7a723058202a8a75d7d795b5bcb9"
        "042fb18b283daa90b999a11ddec892f548732235342eb60029"
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
