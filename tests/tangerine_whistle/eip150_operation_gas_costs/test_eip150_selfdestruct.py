"""
Tests for EIP-150 SELFDESTRUCT operation gas costs.

EIP-150 introduced G_SELF_DESTRUCT for SELFDESTRUCT and precise gas
boundaries for state access during the operation.
"""

from typing import Dict

import pytest
from execution_testing import (
    EOA,
    AccessList,
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    BalCodeChange,
    BalNonceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Initcode,
    Op,
    Transaction,
    compute_create_address,
)
from execution_testing import (
    Macros as Om,
)
from execution_testing.forks import (
    Berlin,
    Cancun,
    SpuriousDragon,
)
from execution_testing.forks.helpers import Fork

from .spec import ref_spec_150

REFERENCE_SPEC_GIT_PATH = ref_spec_150.git_path
REFERENCE_SPEC_VERSION = ref_spec_150.version


# --- helper functions --- #


def calculate_selfdestruct_gas(
    fork: Fork,
    beneficiary_warm: bool,
    beneficiary_dead: bool,
    originator_balance: int,
) -> int:
    """Calculate exact gas needed for SELFDESTRUCT."""
    gas_costs = fork.gas_costs()
    gas = (
        # PUSH + SELFDESTRUCT
        gas_costs.G_VERY_LOW + gas_costs.G_SELF_DESTRUCT
    )

    # Cold access cost (>=Berlin only)
    if fork >= Berlin and not beneficiary_warm:
        gas += gas_costs.G_COLD_ACCOUNT_ACCESS

    # G_NEW_ACCOUNT:
    # - Pre-EIP-161 (TangerineWhistle): charged when beneficiary is dead
    # - Post-EIP-161 (>=SpuriousDragon): charged when beneficiary is dead
    #   AND originator has balance > 0
    if beneficiary_dead:
        if fork >= SpuriousDragon:
            if originator_balance > 0:
                gas += gas_costs.G_NEW_ACCOUNT
        else:
            # Pre-EIP-161: always charged when beneficiary is dead
            gas += gas_costs.G_NEW_ACCOUNT

    return gas


def setup_selfdestruct_test(
    pre: Alloc,
    fork: Fork,
    beneficiary: Address,
    originator_balance: int,
    same_tx: bool,
    beneficiary_warm: bool,
    inner_call_gas: int,
) -> tuple[Address, Address, Address, Transaction]:
    """
    Set up SELFDESTRUCT test with caller contract pattern.

    Returns: (alice, caller, victim, tx)
    """
    alice = pre.fund_eoa()
    victim_code = Op.SELFDESTRUCT(beneficiary)

    if same_tx:
        # Deploy and selfdestruct in same transaction via factory
        initcode = Initcode(deploy_code=victim_code)
        initcode_len = len(initcode)

        factory_code = Om.MSTORE(initcode, 0) + Op.CALL(
            gas=inner_call_gas,
            address=Op.CREATE(
                value=originator_balance, offset=0, size=initcode_len
            ),
        )
        caller = pre.deploy_contract(
            code=factory_code, balance=originator_balance
        )
        victim = compute_create_address(address=caller, nonce=1)
    else:
        # Pre-existing contract
        victim = pre.deploy_contract(
            code=victim_code, balance=originator_balance
        )
        caller = pre.deploy_contract(
            code=Op.CALL(gas=inner_call_gas, address=victim)
        )

    # Warm beneficiary via access list (>=Berlin only,
    # doesn't add to BAL >= Amsterdam)
    access_list = (
        [AccessList(address=beneficiary, storage_keys=[])]
        if beneficiary_warm and fork >= Berlin
        else None
    )

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=500_000,
        protected=fork.supports_protected_txs(),
        access_list=access_list,
    )

    return alice, caller, victim, tx


