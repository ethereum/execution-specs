"""
Test_suicide_to_existing_contract.

Ported from:
state_tests/stEIP150Specific/SuicideToExistingContractFiller.json

@manually-enhanced: Do not overwrite. The measured slot captures the
regular gas of a value-0 CALL to a cold contract that then
SELFDESTRUCTs back to its (warm, alive) caller. EIP-8038 reprices the
cold account access of that CALL; the beneficiary is warm so the
SELFDESTRUCT is unchanged. The delta is therefore the fork's
`COLD_ACCOUNT_ACCESS` less Cancun's, exactly 0 before EIP-8038.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Cancun, Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP150Specific/SuicideToExistingContractFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_suicide_to_existing_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_suicide_to_existing_contract."""
    # EIP-8038 cold account access reprice; 0 before EIP-8038.
    cold_account_delta = (
        fork.gas_costs().COLD_ACCOUNT_ACCESS
        - Cancun.gas_costs().COLD_ACCOUNT_ACCESS
    )
    sender = pre.fund_eoa()

    # Source: lll
    # { (SELFDESTRUCT <contract:target:0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }  # noqa: E501
    addr = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=Op.CALLER) + Op.STOP,
    )

    # Source: lll
    # { [0] (GAS) (CALL 60000 <contract:0x1000000000000000000000000000000000000118> 0 0 0 0 0) [[1]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0xEA60,
                address=addr,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
    )
    tx = Transaction(
        sender=sender,
        to=target,
        gas_limit=600000,
    )

    post = {
        addr: Account(
            storage={},
            code=Op.SELFDESTRUCT(address=Op.CALLER) + Op.STOP,
        ),
        target: Account(storage={1: 7636 + cold_account_delta}),
    }

    state_test(pre=pre, post=post, tx=tx)
