"""
Tests for the EIP-8038 [State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038)
``SELFDESTRUCT`` regular-gas dimension.

Under EIP-8038 ``SELFDESTRUCT`` is charged, in its *regular* gas
dimension:

- ``OPCODE_SELFDESTRUCT_BASE`` (5,000);
- a ``COLD_ACCOUNT_ACCESS`` (3,000) surcharge when the beneficiary is
  cold (a warm beneficiary adds nothing — SELFDESTRUCT has no
  ``WARM_ACCESS`` surcharge);
- a net-new ``ACCOUNT_WRITE`` (8,000) when a positive balance is sent to
  an empty (or non-existent) beneficiary, replacing the legacy combined
  25,000 regular account-creation cost.

So ``regular = 5,000 + (3,000 if cold) + (8,000 if creating)``: 13,000
warm / 16,000 cold when a new beneficiary is created, 5,000 warm / 8,000
cold otherwise.

The beneficiary account-creation charge ``GAS_NEW_ACCOUNT`` (183,600) is
the EIP-8037 *state* dimension (`charge_state_gas` in the spec), covered
in ``eip8037_state_creation_gas_cost_increase/test_state_gas_selfdestruct.py``.

``SELFDESTRUCT`` halts the frame, so it is driven via a wrapping ``CALL``
and verified through block ``gas_used`` accounting and balances. Per
EIP-6780, a contract not created in the same transaction is not deleted,
but its balance is still transferred and the beneficiary creation charge
still applies.

The framework opcode-gas model splits the two dimensions for
``SELFDESTRUCT`` exactly as the spec does: ``ACCOUNT_WRITE`` is charged
as regular gas and ``GAS_NEW_ACCOUNT`` as state gas, so
``Op.SELFDESTRUCT(account_new=True).regular_cost(fork)`` is the regular
charge (16,000 cold / 13,000 warm) and ``.state_cost(fork)`` is
``GAS_NEW_ACCOUNT``. These tests assert the regular dimension and verify
account-creation via balances; the state dimension is owned by
``eip8037_state_creation_gas_cost_increase/test_state_gas_selfdestruct.py``.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Environment,
    Fork,
    Header,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
    compute_create_address,
)
from execution_testing.checklists import EIPChecklist

from ..eip7708_eth_transfer_logs.spec import burn_log, transfer_log
from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")


def _selfdestruct_regular(fork: Fork, *, warm: bool, account_new: bool) -> int:
    """
    Return the EIP-8038 *regular* gas charged by SELFDESTRUCT.

    ``OPCODE_SELFDESTRUCT_BASE + access + (ACCOUNT_WRITE if account_new)``;
    the ``GAS_NEW_ACCOUNT`` account-creation cost is the EIP-8037 state
    dimension and is excluded from ``regular_cost``.
    """
    gas_costs = fork.gas_costs()
    regular = Op.SELFDESTRUCT(
        address_warm=warm, account_new=account_new
    ).regular_cost(fork)
    # SELFDESTRUCT charges a cold-access surcharge only; a warm
    # beneficiary adds nothing beyond the base (no WARM_ACCESS).
    access = 0 if warm else gas_costs.COLD_ACCOUNT_ACCESS
    expected = (
        gas_costs.OPCODE_SELFDESTRUCT_BASE
        + access
        + (gas_costs.ACCOUNT_WRITE if account_new else 0)
    )
    assert regular == expected
    return regular


def _destructor_code(
    beneficiary: Address | Bytecode, *, warm: bool, account_new: bool
) -> Bytecode:
    """
    Build SELFDESTRUCT bytecode with metadata so ``regular_cost(fork)``
    folds the beneficiary PUSH and the correct access/account-write
    charge (account-creation state gas excluded — it is charged
    separately by the spec).
    """
    return Op.SELFDESTRUCT.with_metadata(
        address_warm=warm, account_new=account_new
    )(beneficiary)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
def test_selfdestruct_new_beneficiary_regular_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    warm: bool,
) -> None:
    """
    SELFDESTRUCT to an empty beneficiary with balance charges
    ACCOUNT_WRITE.

    The destructor has a non-zero balance and targets an empty,
    non-existent beneficiary, so the net-new ``ACCOUNT_WRITE`` applies:
    ``regular = 5,000 + access + 8,000`` (13,000 warm, 16,000 cold). The
    creation gas ``GAS_NEW_ACCOUNT`` is charged on the state axis (the
    EIP-8037 suite asserts it); here it is funded from the reservoir and
    the value transfer to the new beneficiary confirms the path.
    """
    gas_costs = fork.gas_costs()
    new_account_state_gas = gas_costs.NEW_ACCOUNT

    regular = _selfdestruct_regular(fork, warm=warm, account_new=True)
    assert regular == (13_000 if warm else 16_000)

    beneficiary = Address(0xDEAD)  # empty, non-existent

    destructor_code = Op.SELFDESTRUCT(beneficiary)
    destructor = pre.deploy_contract(code=destructor_code, balance=1)

    storage = Storage()
    caller_code = Op.SSTORE(
        storage.store_next(1, "call_succeeds"),
        Op.CALL(gas=Op.GAS, address=destructor),
    )
    caller = pre.deploy_contract(code=caller_code)

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        access_list=[AccessList(address=beneficiary, storage_keys=[])]
        if warm
        else None,
        state_gas_reservoir=new_account_state_gas,
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={
            caller: Account(storage=storage),
            # New beneficiary created and credited the destructor balance.
            beneficiary: Account(balance=1),
        },
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
def test_selfdestruct_alive_beneficiary_no_account_write(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    warm: bool,
) -> None:
    """
    SELFDESTRUCT to an already-alive beneficiary charges no ACCOUNT_WRITE.

    The beneficiary already exists, so no account is created: regular =
    ``5,000 + (3,000 if cold)`` (5,000 warm, 8,000 cold) and no state gas is
    charged. The block header reflects the pure regular consumption.
    """
    regular = _selfdestruct_regular(fork, warm=warm, account_new=False)
    assert regular == (5_000 if warm else 8_000)

    beneficiary = pre.fund_eoa(amount=1)  # alive

    destructor_code = _destructor_code(
        beneficiary, warm=warm, account_new=False
    )
    destructor = pre.deploy_contract(code=destructor_code, balance=1)

    caller_code = Op.POP(Op.CALL(gas=Op.GAS, address=destructor)) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    access_list = (
        [AccessList(address=beneficiary, storage_keys=[])] if warm else None
    )
    # Intrinsic must include the access-list cost that warms the
    # beneficiary; pass the list so the calculator folds it in.
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list
    )

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        access_list=access_list,
        state_gas_reservoir=0,
    )

    # Pure regular: intrinsic + caller frame + destructor frame (whose
    # regular_cost folds the SELFDESTRUCT charge and beneficiary PUSH).
    expected_gas_used = (
        intrinsic
        + caller_code.gas_cost(fork)
        + destructor_code.regular_cost(fork)
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], header_verify=Header(gas_used=expected_gas_used))
        ],
        # EIP-6780: the pre-deployed destructor is not same-tx-created,
        # so it is not deleted; its balance still transfers.
        post={
            destructor: Account(balance=0, code=destructor_code),
            beneficiary: Account(balance=2),
        },
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
def test_selfdestruct_codebearing_zero_balance_beneficiary_no_account_write(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    warm: bool,
) -> None:
    """
    SELFDESTRUCT to a code-bearing zero-balance beneficiary: no
    ACCOUNT_WRITE.

    The beneficiary is alive because it has code, not balance: it holds a
    zero balance but a non-empty code (``Op.STOP``), so EIP-161 emptiness
    does not apply and no account is created when a positive balance is
    sent to it. Regular = ``5,000 + (3,000 if cold)`` (5,000 warm, 8,000
    cold) with no ACCOUNT_WRITE and no state gas — distinct from the
    alive-via-balance case, which exercises the same path through a
    different liveness source.
    """
    regular = _selfdestruct_regular(fork, warm=warm, account_new=False)
    assert regular == (5_000 if warm else 8_000)

    # Alive via code (non-empty code), with zero balance.
    beneficiary = pre.deploy_contract(code=Op.STOP, balance=0)

    destructor_code = _destructor_code(
        beneficiary, warm=warm, account_new=False
    )
    destructor = pre.deploy_contract(code=destructor_code, balance=1)

    caller_code = Op.POP(Op.CALL(gas=Op.GAS, address=destructor)) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    access_list = (
        [AccessList(address=beneficiary, storage_keys=[])] if warm else None
    )
    # Intrinsic must include the access-list cost that warms the
    # beneficiary; pass the list so the calculator folds it in.
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list
    )

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        access_list=access_list,
        state_gas_reservoir=0,
    )

    # Pure regular: intrinsic + caller frame + destructor frame (whose
    # regular_cost folds the SELFDESTRUCT charge and beneficiary PUSH).
    expected_gas_used = (
        intrinsic
        + caller_code.gas_cost(fork)
        + destructor_code.regular_cost(fork)
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], header_verify=Header(gas_used=expected_gas_used))
        ],
        # EIP-6780: the pre-deployed destructor is not same-tx-created,
        # so it is not deleted; its balance still transfers.
        post={
            destructor: Account(balance=0, code=destructor_code),
            # Code-bearing beneficiary credited the destructor balance.
            beneficiary: Account(balance=1, code=Op.STOP),
        },
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
def test_selfdestruct_zero_balance_no_account_write(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    warm: bool,
) -> None:
    """
    SELFDESTRUCT with a zero-balance destructor charges no ACCOUNT_WRITE.

    No value is transferred, so even a non-existent beneficiary is not
    created: regular = ``5,000 + access`` and no state gas is charged.
    """
    regular = _selfdestruct_regular(fork, warm=warm, account_new=False)
    assert regular == (5_000 if warm else 8_000)

    beneficiary = Address(0xDEAD)  # non-existent, but no value sent

    destructor_code = _destructor_code(
        beneficiary, warm=warm, account_new=False
    )
    destructor = pre.deploy_contract(code=destructor_code, balance=0)

    caller_code = Op.POP(Op.CALL(gas=Op.GAS, address=destructor)) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    access_list = (
        [AccessList(address=beneficiary, storage_keys=[])] if warm else None
    )
    intrinsic = fork.transaction_intrinsic_cost_calculator()(
        access_list=access_list
    )

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        access_list=access_list,
        state_gas_reservoir=0,
    )

    expected_gas_used = (
        intrinsic
        + caller_code.gas_cost(fork)
        + destructor_code.regular_cost(fork)
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], header_verify=Header(gas_used=expected_gas_used))
        ],
        post={
            destructor: Account(balance=0, code=destructor_code),
            beneficiary: Account.NONEXISTENT,
        },
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "beneficiary_kind",
    [
        pytest.param("self", id="self_beneficiary"),
        pytest.param("precompile", id="precompile_beneficiary"),
    ],
)
def test_selfdestruct_self_or_precompile_beneficiary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    beneficiary_kind: str,
) -> None:
    """
    SELFDESTRUCT to self or a precompile is warm and charges no
    ACCOUNT_WRITE.

    The executing account is in the accessed set on entry (self), and
    precompiles are pre-warmed from the start, so neither pays a cold
    surcharge: regular = ``5,000`` (warm base, no ``WARM_ACCESS``) with no
    state gas.

    The destructor balance is chosen so no account creation occurs: self
    is alive (sending to itself never creates), and the precompile case
    sends zero value (precompiles hold no state entry, so a value
    transfer would otherwise create one and charge ``GAS_NEW_ACCOUNT`` on
    the state axis).
    """
    gas_costs = fork.gas_costs()

    regular = _selfdestruct_regular(fork, warm=True, account_new=False)
    # SELFDESTRUCT has no warm-access surcharge: warm == base only.
    assert regular == gas_costs.OPCODE_SELFDESTRUCT_BASE

    if beneficiary_kind == "self":
        # Self is warm on entry; the PUSH is `ADDRESS` (BASE=2). A
        # non-zero balance is transferred to self (no creation).
        destructor_code = Op.SELFDESTRUCT.with_metadata(address_warm=True)(
            Op.ADDRESS
        )
        balance = 1
    else:
        # Identity precompile (address 4) is pre-warmed. Zero balance so
        # no value transfer and thus no account creation.
        destructor_code = Op.SELFDESTRUCT.with_metadata(address_warm=True)(
            Address(4)
        )
        balance = 0
    destructor = pre.deploy_contract(code=destructor_code, balance=balance)

    caller_code = Op.POP(Op.CALL(gas=Op.GAS, address=destructor)) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    intrinsic = fork.transaction_intrinsic_cost_calculator()()

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        state_gas_reservoir=0,
    )

    expected_gas_used = (
        intrinsic
        + caller_code.gas_cost(fork)
        + destructor_code.regular_cost(fork)
    )

    # EIP-6780: the pre-deployed destructor is not deleted. The self case
    # keeps its balance (transferred to itself); the precompile case sent
    # nothing.
    post = {destructor: Account(balance=balance, code=destructor_code)}

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx], header_verify=Header(gas_used=expected_gas_used))
        ],
        post=post,
    )


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.parametrize(
    "sufficient_gas", [True, False], ids=["sufficient", "insufficient"]
)
def test_selfdestruct_oog_boundary(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    sufficient_gas: bool,
) -> None:
    """
    Drive a cold SELFDESTRUCT that funds a new account at its exact total
    gas and one short.

    The destructor sends value to an empty beneficiary, charging
    ``5,000 + COLD_ACCOUNT_ACCESS + ACCOUNT_WRITE`` (16,000) in regular gas
    and ``GAS_NEW_ACCOUNT`` in state gas. The child CALL frame has no state
    reservoir of its own, so the state gas spills into the forwarded
    regular gas and the frame needs its full ``gas_cost`` total. Forwarding
    exactly that total lets the SELFDESTRUCT succeed (CALL returns 1); one
    gas short OOGs (CALL returns 0) before the value transfer, so the
    beneficiary is never created.
    """
    gas_costs = fork.gas_costs()

    beneficiary = Address(0xDEAD)
    regular = _selfdestruct_regular(fork, warm=False, account_new=True)
    assert regular == (
        gas_costs.OPCODE_SELFDESTRUCT_BASE
        + gas_costs.COLD_ACCOUNT_ACCESS
        + gas_costs.ACCOUNT_WRITE
    )

    destructor_code = _destructor_code(
        beneficiary, warm=False, account_new=True
    )
    destructor = pre.deploy_contract(code=destructor_code, balance=1)

    # The child CALL frame gets no state reservoir, so the NEW_ACCOUNT
    # state gas spills into the forwarded regular gas: forward the full
    # total. One gas short forces an out-of-gas before the value transfer.
    forwarded = destructor_code.gas_cost(fork)
    if not sufficient_gas:
        forwarded -= 1

    storage = Storage()
    caller_code = Op.SSTORE(
        storage.store_next(1 if sufficient_gas else 0, "sd_result"),
        Op.CALL(gas=forwarded, address=destructor),
    )
    caller = pre.deploy_contract(code=caller_code)

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        gas_limit=1_000_000,
    )

    if sufficient_gas:
        post: dict = {
            caller: Account(storage=storage),
            beneficiary: Account(balance=1),
        }
    else:
        post = {
            caller: Account(storage=storage),
            beneficiary: Account.NONEXISTENT,
            destructor: Account(balance=1),
        }

    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.pre_alloc_mutable()
def test_same_tx_created_selfdestruct_self_burn(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    EIP-6780: a same-tx-created contract SELFDESTRUCTs to itself, burning
    its balance, charged the warm base only.

    A creation transaction whose initcode SELFDESTRUCTs the new contract
    to ITSELF: the originator is created in this transaction so it is
    deleted, and because a same-tx-created contract holding balance is
    alive, ``account_new`` is false for the self-beneficiary —
    ``regular = 5,000`` (warm self, no ``ACCOUNT_WRITE``) and no
    SELFDESTRUCT state gas. The originator balance is burnt (a ``Burn``
    log, not a ``Transfer``), distinguishing the same-tx self-destruct
    path: the funding-empty-beneficiary charge keys on the beneficiary,
    but same-tx deletion keys on the originator independently.

    No net state gas is charged: the only state cost is the intrinsic
    creation ``NEW_ACCOUNT``, but the pre-funded created target is alive
    at message entry, so EIP-8037 refunds it (the create-tx
    ``created_target_alive`` refund), and the self-burn beneficiary
    already exists. The block ``gas_used`` is therefore the pure regular
    consumption.
    """
    new_account_state_gas = fork.gas_costs().NEW_ACCOUNT
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()

    amount = 1
    sender = pre.fund_eoa(amount=10**18)
    created = compute_create_address(address=sender, nonce=0)
    # Pre-fund the created address so its balance is present without an
    # in-tx value transfer (which would emit its own Transfer log). The
    # pre-funded target is alive at message entry, so the create-tx
    # intrinsic NEW_ACCOUNT is refunded (EIP-8037).
    pre.fund_address(created, amount)

    # Self is the executing account, warm on entry: no cold surcharge.
    init_code = Op.SELFDESTRUCT.with_metadata(address_warm=True)(Op.ADDRESS)

    # Self-beneficiary on a balance-bearing same-tx-created contract is
    # alive: account_new is false, so only the warm base is charged.
    regular = _selfdestruct_regular(fork, warm=True, account_new=False)
    assert regular == fork.gas_costs().OPCODE_SELFDESTRUCT_BASE

    intrinsic_total = intrinsic_calc(
        calldata=bytes(init_code), contract_creation=True
    )
    # The creation NEW_ACCOUNT is refunded (target alive at entry) and the
    # self-burn adds no state gas, so net state gas is zero.
    intrinsic_regular = intrinsic_total - new_account_state_gas
    expected_regular = intrinsic_regular + init_code.regular_cost(fork)
    expected_gas_used = expected_regular

    tx = Transaction(
        to=None,
        data=init_code,
        # Slack covers the create-side NEW_ACCOUNT charged transiently
        # before its refund, even though net state gas is zero.
        gas_limit=intrinsic_total + 100_000 + new_account_state_gas,
        sender=sender,
        value=0,
        expected_receipt=TransactionReceipt(logs=[burn_log(created, amount)]),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_gas_used),
            ),
        ],
        # Same-tx-created originator is deleted; its balance is burnt.
        post={created: Account.NONEXISTENT},
    )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.pre_alloc_mutable()