def build_bal_expectations(
    fork: Fork,
    alice: Address,
    caller: Address,
    victim: Address,
    beneficiary: Address,
    originator_balance: int,
    beneficiary_initial_balance: int,
    same_tx: bool,
    success: bool,
    beneficiary_in_bal: bool,
) -> BlockAccessListExpectation | None:
    """Build BAL expectations for >=Amsterdam."""
    if not fork.header_bal_hash_required():
        return None

    victim_code = Op.SELFDESTRUCT(beneficiary)

    # Beneficiary expectation
    if not beneficiary_in_bal:
        beneficiary_expectation: BalAccountExpectation | None = None
    elif not success:
        beneficiary_expectation = BalAccountExpectation.empty()
    else:
        # Success: balance transferred
        final_balance = beneficiary_initial_balance + originator_balance
        if final_balance > beneficiary_initial_balance:
            beneficiary_expectation = BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(
                        block_access_index=1, post_balance=final_balance
                    )
                ],
            )
        else:
            beneficiary_expectation = BalAccountExpectation.empty()

    # Victim expectation
    if same_tx:
        if success:
            # Created and destroyed in same tx - no net changes
            victim_expectation = BalAccountExpectation.empty()
        else:
            # OOG: CREATE succeeded but SELFDESTRUCT failed
            # Only include balance_changes if originator_balance > 0
            victim_expectation = BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1)
                ],
                code_changes=[
                    BalCodeChange(
                        block_access_index=1, new_code=bytes(victim_code)
                    )
                ],
            )
            if originator_balance > 0:
                victim_expectation.balance_changes.append(
                    BalBalanceChange(
                        block_access_index=1, post_balance=originator_balance
                    )
                )
    else:
        if success and originator_balance > 0:
            victim_expectation = BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(block_access_index=1, post_balance=0)
                ],
            )
        else:
            victim_expectation = BalAccountExpectation.empty()

    # Caller expectation
    if same_tx:
        caller_expectation = BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=2)],
        )
        if originator_balance > 0:
            caller_expectation.balance_changes.append(
                BalBalanceChange(block_access_index=1, post_balance=0)
            )
    else:
        caller_expectation = BalAccountExpectation.empty()

    return BlockAccessListExpectation(
        account_expectations={
            alice: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1)
                ],
            ),
            caller: caller_expectation,
            victim: victim_expectation,
            beneficiary: beneficiary_expectation,
        }
    )


def build_post_state(
    fork: Fork,
    alice: Address,
    caller: Address,
    victim: Address,
    beneficiary: Address,
    originator_balance: int,
    beneficiary_initial_balance: int,
    same_tx: bool,
    success: bool,
    beneficiary_has_code: bool = False,
) -> dict:
    """Build expected post state."""
    victim_code = Op.SELFDESTRUCT(beneficiary)
    caller_nonce = 2 if same_tx else 1

    if success:
        contract_destroyed = fork < Cancun or same_tx
        final_beneficiary_balance = (
            beneficiary_initial_balance + originator_balance
        )

        if contract_destroyed:
            post: dict = {
                alice: Account(nonce=1),
                caller: Account(nonce=caller_nonce),
                victim: Account.NONEXISTENT,
            }
        else:
            # >=Cancun pre-existing: code preserved, balance transferred
            post = {
                alice: Account(nonce=1),
                caller: Account(nonce=caller_nonce),
                victim: Account(balance=0, code=victim_code),
            }

        # Beneficiary: verify balance if non-empty, NONEXISTENT if empty
        # Pre-EIP-161: empty accounts touched during execution persist
        if final_beneficiary_balance > 0 or beneficiary_has_code:
            post[beneficiary] = Account(balance=final_beneficiary_balance)
        elif fork >= SpuriousDragon:
            # EIP-161 (>=SpuriousDragon): empty accounts are deleted
            post[beneficiary] = Account.NONEXISTENT
        else:
            # Pre-EIP-161: empty accounts persist after being touched
            post[beneficiary] = Account(balance=0)
    else:
        # OOG: SELFDESTRUCT failed
        if same_tx:
            post = {
                alice: Account(nonce=1),
                caller: Account(nonce=caller_nonce, balance=0),
                victim: Account(balance=originator_balance, code=victim_code),
            }
        else:
            post = {
                alice: Account(nonce=1),
                caller: Account(nonce=caller_nonce),
                victim: Account(balance=originator_balance, code=victim_code),
            }

    return post


# --- tests --- #


