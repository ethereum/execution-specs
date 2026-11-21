"""
Test_random_statetest184.

Ported from:
state_tests/stRandom/randomStatetest184Filler.json

@manually-enhanced: Do not overwrite. tx `gas_limit` has been removed.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest184Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.execute(pytest.mark.skip(reason="needs a high-nonce contract"))
def test_random_statetest184(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest184."""
    coinbase = Address(0x6D6E40885310545835A5B582DBC23EF026404BDA)
    sender = pre.fund_eoa(amount=0x10C1142F2B8E8EB058)

    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x8C, value=0x823A02877CEF7C1AFB60663009DEF564)
        + Op.SUB(
            0xE130184B64F2507582C502D450349FF24FB8AEB2A46146687B666BD7BD,
            0xAD2AE05769B991313726EDBFA0881D9CC955B0F5154751DA315696EA,
        )
        + Op.PUSH5[0x946CB720C7]
        + Op.PUSH14[0x483F5AFEA0049251FD9793C4B037]
        + Op.PUSH11[0xFBB4EBCDC42FDD42EDCD4B]
        + Op.PUSH2[0x9CEC]
        + Op.PUSH25[0x7638009CEA26A1ABE570E3186AB790B7DC7DB36E4CDA2570B0]
        + Op.DUP5
        + Op.DIV(
            0xD34A4B816B80,
            0xDF6E39579C7C43A4AC976CD507D493CDFAEBE09936078E31C71C46,
        ),
        balance=0x70A217C02C8F2D4,
        nonce=117,
    )

    env = Environment(
        fee_recipient=coinbase, timestamp=10000, prev_randao=0x20000
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("64dd3e4e84676723342c1dfaf9af4ef3"),
        value=0x6D1DD024,
        gas_price=28,
    )

    post = {
        target: Account(
            storage={140: 0x823A02877CEF7C1AFB60663009DEF564},
            nonce=117,
        ),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
