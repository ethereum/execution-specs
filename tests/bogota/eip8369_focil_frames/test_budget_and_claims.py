"""Exercise the per-list budget fill and state at a claimed index."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Conditional,
    Environment,
    Fork,
    Frame,
    InclusionListClaim,
    InclusionListReplayLimits,
    Initcode,
    Op,
    Transaction,
    compute_create2_address,
    compute_create_address,
)
from execution_testing import (
    Macros as Om,
)

from .spec import ref_spec_8369

REFERENCE_SPEC_GIT_PATH = ref_spec_8369.git_path
REFERENCE_SPEC_VERSION = ref_spec_8369.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.blockchain_test_engine_only,
]

# Explicit policy for this experimental fork, not protocol default limits.
REPLAY_LIMITS = InclusionListReplayLimits(
    max_code_bodies=32, max_code_bytes=65_536
)

EXPIRY_VERIFIER = Address(0x81413F0CF12E9B6A49B1D0439E081C577D57FFFF)

# Four fillers at this cost leave less than a candidate's cost of the
# 2**20 list budget, and each stays under the 2**18 transaction cap.
FILLER_COUNT = 4
FILLER_VERIFY_GAS = 260_000
CANDIDATE_VERIFY_GAS = 50_000


def frame_tx(
    sender: Address,
    data: int,
    gas_limit: int,
    flags: int = 3,
    nonce: int = 1,
    chain_id: int = 1,
    deploy_target: Address | None = None,
) -> Transaction:
    """Return a validation-prefix transaction whose data selects its hash."""
    deploy = (
        []
        if deploy_target is None
        else [Frame(mode=0, target=deploy_target, state_gas_limit=0)]
    )
    return Transaction(
        sender=sender,
        nonce=nonce,
        chain_id=chain_id,
        frames=[
            *deploy,
            Frame(
                mode=1,
                flags=flags,
                gas_limit=gas_limit - sum(f.gas_limit for f in deploy),
                state_gas_limit=0,
                data=data.to_bytes(4, "big"),
            ),
        ],
    ).with_signature_and_sender()


@pytest.mark.parametrize(
    ("filler", "satisfied"),
    [
        pytest.param("noncandidate", False, id="noncandidates-skip-debit"),
        pytest.param("stale-nonce", True, id="candidates-debit"),
        pytest.param("other-chain", True, id="chain-id-is-not-static"),
        pytest.param("deploy-to-verifier", True, id="default-frame-is-deploy"),
    ],
)
def test_fill_debits_only_candidates(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    filler: str,
    satisfied: bool,
) -> None:
    """
    Skip entries outside the candidate conditions without a debit.

    The fillers sort before the candidate. Candidates debit their cost
    and then fail replay, so the candidate no longer fits the list's
    budget. A prefix outside the admitted shapes is skipped instead. A
    chain ID is checked by replay, not by the static candidate checks. A
    `DEFAULT` frame to the expiry verifier is a deploy frame, not an
    expiry verifier frame.
    """
    sender = pre.deploy_contract(code=Op.APPROVE(0, 0, 3), balance=10**18)
    candidate = next(
        tx
        for tx in (
            frame_tx(sender, i, CANDIDATE_VERIFY_GAS) for i in range(1_000)
        )
        if int.from_bytes(tx.hash, "big") >= 2**255
    )
    flags, nonce, chain_id, deploy_target = {
        "noncandidate": (0, 1, 1, None),
        "stale-nonce": (3, 99, 1, None),
        "other-chain": (3, 1, 2, None),
        "deploy-to-verifier": (3, 1, 1, EXPIRY_VERIFIER),
    }[filler]
    fillers = [
        tx
        for tx in (
            frame_tx(
                sender,
                i,
                FILLER_VERIFY_GAS,
                flags,
                nonce,
                chain_id,
                deploy_target,
            )
            for i in range(1_000, 2_000)
        )
        if tx.hash < candidate.hash
    ][:FILLER_COUNT]
    blockchain_test(
        pre=pre,
        post={sender: Account(nonce=1, balance=10**18)},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=[*fillers, candidate],
                inclusion_list_membership=[b"\x01\x00"] * (FILLER_COUNT + 1),
                inclusion_list_replay_limits=REPLAY_LIMITS,
                expected_inclusion_list_satisfied=satisfied,
            )
        ],
    )


@pytest.mark.parametrize("claimed", [False, True])
def test_claim_fits_gas_used_before_index(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    claimed: bool,
) -> None:
    """
    Check gas fit against the block's gas used before the claimed index.

    The body transfers leave one gas too little for the candidate's
    execution reservation at the end of the payload, which excuses an
    unclaimed omission. A claim before the transfers condemns it.
    """
    sender = pre.deploy_contract(code=Op.APPROVE(0, 0, 3), balance=10**18)
    omitted = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            Frame(mode=1, flags=3, gas_limit=50_000, state_gas_limit=0),
            Frame(mode=2, target=sender, gas_limit=200_000, state_gas_limit=0),
        ],
    ).with_signature_and_sender()
    assert omitted.frames is not None
    reservation = fork.frame_transaction_intrinsic_cost_calculator()(
        frames=omitted.frames, signatures=omitted.signatures or []
    )
    transfer_gas = fork.transaction_intrinsic_cost_calculator()()
    transfers = [
        Transaction(
            sender=pre.fund_eoa(),
            to=pre.nonexistent_account(),
            gas_limit=transfer_gas,
        )
        for _ in range(20)
    ]
    claims = (
        [
            InclusionListClaim(
                transaction_hash=omitted.hash, transaction_index=0
            )
        ]
        if claimed
        else []
    )
    blockchain_test(
        genesis_environment=Environment(
            gas_limit=transfer_gas * len(transfers) + reservation - 1
        ),
        pre=pre,
        post={sender: Account(nonce=1, balance=10**18)},
        blocks=[
            Block(
                txs=transfers,
                inclusion_list_txs=[omitted],
                inclusion_list_membership=[b"\x01\x00"],
                inclusion_list_claims=claims,
                inclusion_list_replay_limits=REPLAY_LIMITS,
                expected_inclusion_list_satisfied=not claimed,
            )
        ],
    )


@pytest.mark.parametrize("claimed", [False, True])
def test_claim_uses_payer_balance_at_index(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    claimed: bool,
) -> None:
    """
    Collect the maximum cost from the payer's balance at the claimed index.

    A body transaction drains the sender, which excuses an unclaimed
    omission. A claim before the drain condemns it.
    """
    sink = pre.fund_eoa(amount=1)
    sender = pre.deploy_contract(
        code=Conditional(
            condition=Op.CALLDATASIZE,
            if_true=Op.POP(
                Op.CALL(gas=Op.GAS, address=sink, value=Op.SELFBALANCE)
            ),
            if_false=Op.APPROVE(0, 0, 3),
        ),
        balance=10**18,
    )
    omitted = Transaction(
        sender=sender,
        nonce=1,
        frames=[Frame(mode=1, flags=3, gas_limit=50_000, state_gas_limit=0)],
    ).with_signature_and_sender()
    drain = Transaction(
        sender=pre.fund_eoa(), to=sender, data=b"\x01", gas_limit=100_000
    )
    claims = (
        [
            InclusionListClaim(
                transaction_hash=omitted.hash, transaction_index=0
            )
        ]
        if claimed
        else []
    )
    blockchain_test(
        pre=pre,
        post={
            sender: Account(nonce=1, balance=0),
            sink: Account(balance=10**18 + 1),
        },
        blocks=[
            Block(
                txs=[drain],
                inclusion_list_txs=[omitted],
                inclusion_list_membership=[b"\x01\x00"],
                inclusion_list_claims=claims,
                inclusion_list_replay_limits=REPLAY_LIMITS,
                expected_inclusion_list_satisfied=not claimed,
            )
        ],
    )


@pytest.mark.parametrize("opcode", [Op.CREATE, Op.CREATE2])
def test_deploy_frame_creates_sender(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    opcode: Op,
) -> None:
    """
    Admit a deploy frame whose factory installs the sender's code.

    Deployment bookkeeping includes the creator's nonce, so `CREATE` is
    permitted as well as `CREATE2`. The replay's deployment is discarded.
    """
    initcode = Initcode(deploy_code=Op.APPROVE(0, 0, 3))
    factory = pre.deploy_contract(
        code=Om.MSTORE(bytes(initcode), 0)
        + Op.POP(
            Op.CREATE(value=0, offset=0, size=len(initcode))
            if opcode == Op.CREATE
            else Op.CREATE2(value=0, offset=0, size=len(initcode), salt=0)
        )
    )
    sender = (
        compute_create_address(address=factory, nonce=1)
        if opcode == Op.CREATE
        else compute_create2_address(
            address=factory, salt=0, initcode=initcode
        )
    )
    pre.fund_address(sender, 10**18)
    omitted = Transaction(
        sender=sender,
        frames=[
            Frame(mode=0, target=factory),
            Frame(mode=1, flags=3, gas_limit=50_000, state_gas_limit=0),
        ],
    )
    blockchain_test(
        pre=pre,
        post={sender: Account(nonce=0, balance=10**18, code=b"")},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=[omitted],
                inclusion_list_membership=[b"\x01\x00"],
                inclusion_list_replay_limits=REPLAY_LIMITS,
                expected_inclusion_list_satisfied=False,
            )
        ],
    )