@pytest.mark.parametrize(
    "is_success", [True, False], ids=["exact_gas", "exact_gas_minus_1"]
)
@pytest.mark.parametrize(
    "beneficiary", ["eoa", "contract"], ids=["eoa", "contract"]
)
@pytest.mark.parametrize(
    "warm",
    [
        pytest.param(
            False, id="cold", marks=pytest.mark.valid_from("TangerineWhistle")
        ),
        pytest.param(True, id="warm", marks=pytest.mark.valid_from("Berlin")),
    ],
)
@pytest.mark.parametrize(
    "same_tx", [False, True], ids=["pre_deploy", "same_tx"]
)
@pytest.mark.parametrize(
    "originator_balance",
    [0, 1],
    ids=["no_balance", "has_balance"],
)
@pytest.mark.parametrize(
    "beneficiary_initial_balance",
    [0, 1],
    ids=["dead_beneficiary", "alive_beneficiary"],
)
def test_selfdestruct_to_account(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    is_success: bool,
    beneficiary: str,
    warm: bool,
    same_tx: bool,
    originator_balance: int,
    beneficiary_initial_balance: int,
) -> None:
    """
    Test SELFDESTRUCT success boundary for account beneficiaries.

    - exact_gas: succeeds, balance transferred, contract destroyed
    - exact_gas_minus_1: OOG, operation fails
    """
    # Create beneficiary
    if beneficiary == "eoa":
        beneficiary_addr: EOA | Address = pre.fund_eoa(
            amount=beneficiary_initial_balance
        )
    else:
        beneficiary_addr = pre.deploy_contract(
            code=Op.STOP, balance=beneficiary_initial_balance
        )

    # Determine if beneficiary is dead (for G_NEW_ACCOUNT calculation)
    # Contract with code is NOT dead even with balance=0
    beneficiary_dead = (
        beneficiary_initial_balance == 0 and beneficiary == "eoa"
    )

    # Calculate exact gas for success (includes G_NEW_ACCOUNT if applicable)
    inner_call_gas = calculate_selfdestruct_gas(
        fork,
        beneficiary_warm=warm,
        beneficiary_dead=beneficiary_dead,
        originator_balance=originator_balance,
    )
    if not is_success:
        inner_call_gas -= 1

    # In BAL if: success OR G_NEW_ACCOUNT charged (OOG after access)
    needs_new_account = False
    if beneficiary_dead:
        if fork >= SpuriousDragon:
            needs_new_account = originator_balance > 0
        else:
            needs_new_account = True

    beneficiary_in_bal = is_success or needs_new_account

    alice, caller, victim, tx = setup_selfdestruct_test(
        pre,
        fork,
        beneficiary_addr,
        originator_balance,
        same_tx,
        beneficiary_warm=warm,
        inner_call_gas=inner_call_gas,
    )

    expected_bal = build_bal_expectations(
        fork,
        alice,
        caller,
        victim,
        beneficiary_addr,
        originator_balance,
        beneficiary_initial_balance,
        same_tx,
        success=is_success,
        beneficiary_in_bal=beneficiary_in_bal,
    )

    post = build_post_state(
        fork,
        alice,
        caller,
        victim,
        beneficiary_addr,
        originator_balance,
        beneficiary_initial_balance,
        same_tx,
        success=is_success,
        beneficiary_has_code=(beneficiary == "contract"),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], expected_block_access_list=expected_bal)],
        post=post,
    )


