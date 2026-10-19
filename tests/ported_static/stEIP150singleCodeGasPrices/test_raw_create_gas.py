"""
Measure the gas cost of CREATE with CodeGasMeasure, across value-transfer,
memory-expansion, and insufficient-balance (failure) variants.

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawCreateGasFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCreateGasMemoryFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCreateGasValueTransferFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCreateGasValueTransferMemoryFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCreateFailGasValueTransferFiller.json
state_tests/stEIP150singleCodeGasPrices/RawCreateFailGasValueTransfer2Filler.json

@manually-enhanced: Do not overwrite. Six RawCreate*Gas fillers folded into one
CodeGasMeasure parametrize; failure path charges execution_cost (no state gas).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    CodeGasMeasure,
    Fork,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

GAS_SLOT = 0x1
MEMORY_SIZE = 0x1F40  # 8000-byte init-code window for the memory variants


@pytest.mark.ported_from(
    [
        "state_tests/stEIP150singleCodeGasPrices/RawCreateGasFiller.json",
        "state_tests/stEIP150singleCodeGasPrices/RawCreateGasMemoryFiller.json",
        "state_tests/stEIP150singleCodeGasPrices/RawCreateGasValueTransferFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawCreateGasValueTransferMemoryFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawCreateFailGasValueTransferFiller.json",  # noqa: E501
        "state_tests/stEIP150singleCodeGasPrices/RawCreateFailGasValueTransfer2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("SpuriousDragon")
@pytest.mark.parametrize(
    "create_value, size, fails",
    [
        pytest.param(0x0, 0x0, False, id="raw_create_gas"),
        pytest.param(0x0, MEMORY_SIZE, False, id="raw_create_gas_memory"),
        pytest.param(0xA, 0x0, False, id="raw_create_gas_value_transfer"),
        pytest.param(
            0xA, MEMORY_SIZE, False, id="raw_create_gas_value_transfer_memory"
        ),
        pytest.param(0xB, 0x0, True, id="raw_create_fail_gas_value_transfer"),
        pytest.param(
            0xB, MEMORY_SIZE, True, id="raw_create_fail_gas_value_transfer2"
        ),
    ],
)
def test_raw_create_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_value: int,
    size: int,
    fails: bool,
) -> None:
    """Measure CREATE gas; a balance-failure path is cheaper (no state gas)."""
    # Init code is never written, so it is `size` zero bytes: the created
    # contract STOPs immediately and deposits no code.
    create_code = Op.CREATE(
        value=create_value,
        offset=0x0,
        size=size,
        new_memory_size=size,
        init_code_size=size,
    )
    # Fund the creator one wei short of `create_value` on the failure cases so
    # the CREATE aborts on the balance check; otherwise give it exactly enough.
    balance = create_value - 1 if fails else create_value
    contract = pre.deploy_contract(
        code=CodeGasMeasure(
            code=create_code,
            extra_stack_items=1,
            sstore_key=GAS_SLOT,
        ),
        balance=balance,
    )

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        state_gas_reservoir=0,
    )

    created = compute_create_address(address=contract, nonce=1)
    if fails:
        # A balance-check failure runs no init code and creates no account, so
        # only the regular (execution) gas is charged, never state gas.
        expected_gas = create_code.execution_cost(fork)
        created_account = Account.NONEXISTENT
    else:
        expected_gas = create_code.gas_cost(fork)
        created_account = Account(balance=create_value)

    post = {
        contract: Account(storage={GAS_SLOT: expected_gas}),
        created: created_account,
    }

    state_test(pre=pre, post=post, tx=tx)
