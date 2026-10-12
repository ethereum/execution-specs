"""Check deterministic inclusion-list accounting and isolated EVM replay."""

from dataclasses import replace

import pytest
from ethereum_rlp import rlp
from ethereum_types.bytes import Bytes, Bytes8, Bytes32, Bytes256
from ethereum_types.numeric import U64, U256, Uint
from execution_testing import Address as AuthoredAddress
from execution_testing import (
    Bytecode,
    Frame,
    FrameSignature,
    Initcode,
    Op,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Bogota

from ethereum.crypto.hash import keccak256
from ethereum.exceptions import InvalidBlock
from ethereum.forks.bogota import fork
from ethereum.forks.bogota.block_access_lists import (
    BlockAccessListBuilder,
    hash_block_access_list,
)
from ethereum.forks.bogota.blocks import Block, Header
from ethereum.forks.bogota.bloom import logs_bloom
from ethereum.forks.bogota.fork_types import ExecutionGas, StateGas
from ethereum.forks.bogota.inclusion_list_frames import (
    MAX_REPLAY_CODE_BODIES,
    MAX_REPLAY_CODE_BYTES,
    classify_frame_candidate,
    verify_candidate_signatures,
)
from ethereum.forks.bogota.inclusion_lists import (
    MAX_VERIFY_GAS_PER_IL,
    InclusionClaim,
    InclusionListInputs,
    admitted_frame_candidates,
    capture_inclusion_list_state,
    check_inclusion_list,
    decode_inclusion_transaction,
    evaluation_indices,
    snapshot_indices,
    validate_inclusion_list_inputs,
)
from ethereum.forks.bogota.state_tracker import BlockState, extract_block_diff
from ethereum.forks.bogota.transactions.frame_transaction import (
    FrameTransaction,
)
from ethereum.forks.bogota.vm import BlockEnvironment, BlockOutput
from ethereum.merkle_patricia_trie import root
from ethereum.state import EMPTY_CODE_HASH, Account, Address
from ethereum.state_mpt import State, set_account, set_storage, store_code
from tests.bogota.eip8272_recent_roots.spec import Spec as RecentRootSpec


def frame_envelope(
    sender: int = 0x1000,
    *,
    execution: int = 50_000,
    state: int = 0,
    nonce: int = 1,
    signatures: list[FrameSignature] | None = None,
    suffix: list[Frame] | None = None,
) -> Bytes:
    """Encode a contract account transaction with explicit frame budgets."""
    tx = Transaction(
        sender=AuthoredAddress(sender),
        nonce=nonce,
        frames=[
            Frame(
                mode=1,
                flags=3,
                gas_limit=execution,
                state_gas_limit=state,
            ),
            *(suffix or []),
        ],
        signatures=[] if signatures is None else signatures,
    ).with_signature_and_sender()
    return Bytes(tx.rlp())


def inclusion_inputs(
    envelopes: tuple[Bytes, ...],
    *,
    membership: tuple[Bytes, ...] | None = None,
    claims: tuple[InclusionClaim, ...] = (),
) -> InclusionListInputs:
    """Supply explicit membership for every envelope unless given."""
    return InclusionListInputs(
        transactions=envelopes,
        membership=(
            tuple(Bytes(b"\x01\x00") for _ in envelopes)
            if membership is None
            else membership
        ),
        claims=claims,
    )


@pytest.fixture
def replay_environment() -> BlockEnvironment:
    """Create a funded sender whose real EVM code approves validation."""
    state = State()
    code_hash = store_code(state, Bytes(Op.APPROVE(0, 0, 3)))
    set_account(
        state,
        Address((0x1000).to_bytes(20, "big")),
        Account(nonce=Uint(1), balance=U256(10**18), code_hash=code_hash),
    )
    return BlockEnvironment(
        chain_id=U64(1),
        state=BlockState(pre_state=state),
        block_gas_limit=Uint(30_000_000),
        block_hashes=[],
        coinbase=Address(bytes(20)),
        number=Uint(1),
        base_fee_per_gas=Uint(0),
        time=U256(12),
        prev_randao=Bytes32(bytes(32)),
        excess_blob_gas=U64(0),
        parent_beacon_block_root=Bytes32(bytes(32)),
        block_access_list_builder=BlockAccessListBuilder(),
        slot_number=U64(2),
    )


def test_budget_order_is_by_hash_not_input_order() -> None:
    """Admit exactly four maximum-cost candidates in canonical hash order."""
    cost = int(MAX_VERIFY_GAS_PER_IL) // 4
    envelopes = tuple(
        frame_envelope(nonce=i, execution=cost) for i in range(5)
    )
    ordered = sorted(envelopes, key=lambda item: (keccak256(item), item))
    expected = ordered[:4]
    for permutation in (envelopes, envelopes[::-1], tuple(ordered[::-1])):
        inputs = inclusion_inputs(permutation)
        validate_inclusion_list_inputs(inputs)
        assert list(admitted_frame_candidates(inputs)) == expected


@pytest.mark.parametrize("duplicate_position", [False, True])
def test_membership_positions_do_not_pool_budgets(
    duplicate_position: bool,
) -> None:
    """Repeating one list in two positions does not admit its fifth item."""
    cost = int(MAX_VERIFY_GAS_PER_IL) // 4
    envelopes = tuple(
        frame_envelope(nonce=i, execution=cost) for i in range(5)
    )
    ordered = tuple(
        sorted(envelopes, key=lambda item: (keccak256(item), item))
    )
    mask = Bytes(b"\x03\x00" if duplicate_position else b"\x01\x00")
    inputs = inclusion_inputs(ordered, membership=(mask,) * 5)
    assert set(admitted_frame_candidates(inputs)) == set(ordered[:4])
    # An independent position containing only the final item protects it.
    inputs = replace(
        inputs, membership=inputs.membership[:4] + (Bytes(b"\x05\x00"),)
    )
    assert set(admitted_frame_candidates(inputs)) == set(ordered)


def envelope_in_hash_bucket(
    bucket: int,
    *,
    execution: int,
    signatures: list[FrameSignature] | None = None,
) -> Bytes:
    """Choose deterministic nonces to exercise a specified fill order."""
    for nonce in range(4096):
        envelope = frame_envelope(
            nonce=nonce, execution=execution, signatures=signatures
        )
        if keccak256(envelope)[0] // 32 == bucket:
            return envelope
    raise AssertionError("No envelope found in the requested hash bucket")


@pytest.mark.parametrize("malformed", [False, True])
def test_signature_failure_budget_charging(malformed: bool) -> None:
    """Distinguish no debit, signature-only debit and erroneous full debit."""
    invalid_signature = FrameSignature(
        scheme=1,
        signer=AuthoredAddress(0x1000),
        signature=b"\x00" + (1).to_bytes(32, "big") * 2,
    )
    wrong_signer = envelope_in_hash_bucket(
        0, execution=200_000, signatures=[invalid_signature]
    )
    tx = decode_inclusion_transaction(wrong_signer)
    assert isinstance(tx, FrameTransaction)
    candidate = classify_frame_candidate(tx)
    assert candidate is not None
    assert not verify_candidate_signatures(candidate)
    signature_cost = int(candidate.signature_cost)
    assert 0 < signature_cost < 2**18

    invalid = wrong_signer
    if malformed:
        invalid = envelope_in_hash_bucket(
            0,
            execution=200_000,
            signatures=[
                invalid_signature.model_copy(update={"signature": bytes(65)})
            ],
        )
        malformed_tx = decode_inclusion_transaction(invalid)
        assert isinstance(malformed_tx, FrameTransaction)
        assert classify_frame_candidate(malformed_tx) is None

    valid = tuple(
        envelope_in_hash_bucket(bucket, execution=cost)
        for bucket, cost in enumerate(
            [2**18, 2**18, 2**18, 2**18 - signature_cost, signature_cost],
            start=1,
        )
    )
    # The first four spend exactly the fill budget minus signature work.
    # A free malformed item leaves room for the fifth; a wrong signer
    # consumes that room, without spending its unexecuted 200,000 gas.
    inputs = inclusion_inputs((invalid, *valid))
    validate_inclusion_list_inputs(inputs)
    expected = valid if malformed else valid[:4]
    assert set(admitted_frame_candidates(inputs)) == set(expected)


@pytest.mark.parametrize("over_limit", [False, True])
def test_declared_prefix_work_boundary(over_limit: bool) -> None:
    """Apply the declared work bound before state or code execution."""
    envelope = frame_envelope(execution=2**18 + int(over_limit))
    tx = decode_inclusion_transaction(envelope)
    assert isinstance(tx, FrameTransaction)
    candidate = classify_frame_candidate(tx)
    assert (candidate is None) == over_limit


@pytest.mark.parametrize("duplicate_indices", [(0, 0), (0, 1)])
def test_duplicate_claim_hashes_default_to_end(
    duplicate_indices: tuple[int, int],
) -> None:
    """Ignore every occurrence of a repeated hash, even equal claims."""
    envelope = frame_envelope()
    tx_hash = keccak256(envelope)
    inputs = inclusion_inputs(
        (envelope,),
        claims=tuple(
            InclusionClaim(tx_hash, U64(index)) for index in duplicate_indices
        ),
    )
    assert tx_hash not in evaluation_indices(inputs, Uint(1))
    assert snapshot_indices(inputs, Uint(1)) == {Uint(1)}


def test_claim_max_uint64_clamps_without_overflow() -> None:
    """Clamp a valid maximum integer to the payload transaction count."""
    envelope = frame_envelope()
    tx_hash = keccak256(envelope)
    inputs = inclusion_inputs(
        (envelope,), claims=(InclusionClaim(tx_hash, U64.MAX_VALUE),)
    )
    assert evaluation_indices(inputs, Uint(2)) == {tx_hash: Uint(2)}


def test_irrelevant_claims_do_not_require_early_snapshots() -> None:
    """Avoid copying states for included, ordinary and unmatched claims."""
    frame = frame_envelope()
    ordinary = Bytes(
        Transaction(to=AuthoredAddress(0x2000), gas_limit=21_000)
        .with_signature_and_sender()
        .rlp()
    )
    inputs = inclusion_inputs(
        (frame, ordinary),
        claims=tuple(
            InclusionClaim(tx_hash, U64(0))
            for tx_hash in (
                keccak256(frame),
                keccak256(ordinary),
                Bytes32(b"\xff" * 32),
            )
        ),
    )
    assert snapshot_indices(inputs, Uint(2), transactions=(frame,)) == {
        Uint(2)
    }


@pytest.mark.parametrize(
    "membership",
    [b"", b"\x01", b"\x00\x00", b"\x01\x00\x00"],
)
def test_malformed_membership_is_container_error(membership: bytes) -> None:
    """Reject metadata errors without treating them as omission grounds."""
    inputs = inclusion_inputs(
        (frame_envelope(),), membership=(Bytes(membership),)
    )
    with pytest.raises(ValueError, match="membership"):
        validate_inclusion_list_inputs(inputs)


@pytest.mark.parametrize("over_limit", [False, True])
def test_per_position_byte_limit(over_limit: bool) -> None:
    """Apply the byte bound independently, including committee position 15."""
    envelope = Bytes(b"\x06" + bytes(8191 + int(over_limit)))
    inputs = inclusion_inputs((envelope,), membership=(Bytes(b"\x00\x80"),))
    if over_limit:
        with pytest.raises(ValueError, match="byte limit"):
            validate_inclusion_list_inputs(inputs)
    else:
        validate_inclusion_list_inputs(inputs)


@pytest.mark.parametrize("over_limit", [False, True])
def test_claim_count_bound_preserves_duplicates(over_limit: bool) -> None:
    """Count ordered claims before duplicate hashes are ignored."""
    envelope = frame_envelope()
    claim = InclusionClaim(keccak256(envelope), U64(0))
    inputs = inclusion_inputs(
        (envelope,), claims=(claim,) * (4096 + int(over_limit))
    )
    if over_limit:
        with pytest.raises(ValueError, match="Too many"):
            validate_inclusion_list_inputs(inputs)
    else:
        validate_inclusion_list_inputs(inputs)
        assert evaluation_indices(inputs, Uint(1)) == {}


def test_replay_isolation(replay_environment: BlockEnvironment) -> None:
    """Keep approval fees, nonce and accesses out of payload state."""
    env = replay_environment
    inputs = inclusion_inputs((frame_envelope(),))
    output = BlockOutput()
    snapshots = {Uint(0): capture_inclusion_list_state(env, output)}
    assert not check_inclusion_list(env, (), inputs, snapshots)
    assert not check_inclusion_list(env, (), inputs, snapshots)
    assert env.state.account_writes == {}
    assert env.state.account_reads == set()
    assert env.state.storage_writes == {}
    assert env.state.storage_reads == set()
    assert snapshots[Uint(0)].state.account_writes == {}
    assert snapshots[Uint(0)].state.account_reads == set()
    assert output.block_gas_used == 0
    assert output.block_state_gas_used == 0


@pytest.mark.parametrize("dimension", ["execution", "state"])
@pytest.mark.parametrize("fits", [False, True])
def test_full_transaction_reservations_at_index(
    replay_environment: BlockEnvironment,
    dimension: str,
    fits: bool,
) -> None:
    """Reserve the entire transaction, including the unreplayed body."""
    env = replay_environment
    suffix = Frame(mode=2, gas_limit=200_000, state_gas_limit=200_000)
    envelope = frame_envelope(suffix=[suffix])
    inputs = inclusion_inputs((envelope,))
    # Only one gas dimension binds; the other remains comfortably free.
    used = int(env.block_gas_limit) - (1_000_000 if fits else 100_000)
    output = BlockOutput(
        block_gas_used=ExecutionGas(
            Uint(used if dimension == "execution" else 0)
        ),
        block_state_gas_used=StateGas(
            Uint(used if dimension == "state" else 0)
        ),
    )
    snapshots = {Uint(0): capture_inclusion_list_state(env, output)}
    assert check_inclusion_list(env, (), inputs, snapshots) == (not fits)


def test_included_items_still_consume_fill_budget(
    replay_environment: BlockEnvironment,
) -> None:
    """Charge included candidates before considering omitted candidates."""
    cost = int(MAX_VERIFY_GAS_PER_IL) // 4
    envelopes = tuple(
        frame_envelope(nonce=i, execution=cost) for i in range(5)
    )
    ordered = tuple(
        sorted(envelopes, key=lambda item: (keccak256(item), item))
    )
    inputs = inclusion_inputs(ordered)
    included = ordered[:4]
    # No snapshot is needed: every admitted item is included, the last is
    # over budget and must not cause an EVM replay or a state lookup.
    assert check_inclusion_list(replay_environment, included, inputs, {})


def test_malformed_transaction_is_skipped_not_container_error(
    replay_environment: BlockEnvironment,
) -> None:
    """A nonempty but undecodable envelope imposes no inclusion obligation."""
    inputs = inclusion_inputs((Bytes(b"\x06\xff"),))
    validate_inclusion_list_inputs(inputs)
    assert check_inclusion_list(replay_environment, (), inputs, {})


@pytest.mark.parametrize(
    ("kind", "satisfied"),
    [
        ("canonical", False),
        ("nested", True),
        ("wrong-code", True),
        ("expired", True),
        ("future", True),
        ("out-of-gas", True),
    ],
)
def test_recent_root_exception_is_canonical_and_top_level(
    replay_environment: BlockEnvironment, kind: str, satisfied: bool
) -> None:
    """Grant only the canonical top-level recent-root frame its exceptions."""
    env = replay_environment
    state = env.state.pre_state
    assert isinstance(state, State)
    address = Address(RecentRootSpec.RECENT_ROOT_ADDRESS)
    code = RecentRootSpec.RECENT_ROOT_CODE
    if kind == "wrong-code":
        # Unreachable trailing code preserves EVM behavior but changes the
        # canonical runtime identity required to grant the exception.
        code += bytes(Op.STOP)
    code_hash = store_code(state, Bytes(code))
    set_account(
        state,
        address,
        Account(nonce=Uint(1), balance=U256(0), code_hash=code_hash),
    )
    set_storage(
        state,
        address,
        Bytes32(RecentRootSpec.VECTOR_STORAGE_KEY),
        U256.from_be_bytes(RecentRootSpec.VECTOR_ENTRY_HASH),
    )
    data = (
        RecentRootSpec.VECTOR_SOURCE_ID
        + RecentRootSpec.VECTOR_SLOT.to_bytes(8, "big")
        + RecentRootSpec.VECTOR_ROOT
    )
    recent = Frame(
        mode=1,
        flags=0,
        target=AuthoredAddress(address),
        gas_limit=1 if kind == "out-of-gas" else 20_000,
        state_gas_limit=0,
        data=data,
    )
    approve = Frame(mode=1, flags=3, gas_limit=50_000, state_gas_limit=0)
    frames = [recent, approve]
    if kind == "nested":
        sender_code = (
            Op.CALLDATACOPY(0, 0, len(data))
            + Op.POP(
                Op.STATICCALL(
                    gas=20_000,
                    address=address,
                    args_offset=0,
                    args_size=len(data),
                )
            )
            + Op.APPROVE(0, 0, 3)
        )
        set_account(
            state,
            Address((0x1000).to_bytes(20, "big")),
            Account(
                nonce=Uint(1),
                balance=U256(10**18),
                code_hash=store_code(state, Bytes(sender_code)),
            ),
        )
        frames = [approve.model_copy(update={"data": data})]
    elif kind == "expired":
        env.slot_number = U64(RecentRootSpec.RECENT_ROOT_LENGTH + 1)
    elif kind == "future":
        env.slot_number = U64(RecentRootSpec.VECTOR_SLOT)
    elif kind not in ("canonical", "wrong-code", "out-of-gas"):
        raise ValueError(kind)
    tx = Transaction(
        sender=AuthoredAddress(0x1000), nonce=1, frames=frames, signatures=[]
    ).with_signature_and_sender()
    inputs = inclusion_inputs((Bytes(tx.rlp()),))
    snapshots = {Uint(0): capture_inclusion_list_state(env, BlockOutput())}
    assert check_inclusion_list(env, (), inputs, snapshots) == satisfied


@pytest.mark.parametrize("dimension", ["bodies", "bytes"])
@pytest.mark.parametrize("fits", [False, True])
def test_replay_code_limits_are_enforced(
    replay_environment: BlockEnvironment, dimension: str, fits: bool
) -> None:
    """
    Bound distinct code bodies and their bytes before continuing replay.

    The sender's own code is a body, and each helper it calls is another.
    """
    env = replay_environment
    state = env.state.pre_state
    assert isinstance(state, State)
    helper_count = MAX_REPLAY_CODE_BODIES - 1 if dimension == "bodies" else 2
    if dimension == "bodies" and not fits:
        helper_count += 1
    helpers = [
        Address((0x2000 + i).to_bytes(20, "big")) for i in range(helper_count)
    ]
    sender_code = Bytes(
        sum(
            (Op.POP(Op.STATICCALL(gas=5_000, address=h)) for h in helpers),
            Bytecode(),
        )
        + Op.APPROVE(0, 0, 3)
    )
    if dimension == "bodies":
        helper_codes = [
            Bytes(Op.PUSH2(i) + Op.STOP) for i in range(helper_count)
        ]
    else:
        # Two helpers fill the byte limit exactly with the sender's code.
        first = 2**16
        second = MAX_REPLAY_CODE_BYTES - len(sender_code) - first
        if not fits:
            second += 1
        helper_codes = [
            Bytes(Op.STOP + b"\x5b" * (first - 1)),
            Bytes(Op.STOP + b"\x5c" * (second - 1)),
        ]
    for address, code in (
        *zip(helpers, helper_codes, strict=True),
        (Address((0x1000).to_bytes(20, "big")), sender_code),
    ):
        set_account(
            state,
            address,
            Account(
                nonce=Uint(1),
                balance=U256(10**18),
                code_hash=store_code(state, code),
            ),
        )
    inputs = inclusion_inputs((frame_envelope(execution=200_000),))
    snapshots = {Uint(0): capture_inclusion_list_state(env, BlockOutput())}
    assert check_inclusion_list(env, (), inputs, snapshots) == (not fits)


def test_missing_code_is_not_an_omission_excuse(
    replay_environment: BlockEnvironment,
) -> None:
    """Propagate unavailable state instead of treating it as failed replay."""
    env = replay_environment
    state = env.state.pre_state
    assert isinstance(state, State)
    state._code_store.clear()
    inputs = inclusion_inputs((frame_envelope(),))
    snapshots = {Uint(0): capture_inclusion_list_state(env, BlockOutput())}
    with pytest.raises(KeyError):
        check_inclusion_list(env, (), inputs, snapshots)


def valid_empty_block(
    env: BlockEnvironment,
) -> tuple[Block, fork.ChainContext]:
    """Build an empty payload from actual system-call execution outputs."""
    state = env.state.pre_state
    assert isinstance(state, State)
    prealloc = Bogota.pre_allocation_blockchain()
    for address in (
        fork.WITHDRAWAL_REQUEST_PREDEPLOY_ADDRESS,
        fork.CONSOLIDATION_REQUEST_PREDEPLOY_ADDRESS,
        fork.BUILDER_DEPOSIT_CONTRACT_ADDRESS,
        fork.BUILDER_EXIT_CONTRACT_ADDRESS,
    ):
        account = prealloc[int.from_bytes(address, "big")]
        set_account(
            state,
            address,
            Account(
                nonce=Uint(account["nonce"]),
                balance=U256(0),
                code_hash=store_code(state, Bytes(account["code"])),
            ),
        )
    zero = Bytes32(bytes(32))
    parent = Header(
        parent_hash=zero,
        ommers_hash=fork.EMPTY_OMMER_HASH,
        coinbase=env.coinbase,
        state_root=zero,
        transactions_root=zero,
        receipt_root=zero,
        bloom=Bytes256(bytes(256)),
        difficulty=Uint(0),
        number=Uint(0),
        gas_limit=env.block_gas_limit,
        gas_used=Uint(0),
        timestamp=U256(0),
        extra_data=Bytes(b""),
        prev_randao=zero,
        nonce=Bytes8(bytes(8)),
        base_fee_per_gas=Uint(0),
        withdrawals_root=zero,
        blob_gas_used=U64(0),
        excess_blob_gas=U64(0),
        parent_beacon_block_root=zero,
        requests_hash=zero,
        block_access_list_hash=zero,
        slot_number=U64(0),
    )
    parent_hash = keccak256(rlp.encode(parent))
    context = fork.ChainContext(
        chain_id=env.chain_id, block_hashes=[parent_hash], parent_header=parent
    )
    block_env = replace(
        env,
        state=BlockState(pre_state=env.state.pre_state),
        block_hashes=[parent_hash],
        block_access_list_builder=BlockAccessListBuilder(),
    )
    output = fork.apply_body(block_env, (), ())
    header = replace(
        parent,
        parent_hash=parent_hash,
        number=env.number,
        timestamp=env.time,
        slot_number=env.slot_number,
        state_root=env.state.pre_state.compute_state_root(
            extract_block_diff(block_env.state)
        ),
        transactions_root=root(output.transactions_trie),
        receipt_root=root(output.receipts_trie),
        bloom=logs_bloom(output.block_logs),
        withdrawals_root=root(output.withdrawals_trie),
        requests_hash=Bytes32(fork.compute_requests_hash(output.requests)),
        block_access_list_hash=hash_block_access_list(
            output.block_access_list
        ),
    )
    return Block(
        header=header, transactions=(), ommers=(), withdrawals=()
    ), context


@pytest.mark.parametrize(
    "invalid_field", ["state_root", "block_access_list_hash"]
)
def test_payload_roots_are_validated_before_replay(
    replay_environment: BlockEnvironment,
    monkeypatch: pytest.MonkeyPatch,
    invalid_field: str,
) -> None:
    """Validate state and BAL commitments before deriving an IL verdict."""
    env = replay_environment
    state = env.state.pre_state
    assert isinstance(state, State)
    block, context = valid_empty_block(env)
    inputs = inclusion_inputs((frame_envelope(),))
    # First prove the exact valid block really reaches the EVM replay and
    # reports unsatisfied independently from its valid execution result.
    _, satisfied = fork.execute_block_with_inclusion_list(
        block, state, context, inputs
    )
    assert not satisfied

    def unexpected_replay(*args: object, **kwargs: object) -> bool:
        raise AssertionError("Replay ran before payload root validation")

    monkeypatch.setattr(fork, "check_inclusion_list", unexpected_replay)
    if invalid_field == "state_root":
        invalid_header = replace(
            block.header, state_root=Bytes32(b"\xff" * 32)
        )
    elif invalid_field == "block_access_list_hash":
        invalid_header = replace(
            block.header, block_access_list_hash=Bytes32(b"\xff" * 32)
        )
    else:
        raise ValueError(invalid_field)
    with pytest.raises(InvalidBlock):
        fork.execute_block_with_inclusion_list(
            replace(block, header=invalid_header), state, context, inputs
        )


@pytest.mark.parametrize("creation", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("scenario", ["deploy", "no-op", "collision"])
def test_deploy_prefix_must_install_sender_code(
    replay_environment: BlockEnvironment, creation: Op, scenario: str
) -> None:
    """Require a surviving installation, not merely existing sender code."""
    env = replay_environment
    state = env.state.pre_state
    assert isinstance(state, State)
    factory = AuthoredAddress(0x2000)
    runtime = Op.APPROVE(0, 0, 3)
    initcode = Initcode(deploy_code=runtime, initcode_prefix=Op.SSTORE(0, 7))
    sender = compute_create_address(
        address=factory, nonce=1, salt=0, initcode=initcode, opcode=creation
    )
    factory_code: Bytecode = Op.STOP
    if scenario != "no-op":
        create = (
            Op.CREATE(value=0, offset=0, size=len(initcode))
            if creation == Op.CREATE
            else Op.CREATE2(value=0, offset=0, size=len(initcode), salt=0)
        )
        factory_code = Op.CALLDATACOPY(0, 0, len(initcode)) + Op.POP(create)
    set_account(
        state,
        Address(factory),
        Account(
            nonce=Uint(1),
            balance=U256(0),
            code_hash=store_code(state, Bytes(factory_code)),
        ),
    )
    preexisting = scenario != "deploy"
    sender_account = Account(
        nonce=Uint(1 if preexisting else 0),
        balance=U256(10**18),
        code_hash=(
            store_code(state, Bytes(runtime))
            if preexisting
            else EMPTY_CODE_HASH
        ),
    )
    set_account(state, Address(sender), sender_account)
    tx = Transaction(
        sender=sender,
        nonce=int(sender_account.nonce),
        signatures=[],
        frames=[
            Frame(
                mode=0,
                target=factory,
                gas_limit=100_000,
                state_gas_limit=500_000,
                data=initcode,
            ),
            Frame(mode=1, flags=3, gas_limit=50_000, state_gas_limit=0),
        ],
    ).with_signature_and_sender()
    inputs = inclusion_inputs((Bytes(tx.rlp()),))
    snapshots = {Uint(0): capture_inclusion_list_state(env, BlockOutput())}
    assert check_inclusion_list(env, (), inputs, snapshots) == preexisting
    assert state.get_account_optional(Address(sender)) == sender_account
    assert env.state.account_writes == {}
    assert env.state.storage_writes == {}