@pytest.mark.parametrize(
    "is_success", [True, False], ids=["exact_gas", "exact_gas_minus_1"]
)
@pytest.mark.parametrize(
    "beneficiary", ["eoa", "contract"], ids=["eoa", "contract"]
)
@pytest.mark.parametrize(
    "warm",
    [
        pytest.param(
            False, id="cold", marks=pytest.mark.valid_from("TangerineWhistle")
        ),
        pytest.param(True, id="warm", marks=pytest.mark.valid_from("Berlin")),
    ],
)
@pytest.mark.parametrize(
    "same_tx", [False, True], ids=["pre_deploy", "same_tx"]
)
@pytest.mark.parametrize(
    "originator_balance",
    [0, 1],
    ids=["no_balance", "has_balance"],
)
@pytest.mark.parametrize(
    "beneficiary_initial_balance",
    [0, 1],
    ids=["dead_beneficiary", "alive_beneficiary"],
)
def test_selfdestruct_state_access_boundary(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    is_success: bool,
    beneficiary: str,
    warm: bool,
    same_tx: bool,
    originator_balance: int,
    beneficiary_initial_balance: int,
) -> None:
    """
    Test state access boundary for account beneficiaries.

    Consensus check: beneficiary must be accessed at base cost boundary,
    before G_NEW_ACCOUNT is evaluated.

    - exact_gas: beneficiary IS accessed (in BAL)
    - exact_gas_minus_1: beneficiary NOT accessed (not in BAL)
    """
    # Create beneficiary
    if beneficiary == "eoa":
        beneficiary_addr: EOA | Address = pre.fund_eoa(
            amount=beneficiary_initial_balance
        )
    else:
        beneficiary_addr = pre.deploy_contract(
            code=Op.STOP, balance=beneficiary_initial_balance
        )

    # Determine if beneficiary is dead (for G_NEW_ACCOUNT calculation)
    # Contract with code is NOT dead even with balance=0
    beneficiary_dead = (
        beneficiary_initial_balance == 0 and beneficiary == "eoa"
    )

    # Calculate gas for state access boundary only (base + cold access)
    # Does NOT include G_NEW_ACCOUNT
    gas_costs = fork.gas_costs()
    inner_call_gas = gas_costs.G_VERY_LOW + gas_costs.G_SELF_DESTRUCT
    if fork >= Berlin and not warm:
        inner_call_gas += gas_costs.G_COLD_ACCOUNT_ACCESS

    if not is_success:
        inner_call_gas -= 1

    # Determine if operation succeeds at this gas level
    # At state access boundary, we have enough gas for base + cold access
    # Operation succeeds if NO G_NEW_ACCOUNT is needed:
    # - Beneficiary is alive (has balance or has code)
    # - OR beneficiary is dead but originator_balance=0 (>=SpuriousDragon)
    needs_new_account = False
    if beneficiary_dead:
        if fork >= SpuriousDragon:
            needs_new_account = originator_balance > 0
        else:
            needs_new_account = True

    # At exact_gas: success if no G_NEW_ACCOUNT needed
    # At exact_gas_minus_1: always OOG (before state access)
    operation_success = is_success and not needs_new_account

    alice, caller, victim, tx = setup_selfdestruct_test(
        pre,
        fork,
        beneficiary_addr,
        originator_balance,
        same_tx,
        beneficiary_warm=warm,
        inner_call_gas=inner_call_gas,
    )

    # Key difference: beneficiary_in_bal depends on is_success
    # exact_gas: state accessed, beneficiary in BAL
    # exact_gas_minus_1: OOG before state access, beneficiary NOT in BAL
    expected_bal = build_bal_expectations(
        fork,
        alice,
        caller,
        victim,
        beneficiary_addr,
        originator_balance,
        beneficiary_initial_balance,
        same_tx,
        success=operation_success,
        beneficiary_in_bal=is_success,
    )

    post = build_post_state(
        fork,
        alice,
        caller,
        victim,
        beneficiary_addr,
        originator_balance,
        beneficiary_initial_balance,
        same_tx,
        success=operation_success,
        beneficiary_has_code=(beneficiary == "contract"),
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], expected_block_access_list=expected_bal)],
        post=post,
    )


