"""
Tests for the EIP-8038 [State-access gas cost update](https://eips.ethereum.org/EIPS/eip-8038)
``CREATE``/``CREATE2`` execution-gas dimension.

Under EIP-8038 the contract-creation opcodes are repriced in their
*execution* gas dimension to ``CREATE_ACCESS`` (``ACCOUNT_WRITE`` +
``COLD_ACCOUNT_ACCESS``), on top of which the EIP-3860 init code
word cost and, for ``CREATE2`` only, an additional keccak word cost
are charged. The new-account creation
and per-byte code deposit charges are the EIP-8037 *state* dimension,
covered in
``eip8037_state_creation_gas_cost_increase/test_state_gas_create.py``.

These tests isolate and assert the EIP-8038 *execution* dimension. At the
contract-creating-transaction boundary the state component is re-derived
only to feed the ``max(execution, state)`` block-header accounting.
"""

from typing import List

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Fork,
    Hash,
    Header,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
    compute_create_address,
    create_op,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_create_opcodes()
@pytest.mark.parametrize(
    "init_code_size",
    [
        pytest.param(0, id="empty"),
        pytest.param(32, id="one_word"),
        pytest.param(33, id="two_words"),
        pytest.param(96, id="three_words"),
    ],
)
def test_create_execution_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    init_code_size: int,
) -> None:
    """
    Measure the execution gas of CREATE/CREATE2 and assert the schedule.

    The EIP-8038 *execution* dimension is ``CREATE_ACCESS`` plus the
    EIP-3860 init code word cost plus, for ``CREATE2`` only, an
    additional keccak word cost. The EIP-8037
    account-creation state gas is excluded by subtracting
    ``create_state_gas(0)``.
    """
    # Isolate the execution dimension: opcode total minus its account
    # creation state gas (the only state component carried by the CREATE
    # opcode itself; code deposit is charged on RETURN inside initcode).
    create_meta = create_opcode(init_code_size=init_code_size)
    execution_gas = create_meta.gas_cost(fork) - fork.create_state_gas(
        code_size=0
    )
    # Equivalent isolation via the execution_cost helper.
    assert execution_gas == create_meta.execution_cost(fork)

    # Runtime confirmation via CodeGasMeasure: a factory whose CREATE
    # deploys empty code, so no code-deposit state gas is charged and the
    # only state component is the account-creation gas funded from the
    # reservoir. The initcode is brought into memory BEFORE the measured
    # window, so the memory-expansion charge is excluded; the measured
    # value is the CREATE opcode's execution cost exactly. The overhead
    # subtracts the create-call argument pushes (the create leaves one
    # stack item, its result).
    #
    # The initcode is all-zero bytes (`STOP`), so the child frame halts
    # immediately consuming zero gas and deposits empty code. This keeps
    # the measured value the CREATE opcode's own execution cost, with no
    # child-execution gas folded in. `init_code_size` still drives the
    # opcode's per-init-word charge.
    padded_init = b"\x00" * init_code_size

    create_call = create_op(create_opcode, size=init_code_size)
    push_cost = Op.PUSH1(0).execution_cost(fork)
    arg_pushes = create_opcode.popped_stack_items * push_cost

    memory_setup = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE, new_memory_size=init_code_size)
        if init_code_size
        else Bytecode()
    )
    storage = Storage()
    measure = CodeGasMeasure(
        code=create_call,
        overhead_cost=arg_pushes,
        extra_stack_items=1,
        sstore_key=storage.store_next(execution_gas, "create_execution_gas"),
    )
    factory = pre.deploy_contract(code=memory_setup + measure)

    tx = Transaction(
        to=factory,
        data=padded_init,
        # Reservoir funds the account-creation state gas; leaving
        # gas_limit unset keeps `Op.GAS` honest about gas_left.
        state_gas_reservoir=fork.create_state_gas(code_size=0),
        sender=pre.fund_eoa(),
    )

    post = {factory: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "init_code_size",
    [
        pytest.param(32, id="one_word"),
        pytest.param(64, id="two_words"),
        pytest.param(128, id="four_words"),
    ],
)
def test_create2_keccak_word_delta(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    init_code_size: int,
) -> None:
    """
    Verify CREATE2 costs exactly the keccak word surcharge over CREATE.

    ``CREATE2`` hashes the init code to derive the salted address, adding
    ``OPCODE_KECCAK256_PER_WORD`` (6) per init-code word on top of the
    execution cost shared with ``CREATE``. Both opcodes carry the identical
    EIP-8038 ``CREATE_ACCESS`` base and EIP-3860 word cost.

    A factory measures a single ``CREATE2`` with ``CodeGasMeasure`` and
    stores its absolute execution cost, confirming the opcode's own
    ``execution_cost`` (which folds the keccak word surcharge) against the
    runtime charge.
    """
    create2_execution = Op.CREATE2(
        init_code_size=init_code_size
    ).execution_cost(fork)

    # Init code is all-zero bytes (`STOP`), so the child frame halts
    # immediately (zero gas) depositing empty code; the CREATE2 charges no
    # code-deposit state gas and no child execution gas is folded into the
    # measurement. The single CREATE2 execution cost is measured via
    # CodeGasMeasure with a reservoir sized for its account creation state
    # gas, keeping the GAS-measured `gas_left` free of state-gas spill.
    padded = b"\x00" * init_code_size

    push4 = 4 * Op.PUSH1(0).execution_cost(fork)
    storage = Storage()
    measure_create2 = CodeGasMeasure(
        code=Op.CREATE2(value=0, offset=0, size=init_code_size, salt=0),
        overhead_cost=push4,
        extra_stack_items=1,
        sstore_key=storage.store_next(create2_execution, "create2_execution"),
    )
    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE, new_memory_size=init_code_size)
        + measure_create2
    )
    factory = pre.deploy_contract(code=factory_code)

    tx = Transaction(
        to=factory,
        data=padded,
        state_gas_reservoir=fork.create_state_gas(code_size=0),
        sender=pre.fund_eoa(),
    )

    post = {factory: Account(storage=storage)}
    state_test(pre=pre, post=post, tx=tx)


