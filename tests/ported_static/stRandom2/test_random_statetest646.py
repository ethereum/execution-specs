"""
Geth Failed this test on all networks.

Ported from:
tests/static/state_tests/stRandom2/randomStatetest646Filler.json
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
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )
    callee = Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=18857228215205537,
    )

    pre[sender] = Account(balance=0x54465EF1C769628B)
    pre[callee] = Account(balance=0x33888D4CE6B934, nonce=7)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.SLOAD(key=0xBA8B878E01)
            + Op.PUSH9[0x9B908F27ACB42E5269]
            + Op.SSTORE(
                key=0x609834BF9A7E578E45609242172907DD75A925, value=0x39
            )
            + Op.PUSH6[0x6C5AA6E92481]
            + Op.CREATE(value=0x446D325D, offset=0x38648, size=0x13FFA)
            + Op.CALLER
            + Op.NOT(0x2C38CFA2F1CDF8CB623C05919874)
        ),
        balance=0xD61773F0C27B842F,
        nonce=28,
        address=Address("0xffffffffffffffffffffffffffffffffffffffff"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "785196fdcb5d7e54c4b381e68c7eaeae2735e5537830130057f554672e70a6b867385ea2"  # noqa: E501
            "714ea3185b854bf0b4f9617fb47e6afe9ed4ed68f94b50776420fa24010960ce6b65e2a1"  # noqa: E501
            "ebdce518181d6c69a678989d767fc3d28b6c524f52a87d05519cb32e38fbdc5f801f7569"  # noqa: E501
            "22b90c0e2e5bc848bb9c6a5d08ee65470af4fbbeacf87a65c90dc57babd8cdc9819f8985"  # noqa: E501
            "51925828bfd360e8a1f1616619d171c23004b0045424cc962e09d8a65d9fd94af9863d61"  # noqa: E501
            "eba97d76dc150e19d991ff1b5fd340dd4fd7e522a659ddf69bcbc729599667aa30536cd8"  # noqa: E501
            "5576cc3477495dae10c85b56"
        ),
        gas_limit=5786929,
        value=1451538698,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
