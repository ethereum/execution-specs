"""
Test_create_name_registrator_zero_mem2.

Ported from:
state_tests/stSystemOperationsTest/createNameRegistratorZeroMem2Filler.json
@manually-enhanced: Do not overwrite. tx `gas_limit` bumped on Amsterdam
to cover EIP-8037 state-gas spill; pre-EIP-8037 unchanged.

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
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stSystemOperationsTest/createNameRegistratorZeroMem2Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
def test_create_name_registrator_zero_mem2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_create_name_registrator_zero_mem2."""
    # EIP-8037 state-gas spill on Amsterdam exceeds 300k tx_gas.
    tx_gas_limit = 300000
    if fork.is_eip_enabled(8037):
        tx_gas_limit = 1_000_000

    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    # Source: lll
    # { (MSTORE 0 0x601080600c6000396000f3006000355415600957005b60203560003555) [[ 0 ]] (CREATE 23 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0) }  # noqa: E501
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(
            offset=0x0,
            value=0x601080600C6000396000F3006000355415600957005B60203560003555,
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE(
                value=0x17,
                offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=tx_gas_limit,
        value=0x186A0,
    )

    post = {
        contract_0: Account(
            storage={
                0: compute_create_address(address=contract_0, nonce=1),
            },
            nonce=2,
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
