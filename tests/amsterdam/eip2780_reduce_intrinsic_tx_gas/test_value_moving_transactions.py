"""
Tests for EIP-2780 Reduce Transaction Intrinsic Cost.

Test gas costs with EIP-2780 for value-moving transactions to:
- EOAs,
- contracts,
- empty accounts,
- the sender itself,
- delegated EOAs,
- newly created contracts, and
- precompiles.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Fork,
    Initcode,
    Op,
    RecipientType,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)

from ..eip7708_eth_transfer_logs.spec import transfer_log
from .helpers import (
    EOA_INITIAL_BALANCE,
    RECIPIENT_TYPES_NON_CREATE,
    setup_target,
)
from .spec import ref_spec_2780

REFERENCE_SPEC_GIT_PATH = ref_spec_2780.git_path
REFERENCE_SPEC_VERSION = ref_spec_2780.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@pytest.mark.parametrize("recipient_type", RECIPIENT_TYPES_NON_CREATE)
@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
def test_value_moving_transactions(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    recipient_type: RecipientType,
    value: int,
) -> None:
    """
    Ensure value-moving transactions charge gas correctly across every
    non-create recipient type.

    Self-transfers are carved out: the sender pays only the recipient
    -access-free intrinsic and the value is moved to itself, so the
    sender's post-tx balance reflects only gas. Pre-existing 7702
    delegations on the recipient surface as an extra top-frame
    ``COLD_ACCOUNT_ACCESS``; empty recipients trigger the top-frame
    ``NEW_ACCOUNT`` state charge when value is transferred.

    The EIP-7708 transfer log is asserted to fire exactly when
    ``TRANSFER_LOG_COST`` is charged: for a non-self value transfer,
    and never for a self-transfer (carve-out) or a zero-value tx.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)
    target = setup_target(pre, recipient_type, sender)

    target_initial_balance = (
        EOA_INITIAL_BALANCE if recipient_type == RecipientType.EOA else 0
    )

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        sends_value=bool(value),
        recipient_type=recipient_type,
        return_cost_deducted_prior_execution=True,
    )
    top_frame_gas = fork.transaction_top_frame_gas_calculator()(
        sends_value=bool(value),
        recipient_type=recipient_type,
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=bool(value),
        recipient_type=recipient_type,
    )
    # Under the default zero state-gas reservoir, top-frame state gas
    # spills entirely into regular gas.
    total_gas_cost = intrinsic_gas + top_frame_gas + top_frame_state_gas

    tx_gas_limit = total_gas_cost + 1000  # add a small buffer
    gas_price = 1_000_000_000

    is_self_transfer = recipient_type == RecipientType.SELF

    # A transfer log is emitted iff value moves to a distinct account,
    # which is exactly when the intrinsic includes ``TRANSFER_LOG_COST``.
    # ``logs=[]`` asserts no log fires for the carved-out cases.
    if value > 0 and not is_self_transfer:
        expected_logs = [transfer_log(sender, target, value)]
    else:
        expected_logs = []

    tx = Transaction(
        sender=sender,
        to=target,
        value=value,
        gas_limit=tx_gas_limit,
        gas_price=gas_price,
        expected_receipt=TransactionReceipt(logs=expected_logs),
    )

    sender_value_delta = 0 if is_self_transfer else value
    sender_final_balance = (
        sender_initial_balance
        - sender_value_delta
        - total_gas_cost * gas_price
    )

    post: dict[Address, Account | None] = {
        sender: Account(nonce=1, balance=sender_final_balance),
    }
    if not is_self_transfer:
        if recipient_type == RecipientType.EMPTY_ACCOUNT and value == 0:
            post[target] = None
        else:
            post[target] = Account(balance=target_initial_balance + value)

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
@pytest.mark.parametrize(
    "tx_reverts",
    [
        pytest.param(False, id="success"),
        pytest.param(True, id="init_reverts"),
    ],
)
def test_value_contract_creation_tx(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    tx_reverts: bool,
    value: int,
) -> None:
    """
    Test value moving contract creation transactions.

    When the init code succeeds, the contract is deployed with the
    transferred value and the receipt's ``gas_used`` equals the
    intrinsic plus the execution gas.

    When the init code reverts, the deploy is rolled back: no code is
    set, the value transfer is reversed, and the intrinsic
    ``NEW_ACCOUNT`` state-gas charge is refilled to the reservoir.
    Under the default zero state-gas reservoir, the refill cancels
    the spilled-to-regular portion of the intrinsic exactly, so the
    sender pays only the regular portion of the intrinsic plus the
    few EVM gas units spent before the revert.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    code_to_deploy = Op.STOP
    if tx_reverts:
        # ``PUSH1 0 PUSH1 0 REVERT`` -- aborts immediately, so no
        # code is deployed.
        call_data = Op.REVERT(0, 0)
    else:
        call_data = Initcode(deploy_code=code_to_deploy)
    execution_gas = call_data.gas_cost(fork)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=call_data,
        contract_creation=True,
        sends_value=bool(value),
        return_cost_deducted_prior_execution=True,
    )

    if tx_reverts:
        # The ``NEW_ACCOUNT`` state portion of the intrinsic is
        # refilled to the reservoir on revert, so it does not appear
        # on the receipt.
        new_account_refund = fork.transaction_intrinsic_state_gas(
            contract_creation=True,
        )
        gas_used = intrinsic_gas + execution_gas - new_account_refund
        # Value transfer rolled back.
        sender_value_delta = 0
        expected_target = None
    else:
        gas_used = intrinsic_gas + execution_gas
        sender_value_delta = value
        expected_target = Account(code=code_to_deploy, balance=value)

    gas_price = 1_000_000_000
    gas_limit = intrinsic_gas + execution_gas + 1000

    tx = Transaction(
        sender=sender,
        to=None,
        value=value,
        data=call_data,
        gas_limit=gas_limit,
        gas_price=gas_price,
    )

    expected_target_address = compute_create_address(address=sender, nonce=0)
    sender_final_balance = (
        sender_initial_balance - sender_value_delta - gas_used * gas_price
    )

    post = {
        sender: Account(nonce=1, balance=sender_final_balance),
        expected_target_address: expected_target,
    }

    state_test(pre=pre, tx=tx, post=post)


def _precompile_calldata(precompile: Address) -> bytes:
    """Return minimal valid calldata for the given precompile address."""
    addr_int = int.from_bytes(precompile, "big")

    if addr_int == 0x0A:
        # Valid point evaluation input from mainnet tx:
        # https://etherscan.io/tx/0xcb3dc8f3b14f1cda0c16a619a112102a8ec70dce1b3f1b28272227cf8d5fbb0e
        return (
            bytes.fromhex(
                # versioned_hash (32)
                "018156B94FE9735E573BAB36DAD05D60FEB720D424CCD20AAF719343C31E4246"
            )
            + bytes.fromhex(
                # z (32)
                "019123BCB9D06356701F7BE08B4494625B87A7B02EDC566126FB81F6306E915F"
            )
            + bytes.fromhex(
                # y (32)
                "6C2EB1E94C2532935B8465351BA1BD88EABE2B3FA1AADFF7D1CD816E8315BD38"
            )
            + bytes.fromhex(
                # kzg_commitment (48)
                "A9546D41993E10DF2A7429B8490394EA9EE62807BAE6F326D1044A51581306F58D4B9DFD5931E044688855280FF3799E"
            )
            + bytes.fromhex(
                # kzg_proof (48)
                "A2EA83D9391E0EE42E0C650ACC7A1F842A7D385189485DDB4FD54ADE3D9FD50D608167DCA6C776AAD4B8AD5C20691BFE"
            )
        )

    precompile_min_input = {
        0x01: 128,  # ECRECOVER
        0x02: 0,  # SHA256 (accepts empty)
        0x03: 0,  # RIPEMD160 (accepts empty)
        0x04: 0,  # IDENTITY (accepts empty)
        0x05: 96,  # MODEXP
        0x06: 128,  # BN256ADD
        0x07: 96,  # BN256MUL
        0x08: 0,  # BN256PAIRING (empty is valid)
        0x09: 213,  # BLAKE2F
        0x0B: 256,  # BLS12_G1_ADD
        0x0C: 160,  # BLS12_G1_MSM
        0x0D: 512,  # BLS12_G2_ADD
        0x0E: 288,  # BLS12_G2_MSM
        0x0F: 384,  # BLS12_PAIRING
        0x10: 64,  # BLS12_MAP_FP_TO_G1
        0x11: 128,  # BLS12_MAP_FP2_TO_G2
        0x100: 160,  # P256VERIFY
    }

    input_size = precompile_min_input.get(addr_int, 0)
    return bytes([0x00] * input_size if input_size > 0 else [])


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(0, id="zero_value"),
        pytest.param(1, id="non-zero_value"),
    ],
)
@pytest.mark.parametrize(
    "pre_funded",
    [
        pytest.param(True, id="pre_funded"),
        pytest.param(False, id="not_funded"),
    ],
)
@pytest.mark.with_all_precompiles
def test_value_move_to_precompiles(
    fork: Fork,
    pre: Alloc,
    state_test: StateTestFiller,
    precompile: Address,
    pre_funded: bool,
    value: int,
) -> None:
    """
    Ensure value moving transactions to precompiles charge gas correctly.

    Precompile recipients pay the same ``COLD_ACCOUNT_ACCESS`` at
    intrinsic time as any other non-self target -- access lists do
    not warm transaction-level accounts. A value transfer to a
    precompile additionally pays the transfer-log and value-transfer
    charges.

    The top-frame ``NEW_ACCOUNT`` state charge keys solely on EIP-161
    emptiness; a precompile address is not special-cased. The
    ``pre_funded`` parameter exercises both pre-tx states:

    - ``not_funded``: the precompile address is empty per EIP-161, so a
      value transfer creates it and pays ``NEW_ACCOUNT`` -- exactly
      like any other empty recipient.
    - ``pre_funded``: the precompile already holds a balance and is
      therefore alive, so no ``NEW_ACCOUNT`` charge applies.
    """
    sender_initial_balance = 10**18
    sender = pre.fund_eoa(sender_initial_balance)

    pre_funded_amount = 0
    if pre_funded:
        pre_funded_amount = 1
        pre.fund_address(precompile, amount=pre_funded_amount)

    tx_data = _precompile_calldata(precompile)

    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=tx_data,
        sends_value=bool(value),
        recipient_type=RecipientType.PRECOMPILE,
        return_cost_deducted_prior_execution=True,
    )
    # A value transfer to an empty (not pre-funded) precompile fires the
    # top-frame ``NEW_ACCOUNT`` state charge, modelled via
    # ``EMPTY_ACCOUNT``; a pre-funded precompile is alive and exempt.
    state_recipient_type = (
        RecipientType.PRECOMPILE if pre_funded else RecipientType.EMPTY_ACCOUNT
    )
    top_frame_state_gas = fork.transaction_top_frame_state_gas(
        sends_value=bool(value),
        recipient_type=state_recipient_type,
    )

    gas_price = 1_000_000_000

    tx = Transaction(
        sender=sender,
        to=precompile,
        value=value,
        data=tx_data,
        gas_price=gas_price,
    )

    # Exact sender balance is generally not checked because precompile
    # execution gas varies across the matrix. For identity with empty
    # calldata, the execution gas is deterministic, so pin the exact
    # balance to make the empty-precompile ``NEW_ACCOUNT`` charge a
    # source-level assertion.
    final_precompile_balance = pre_funded_amount + value
    expected_precompile: Account | None
    if final_precompile_balance > 0:
        expected_precompile = Account(balance=final_precompile_balance)
    else:
        expected_precompile = None
    expected_sender = Account(nonce=1)
    if precompile == Address(0x04):
        gas_costs = fork.gas_costs()
        precompile_execution_gas = (
            gas_costs.PRECOMPILE_IDENTITY_BASE
            + gas_costs.PRECOMPILE_IDENTITY_PER_WORD
            * ((len(tx_data) + 31) // 32)
        )
        total_gas_cost = (
            intrinsic_gas + top_frame_state_gas + precompile_execution_gas
        )
        expected_sender = Account(
            nonce=1,
            balance=(
                sender_initial_balance - value - total_gas_cost * gas_price
            ),
        )
    post = {
        sender: expected_sender,
        precompile: expected_precompile,
    }

    state_test(pre=pre, tx=tx, post=post)
