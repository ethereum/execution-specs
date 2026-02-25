"""
Ported from:
tests/static/state_tests/stRevertTest/NashatyrevSuicideRevertFiller.json
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
    ["tests/static/state_tests/stRevertTest/NashatyrevSuicideRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_nashatyrev_suicide_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0xd926bbc3745f0070528fc04cbfd3a2c9f9ca6a19")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=bytes.fromhex(
        "60606040526000357c010000000000000000000000000000000000000000000000000000"
        "0000900463ffffffff1680639c3674fc14610049578063c040622614610058575b610000"
        "565b3461000057610056610067565b005b3461000057610065610147565b005b60006040"
        "5160a680610200833901809050604051809103906000f080156100005790508073ffffff"
        "ffffffffffffffffffffffffffffffffff1660405180807f662829000000000000000000"
        "000000000000000000000000000000000000000081525060030190506040518091039020"
        "7c0100000000000000000000000000000000000000000000000000000000900460405181"
        "63ffffffff167c0100000000000000000000000000000000000000000000000000000000"
        "0281526004018090506000604051808303816000876161da5a03f1925050505061000056"
        "5b50565b3073ffffffffffffffffffffffffffffffffffffffff1660405180807f626164"
        "282900000000000000000000000000000000000000000000000000000081525060050190"
        "5060405180910390207c0100000000000000000000000000000000000000000000000000"
        "00000090046040518163ffffffff167c0100000000000000000000000000000000000000"
        "0000000000000000000281526004018090506000604051808303816000876161da5a03f1"
        "92505050505b56006060604052346000575b608f806100176000396000f3006060604052"
        "6000357c0100000000000000000000000000000000000000000000000000000000900463"
        "ffffffff16806326121ff014603c575b6000565b3460005760466048565b005b3373ffff"
        "ffffffffffffffffffffffffffffffffffff16ff5b5600a165627a7a723058203d1a897b"
        "efde21eff26abc325fb3da2f526bbc99de1c5c857d1835f673744ebd0029a165627a7a72"
        "305820850a52b31ec4745b7af15ba3bffdb1ba17f5d9a00a5f263ee287a92b568f534c00"
        "29"
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=500000,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
