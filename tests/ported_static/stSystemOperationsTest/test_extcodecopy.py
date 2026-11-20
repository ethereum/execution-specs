"""
God knows what is happening in this test.

Ported from:
state_tests/stSystemOperationsTest/extcodecopyFiller.json

@manually-enhanced: Do not overwrite. Addresses unpinned.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSystemOperationsTest/extcodecopyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_extcodecopy(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """God knows what is happening in this test."""
    sender = pre.fund_eoa()

    target = pre.deploy_contract(
        code=Op.PUSH32[
            0x15688566A82F5F946C68028BF626B349E495DAA43E33529A76437AC416CD1B7D
        ]
        + Op.MOD(
            0xCEA0C5CC171FA61277E5604A3BC8AEF4DE3D3882,
            0x7DAE7454BB193B1C28E64A6A935BC3,
        )
        + Op.EXTCODECOPY(
            address=0x7ADA6E82E95F6520383F95F5C7DAE56B4DC13B6F22ECABFCE07C,
            dest_offset=Op.DUP1,
            offset=0xB,
            size=Op.PC,
        )
        + Op.SELFDESTRUCT
        + Op.MLOAD,
        balance=0x5C81EB0,
        nonce=254,
    )
    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "6e27b0577f2549e5fa01e3db96e7b03a62e489115538620295677faf15040c1c1796bad130e2462a8b8d6bbe0fa35bf12087047ef4ff4e66df8772196b4401998ff7f4219c013a0d927b22d8d3fdf625809abb182507d180e687b666f4f1e4f3b8172e87760f436c701264b89739f3d7c50ec524f16b1a4f91397b760a5209b9b7710544694ecf2729643b3ca545c7"  # noqa: E501
        ),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
        value=0x24A39757,
    )

    post = {
        Address(0x00000000002147C39FD6B5C19B7B89FC003E6B16): Account(
            storage={}, nonce=0
        ),
        sender: Account(storage={}, nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
