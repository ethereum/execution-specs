"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/NashatyrevSuicideRevertFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stRevertTest/NashatyrevSuicideRevertFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_nashatyrev_suicide_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=bytes.fromhex(
            "60606040526000357c010000000000000000000000000000000000000000000000000000"  # noqa: E501
            "0000900463ffffffff1680639c3674fc14610049578063c040622614610058575b610000"  # noqa: E501
            "565b3461000057610056610067565b005b3461000057610065610147565b005b60006040"  # noqa: E501
            "5160a680610200833901809050604051809103906000f080156100005790508073ffffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffff1660405180807f662829000000000000000000"  # noqa: E501
            "000000000000000000000000000000000000000081525060030190506040518091039020"  # noqa: E501
            "7c0100000000000000000000000000000000000000000000000000000000900460405181"  # noqa: E501
            "63ffffffff167c0100000000000000000000000000000000000000000000000000000000"  # noqa: E501
            "0281526004018090506000604051808303816000876161da5a03f1925050505061000056"  # noqa: E501
            "5b50565b3073ffffffffffffffffffffffffffffffffffffffff1660405180807f626164"  # noqa: E501
            "282900000000000000000000000000000000000000000000000000000081525060050190"  # noqa: E501
            "5060405180910390207c0100000000000000000000000000000000000000000000000000"  # noqa: E501
            "00000090046040518163ffffffff167c0100000000000000000000000000000000000000"  # noqa: E501
            "0000000000000000000281526004018090506000604051808303816000876161da5a03f1"  # noqa: E501
            "92505050505b56006060604052346000575b608f806100176000396000f3006060604052"  # noqa: E501
            "6000357c0100000000000000000000000000000000000000000000000000000000900463"  # noqa: E501
            "ffffffff16806326121ff014603c575b6000565b3460005760466048565b005b3373ffff"  # noqa: E501
            "ffffffffffffffffffffffffffffffffffff16ff5b5600a165627a7a723058203d1a897b"  # noqa: E501
            "efde21eff26abc325fb3da2f526bbc99de1c5c857d1835f673744ebd0029a165627a7a72"  # noqa: E501
            "305820850a52b31ec4745b7af15ba3bffdb1ba17f5d9a00a5f263ee287a92b568f534c00"  # noqa: E501
            "29"
        ),
        nonce=0,
        address=Address("0xd926bbc3745f0070528fc04cbfd3a2c9f9ca6a19"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=500000,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
