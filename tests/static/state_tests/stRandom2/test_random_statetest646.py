"""
Geth Failed this test on all networks

Ported from:
tests/static/state_tests/stRandom2/randomStatetest646Filler.json

contract code:
    push5 0xba8b878e01
    sload
    push9 0x9b908f27acb42e5269
    push1 0x39
    push19 0x609834bf9a7e578e45609242172907dd75a925
    sstore
    push6 0x6c5aa6e92481
    push3 0x013ffa
    push3 0x038648
    push4 0x446d325d
    create
    caller
    push14 0x2c38cfa2f1cdf8cb623c05919874
    not
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
    ["tests/static/state_tests/stRandom2/randomStatetest646Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest646(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Geth Failed this test on all networks."""
    coinbase = Address("0xd94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xffffffffffffffffffffffffffffffffffffffff")
    callee = Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=18857228215205537,
    )

    pre[sender] = Account(balance=0x54465ef1c769628b, nonce=0)
    pre[callee] = Account(balance=0x33888d4ce6b934, nonce=7)
    pre[contract] = Account(
        balance=0xd61773f0c27b842f,
        nonce=28,
        code=(
        Op.PUSH5[0xba8b878e01] + Op.SLOAD + Op.PUSH9[0x9b908f27acb42e5269]
        + Op.PUSH1[0x39] + Op.PUSH19[0x609834bf9a7e578e45609242172907dd75a925]
        + Op.SSTORE + Op.PUSH6[0x6c5aa6e92481] + Op.PUSH3[0x13ffa] + Op.PUSH3[0x38648]
        + Op.PUSH4[0x446d325d] + Op.CREATE + Op.CALLER
        + Op.PUSH14[0x2c38cfa2f1cdf8cb623c05919874] + Op.NOT
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=bytes.fromhex(
            "785196fdcb5d7e54c4b381e68c7eaeae2735e5537830130057f554672e70a6b867385ea2"
            "714ea3185b854bf0b4f9617fb47e6afe9ed4ed68f94b50776420fa24010960ce6b65e2a1"
            "ebdce518181d6c69a678989d767fc3d28b6c524f52a87d05519cb32e38fbdc5f801f7569"
            "22b90c0e2e5bc848bb9c6a5d08ee65470af4fbbeacf87a65c90dc57babd8cdc9819f8985"
            "51925828bfd360e8a1f1616619d171c23004b0045424cc962e09d8a65d9fd94af9863d61"
            "eba97d76dc150e19d991ff1b5fd340dd4fd7e522a659ddf69bcbc729599667aa30536cd8"
            "5576cc3477495dae10c85b56"
        ),
        gas_limit=5786929,
        gas_price=10,
        nonce=0,
        value=1451538698,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
