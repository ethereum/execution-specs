"""
Test_create2_contract_suicide_during_init_then_store_then_return.

Ported from:
state_tests/stCreate2/CREATE2_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json

@manually-enhanced: Do not overwrite. The inner CALL gas was raised
from 0x249F0 to 0x100000 and the tx gas_limit from 600 000 to
5 000 000 so the nested CREATE2 + init-code SELFDESTRUCT to address
0x01 can afford its EIP-8037 NEW_ACCOUNT state gas on Amsterdam
(post-state expectations are unchanged on all forks).
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCreate2/CREATE2_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_create2_contract_suicide_during_init_then_store_then_return(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_create2_contract_suicide_during_init_then_store_then_return."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # EIP-8037 NEW_ACCOUNT state-gas on Amsterdam pushes both the inner
    # CALL and the outer tx over the original budgets; pre-EIP-8037
    # forks keep the values the original filler was tuned for.
    inner_call_gas = 0x249F0
    tx_gas_limit = 600_000
    if fork.is_eip_enabled(8037):
        inner_call_gas = 0x100000
        tx_gas_limit = 5_000_000
    # Source: lll
    # { (MSTORE 0 0x6d64600c6000556000526005601bf36000526001ff) (CREATE2 1 11 21 0) [[0]] 11 (RETURN 18 14) }  # noqa: E501
    contract_1 = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0, value=0x6D64600C6000556000526005601BF36000526001FF
        )
        + Op.POP(Op.CREATE2(value=0x1, offset=0xB, size=0x15, salt=0x0))
        + Op.SSTORE(key=0x0, value=0xB)
        + Op.RETURN(offset=0x12, size=0xE)
        + Op.STOP,
        balance=0xE8D4A51000,
    )
    # Source: lll
    # { (CALL 150000 0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b 1 0 0 0 32) (SSTORE 1 (MLOAD 0)) }  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=inner_call_gas,
                address=contract_1,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xE8D4A51000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=tx_gas_limit,
        value=10,
    )

    post = {
        Address(0x0000000000000000000000000000000000000001): Account(
            balance=1
        ),
        contract_0: Account(
            storage={
                1: 0x6000526005601BF36000526001FF000000000000000000000000000000000000,  # noqa: E501
            },
        ),
        contract_1: Account(storage={0: 11}),
    }

    state_test(pre=pre, post=post, tx=tx)
