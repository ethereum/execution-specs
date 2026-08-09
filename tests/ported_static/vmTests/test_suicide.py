"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmTests/suicideFiller.yml

@manually-enhanced: Do not overwrite. For the `caller` case the post-state
asserts the sender balance, which equals its start minus
`gas_used * gas_price`. The transaction calls a contract that CALLs a
cold, existing account (slot 0x1000) before it self-destructs; EIP-8038
raises the cold account-access surcharge on that CALL from 2600 to 3000.
The SELFDESTRUCT itself is to a warm, non-empty beneficiary (the caller),
so its charge is unchanged, and there is no refund. Derive the
account-access delta from the fork gas model (0 pre-EIP-8037) and
subtract `gas_price * delta` from the Cancun balance; do not hardcode the
Amsterdam value. The `random` and `myself` cases assert only
non-gas-dependent balances and need no adjustment.
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
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmTests/suicideFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="caller",
        ),
        pytest.param(
            1,
            0,
            0,
            id="random",
        ),
        pytest.param(
            2,
            0,
            0,
            id="myself",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_suicide(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x0000000000000000000000000000000000001000)
    contract_1 = Address(0x0000000000000000000000000000000000001001)
    contract_2 = Address(0x0000000000000000000000000000000000001002)
    contract_3 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0x5AF3107A4000)
    # Source: lll
    # {
    #    (selfdestruct (caller))
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=Op.CALLER) + Op.STOP,
        balance=0xFF000000000000,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: lll
    # {
    #    (selfdestruct 0xdead)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=0xDEAD) + Op.STOP,
        balance=0x100000000000,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001001),  # noqa: E501
    )
    # Source: lll
    # {
    #    (selfdestruct (address))
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(address=Op.ADDRESS) + Op.STOP,
        balance=0x100000000000,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001002),  # noqa: E501
    )
    # Source: lll
    # {
    #    (call (gas) $4 0 0 0 0 0)
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=Op.GAS,
            address=Op.CALLDATALOAD(offset=0x4),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0x100000000000,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )

    # The CALL into the self-destructing contract touches a cold, already
    # existing account; EIP-8038 raises that cold account-access surcharge
    # from 2600 to 3000. The SELFDESTRUCT beneficiary is warm and
    # non-empty, so its charge is unchanged. EIP-2780 separately reshapes
    # the tx intrinsic for this non-self non-value call. The sender pays
    # the combined delta at the base fee (no priority fee).
    cold_account_access_delta = fork.gas_costs().COLD_ACCOUNT_ACCESS - 2600
    intrinsic_delta = fork.transaction_intrinsic_cost_calculator()() - 21_000
    caller_balance = (
        0x5AF31075D9DE - 10 * cold_account_access_delta - 10 * intrinsic_delta
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(balance=caller_balance),
                contract_3: Account(balance=0xFF100000000000),
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0x000000000000000000000000000000000000DEAD): Account(
                    balance=0x100000000000
                ),
            },
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_3: Account(balance=0x100000000000)},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(contract_0, left_padding=True),
        Bytes("693c6139") + Hash(contract_1, left_padding=True),
        Bytes("693c6139") + Hash(contract_2, left_padding=True),
    ]
    tx_gas = [16777216]

    tx = Transaction(
        sender=sender,
        to=contract_3,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