@pytest.mark.parametrize(
    "is_success", [True, False], ids=["exact_gas", "exact_gas_minus_1"]
)
@pytest.mark.with_all_precompiles
@pytest.mark.parametrize(
    "same_tx", [False, True], ids=["pre_deploy", "same_tx"]
)
@pytest.mark.parametrize(
    "originator_balance",
    [0, 1],
    ids=["no_balance", "has_balance"],
)
@pytest.mark.parametrize(
    "beneficiary_initial_balance",
    [
        pytest.param(
            0,
            id="dead_beneficiary",
            marks=pytest.mark.pre_alloc_group(
                "eip150_selfdestruct_precompile_dead"
            ),
        ),
        pytest.param(
            1,
            id="alive_beneficiary",
            marks=pytest.mark.pre_alloc_group(
                "eip150_selfdestruct_precompile_alive"
            ),
        ),
    ],
)
@pytest.mark.valid_from("TangerineWhistle")
def test_selfdestruct_to_precompile(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    is_success: bool,
    precompile: Address,
    same_tx: bool,
    originator_balance: int,
    beneficiary_initial_balance: int,
) -> None:
    """
    Test SELFDESTRUCT success boundary for precompile beneficiaries.

    Precompiles are always warm (no cold access charge).

    - exact_gas: succeeds, balance transferred, contract destroyed
    - exact_gas_minus_1: OOG, operation fails
    """
    # Fund precompile if needed
    if beneficiary_initial_balance > 0:
        pre.fund_address(precompile, beneficiary_initial_balance)

    # Precompiles are dead when they have no balance
    beneficiary_dead = beneficiary_initial_balance == 0

    # Calculate exact gas for success (includes G_NEW_ACCOUNT if applicable)
    # Precompiles are always warm
    inner_call_gas = calculate_selfdestruct_gas(
        fork,
        beneficiary_warm=True,  # Precompiles are always warm
        beneficiary_dead=beneficiary_dead,
        originator_balance=originator_balance,
    )
    if not is_success:
        inner_call_gas -= 1

    # In BAL if: success OR G_NEW_ACCOUNT charged (OOG after access)
    needs_new_account = False
    if beneficiary_dead:
        if fork >= SpuriousDragon:
            needs_new_account = originator_balance > 0
        else:
            needs_new_account = True

    beneficiary_in_bal = is_success or needs_new_account

    alice, caller, victim, tx = setup_selfdestruct_test(
        pre,
        fork,
        precompile,
        originator_balance,
        same_tx,
        beneficiary_warm=True,  # Precompiles are always warm
        inner_call_gas=inner_call_gas,
    )

    expected_bal = build_bal_expectations(
        fork,
        alice,
        caller,
        victim,
        precompile,
        originator_balance,
        beneficiary_initial_balance,
        same_tx,
        success=is_success,
        beneficiary_in_bal=beneficiary_in_bal,
    )

    post = build_post_state(
        fork,
        alice,
        caller,
        victim,
        precompile,
        originator_balance,
        beneficiary_initial_balance,
        same_tx,
        success=is_success,
        beneficiary_has_code=False,  # Precompiles don't have stored code
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], expected_block_access_list=expected_bal)],
        post=post,
    )


@pytest.mark.parametrize(
    "is_success", [True, False], ids=["exact_gas", "exact_gas_minus_1"]
)
@pytest.mark.with_all_precompiles
@pytest.mark.parametrize(
    "same_tx", [False, True], ids=["pre_deploy", "same_tx"]
)
@pytest.mark.parametrize(
    "originator_balance",
    [0, 1],
    ids=["no_balance", "has_balance"],
)
@pytest.mark.parametrize(
    "beneficiary_initial_balance",
    [
        pytest.param(
            0,
            id="dead_beneficiary",
            marks=pytest.mark.pre_alloc_group(
                "eip150_selfdestruct_precompile_boundary_dead"
            ),
        ),
        pytest.param(
            1,
            id="alive_beneficiary",
            marks=pytest.mark.pre_alloc_group(
                "eip150_selfdestruct_precompile_boundary_alive"
            ),
        ),
    ],
)
@pytest.mark.valid_from("TangerineWhistle")
def test_selfdestruct_to_precompile_state_access_boundary(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    is_success: bool,
    precompile: Address,
    same_tx: bool,
    originator_balance: int,
    beneficiary_initial_balance: int,
) -> None:
    """
    Test state access boundary for precompile beneficiaries.

    Consensus check: precompile must be accessed at base cost boundary,
    before G_NEW_ACCOUNT is evaluated. Precompiles are always warm.

    - exact_gas: precompile IS accessed (in BAL)
    - exact_gas_minus_1: precompile NOT accessed (not in BAL)
    """
    # Fund precompile if needed
    if beneficiary_initial_balance > 0:
        pre.fund_address(precompile, beneficiary_initial_balance)

    beneficiary_dead = beneficiary_initial_balance == 0

    # State access boundary: base cost only (no G_NEW_ACCOUNT)
    gas_costs = fork.gas_costs()
    inner_call_gas = gas_costs.G_VERY_LOW + gas_costs.G_SELF_DESTRUCT

    if not is_success:
        inner_call_gas -= 1

    # Success at base cost if no G_NEW_ACCOUNT needed
    needs_new_account = False
    if beneficiary_dead:
        if fork >= SpuriousDragon:
            needs_new_account = originator_balance > 0
        else:
            needs_new_account = True

    operation_success = is_success and not needs_new_account

    alice, caller, victim, tx = setup_selfdestruct_test(
        pre,
        fork,
        precompile,
        originator_balance,
        same_tx,
        beneficiary_warm=True,  # Precompiles are always warm
        inner_call_gas=inner_call_gas,
    )

    # Key difference: beneficiary_in_bal depends on is_success
    # exact_gas: state accessed, precompile in BAL
    # exact_gas_minus_1: OOG before state access, precompile NOT in BAL
    expected_bal = build_bal_expectations(
        fork,
        alice,
        caller,
        victim,
        precompile,
        originator_balance,
        beneficiary_initial_balance,
        same_tx,
        success=operation_success,
        beneficiary_in_bal=is_success,
    )

    post = build_post_state(
        fork,
        alice,
        caller,
        victim,
        precompile,
        originator_balance,
        beneficiary_initial_balance,
        same_tx,
        success=operation_success,
        beneficiary_has_code=False,  # Precompiles don't have stored code
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], expected_block_access_list=expected_bal)],
        post=post,
    )