def test_same_tx_created_selfdestruct_to_fresh_beneficiary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    EIP-6780: a same-tx-created contract sends value to a fresh
    beneficiary, charged ``ACCOUNT_WRITE`` and creation state gas.

    A creation transaction whose initcode SELFDESTRUCTs the new contract
    to a fresh ``Address(0xDEAD)``: the fresh, non-existent beneficiary
    receives a positive balance, so ``account_new`` is true —
    ``regular = 5,000 + COLD_ACCOUNT_ACCESS + ACCOUNT_WRITE`` (16,000
    cold) plus a beneficiary ``NEW_ACCOUNT`` on the state axis. The
    beneficiary creation charge keys on the beneficiary, while the
    originator (created in this transaction) is still deleted: a
    ``Transfer`` log is emitted (not a ``Burn``).

    The net state gas is a single beneficiary ``NEW_ACCOUNT``: the
    intrinsic creation ``NEW_ACCOUNT`` is refunded because the pre-funded
    created target is alive at message entry (EIP-8037), while the fresh
    beneficiary's ``NEW_ACCOUNT`` persists.
    """
    new_account_state_gas = fork.gas_costs().NEW_ACCOUNT
    intrinsic_calc = fork.transaction_intrinsic_cost_calculator()

    amount = 1
    beneficiary = Address(0xDEAD)  # fresh, non-existent
    sender = pre.fund_eoa(amount=10**18)
    created = compute_create_address(address=sender, nonce=0)
    # Pre-fund the created address so its balance is present without an
    # in-tx value transfer (which would emit its own Transfer log). The
    # pre-funded target is alive at message entry, so the create-tx
    # intrinsic NEW_ACCOUNT is refunded (EIP-8037).
    pre.fund_address(created, amount)

    # Cold beneficiary receiving value: account_new is true.
    init_code = Op.SELFDESTRUCT.with_metadata(
        address_warm=False, account_new=True
    )(beneficiary)

    regular = _selfdestruct_regular(fork, warm=False, account_new=True)
    assert regular == 16_000

    intrinsic_total = intrinsic_calc(
        calldata=bytes(init_code), contract_creation=True
    )
    # The creation NEW_ACCOUNT is refunded (target alive at entry); only
    # the fresh beneficiary's NEW_ACCOUNT remains as net state gas.
    intrinsic_regular = intrinsic_total - new_account_state_gas
    expected_state = new_account_state_gas
    expected_regular = intrinsic_regular + init_code.regular_cost(fork)
    expected_gas_used = max(expected_regular, expected_state)

    tx = Transaction(
        to=None,
        data=init_code,
        gas_limit=intrinsic_total + 100_000 + expected_state,
        sender=sender,
        value=0,
        # Reservoir holds the beneficiary-creation state gas (above the
        # creation's intrinsic NEW_ACCOUNT) so it does not spill into
        # regular gas.
        state_gas_reservoir=new_account_state_gas,
        expected_receipt=TransactionReceipt(
            logs=[transfer_log(created, beneficiary, amount)]
        ),
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                header_verify=Header(gas_used=expected_gas_used),
            ),
        ],
        # Same-tx-created originator is deleted; the fresh beneficiary is
        # created and credited the originator balance.
        post={
            created: Account.NONEXISTENT,
            beneficiary: Account(balance=amount),
        },
    )
