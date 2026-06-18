"""
Test_suicide_to_not_existing_contract.

Ported from:
state_tests/stEIP150Specific/SuicideToNotExistingContractFiller.json

@manually-enhanced: Do not overwrite. The measured slot captures the
regular gas of a value-0 CALL to a cold contract that then
SELFDESTRUCTs (with a zero balance) to a cold, non-alive beneficiary.
EIP-8038 reprices both the CALL's cold account access and the
SELFDESTRUCT beneficiary's cold access; no value is sent so there is
no new-account write. The delta is therefore twice the fork's
`COLD_ACCOUNT_ACCESS - 2600`, exactly 0 before EIP-8038.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP150Specific/SuicideToNotExistingContractFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicide_to_not_existing_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_suicide_to_not_existing_contract."""
    # EIP-8038 cold account access reprice; 0 before EIP-8038. Charged
    # twice: once for the CALL target, once for the cold SELFDESTRUCT
    # beneficiary.
    cold_account_delta = fork.gas_costs().COLD_ACCOUNT_ACCESS - 2600
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # { (SELFDESTRUCT 0x2000000000000000000000000000000000000115) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0x2000000000000000000000000000000000000115
        )
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { [0] (GAS) (CALL 60000 <contract:0x1000000000000000000000000000000000000116> 0 0 0 0 0) [[1]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
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
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        addr: Account(
            storage={},
            code=bytes.fromhex(
                "732000000000000000000000000000000000000115ff00"
            ),
            balance=0,
            nonce=0,
        ),
        target: Account(storage={1: 10237 + 2 * cold_account_delta}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
