"""
Calls a contract that runs CREATE which deploy a code. then after...

Ported from:
state_tests/stCreateTest/CreateOOGafterInitCodeRevertFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateOOGafterInitCodeRevertFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_create_oo_gafter_init_code_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Calls a contract that runs CREATE which deploy a code."""
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    # Source: lll
    # { (KECCAK256 0x00 0x2fffff) }
    contract_2 = pre.deploy_contract(
        code=Op.SHA3(offset=0x0, size=0x2FFFFF) + Op.STOP,
    )
    # Source: lll
    # { (MSTORE 0 0x6460016001556000526005601bf3) (CREATE 0 18 14) (CALLCODE 10000 0x094f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0 0) (REVERT 0 32) }  # noqa: E501
    contract_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x6460016001556000526005601BF3)
        + Op.POP(Op.CREATE(value=0x0, offset=0x12, size=0xE))
        + Op.POP(
            Op.CALLCODE(
                gas=0x2710,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.REVERT(offset=0x0, size=0x20)
        + Op.STOP,
    )
    # Source: lll
    # { (CALL (GAS) 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0 32) [[ 1 ]] (MLOAD 0) }  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=contract_1,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=285000,
    )

    post = {
        contract_0: Account(storage={1: 0x6460016001556000526005601BF3}),
        compute_create_address(
            address=contract_1, nonce=1
        ): Account.NONEXISTENT,
    }

    state_test(pre=pre, post=post, tx=tx)