@pytest.mark.parametrize(
    "is_success", [True, False], ids=["exact_gas", "exact_gas_minus_1"]
)
@pytest.mark.with_all_system_contracts
@pytest.mark.parametrize(
    "same_tx", [False, True], ids=["pre_deploy", "same_tx"]
)
@pytest.mark.parametrize(
    "originator_balance",
    [0, 1],
    ids=["no_balance", "has_balance"],
)
@pytest.mark.valid_from("Cancun")
def test_selfdestruct_to_system_contract(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    is_success: bool,
    system_contract: Address,
    same_tx: bool,
    originator_balance: int,
) -> None:
    """
    Test SELFDESTRUCT success boundary for system contract beneficiaries.

    System contracts are always warm (no cold access charge) and always have
    code (so beneficiary is never dead, no G_NEW_ACCOUNT charge).

    - exact_gas: succeeds, balance transferred
    - exact_gas_minus_1: OOG, operation fails
    """
    # Calculate exact gas for success
    # System contracts are always warm and never dead (have code)
    inner_call_gas = calculate_selfdestruct_gas(
        fork,
        beneficiary_warm=True,
        beneficiary_dead=False,
        originator_balance=originator_balance,
    )
    if not is_success:
        inner_call_gas -= 1

    alice, caller, victim, tx = setup_selfdestruct_test(
        pre,
        fork,
        system_contract,
        originator_balance,
        same_tx,
        beneficiary_warm=True,
        inner_call_gas=inner_call_gas,
    )

    # Build minimal BAL expectations for test-specific accounts only
    expected_bal: BlockAccessListExpectation | None = None
    if fork.header_bal_hash_required():
        account_expectations: Dict[Address, BalAccountExpectation | None] = {
            alice: BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=1)
                ],
            ),
        }

        # Victim expectation
        if same_tx:
            if is_success:
                # Created and destroyed in same tx - no net changes
                victim_expectation = BalAccountExpectation.empty()
            else:
                # OOG: contract created but selfdestruct failed
                victim_expectation = BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    code_changes=[
                        BalCodeChange(
                            block_access_index=1,
                            new_code=bytes(Op.SELFDESTRUCT(system_contract)),
                        )
                    ],
                )
                if originator_balance > 0:
                    victim_expectation.balance_changes.append(
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=originator_balance,
                        )
                    )
            # Caller nonce incremented for CREATE
            caller_expectation = BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=2)
                ],
            )
            if originator_balance > 0 and is_success:
                caller_expectation.balance_changes.append(
                    BalBalanceChange(block_access_index=1, post_balance=0)
                )
            account_expectations[caller] = caller_expectation
        else:
            # Pre-existing victim
            if is_success and originator_balance > 0:
                victim_expectation = BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=0)
                    ],
                )
            else:
                victim_expectation = BalAccountExpectation.empty()
            account_expectations[caller] = BalAccountExpectation.empty()

        account_expectations[victim] = victim_expectation

        # System contract receives balance if success and originator
        # had balance
        if is_success and originator_balance > 0:
            account_expectations[system_contract] = BalAccountExpectation(
                balance_changes=[
                    BalBalanceChange(
                        block_access_index=1, post_balance=originator_balance
                    )
                ],
            )

        expected_bal = BlockAccessListExpectation(
            account_expectations=account_expectations
        )

    post = build_post_state(
        fork,
        alice,
        caller,
        victim,
        system_contract,
        originator_balance,
        beneficiary_initial_balance=0,
        same_tx=same_tx,
        success=is_success,
        beneficiary_has_code=True,
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], expected_block_access_list=expected_bal)],
        post=post,
    )


