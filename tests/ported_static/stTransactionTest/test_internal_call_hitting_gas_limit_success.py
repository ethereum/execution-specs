"""
Test_internal_call_hitting_gas_limit_success.

Ported from:
state_tests/stTransactionTest/InternalCallHittingGasLimitSuccessFiller.json
@manually-enhanced: Do not overwrite. Inner-CALL gas and outer tx gas
bumped on Amsterdam to cover EIP-8037 SSTORE-set state-gas spill;
pre-EIP-8037 unchanged.

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
    [
        "state_tests/stTransactionTest/InternalCallHittingGasLimitSuccessFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.valid_before("EIP8368")
def test_internal_call_hitting_gas_limit_success(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_internal_call_hitting_gas_limit_success."""
    # EIP-8037 SSTORE-set state-gas spill OoGs the 25k inner CALL.
    inner_call_gas = 25000
    tx_gas_limit = 150000
    env_gas_limit = 220000
    if fork.is_eip_enabled(8037):
        inner_call_gas = 200000
        tx_gas_limit = 500000
        env_gas_limit = 1_000_000

    coinbase = Address(0x2ADF5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0x3B9ACA00)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=env_gas_limit,
    )

    # Source: lll
    # {[[1]]55}
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x37) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (CALL 25000 <contract:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 1 0 0 0 0) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=inner_call_gas,
            address=addr,
            value=0x1,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=tx_gas_limit,
        value=10,
    )

    post = {addr: Account(storage={1: 55}, balance=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
