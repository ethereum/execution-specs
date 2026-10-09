"""
Test_static_contract_creation_oo_gdont_leave_empty_contract_via_transact...

Ported from:
state_tests/stStaticCall/static_contractCreationOOGdontLeaveEmptyContractViaTransactionFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_contractCreationOOGdontLeaveEmptyContractViaTransactionFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
def test_static_contract_creation_oo_gdont_leave_empty_contract_via_transaction(  # noqa: E501
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_static_contract_creation_oo_gdont_leave_empty_contract_via_tra..."""  # noqa: E501
    sender_amount = 0x10C8E0
    if fork.is_eip_enabled(8037):
        sender_amount += fork.gas_costs().NEW_ACCOUNT * 10
    sender = pre.fund_eoa(amount=sender_amount)

    # Source: lll
    # {(MSTORE 1 1)}
    contract_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    contract_2 = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1C, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.STOP,
    )
    # Source: lll
    # {(STATICCALL 50000 0x1000000000000000000000000000000000000001 0 64 0 64)}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0xC350,
            address=contract_1,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x186A0,
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.STATICCALL(
            gas=0xC350,
            address=contract_2,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        ),
        gas_limit=(
            96000 + fork.gas_costs().NEW_ACCOUNT
            if fork.is_eip_enabled(8037)
            else 96000
        ),
    )

    post = {compute_create_address(address=sender, nonce=0): Account(nonce=1)}

    state_test(pre=pre, post=post, tx=tx)