@pytest.mark.parametrize(
    "is_success", [True, False], ids=["exact_gas", "exact_gas_minus_1"]
)
@pytest.mark.parametrize(
    "originator_balance",
    [0, 1],
    ids=["no_balance", "has_balance"],
)
@pytest.mark.parametrize(
    "same_tx", [False, True], ids=["pre_deploy", "same_tx"]
)
@pytest.mark.valid_from("TangerineWhistle")
def test_selfdestruct_to_self(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    is_success: bool,
    originator_balance: int,
    same_tx: bool,
) -> None:
    """
    Test SELFDESTRUCT where beneficiary is the executing contract itself.

    Uses Op.SELFDESTRUCT(Op.ADDRESS) - the victim selfdestructs to itself.

    Key characteristics:
    - Beneficiary is always warm (it's the executing contract)
    - Beneficiary is always alive (EIP-161 nonce=1)
    - No G_NEW_ACCOUNT charge
    - No cold access charge (>=Berlin)
    - Balance is "transferred" to self (no net change until destruction)

    Gas boundary:
    - exact_gas: SELFDESTRUCT completes successfully
    - exact_gas_minus_1: OOG, SELFDESTRUCT fails

    Post-destruction behavior (is_success=True only):
    - Pre-Cancun or same_tx: contract destroyed, balance = 0
    - >=Cancun pre-existing: contract NOT destroyed, balance preserved
    """
    alice = pre.fund_eoa()
    victim_code = Op.SELFDESTRUCT(Op.ADDRESS)

    # Gas: ADDRESS + SELFDESTRUCT (no cold access, no G_NEW_ACCOUNT)
    # Note: ADDRESS opcode costs G_BASE, not G_VERY_LOW like PUSH
    gas_costs = fork.gas_costs()
    base_gas = gas_costs.G_BASE + gas_costs.G_SELF_DESTRUCT
    inner_call_gas = base_gas if is_success else base_gas - 1

    if same_tx:
        # Deploy and selfdestruct in same transaction via factory
        initcode = Initcode(deploy_code=victim_code)
        initcode_len = len(initcode)

        factory_code = Om.MSTORE(initcode, 0) + Op.CALL(
            gas=inner_call_gas,
            address=Op.CREATE(
                value=originator_balance, offset=0, size=initcode_len
            ),
        )
        caller = pre.deploy_contract(
            code=factory_code,
            balance=originator_balance,
        )
        victim = compute_create_address(address=caller, nonce=1)
    else:
        # Pre-existing contract
        victim = pre.deploy_contract(
            code=victim_code, balance=originator_balance
        )
        caller_code = Op.CALL(gas=inner_call_gas, address=victim)
        caller = pre.deploy_contract(code=caller_code)

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=500_000,
        protected=fork.supports_protected_txs(),
    )

    # Build BAL expectations
    expected_bal: BlockAccessListExpectation | None = None
    if fork.header_bal_hash_required():
        if same_tx:
            if is_success:
                # Created and destroyed in same tx - no net changes for victim
                victim_expectation = BalAccountExpectation.empty()
            else:
                # OOG: CREATE succeeded but SELFDESTRUCT failed
                victim_expectation = BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                    code_changes=[
                        BalCodeChange(
                            block_access_index=1,
                            new_code=bytes(victim_code),
                        )
                    ],
                )
                if originator_balance > 0:
                    victim_expectation.balance_changes.append(
                        BalBalanceChange(
                            block_access_index=1,
                            post_balance=originator_balance,
                        )
                    )

            caller_expectation = BalAccountExpectation(
                nonce_changes=[
                    BalNonceChange(block_access_index=1, post_nonce=2)
                ],
            )
            if originator_balance > 0:
                caller_expectation.balance_changes.append(
                    BalBalanceChange(block_access_index=1, post_balance=0)
                )
        else:
            # Pre-existing: victim in BAL
            if not is_success:
                # OOG: victim accessed but no state changes
                victim_expectation = BalAccountExpectation.empty()
            elif fork >= Cancun:
                # >=Cancun success: contract survives with original balance
                victim_expectation = BalAccountExpectation.empty()
            elif originator_balance > 0:
                # Pre-Cancun success: contract destroyed
                victim_expectation = BalAccountExpectation(
                    balance_changes=[
                        BalBalanceChange(block_access_index=1, post_balance=0)
                    ],
                )
            else:
                victim_expectation = BalAccountExpectation.empty()
            caller_expectation = BalAccountExpectation.empty()

        expected_bal = BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                caller: caller_expectation,
                victim: victim_expectation,
            }
        )

    # Build post state
    caller_nonce = 2 if same_tx else 1

    if not is_success:
        # OOG: SELFDESTRUCT failed, contract survives
        if same_tx:
            post: dict = {
                alice: Account(nonce=1),
                caller: Account(nonce=caller_nonce, balance=0),
                victim: Account(balance=originator_balance, code=victim_code),
            }
        else:
            post = {
                alice: Account(nonce=1),
                caller: Account(nonce=caller_nonce),
                victim: Account(balance=originator_balance, code=victim_code),
            }
    else:
        contract_destroyed = fork < Cancun or same_tx
        if contract_destroyed:
            post = {
                alice: Account(nonce=1),
                caller: Account(nonce=caller_nonce),
                victim: Account.NONEXISTENT,
            }
        else:
            # >=Cancun pre-existing: code preserved, balance preserved
            post = {
                alice: Account(nonce=1),
                caller: Account(nonce=caller_nonce),
                victim: Account(balance=originator_balance, code=victim_code),
            }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], expected_block_access_list=expected_bal)],
        post=post,
    )


