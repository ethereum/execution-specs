"""
Geth Failed this test on all networks.

Ported from:
state_tests/stRandom2/randomStatetest646Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom2/randomStatetest646Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest646(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Geth Failed this test on all networks."""
    coinbase = Address(0xD94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_0 = Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=18857228215205537,
    )

    pre[sender] = Account(balance=0x54465EF1C769628B)
    pre[contract_0] = Account(balance=0x33888D4CE6B934, nonce=7)
    # Source: raw
    # 0x64ba8b878e0154689b908f27acb42e5269603972609834bf9a7e578e45609242172907dd75a92555656c5aa6e9248162013ffa6203864863446d325df0336d2c38cfa2f1cdf8cb623c0591987419  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SLOAD(key=0xBA8B878E01)
        + Op.PUSH9[0x9B908F27ACB42E5269]
        + Op.SSTORE(key=0x609834BF9A7E578E45609242172907DD75A925, value=0x39)
        + Op.PUSH6[0x6C5AA6E92481]
        + Op.CREATE(value=0x446D325D, offset=0x38648, size=0x13FFA)
        + Op.CALLER
        + Op.NOT(0x2C38CFA2F1CDF8CB623C05919874),
        balance=0xD61773F0C27B842F,
        nonce=28,
        address=Address(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=Bytes("785196fd")
        + Hash(
            0xCB5D7E54C4B381E68C7EAEAE2735E5537830130057F554672E70A6B867385EA2
        )
        + Hash(
            0x714EA3185B854BF0B4F9617FB47E6AFE9ED4ED68F94B50776420FA24010960CE
        )
        + Hash(
            0x6B65E2A1EBDCE518181D6C69A678989D767FC3D28B6C524F52A87D05519CB32E
        )
        + Hash(
            0x38FBDC5F801F756922B90C0E2E5BC848BB9C6A5D08EE65470AF4FBBEACF87A65
        )
        + Hash(
            0xC90DC57BABD8CDC9819F898551925828BFD360E8A1F1616619D171C23004B004
        )
        + Hash(
            0x5424CC962E09D8A65D9FD94AF9863D61EBA97D76DC150E19D991FF1B5FD340DD
        )
        + Hash(
            0x4FD7E522A659DDF69BCBC729599667AA30536CD85576CC3477495DAE10C85B56
        ),
        gas_limit=5786929,
        value=0x5684B90A,
    )

    post = {
        sender: Account(storage={}, code=b"", nonce=1),
        compute_create_address(
            address=contract_1, nonce=28
        ): Account.NONEXISTENT,
        contract_0: Account(storage={}, code=b"", nonce=7),
        contract_1: Account(storage={}, nonce=28),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
