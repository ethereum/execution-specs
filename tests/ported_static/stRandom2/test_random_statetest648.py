"""
Consensus issue test produced by fuzz testing team 00000005-storagefuzz-1

Ported from:
state_tests/stRandom2/randomStatetest648Filler.json
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
    ["state_tests/stRandom2/randomStatetest648Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest648(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Consensus issue test produced by fuzz testing team 00000005-storage..."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xff348633b687ec0f553647f4ddeed7590e90c7ea65b87c5bd399f4c869b9c9fc
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10944489199640098,
    )

    # Source: raw
    # 0x600060006000600060f15af450600060005060f5fffd
    target = pre.deploy_contract(
        code=Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=0xf1, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.PUSH1[0x0] + Op.POP(0x0) + Op.SELFDESTRUCT(address=0xf5) + Op.REVERT,
        nonce=0,
        address=Address("0xca5c69fa03b9dff4d059971ac17edac7ef758725"),  # noqa: E501
    )
    # Source: raw
    # 0x600050
    addr_0x00000000000000000000000000000000000000f5 = pre.deploy_contract(
        code=Op.POP(0x0),
        nonce=0,
        address=Address("0xa828265d4b2db08e65a1c68d2878f15368b5ae75"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xffffffff)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("384c289327fda733f319011b605929b98b6cc52e4915c942369264c71a3ca70ebce56fef7e41103f1acc71e91f299bf6c5730b265d6f9d475936735ea60c58b9bb125a78178171784759606d696e98f8522b52fe213edee397b3df6ca9f0c6"),  # noqa: E501
        gas_limit=343469,
        value=0xdb2206,
        nonce=0,
        gas_price=10,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
