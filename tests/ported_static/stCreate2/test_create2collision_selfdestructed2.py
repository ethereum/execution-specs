"""
A contract which performs SUICIDE, and is then attempted to be...

Ported from:
state_tests/stCreate2/create2collisionSelfdestructed2Filler.json

@manually-enhanced: Do not overwrite. The inner CALL's gas budget was
raised from 0xC350 to 0x40000 and the outer tx gas from 400 000 to
1 000 000 so the SELFDESTRUCT-to-empty path can afford its EIP-8037
NEW_ACCOUNT state gas on Amsterdam (the test's intent — exercising
CREATE2 collision against a freshly self-destructed address — is
preserved on all forks).
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
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreate2/create2collisionSelfdestructed2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.valid_before("EIP8368")
def test_create2collision_selfdestructed2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """A contract which performs SUICIDE, and is then attempted to be..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xFCE41D047B4A1D4450382DCC29EC7E5FEDC5F9A3)
    contract_1 = Address(0xCFF64F4C5DF8F436C4F2C1AF4B2E3F9E3004C779)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: lll
    # { (SELFDESTRUCT 0x10) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=0x10) + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0xFCE41D047B4A1D4450382DCC29EC7E5FEDC5F9A3),  # noqa: E501
    )
    # Source: raw
    # 0x6010ff
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=0x10),
        balance=1,
        nonce=1,
        address=Address(0xCFF64F4C5DF8F436C4F2C1AF4B2E3F9E3004C779),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={},
                    code=bytes.fromhex("6010ff00"),
                    balance=0,
                    nonce=0,
                ),
                Address(0x0000000000000000000000000000000000000010): Account(
                    balance=1
                ),
                sender: Account(nonce=1),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_1: Account(balance=0, nonce=1),
                Address(0x0000000000000000000000000000000000000010): Account(
                    balance=1
                ),
                sender: Account(nonce=1),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    # EIP-8037 NEW_ACCOUNT state-gas pushes both the outer tx and the
    # inner CALL over their original budgets on Amsterdam. Pre-EIP-8037
    # forks keep the original tuned values.
    inner_call_gas = 0xC350
    outer_tx_gas = 400_000
    if fork.is_eip_enabled(8037):
        inner_call_gas = 0x40000
        outer_tx_gas = 1_000_000

    tx_data = [
        Op.POP(
            Op.CALL(
                gas=inner_call_gas,
                address=contract_0,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x620102036000526003601DF3)
        + Op.CREATE2(value=0x0, offset=0x14, size=0xC, salt=0x0)
        + Op.STOP,
        Op.POP(
            Op.CALL(
                gas=inner_call_gas,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x626010FF6000526003601DF3)
        + Op.CREATE2(value=0x0, offset=0x14, size=0xC, salt=0x0)
        + Op.STOP,
    ]
    tx_gas = [outer_tx_gas]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
