"""
Account attempts to send tx to create a contract on a non-empty address.

Ported from:
state_tests/stEIP3607/initCollidingWithNonEmptyAccountFiller.yml
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
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP3607/initCollidingWithNonEmptyAccountFiller.yml"],
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
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_init_colliding_with_non_empty_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Account attempts to send tx to create a contract on a non-empty..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x6295EE1B4F6DD65047762F924ECD367C17EABF8F)
    contract_1 = Address(0xD0D0D0D0D0D0D0D0D0D0D0D0D0D0D0D0D0D0D0D0)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw
    # 0x6000600155
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x0),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x6295EE1B4F6DD65047762F924ECD367C17EABF8F),  # noqa: E501
    )
    # Source: raw
    # 0x00
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.STOP,
        nonce=0,
        address=Address(0xD0D0D0D0D0D0D0D0D0D0D0D0D0D0D0D0D0D0D0D0),  # noqa: E501
    )

    tx_data = [
        Op.RETURN(offset=0x0, size=0x20),
        Op.SSTORE(key=0x0, value=0x1)
        + Op.CALL(
            gas=Op.GAS,
            address=contract_1,
            value=0x2710,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.SSTORE(key=0x0, value=0x1)
        + Op.CREATE2(value=0x2710, offset=Op.DUP2, size=0x20, salt=0x0)
        + Op.STOP,
        Op.SSTORE(key=0x0, value=0x1)
        + Op.CREATE(value=0x2710, offset=0x0, size=0x20)
        + Op.STOP,
        Op.SSTORE(key=0x0, value=0x1)
        + Op.DELEGATECALL(
            gas=Op.GAS,
            address=contract_1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
    ]
    tx_gas = [400000]
    tx_value = [100000]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
    )

    post = {
        contract_0: Account(
            storage={},
            code=bytes.fromhex("6000600155"),
            balance=0xDE0B6B3A7640000,
            nonce=0,
        ),
        contract_1: Account(balance=0),
        Address(
            0x05CD8493115C3299094A269E839E2F5F25691785
        ): Account.NONEXISTENT,
        compute_create_address(
            address=contract_0, nonce=0
        ): Account.NONEXISTENT,
        sender: Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
