"""
Tests for the EIP-8038 [State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038)
``CREATE``/``CREATE2`` regular-gas dimension.

Under EIP-8038 the contract-creation opcodes are repriced in their
*regular* gas dimension to ``CREATE_ACCESS`` (``ACCOUNT_WRITE`` +
``COLD_STORAGE_ACCESS`` = 11,000), on top of which the EIP-3860 init
code word cost (2 per word) and, for ``CREATE2`` only, an additional
keccak word cost (6 per word) are charged. The new-account creation
and per-byte code deposit charges are the EIP-8037 *state* dimension,
covered in
``eip8037_state_creation_gas_cost_increase/test_state_gas_create.py``.

These tests isolate and assert the EIP-8038 *regular* dimension. At the
contract-creating-transaction boundary the state component is re-derived
only to feed the ``max(regular, state)`` block-header accounting.
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
def test_create_regular_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    create_opcode: Op,
    init_code_size: int,
) -> None:
    """
    Measure the regular gas of CREATE/CREATE2 and assert the schedule.

    The EIP-8038 *regular* dimension is ``CREATE_ACCESS`` (11,000) plus
    the EIP-3860 init code word cost (2 per word) plus, for ``CREATE2``
    only, an additional keccak word cost (6 per word). The EIP-8037
    account-creation state gas is excluded by subtracting
    ``create_state_gas(0)``.
    """
    gas_costs = fork.gas_costs()
    # The EIP-8038 CREATE regular base equals ACCOUNT_WRITE +
    # COLD_STORAGE_ACCESS = 11,000.
    assert gas_costs.OPCODE_CREATE_BASE == 11_000
    assert (
        gas_costs.OPCODE_CREATE_BASE
        == gas_costs.ACCOUNT_WRITE + gas_costs.COLD_STORAGE_ACCESS
    )

    # Isolate the regular dimension: opcode total minus its account
    # creation state gas (the only state component carried by the CREATE
    # opcode itself; code deposit is charged on RETURN inside initcode).
    create_meta = create_opcode(init_code_size=init_code_size)
    regular_gas = create_meta.gas_cost(fork) - fork.create_state_gas(
        code_size=0
    )
    # Equivalent isolation via the regular_cost helper.
    assert regular_gas == create_meta.regular_cost(fork)

    init_code_words = (init_code_size + 31) // 32
    expected_regular = (
        gas_costs.OPCODE_CREATE_BASE
        + gas_costs.CODE_INIT_PER_WORD * init_code_words
    )
    if create_opcode == Op.CREATE2:
        expected_regular += (
            gas_costs.OPCODE_KECCAK256_PER_WORD * init_code_words
        )
    assert regular_gas == expected_regular

    # Runtime confirmation via CodeGasMeasure: a factory whose CREATE
    # deploys empty code, so no code-deposit state gas is charged and the
    # only state component is the account-creation gas funded from the
    # reservoir. The initcode is brought into memory BEFORE the measured
    # window, so the memory-expansion charge is excluded; the measured
    # value is the CREATE opcode's regular cost exactly. The overhead
    # subtracts the create-call argument pushes (the create leaves one
    # stack item, its result).
    #
    # The initcode is all-zero bytes (`STOP`), so the child frame halts
    # immediately consuming zero gas and deposits empty code. This keeps
    # the measured value the CREATE opcode's own regular cost, with no
    # child-execution gas folded in. `init_code_size` still drives the
    # opcode's per-init-word charge.
    padded_init = b"\x00" * init_code_size

    create_call = (
        Op.CREATE2(value=0, offset=0, size=init_code_size, salt=0)
        if create_opcode == Op.CREATE2
        else Op.CREATE(value=0, offset=0, size=init_code_size)
    )
    arg_pushes = (4 if create_opcode == Op.CREATE2 else 3) * gas_costs.VERY_LOW

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
        sstore_key=storage.store_next(regular_gas, "create_regular_gas"),
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
    regular cost shared with ``CREATE``. Both opcodes carry the identical
    EIP-8038 ``CREATE_ACCESS`` base and EIP-3860 word cost.

    The regular-gas delta is asserted via the opcode model
    (``create2_regular - create_regular`` equals the keccak word
    surcharge). At runtime a factory then measures a single ``CREATE2``
    with ``CodeGasMeasure`` and stores its absolute regular cost: the
    surcharge is established by the model assertion, and the runtime leg
    confirms the absolute ``CREATE2`` regular cost.
    """
    gas_costs = fork.gas_costs()
    init_code_words = (init_code_size + 31) // 32
    keccak_surcharge = gas_costs.OPCODE_KECCAK256_PER_WORD * init_code_words

    create_regular = Op.CREATE(init_code_size=init_code_size).regular_cost(
        fork
    )
    create2_regular = Op.CREATE2(init_code_size=init_code_size).regular_cost(
        fork
    )
    assert create2_regular - create_regular == keccak_surcharge

    # Runtime confirmation. Init code is all-zero bytes (`STOP`), so the
    # child frame halts immediately (zero gas) depositing empty code; the
    # CREATE2 charges no code-deposit state gas and no child execution gas
    # is folded into the measurement. The single CREATE2 regular cost is
    # measured via CodeGasMeasure with a reservoir sized for its account
    # creation state gas, keeping the GAS-measured `gas_left` free of
    # state-gas spill. The opcode-model assertion above is the
    # load-bearing keccak-delta check; this confirms the absolute value.
    padded = b"\x00" * init_code_size

    push4 = 4 * gas_costs.VERY_LOW
    storage = Storage()
    measure_create2 = CodeGasMeasure(
        code=Op.CREATE2(value=0, offset=0, size=init_code_size, salt=0),
        overhead_cost=push4,
        extra_stack_items=1,
        sstore_key=storage.store_next(create2_regular, "create2_regular"),
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
        """Return the total (regular + state) intrinsic tx gas cost."""
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
        Return the total execution gas: intrinsic plus the initcode
        execution gas plus the code-deposit gas.

        ``deployment_gas`` is fork-aware: under EIP-8037 it splits the
        deposit into the keccak word cost (regular) and the per-byte cost
        (state), while on a fork without state-byte metering it is the
        flat regular per-byte deposit cost. The single call is therefore
        correct in either regime.
        """
        execution = exact_intrinsic_gas + initcode.execution_gas(fork)
        execution += initcode.deployment_gas(fork)
        return execution

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

        # 2D block accounting: gas_used = max(regular, state). The state
        # axis carries the intrinsic NEW_ACCOUNT and (when the deposit
        # succeeds) the per-byte code-deposit gas.
        if tx_error is not None:
            header_verify = None
        else:
            intrinsic_state = (
                fork.transaction_intrinsic_state_gas(contract_creation=True)
                if hasattr(fork, "transaction_intrinsic_state_gas")
                else 0
            )
            regular_used = gas_limit - intrinsic_state
            state_used = intrinsic_state
            if succeeds:
                code_deposit_state = fork.code_deposit_state_gas(
                    code_size=len(initcode.deploy_code)
                )
                state_used += code_deposit_state
                regular_used -= code_deposit_state
            header_verify = Header(gas_used=max(regular_used, state_used))

        state_test(
            pre=pre,
            post=post,
            tx=tx,
            blockchain_test_header_verify=header_verify,
        )


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
    ``COLD_ACCOUNT_ACCESS`` (3,000), not ``WARM_ACCESS`` (100).
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


@pytest.mark.pre_alloc_mutable
def test_create2_to_occupied_address(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify ``CREATE2`` to an occupied address creates nothing and refunds.

    When ``CREATE2`` targets an address that is not deployable (here an
    already-deployed contract, whose ``code_hash`` is non-empty), the
    creation aborts after the account-access charge: the opcode pushes
    ``0``, bumps the factory's nonce, charges the message gas to the
    regular dimension, and refunds the ``NEW_ACCOUNT`` *state* gas so no
    net account-creation charge lands. No child frame runs, so the
    occupied contract's code and storage are left untouched.
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
    # exact CREATE2 target, mirroring the EIP-7610 collision suite.
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
