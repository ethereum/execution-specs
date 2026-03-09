"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom/randomStatetest184Filler.json
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
    ["tests/static/state_tests/stRandom/randomStatetest184Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest184(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x6d6e40885310545835a5b582dbc23ef026404bda")
    sender = EOA(
        key=0x382ACD382CC7A37BB6A57C4A171F216EF77EF04EBD5E6C0744EE5C90B0D962EF
    )
    callee = Address("0xf377657e450772b703a269e12bb487ff421a5c6d")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=10000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=69449279085,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x8C, value=0x823A02877CEF7C1AFB60663009DEF564)
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
            )
        ),
        balance=0x70A217C02C8F2D4,
        nonce=117,
        address=Address("0x898207f2d9b9fb11cec9647a70e9390711732daa"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x10C1142F2B8E8EB058)
    pre[callee] = Account(balance=0x9740421FF0FF3AE3, nonce=29)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("64dd3e4e84676723342c1dfaf9af4ef3"),
        gas_limit=100000,
        gas_price=28,
        value=1830670372,
    )

    post = {
        contract: Account(storage={140: 0x823A02877CEF7C1AFB60663009DEF564}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
