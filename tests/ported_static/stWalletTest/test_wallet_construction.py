"""
Deploy the `multiOwned`, `daylimit` and `Wallet` contracts.

Ported from:
state_tests/stWalletTest/dayLimitConstructionFiller.json
state_tests/stWalletTest/dayLimitConstructionOOGFiller.json
state_tests/stWalletTest/dayLimitConstructionPartialFiller.json
state_tests/stWalletTest/multiOwnedConstructionCorrectFiller.json
state_tests/stWalletTest/multiOwnedConstructionNotEnoughGasFiller.json
state_tests/stWalletTest/multiOwnedConstructionNotEnoughGasPartialFiller.json
state_tests/stWalletTest/walletConstructionFiller.json
state_tests/stWalletTest/walletConstructionOOGFiller.json
state_tests/stWalletTest/walletConstructionPartialFiller.json

@manually-enhanced: Do not overwrite. Merged; derived the gas budget.
"""

from typing import Dict

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork

from tests.ported_static.stWalletTest.wallet_contracts import (
    DAY_LIMIT_CODE,
    DAY_LIMIT_CONSTRUCTOR,
    MULTI_OWNED_CODE,
    MULTI_OWNED_CONSTRUCTOR,
    WALLET_CODE,
    WALLET_CONSTRUCTOR,
    owners_storage,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CONTRACTS = {
    "multi_owned": (MULTI_OWNED_CONSTRUCTOR, MULTI_OWNED_CODE),
    "day_limit": (DAY_LIMIT_CONSTRUCTOR, DAY_LIMIT_CODE),
    "wallet": (WALLET_CONSTRUCTOR, WALLET_CODE),
}


@pytest.mark.ported_from(
    [
        "state_tests/stWalletTest/dayLimitConstructionFiller.json",
        "state_tests/stWalletTest/dayLimitConstructionOOGFiller.json",
        "state_tests/stWalletTest/dayLimitConstructionPartialFiller.json",
        "state_tests/stWalletTest/multiOwnedConstructionCorrectFiller.json",
        "state_tests/stWalletTest/multiOwnedConstructionNotEnoughGasFiller.json",  # noqa: E501
        "state_tests/stWalletTest/multiOwnedConstructionNotEnoughGasPartialFiller.json",  # noqa: E501
        "state_tests/stWalletTest/walletConstructionFiller.json",
        "state_tests/stWalletTest/walletConstructionOOGFiller.json",
        "state_tests/stWalletTest/walletConstructionPartialFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.execute(
    pytest.mark.skip(
        reason="Expects the block number and timestamp of the test env"
    )
)
@pytest.mark.parametrize("contract", list(CONTRACTS))
@pytest.mark.parametrize("out_of_gas", [False, True], ids=["success", "oog"])
def test_wallet_construction(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    contract: str,
    out_of_gas: bool,
) -> None:
    """
    Deploy the contract, with enough gas or without enough gas to deploy.

    The short budget covers the intrinsic cost and the code deposit but not
    the constructor, so the creation runs out of gas.
    """
    constructor, runtime = CONTRACTS[contract]
    initcode = constructor + runtime
    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=0)

    gas_limit = None
    post: Dict[Address, Account | None]
    if out_of_gas:
        gas_limit = fork.transaction_intrinsic_cost_calculator()(
            calldata=initcode, contract_creation=True
        ) + fork.gas_costs().CODE_DEPOSIT_PER_BYTE * len(runtime)
        post = {created: Account.NONEXISTENT}
    else:
        post = {
            created: Account(
                code=runtime, storage=owners_storage(1, [sender]), nonce=1
            )
        }
    post[sender] = Account(nonce=1)

    tx = Transaction(
        sender=sender, to=None, data=initcode, gas_limit=gas_limit
    )
    state_test(pre=pre, post=post, tx=tx)
