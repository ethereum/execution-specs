"""Exercise real prefix execution without changing payload execution."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Conditional,
    Frame,
    Hash,
    InclusionListClaim,
    Op,
    Transaction,
    Withdrawal,
)

from .spec import ref_spec_8369

REFERENCE_SPEC_GIT_PATH = ref_spec_8369.git_path
REFERENCE_SPEC_VERSION = ref_spec_8369.version

pytestmark = [
    pytest.mark.valid_from("Bogota"),
    pytest.mark.blockchain_test_engine_only,
]


@pytest.mark.parametrize(
    ("operation", "satisfied"),
    [
        pytest.param(Op.POP(Op.SLOAD(0)), False, id="sender-slot-zero"),
        pytest.param(Op.POP(Op.SLOAD(3)), False, id="sender-slot-three"),
        pytest.param(Op.POP(Op.SLOAD(4)), True, id="sender-slot-four"),
        pytest.param(Op.POP(Op.BALANCE(0)), True, id="balance-opcode"),
        pytest.param(Op.POP(Op.SELFBALANCE), True, id="self-balance-opcode"),
        pytest.param(Op.POP(Op.TIMESTAMP), True, id="timestamp-opcode"),
        pytest.param(Op.POP(Op.SLOTNUM), True, id="slot-opcode"),
        pytest.param(Op.POP(Op.GAS), True, id="gas-without-call"),
        pytest.param(Op.POP(Op.ORIGIN), False, id="origin-is-allowed"),
    ],
)
def test_omitted_prefix_trace_and_isolation(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    operation: Bytecode,
    satisfied: bool,
) -> None:
    """Apply prefix trace rules and discard nonce, fees and body effects."""
    balance = 10**18
    sender = pre.deploy_contract(
        code=operation + Op.APPROVE(0, 0, 3),
        balance=balance,
        storage={0: 7, 3: 9, 4: 11},
    )
    body = pre.deploy_contract(code=Op.SSTORE(0, 99), storage={0: 23})
    omitted = Transaction(
        sender=sender,
        nonce=1,
        frames=[
            Frame(mode=1, flags=3, gas_limit=50_000, state_gas_limit=0),
            Frame(mode=2, target=body),
        ],
    )
    blockchain_test(
        pre=pre,
        post={
            sender: Account(
                nonce=1, balance=balance, storage={0: 7, 3: 9, 4: 11}
            ),
            body: Account(storage={0: 23}),
        },
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=[omitted],
                inclusion_list_membership=[b"\x01\x00"],
                expected_inclusion_list_satisfied=satisfied,
            )
        ],
    )


@pytest.mark.parametrize("funding", ["transaction", "withdrawal"])
def test_end_index_excludes_withdrawals(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    funding: str,
) -> None:
    """Use balances after body transactions but before withdrawal credits."""
    sender = pre.fund_eoa(amount=1)
    omitted = Transaction(
        sender=sender,
        frames=[Frame(mode=1, flags=3, gas_limit=50_000)],
    )
    transfer = Transaction(sender=pre.fund_eoa(), to=sender, value=10**9)
    withdrawal = Withdrawal(
        index=0, validator_index=0, address=sender, amount=1
    )
    blockchain_test(
        pre=pre,
        post={sender: Account(nonce=0, balance=1 + 10**9)},
        blocks=[
            Block(
                txs=[transfer] if funding == "transaction" else [],
                withdrawals=[withdrawal] if funding == "withdrawal" else [],
                inclusion_list_txs=[omitted],
                inclusion_list_membership=[b"\x01\x00"],
                expected_inclusion_list_satisfied=funding == "withdrawal",
            )
        ],
    )


@pytest.mark.parametrize("forbidden", [False, True])
@pytest.mark.parametrize("child_reverts", [False, True])
def test_child_trace_survives_revert(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    forbidden: bool,
    child_reverts: bool,
) -> None:
    """A parent cannot hide a forbidden dependency by swallowing failure."""
    child = pre.deploy_contract(
        code=(Op.POP(Op.TIMESTAMP) if forbidden else Op.POP(1))
        + (Op.REVERT(0, 0) if child_reverts else Op.STOP)
    )
    sender = pre.deploy_contract(
        code=Op.POP(Op.STATICCALL(gas=20_000, address=child))
        + Op.APPROVE(0, 0, 3),
        balance=10**18,
    )
    omitted = Transaction(
        sender=sender,
        nonce=1,
        frames=[Frame(mode=1, flags=3, gas_limit=50_000, state_gas_limit=0)],
    )
    blockchain_test(
        pre=pre,
        post={sender: Account(nonce=1, balance=10**18)},
        blocks=[
            Block(
                txs=[],
                inclusion_list_txs=[omitted],
                inclusion_list_membership=[b"\x01\x00"],
                expected_inclusion_list_satisfied=forbidden,
            )
        ],
    )


@pytest.mark.parametrize(
    ("claims", "satisfied"),
    [
        pytest.param([], True, id="missing-defaults-to-end"),
        pytest.param([0], False, id="before-first-transaction"),
        pytest.param([1], True, id="after-first-transaction"),
        pytest.param([2**64 - 1], True, id="index-clamped-to-end"),
        pytest.param([0, 0], True, id="identical-duplicate-ignored"),
        pytest.param([0, 1], True, id="conflicting-duplicate-ignored"),
    ],
)
def test_claim_selects_transaction_boundary(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    claims: list[int],
    satisfied: bool,
) -> None:
    """Use the claimed state; duplicate hashes never select an early state."""
    sender = pre.deploy_contract(
        code=Conditional(
            condition=Op.CALLDATASIZE,
            if_true=Op.SSTORE(0, 1),
            if_false=Conditional(
                condition=Op.SLOAD(0),
                if_true=Op.REVERT(0, 0),
                if_false=Op.APPROVE(0, 0, 3),
            ),
        ),
        balance=10**18,
    )
    omitted = Transaction(
        sender=sender,
        nonce=1,
        frames=[Frame(mode=1, flags=3, gas_limit=50_000, state_gas_limit=0)],
    ).with_signature_and_sender()
    mutate = Transaction(sender=pre.fund_eoa(), to=sender, data=b"\x01")
    claim_list = [
        InclusionListClaim(
            transaction_hash=omitted.hash, transaction_index=index
        )
        for index in claims
    ]
    # An unrelated claim must not alter the omitted transaction's default.
    claim_list.append(
        InclusionListClaim(transaction_hash=Hash(123), transaction_index=0)
    )
    blockchain_test(
        pre=pre,
        post={sender: Account(nonce=1, balance=10**18, storage={0: 1})},
        blocks=[
            Block(
                txs=[mutate],
                inclusion_list_txs=[omitted],
                inclusion_list_membership=[b"\x01\x00"],
                inclusion_list_claims=claim_list,
                expected_inclusion_list_satisfied=satisfied,
            )
        ],
    )
