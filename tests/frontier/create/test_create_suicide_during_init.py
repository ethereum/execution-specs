"""Deploy contract that calls selfdestruct in it's initcode."""

from enum import Enum

import pytest

from ethereum_test_forks import Byzantium, Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    Initcode,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from ethereum_test_tools import Opcodes as Op


class Operation(Enum):
    """Enum for created contract actions."""

    SUICIDE = 1
    SUICIDE_TO_ITSELF = 2

    def __int__(self) -> int:
        """Convert to int."""
        return int(self.value)


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stCreateTest/CREATE_ContractSuicideDuringInit_ThenStoreThenReturnFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stCreateTest/CREATE_ContractSuicideDuringInit_WithValueFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stCreateTest/CREATE_ContractSuicideDuringInit_WithValueToItselfFiller.json",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stCreateTest/CREATE_ContractSuicideDuringInitFiller.json",
    ],
    pr=["https://github.com/ethereum/execution-spec-tests/pull/1871"],
    coverage_missed_reason="Tip to coinbase, original test contains empty account.",
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.with_all_create_opcodes
@pytest.mark.parametrize("transaction_create", [False, True])
@pytest.mark.parametrize(
    "operation",
    [Operation.SUICIDE, Operation.SUICIDE_TO_ITSELF],
)
def test_create_suicide_during_transaction_create(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    create_opcode: Op,
    operation: Operation,
    transaction_create: bool,
) -> None:
    """Contract init code calls suicide then measures different metrics."""
    if create_opcode != Op.CREATE and transaction_create:
        pytest.skip(f"Excluded: {create_opcode} with transaction_create=True")

    sender = pre.fund_eoa()
    contract_deploy = pre.deploy_contract(
        code=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + create_opcode(size=Op.CALLDATASIZE(), value=Op.CALLVALUE())
    )
    contract_success = pre.deploy_contract(code=Op.SSTORE(1, 1))
    self_destruct_destination = pre.deploy_contract(code=Op.STOP)
    contract_after_suicide = pre.deploy_contract(code=Op.SSTORE(1, 1))

    contract_initcode = Initcode(
        initcode_prefix=Op.CALL(address=contract_success, gas=Op.SUB(Op.GAS, 100_000))
        + Op.SELFDESTRUCT(
            Op.ADDRESS if operation == Operation.SUICIDE_TO_ITSELF else self_destruct_destination
        )
        + Op.CALL(address=contract_after_suicide, gas=Op.SUB(Op.GAS, 100_000)),
        deploy_code=Op.SSTORE(0, 1),
    )

    expected_create_address = compute_create_address(
        address=sender if transaction_create else contract_deploy,
        nonce=1 if transaction_create else 0,
        initcode=contract_initcode,
        opcode=create_opcode,
    )

    tx_value = 100
    tx = Transaction(
        gas_limit=1_000_000,
        to=None if transaction_create else contract_deploy,
        data=contract_initcode,
        value=tx_value,
        sender=sender,
        protected=fork >= Byzantium,
    )

    post = {
        contract_success: Account(storage={1: 1}),
        self_destruct_destination: Account(
            balance=0 if operation == Operation.SUICIDE_TO_ITSELF else tx_value
        ),
        contract_deploy: Account(storage={0: 0}),
        contract_after_suicide: Account(storage={1: 0}),  # suicide eats all gas
        expected_create_address: Account.NONEXISTENT,
    }
    state_test(env=Environment(), pre=pre, post=post, tx=tx)