@pytest.mark.parametrize(
    "originator_balance",
    [0, 1],
    ids=["no_balance", "has_balance"],
)
@pytest.mark.valid_from("TangerineWhistle")
def test_initcode_selfdestruct_to_self(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    originator_balance: int,
) -> None:
    """
    Test SELFDESTRUCT during initcode execution where beneficiary is self.

    Unlike test_selfdestruct_to_self, this tests the case where the initcode
    itself executes SELFDESTRUCT(ADDRESS) during contract creation, before
    any code is deployed.

    Key characteristics:
    - During initcode, the contract has no code yet
    - Contract has nonce=1 (post-EIP-161) making it non-empty
    - Beneficiary is always warm (it's the executing contract)
    - No G_NEW_ACCOUNT charge (contract has nonce > 0)
    - No cold access charge (>=Berlin)

    Note: Gas boundary testing not possible for initcode since CREATE
    doesn't accept a gas parameter - it uses all available gas.
    """
    alice = pre.fund_eoa()
    initcode = Op.SELFDESTRUCT(Op.ADDRESS)
    initcode_len = len(initcode)

    factory_code = Om.MSTORE(initcode, 0) + Op.CREATE(
        value=originator_balance, offset=0, size=initcode_len
    )
    caller = pre.deploy_contract(code=factory_code, balance=originator_balance)
    victim = compute_create_address(address=caller, nonce=1)

    tx = Transaction(
        sender=alice,
        to=caller,
        gas_limit=500_000,
        protected=fork.supports_protected_txs(),
    )

    # Build BAL expectations
    expected_bal: BlockAccessListExpectation | None = None
    if fork.header_bal_hash_required():
        # Contract created and immediately destroyed - no net changes
        # for victim
        caller_expectation = BalAccountExpectation(
            nonce_changes=[BalNonceChange(block_access_index=1, post_nonce=2)],
        )
        if originator_balance > 0:
            caller_expectation.balance_changes.append(
                BalBalanceChange(block_access_index=1, post_balance=0)
            )

        expected_bal = BlockAccessListExpectation(
            account_expectations={
                alice: BalAccountExpectation(
                    nonce_changes=[
                        BalNonceChange(block_access_index=1, post_nonce=1)
                    ],
                ),
                caller: caller_expectation,
                victim: BalAccountExpectation.empty(),
            }
        )

    # Contract was created and destroyed in same tx
    post: dict = {
        alice: Account(nonce=1),
        caller: Account(nonce=2),
        victim: Account.NONEXISTENT,
    }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx], expected_block_access_list=expected_bal)],
        post=post,
    )