class TestCreateTxGasBoundary:
    """
    Test the contract-creating-transaction gas boundary under EIP-8038.

    Four scenarios pin the boundary, mirroring EIP-3860's
    ``TestContractCreationGasUsage`` but with the EIP-8037/8038 2D gas
    split:

    1. ``too_little_intrinsic_gas``: one below the total intrinsic; the
       transaction is rejected (``INTRINSIC_GAS_TOO_LOW``).
    2. ``exact_intrinsic_gas``: exactly the intrinsic; the tx is valid
       but the initcode runs out of execution gas.
    3. ``too_little_execution_gas``: one below the full execution gas;
       creation fails but the tx is valid.
    4. ``exact_execution_gas``: exactly the full execution gas; creation
       succeeds.
    """

    @pytest.fixture
    def initcode(self) -> Initcode:
        """Return a small initcode that deposits a multi-byte contract."""
        # Deploy 32 bytes (STOP + 31 padding) so code-deposit state gas
        # is non-zero and the code-deposit branch is exercised.
        return Initcode(
            deploy_code=Op.STOP + Op.INVALID * 31, initcode_length=64
        )

    @pytest.fixture
    def tx_access_list(self) -> List[AccessList]:
        """
        Return an access list to raise the intrinsic gas cost above the
        EIP-7623 floor data cost, mirroring EIP-3860's fixture.
        """
        return [
            AccessList(address=Address(i), storage_keys=[])
            for i in range(1, 642)
        ]

    @pytest.fixture
    def exact_intrinsic_gas(
        self,
        fork: Fork,
        initcode: Initcode,
        tx_access_list: List[AccessList],
    ) -> int:
        """Return the total (execution + state) intrinsic tx gas cost."""
        calc = fork.transaction_intrinsic_cost_calculator()
        return calc(
            calldata=initcode,
            contract_creation=True,
            access_list=tx_access_list,
        )

    @pytest.fixture
    def exact_execution_gas(
        self, fork: Fork, exact_intrinsic_gas: int, initcode: Initcode
    ) -> int:
        """
        Return the total execution gas: intrinsic plus the top-frame
        ``NEW_ACCOUNT`` plus the initcode execution gas plus the
        code-deposit gas.

        Under EIP-2780 the created account's ``NEW_ACCOUNT`` state gas
        moved out of the intrinsic and into the top frame, so it is added
        explicitly here (the intrinsic is execution-only).

        ``deployment_gas`` is fork-aware: under EIP-8037 it splits the
        deposit into the keccak word cost (execution) and the per-byte cost
        (state), while on a fork without state-byte metering it is the
        flat execution per-byte deposit cost. The single call is therefore
        correct in either regime.
        """
        execution = exact_intrinsic_gas + fork.transaction_top_frame_state_gas(
            contract_creation=True
        )
        execution += initcode.evm_gas(fork)
        execution += initcode.deployment_gas(fork)
        return execution

    @pytest.mark.inclusion_test
    @pytest.mark.parametrize(
        "gas_test_case",
        [
            pytest.param(
                "too_little_intrinsic_gas", marks=pytest.mark.exception_test
            ),
            pytest.param("exact_intrinsic_gas"),
            pytest.param("too_little_execution_gas"),
            pytest.param("exact_execution_gas"),
        ],
    )
    @EIPChecklist.GasCostChanges.Test.OutOfGas()
    def test_create_tx_gas_boundary(
        self,
        state_test: StateTestFiller,
        pre: Alloc,
        fork: Fork,
        initcode: Initcode,
        tx_access_list: List[AccessList],
        exact_intrinsic_gas: int,
        exact_execution_gas: int,
        gas_test_case: str,
    ) -> None:
        """Drive a creation tx at each of the four gas boundary points."""
        sender = pre.fund_eoa()
        create_address = compute_create_address(address=sender, nonce=0)

        if gas_test_case == "too_little_intrinsic_gas":
            gas_limit = exact_intrinsic_gas - 1
        elif gas_test_case == "exact_intrinsic_gas":
            gas_limit = exact_intrinsic_gas
        elif gas_test_case == "too_little_execution_gas":
            gas_limit = exact_execution_gas - 1
        else:
            gas_limit = exact_execution_gas

        tx_error = (
            TransactionException.INTRINSIC_GAS_TOO_LOW
            if gas_test_case == "too_little_intrinsic_gas"
            else None
        )

        succeeds = gas_test_case == "exact_execution_gas"
        post = {
            create_address: (
                Account(code=initcode.deploy_code)
                if succeeds
                else Account.NONEXISTENT
            )
        }

        tx = Transaction(
            to=None,
            data=initcode,
            access_list=tx_access_list,
            gas_limit=gas_limit,
            error=tx_error,
            sender=sender,
        )

        # 2D block accounting: gas_used = max(execution, state). Under
        # EIP-2780 the state axis carries the fresh target's top-frame
        # NEW_ACCOUNT and (when the deposit succeeds) the per-byte
        # code-deposit gas.
        if tx_error is not None:
            header_verify = None
        elif succeeds:
            # Fresh target: top-frame NEW_ACCOUNT plus the per-byte code
            # deposit are the state-gas axis; the rest is execution.
            state_used = fork.transaction_top_frame_state_gas(
                contract_creation=True
            )
            state_used += fork.code_deposit_state_gas(
                code_size=len(initcode.deploy_code)
            )
            execution_used = gas_limit - state_used
            header_verify = Header(gas_used=max(execution_used, state_used))
        else:
            # exact_intrinsic / too_little_execution: the top-frame
            # NEW_ACCOUNT (and any deposit) cannot be covered, the whole
            # preparation rolls back, and all gas is burned as execution.
            header_verify = Header(gas_used=gas_limit)

        state_test(
            pre=pre,
            post=post,
            tx=tx,
            blockchain_test_header_verify=header_verify,
        )


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.with_all_create_opcodes()
@pytest.mark.parametrize(
    "abort_mode",
    [
        pytest.param("insufficient_balance", id="insufficient_balance"),
        pytest.param("nonce_overflow", id="nonce_overflow"),
        pytest.param(None, id="no_error"),
    ],
)
def test_aborted_create_does_not_warm_address(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    abort_mode: str | None,
) -> None:
    """
    Verify a silently-aborted CREATE does not warm the target address.

    When CREATE aborts before spawning the child frame (insufficient
    balance for the endowment, or nonce overflow), the would-be address
    is never added to the accessed-addresses set. A subsequent
    ``BALANCE`` of that address is therefore charged the full
    ``COLD_ACCOUNT_ACCESS``, not ``WARM_ACCESS``.
    """
    init_code = Op.STOP
    init_code_bytes = bytes(init_code)
    init_code_len = len(init_code)

    create_value = 1
    create_call = create_opcode(
        value=create_value, offset=0, size=init_code_len
    )

    # After the aborted CREATE, measure the BALANCE access of the
    # would-be address (passed via calldata).
    # The address should only be warm when the CREATE/CREATE2 opcode
    # successfully reached initcode execution stage.
    address_warm = abort_mode is None
    balance_code = Op.BALANCE(Op.CALLDATALOAD(0), address_warm=address_warm)
    measure = CodeGasMeasure(code=balance_code, extra_stack_items=1)

    setup = Op.MSTORE(
        0,
        int.from_bytes(init_code_bytes, "big") << (256 - 8 * init_code_len),
    )
    factory_code = setup + Op.POP(create_call) + measure

    factory_nonce = 2**64 - 1 if abort_mode == "nonce_overflow" else 1
    factory_balance = create_value
    if abort_mode == "insufficient_balance":
        factory_balance -= 1
    factory = pre.deploy_contract(
        code=factory_code, nonce=factory_nonce, balance=factory_balance
    )

    target_address = compute_create_address(
        address=factory,
        salt=0,
        initcode=init_code_bytes,
        nonce=factory_nonce,
        opcode=create_opcode,
    )

    tx = Transaction(
        to=factory,
        data=Hash(target_address, left_padding=True),
        sender=pre.fund_eoa(),
    )

    # The BALANCE must be cold: in case of error, the aborted CREATE never
    # warmed the would-be address.
    post = {
        factory: Account(storage={0: balance_code.gas_cost(fork)}),
        target_address: Account(nonce=1)
        if abort_mode is None
        else Account.NONEXISTENT,
    }
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.pre_alloc_mutable
def test_create2_to_occupied_address(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify ``CREATE2`` to an occupied address creates nothing.

    When ``CREATE2`` targets an address that is not deployable (here an
    already-deployed contract, whose ``code_hash`` is non-empty), the
    creation aborts after the account-access charge: the opcode pushes
    ``0``, bumps the factory's nonce, and consumes the withheld child
    gas grant. No child frame runs, so the occupied contract's code and
    storage are left untouched.

    This test asserts the *state* effects only; the gas outcome is
    pinned by ``test_create_collision_consumes_child_grant``.
    """
    # Initcode the factory passes to CREATE2; were the target free it
    # would deposit a single STOP. The salt is fixed so the collision
    # address is deterministic from the factory address.
    init_code = Op.STOP
    init_code_bytes = bytes(init_code)
    init_code_len = len(init_code_bytes)
    salt = 0

    # Factory CREATE2s the calldata initcode and stores the pushed result;
    # a collision pushes 0. The initcode is copied into memory before the
    # CREATE2 so the address derivation hashes exactly ``init_code_bytes``.
    storage = Storage()
    factory_code = Op.CALLDATACOPY(
        0, 0, Op.CALLDATASIZE, new_memory_size=init_code_len
    ) + Op.SSTORE(
        storage.store_next(0, "create2_collision_result"),
        Op.CREATE2(value=0, offset=0, size=init_code_len, salt=salt),
    )
    factory = pre.deploy_contract(code=factory_code)

    # The address CREATE2 would compute from this factory, salt, and
    # initcode. ``compute_create_address`` with ``opcode=Op.CREATE2`` is
    # the unified EEST helper for the CREATE2 derivation.
    collision_address = compute_create_address(
        address=factory,
        salt=salt,
        initcode=init_code_bytes,
        opcode=Op.CREATE2,
    )

    # Pre-occupy the collision address with a contract carrying distinct
    # code and storage so a successful (and therefore incorrect) creation
    # would be detectable. A non-empty ``code_hash`` makes the account
    # non-deployable (``account_deployable`` is False).
    #
    # `address=` hard-codes the occupant at the derived collision address;
    # it requires `pre_alloc_mutable`. This is the only way to pre-seat the
    # exact CREATE2 target, mirroring
    # `tests/frontier/create/test_create_collision.py`.
    occupant_code = Op.SSTORE(0, 0x42) + Op.STOP
    occupant_storage = Storage({0x1: 0xCAFE})  # type: ignore[dict-item]
    pre.deploy_contract(
        code=occupant_code,
        storage=occupant_storage,
        nonce=1,
        address=collision_address,
    )

    tx = Transaction(
        to=factory,
        data=init_code_bytes,
        sender=pre.fund_eoa(),
    )

    # Factory stored a 0 result; the occupant is untouched (its initcode
    # never ran, so slot 0 stays unset and slot 1 keeps its seeded value).
    post = {
        factory: Account(storage=storage),
        collision_address: Account(
            code=occupant_code, storage=occupant_storage
        ),
    }
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.with_all_create_opcodes()
@pytest.mark.parametrize(
    "abort_mode",
    [
        pytest.param("insufficient_balance", id="insufficient_balance"),
        pytest.param("nonce_overflow", id="nonce_overflow"),
    ],
)
@pytest.mark.parametrize(
    "sufficient_gas", [True, False], ids=["sufficient", "insufficient"]
)
def test_aborted_create_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    abort_mode: str,
    sufficient_gas: bool,
) -> None:
    """
    A preflight-aborted ``CREATE`` is charged ``CREATE_ACCESS`` and
    nothing beyond it.

    The abort (insufficient balance for the endowment, or a nonce at
    ``2**64 - 1``) is decided *before* the destination access, so the
    account-creation state gas is never charged and no child gas grant
    is withheld. The whole operation therefore costs exactly the
    opcode's own execution charge.

    Forwarding precisely that much succeeds; one gas less makes the
    opcode itself run out. The boundary is two-sided, so it pins
    ``CREATE_ACCESS`` exactly rather than bounding it from one side.
    Zero-size init code keeps the charge free of memory-expansion and
    EIP-3860 word costs (and, for ``CREATE2``, of keccak word costs),
    leaving ``CREATE_ACCESS`` as the whole of it.
    """
    # A non-zero endowment is what the insufficient-balance arm starves;
    # the nonce-overflow arm funds it so the balance check passes and the
    # nonce is the sole reason for the abort.
    endowment = 1
    create_call = (
        Op.CREATE2(value=endowment, offset=0, size=0, salt=0)
        if create_opcode == Op.CREATE2
        else Op.CREATE(value=endowment, offset=0, size=0)
    )

    # Everything the child frame spends: the operand pushes plus the
    # opcode's execution charge. Nothing follows the CREATE, so the code
    # runs off its end into an implicit STOP at zero gas.
    forwarded = create_call.execution_cost(fork)
    if not sufficient_gas:
        forwarded -= 1

    nonce = 2**64 - 1 if abort_mode == "nonce_overflow" else 1
    balance = 0 if abort_mode == "insufficient_balance" else endowment
    factory = pre.deploy_contract(
        code=create_call, nonce=nonce, balance=balance
    )

    storage = Storage()
    caller = pre.deploy_contract(
        code=Op.SSTORE(
            storage.store_next(1 if sufficient_gas else 0, "call_result"),
            Op.CALL(gas=forwarded, address=factory),
        ),
    )

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        state_gas_reservoir=0,
    )

    # The abort returns before the nonce increment, so the factory is
    # left exactly as deployed in both arms.
    post = {
        caller: Account(storage=storage),
        factory: Account(nonce=nonce, balance=balance),
    }
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.OutOfGas()
@pytest.mark.pre_alloc_mutable
@pytest.mark.parametrize("trailing_gas", [0, 1], ids=["exact", "one_too_many"])
def test_create_collision_consumes_child_grant(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    trailing_gas: int,
) -> None:
    """
    A ``CREATE2`` collision consumes the withheld child gas grant and
    charges no state gas.

    The collision is detected *after* the child grant is withheld, and
    the aborting branch returns without ever restoring it, so the
    frame loses the all-but-one-64th share outright. With ``R`` gas left
    when the grant is withheld, exactly ``R // 64`` survives the
    collision.

    A budget of ``64 * n`` is forwarded past the opcode so that ``n``
    gas remains, and the factory then burns ``n`` gas in ``JUMPDEST``s
    (one gas each, so the budget is spent at the finest granularity
    available). Spending exactly ``n`` succeeds; one more runs out.
    Without the grant being consumed the frame would still hold the
    full ``64 * n``, so this fails loudly if the burn stops happening.

    It also pins the *absence* of a state-gas charge. A collision target
    is necessarily alive — ``account_deployable`` is false only for a
    non-zero nonce or non-empty code, either of which makes the account
    non-empty — so ``NEW_ACCOUNT`` is never charged on this path and
    there is correspondingly nothing to refund. The transaction runs
    with a zero reservoir and a budget far below ``NEW_ACCOUNT``, so a
    spurious charge would spill into execution gas and abort the frame.
    """
    # Zero-size init code: the CREATE2 address derivation hashes the
    # empty string, so the collision address needs no memory setup and
    # the opcode charge carries no keccak or EIP-3860 word cost.
    salt = 0
    create_call = Op.CREATE2(value=0, offset=0, size=0, salt=salt)

    # Gas left when the grant is withheld, chosen as a multiple of 64 so
    # the surviving share is exact rather than rounded.
    surviving_gas = 10
    budget = 64 * surviving_gas

    factory_code = create_call + Op.JUMPDEST * (surviving_gas + trailing_gas)
    factory = pre.deploy_contract(code=factory_code)

    collision_address = compute_create_address(
        address=factory,
        salt=salt,
        initcode=b"",
        opcode=Op.CREATE2,
    )

    # Pre-occupy the derived address so the creation collides. Non-empty
    # code is what makes it non-deployable; `address=` hard-codes the
    # occupant there and requires `pre_alloc_mutable`.
    occupant_code = Op.SSTORE(0, 0x42) + Op.STOP
    pre.deploy_contract(code=occupant_code, nonce=1, address=collision_address)

    sufficient_gas = trailing_gas == 0
    storage = Storage()
    caller = pre.deploy_contract(
        code=Op.SSTORE(
            storage.store_next(1 if sufficient_gas else 0, "call_result"),
            Op.CALL(
                gas=create_call.execution_cost(fork) + budget,
                address=factory,
            ),
        ),
    )

    tx = Transaction(
        to=caller,
        sender=pre.fund_eoa(),
        state_gas_reservoir=0,
    )

    # The collision bumps the factory's nonce (it happens on the
    # aborting branch, after the deployability check) and leaves the
    # occupant untouched, its own initcode never having run. The
    # out-of-gas arm reverts the frame, so the nonce bump is rolled
    # back with it.
    post = {
        caller: Account(storage=storage),
        factory: Account(nonce=2 if sufficient_gas else 1),
        collision_address: Account(code=occupant_code, storage={}),
    }
    state_test(pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize(
    "first_initcode_reverts", [True, False], ids=["reverts", "succeeds"]
)
def test_failed_initcode_refills_creation_state_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    first_initcode_reverts: bool,
) -> None:
    """
    A failed init code refills the account-creation state gas, so one
    creation's worth of reservoir funds a failed creation and a later
    successful one.

    ``CREATE`` charges the account-creation state gas on the
    destination access, before the child runs, and resolves it by the
    state's fate afterwards: a child that errors gets the charge
    credited straight back. This is the one ``CREATE`` failure path that
    moves state gas, and the credit is observable as the absence of a
    spill.

    The factory is given a reservoir sized for exactly *one* creation
    and performs two ``CREATE``s, the second wrapped in
    ``CodeGasMeasure``. When the first init code reverts, its charge is
    credited back and the second creation draws the reservoir, so the
    measured *execution* cost is the bare opcode's. When the first
    init code succeeds, the reservoir is gone and the second creation
    spills the account-creation gas into ``gas_left``, so the measured
    cost is the opcode's full two-dimensional ``gas_cost``. The two arms
    therefore differ by exactly the charge under test.
    """
    # The first creation's init code, five bytes either way so both arms
    # run identical code with identical memory. `REVERT` is used rather
    # than an invalid opcode so the child returns its unused execution
    # gas and the measurement below sees only the state-gas effect.
    first_initcode = bytes(Op.REVERT(0, 0)) if first_initcode_reverts else b""
    initcode_len = 5
    assert len(first_initcode) <= initcode_len
    first_initcode = first_initcode.ljust(initcode_len, b"\x00")
    initcode_word = int.from_bytes(first_initcode, "big") << (
        256 - 8 * initcode_len
    )

    # The second creation uses zero-size init code, so its child halts
    # immediately, deposits empty code and returns its whole grant. That
    # keeps the measured window the CREATE opcode's own charge.
    measured_bare = Op.CREATE(init_code_size=0)
    measured_call = Op.CREATE(value=0, offset=0, size=0)
    arg_pushes = 3 * Op.PUSH1(0).execution_cost(fork)

    # Reservoir funded, so no spill; reservoir spent, so the whole
    # account-creation charge lands on the execution dimension.
    expected_measured = (
        measured_bare.execution_cost(fork)
        if first_initcode_reverts
        else measured_bare.gas_cost(fork)
    )

    storage = Storage()
    factory_code = (
        Op.MSTORE(0, initcode_word)
        + Op.POP(Op.CREATE(value=0, offset=0, size=initcode_len))
        + CodeGasMeasure(
            code=measured_call,
            overhead_cost=arg_pushes,
            extra_stack_items=1,
            sstore_key=storage.store_next(
                expected_measured, "second_create_execution_gas"
            ),
        )
    )
    factory = pre.deploy_contract(code=factory_code)

    # `CREATE` derives from the factory's nonce at the time of the call,
    # and the increment survives a failed child, so the two addresses are
    # the same in both arms.
    first_address = compute_create_address(address=factory, nonce=1)
    second_address = compute_create_address(address=factory, nonce=2)

    tx = Transaction(
        to=factory,
        sender=pre.fund_eoa(),
        state_gas_reservoir=fork.create_state_gas(code_size=0),
    )

    # A reverted creation leaves nothing behind; a successful one
    # deposits the empty code its init code returned. The second
    # creation succeeds in both arms — in the spilling arm because
    # execution gas can cover the charge — which is what makes the
    # measured value, not the post-state, the discriminator.
    post = {
        factory: Account(nonce=3, storage=storage),
        first_address: Account.NONEXISTENT
        if first_initcode_reverts
        else Account(nonce=1, code=b""),
        second_address: Account(nonce=1, code=b""),
    }
    state_test(pre=pre, post=post, tx=tx)
