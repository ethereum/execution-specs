"""
Consensus issue test produced by fuzz testing team 00000005-storagefuzz-1.

Ported from:
state_tests/stRandom2/randomStatetest648Filler.json
"""

import pytest
from execution_testing import (
    EOA,
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
    ["state_tests/stRandom2/randomStatetest648Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest648(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Consensus issue test produced by fuzz testing team..."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0xFF348633B687EC0F553647F4DDEED7590E90C7EA65B87C5BD399F4C869B9C9FC
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10944489199640098,
    )

    # Source: raw
    # 0x600060006000600060f15af450600060005060f5fffd
    target = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.DELEGATECALL(
                gas=Op.GAS,
                address=0xF1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.PUSH1[0x0]
        + Op.POP(0x0)
        + Op.SELFDESTRUCT(address=0xF5)
        + Op.REVERT,
        nonce=0,
        address=Address(0xCA5C69FA03B9DFF4D059971AC17EDAC7EF758725),  # noqa: E501
    )
    # Source: raw
    # 0x600050
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.POP(0x0),
        nonce=0,
        address=Address(0xA828265D4B2DB08E65A1C68D2878F15368B5AE75),  # noqa: E501
    )
    pre[sender] = Account(balance=0xFFFFFFFF)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "384c289327fda733f319011b605929b98b6cc52e4915c942369264c71a3ca70ebce56fef7e41103f1acc71e91f299bf6c5730b265d6f9d475936735ea60c58b9bb125a78178171784759606d696e98f8522b52fe213edee397b3df6ca9f0c6"  # noqa: E501
        ),
        gas_limit=343469,
        value=0xDB2206,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
