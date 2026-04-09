"""
Regression tests for bal-devnet-3 client divergences.

Each test targets a specific EIP-8037 2D gas accounting bug found
during Kurtosis stress testing. All bugs produce block-level gasUsed
mismatches where the delta is an exact multiple of
cost_per_state_byte (1174).

Bug #14 (besu): SSTORE 0->X->0 in OOG tx — state gas refund
    incorrectly applied, delta = 32 * cpsb.
Bug #12 (nethermind): GAS_NEW_ACCOUNT for EIP-7702 setcodetx on
    empty account — overcounted by 112 * cpsb.
Bug #1 (erigon): Block gasUsed = max(regular, state) not enforced
    when state gas dominates — allows blocks with gasUsed > gas_limit.
Bug #15 (nethermind): Failed CREATE tx with EIP-8024 opcodes in
    initcode — state gas for new account incorrectly included in
    block_state_gas_used despite CREATE reverting, delta = 112 * cpsb.
Bug #16 (geth): CREATE tx with internal CREATE2 whose initcode exceeds
    EIP-7954 size limit — GAS_CREATE state gas spills from empty
    reservoir into gas_left, then is misclassified in 2D block accounting
    when the hard error aborts the constructor, delta = 112 * cpsb.

Tests for [EIP-8037: State Creation Gas Cost Increase]
(https://eips.ethereum.org/EIPS/eip-8037).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Fork,
    Op,
    Storage,
    Transaction,
    compute_create_address,
)

from .spec import ref_spec_8037

REFERENCE_SPEC_GIT_PATH = ref_spec_8037.git_path
REFERENCE_SPEC_VERSION = ref_spec_8037.version


# ── Bug #14: SSTORE 0->X->0 under OOG with state gas refund ──────


@pytest.mark.valid_from("Amsterdam")
def test_sstore_restoration_oog_no_state_refund(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify SSTORE 0->X->0 does NOT refund state gas when tx OOGs.

    A contract performs SSTORE(0, 1) then SSTORE(0, 0) (restoration)
    then additional SSTOREs that exhaust gas. When the tx reverts due
    to OOG, the 0->1 state gas (32 * cpsb) is consumed because the
    revert undoes the restoration — slot 0 is still zero (original
    value), but the state gas was charged during execution and must
    appear in block_state_gas_used.

    Besu bug: incorrectly refunds state gas on the 0->0 final state,
    producing block gasUsed that is 32 * cpsb too low.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()

    # Contract: SSTORE(0,1) + SSTORE(0,0) + many SSTOREs to OOG
    # The 0->1->0 restoration grants a refund_counter credit, but
    # the subsequent SSTOREs consume all gas causing OOG revert.
    # On revert, all storage changes are undone but gas is consumed.
    code = (
        Op.SSTORE(0, 1)
        + Op.SSTORE(0, 0)
        + Op.SSTORE(1, 1)
        + Op.SSTORE(2, 1)
        + Op.SSTORE(3, 1)
        + Op.SSTORE(4, 1)
        + Op.SSTORE(5, 1)
        + Op.SSTORE(6, 1)
        + Op.SSTORE(7, 1)
        + Op.SSTORE(8, 1)
        + Op.SSTORE(9, 1)
        + Op.SSTORE(10, 1)
    )
    contract = pre.deploy_contract(code=code)

    # Tight gas: enough for intrinsic + a few SSTOREs but not all
    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    gas_limit = intrinsic_cost() + 200_000

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    # OOG revert — all storage unchanged
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={contract: Account(storage={0: 0})},
    )


@pytest.mark.valid_from("Amsterdam")
def test_sstore_restoration_oog_block_gas_observable(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Observe block gasUsed via coinbase balance after SSTORE OOG.

    Tx 1: Contract does SSTORE 0->1->0 restoration then OOGs on
    additional SSTOREs. The restoration refund is capped by 1/5 rule.
    Tx 2: Reporter reads BALANCE(COINBASE) to make gasUsed observable.

    If a client incorrectly handles the state gas refund on the
    0->1->0 pattern under OOG, the coinbase fee diverges by
    32 * cpsb * priority_fee, causing a state root mismatch.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()

    # Contract that does restoration then burns gas via SSTOREs
    oog_contract = pre.deploy_contract(
        code=(
            Op.SSTORE(0, 1)
            + Op.SSTORE(0, 0)
            + Op.SSTORE(1, 1)
            + Op.SSTORE(2, 1)
            + Op.SSTORE(3, 1)
            + Op.SSTORE(4, 1)
            + Op.SSTORE(5, 1)
            + Op.SSTORE(6, 1)
            + Op.SSTORE(7, 1)
            + Op.SSTORE(8, 1)
            + Op.SSTORE(9, 1)
            + Op.SSTORE(10, 1)
            + Op.SSTORE(11, 1)
            + Op.SSTORE(12, 1)
            + Op.SSTORE(13, 1)
            + Op.SSTORE(14, 1)
        ),
    )

    # Reporter reads coinbase balance after tx 1
    reporter = pre.deploy_contract(
        code=Op.SSTORE(0, Op.BALANCE(Op.COINBASE)),
    )

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    # Tight gas: will OOG mid-way through the SSTOREs
    tx1_gas = intrinsic_cost() + 300_000

    blocks = [
        Block(
            txs=[
                Transaction(
                    to=oog_contract,
                    gas_limit=tx1_gas,
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=8,
                    sender=pre.fund_eoa(),
                ),
                Transaction(
                    to=reporter,
                    gas_limit=gas_limit_cap,
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=8,
                    sender=pre.fund_eoa(),
                ),
            ]
        ),
    ]

    # Don't assert specific storage — the blockchain test fixture
    # captures the correct state root from the reference impl. Any
    # state gas error produces a different coinbase balance in the
    # reporter's slot 0, causing state root mismatch on consume.
    post = {oog_contract: Account(storage={0: 0})}
    blockchain_test(pre=pre, blocks=blocks, post=post)


@pytest.mark.parametrize(
    "num_restorations",
    [
        pytest.param(1, id="single_restoration"),
        pytest.param(5, id="five_restorations"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_sstore_multi_restoration_oog_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_restorations: int,
) -> None:
    """
    Verify state gas for multiple SSTORE restorations that OOG.

    Each restoration (SSTORE 0->1->0 on separate slots) charges
    32 * cpsb state gas then refunds it. When followed by more ops
    that cause OOG, the refund is capped. Multiple restorations
    amplify any per-restoration error by num_restorations * 32 * cpsb.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    code = Bytecode()
    for i in range(num_restorations):
        code += Op.SSTORE(i, 1) + Op.SSTORE(i, 0)
    # Burn remaining gas with expensive ops
    for i in range(num_restorations, num_restorations + 20):
        code += Op.SSTORE(i, 1)

    contract = pre.deploy_contract(code=code)

    intrinsic_cost = fork.transaction_intrinsic_cost_calculator()
    gas_limit = intrinsic_cost() + 400_000

    tx = Transaction(
        to=contract,
        gas_limit=gas_limit,
        sender=pre.fund_eoa(),
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    # OOG — all storage unchanged
    expected_storage = {i: 0 for i in range(num_restorations)}
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={contract: Account(storage=expected_storage)},
    )


# ── Bug #12: GAS_NEW_ACCOUNT for EIP-7702 on empty account ───────


@pytest.mark.valid_from("Amsterdam")
def test_setcodetx_empty_account_new_account_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify PER_EMPTY_ACCOUNT_COST charged for empty signer.

    A SetCode tx authorizes delegation from a previously empty
    account (no balance, no nonce, no code). The intrinsic state gas
    includes 112 * cpsb for GAS_NEW_ACCOUNT which is NOT refunded
    because the account didn't exist before. Block gasUsed must
    include this state gas via max(regular, state).

    Nethermind bug: overcounts by 112 * cpsb because the existing-
    account refund is not applied when it should be (or vice versa),
    producing a gasUsed delta of exactly GAS_NEW_ACCOUNT.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    auth_state_gas = fork.transaction_intrinsic_state_gas(
        authorization_count=1,
    )

    contract = pre.deploy_contract(code=Op.STOP)

    # Empty signer: exists in pre-state with 0 balance (empty account).
    # EIP-161: account with (nonce=0, balance=0, code=nil) is empty.
    # Whether the new-account refund applies depends on the client's
    # account_exists() implementation for genesis-allocated empty EOAs.
    empty_signer = pre.fund_eoa(0)

    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=empty_signer,
        ),
    ]

    sender = pre.fund_eoa()
    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + auth_state_gas,
        authorization_list=authorization_list,
        sender=sender,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={},
    )


@pytest.mark.valid_from("Amsterdam")
def test_setcodetx_empty_account_block_gas_observable(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Observe block gasUsed after SetCode tx on empty signer.

    Tx 1: SetCode tx authorizing an empty account for delegation.
    Tx 2: Reporter reads BALANCE(COINBASE) to make gasUsed observable.

    The coinbase balance after tx 1 reflects the exact gasUsed
    including any GAS_NEW_ACCOUNT state gas. A 112 * cpsb error
    in state gas accounting produces a directly observable coinbase
    balance difference, causing state root mismatch.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    auth_state_gas = fork.transaction_intrinsic_state_gas(
        authorization_count=1,
    )

    contract = pre.deploy_contract(code=Op.STOP)

    # Empty signer (0 balance)
    empty_signer = pre.fund_eoa(0)

    authorization_list = [
        AuthorizationTuple(
            address=contract,
            nonce=0,
            signer=empty_signer,
        ),
    ]

    # Reporter reads coinbase balance
    reporter = pre.deploy_contract(
        code=Op.SSTORE(0, Op.BALANCE(Op.COINBASE)),
    )

    sender = pre.fund_eoa()
    blocks = [
        Block(
            txs=[
                Transaction(
                    to=contract,
                    gas_limit=gas_limit_cap + auth_state_gas,
                    authorization_list=authorization_list,
                    sender=sender,
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=8,
                ),
                Transaction(
                    to=reporter,
                    gas_limit=gas_limit_cap,
                    sender=pre.fund_eoa(),
                    max_priority_fee_per_gas=1,
                    max_fee_per_gas=8,
                ),
            ]
        ),
    ]

    # Don't assert specific reporter storage — the blockchain test
    # captures state root from reference impl. Any state gas error
    # in tx 1 produces wrong coinbase -> state root mismatch.
    blockchain_test(pre=pre, blocks=blocks, post={})


@pytest.mark.parametrize(
    "num_empty,num_existing",
    [
        pytest.param(1, 1, id="one_empty_one_existing"),
        pytest.param(2, 0, id="two_empty"),
        pytest.param(0, 2, id="two_existing"),
        pytest.param(2, 1, id="two_empty_one_existing"),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_setcodetx_mixed_empty_existing_signers(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    num_empty: int,
    num_existing: int,
) -> None:
    """
    Test mixed empty and existing signers in a single SetCode tx.

    Empty signers charge PER_EMPTY_ACCOUNT_COST (112 * cpsb) that
    is not refunded. Existing signers get the new-account state gas
    refunded to the reservoir. The block gasUsed must correctly
    reflect the net state gas from both types.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    auth_state_gas = fork.transaction_intrinsic_state_gas(
        authorization_count=1,
    )

    contract = pre.deploy_contract(code=Op.STOP)

    authorization_list = []

    # Empty signers (0 balance — new account, no refund)
    for _ in range(num_empty):
        signer = pre.fund_eoa(0)
        authorization_list.append(
            AuthorizationTuple(
                address=contract,
                nonce=0,
                signer=signer,
            ),
        )

    # Existing signers (funded — existing account, gets refund)
    for _ in range(num_existing):
        signer = pre.fund_eoa()
        authorization_list.append(
            AuthorizationTuple(
                address=contract,
                nonce=0,
                signer=signer,
            ),
        )

    total_auths = num_empty + num_existing
    sender = pre.fund_eoa()
    tx = Transaction(
        to=contract,
        gas_limit=gas_limit_cap + auth_state_gas * total_auths,
        authorization_list=authorization_list,
        sender=sender,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={},
    )


# ── Bug #1: Block gasUsed = max(regular, state) with many txs ────


@pytest.mark.valid_from("Amsterdam")
def test_block_gas_used_state_dominates_many_txs(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block gasUsed when state gas exceeds regular gas.

    Pack a block with multiple SSTORE transactions where each tx's
    state gas (32 * cpsb from reservoir) exceeds its regular gas.
    The block header gasUsed must be max(blockRegular, blockState).
    When state dominates, gasUsed > sum of receipt regular gas.

    Erigon bug: GasPool only tracks regular gas, allowing more txs
    than the block gas limit permits. The resulting block has
    gasUsed >> gas_limit because state gas was never constrained.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()

    num_txs = 10
    all_contracts = []
    all_storages = []
    txs = []

    for i in range(num_txs):
        storage = Storage()
        # Each contract does 5 zero-to-nonzero SSTOREs
        # Regular gas: ~21000 intrinsic + 5*5000 = ~46000
        # State gas: 5 * 32 * 1174 = 187,840 (state >> regular)
        contract = pre.deploy_contract(
            code=(
                Op.SSTORE(storage.store_next(1), 1)
                + Op.SSTORE(storage.store_next(2), 2)
                + Op.SSTORE(storage.store_next(3), 3)
                + Op.SSTORE(storage.store_next(4), 4)
                + Op.SSTORE(storage.store_next(5), 5)
            ),
        )
        all_contracts.append(contract)
        all_storages.append(storage)

        txs.append(
            Transaction(
                to=contract,
                gas_limit=gas_limit_cap + sstore_state_gas * 5,
                sender=pre.fund_eoa(),
                max_priority_fee_per_gas=1,
                max_fee_per_gas=8,
            )
        )

    post = {
        c: Account(storage=s)
        for c, s in zip(all_contracts, all_storages, strict=False)
    }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=txs)],
        post=post,
    )


@pytest.mark.valid_from("Amsterdam")
def test_block_gas_used_state_dominates_observable(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Observe block gasUsed when state gas dominates via coinbase.

    Tx 1-3: Each does 5 SSTOREs (state gas >> regular gas).
    Tx 4: Reporter reads BALANCE(COINBASE).

    When state gas dominates, block gasUsed = blockStateGas > blockRegular.
    The coinbase earns priority_fee * gasUsed, so any error in the
    max(regular, state) computation produces a different coinbase
    balance, caught by state root comparison.
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None
    sstore_state_gas = fork.sstore_state_gas()

    sstore_txs = []
    sstore_contracts = []
    sstore_storages = []

    for _ in range(3):
        storage = Storage()
        contract = pre.deploy_contract(
            code=(
                Op.SSTORE(storage.store_next(1), 1)
                + Op.SSTORE(storage.store_next(2), 2)
                + Op.SSTORE(storage.store_next(3), 3)
                + Op.SSTORE(storage.store_next(4), 4)
                + Op.SSTORE(storage.store_next(5), 5)
            ),
        )
        sstore_contracts.append(contract)
        sstore_storages.append(storage)

        sstore_txs.append(
            Transaction(
                to=contract,
                gas_limit=gas_limit_cap + sstore_state_gas * 5,
                sender=pre.fund_eoa(),
                max_priority_fee_per_gas=1,
                max_fee_per_gas=8,
            )
        )

    # Reporter reads coinbase balance
    reporter = pre.deploy_contract(
        code=Op.SSTORE(0, Op.BALANCE(Op.COINBASE)),
    )

    all_txs = sstore_txs + [
        Transaction(
            to=reporter,
            gas_limit=gas_limit_cap,
            sender=pre.fund_eoa(),
            max_priority_fee_per_gas=1,
            max_fee_per_gas=8,
        ),
    ]

    post = {
        c: Account(storage=s)
        for c, s in zip(sstore_contracts, sstore_storages, strict=False)
    }

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=all_txs)],
        post=post,
    )


# ── Bug #15: Failed CREATE tx state gas with EIP-8024 opcodes ─────


@pytest.mark.parametrize(
    "initcode_bytes,value",
    [
        pytest.param(
            # Minimal: DUPN(17) in initcode triggers gas overflow on
            # stack underflow, consuming all gas. CREATE reverts.
            bytes(Op.PUSH32(0x200) + Op.PUSH32(0x37) + Op.DUPN(17)),
            0,
            id="dupn_stack_underflow_oog",
        ),
        pytest.param(
            # Exact fuzz bytecode from bal-devnet-3 block 589 TX[1].
            # Uses DUPN(0x01) and various ops that cause gas overflow.
            bytes.fromhex(
                "7f0000000000000000000000000000000000000000000000000000000000000200"
                "7f0000000000000000000000000000000000000000000000000000000000000037"
                "7e0101b8b5a8cce5cc1147cf5b51ab5ca3c67c50e4776e6ef8c0e0c615d924b4"
                "60def538415b5b70ac7d7a380dca8dab2c98d9fde225187a873aff5b63c541fd"
                "5a8465a6a20168e724305b5a06629724c678724ccd7b6ec672afcaceea6d29cd"
                "af5c4e2d2792fe609c582148916202ffff16555b3461008c57603f161a636b82"
                "710f5b1c095b00"
            ),
            0,
            id="block589_tx1_exact_bytecode",
        ),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_failed_create_tx_no_new_account_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode_bytes: bytes,
    value: int,
) -> None:
    """
    Verify failed CREATE tx does not charge new-account state gas.

    A CREATE transaction whose initcode fails (OOG, invalid opcode,
    or stack underflow) must not include GAS_NEW_ACCOUNT (112 * cpsb)
    in block_state_gas_used. The new account was never persisted, so
    its state gas is reverted.

    Nethermind bug: incorrectly includes the failed CREATE's
    new-account state gas in block_state_gas_used, producing a
    block gasUsed delta of exactly 112 * cpsb = 131,488.

    Triggered specifically by EIP-8024 opcodes (DUPN 0x7e) in the
    initcode, which cause gas overflow before the initcode completes.
    Discovered via bal-devnet-3 block 589 chain split (2026-04-08).
    """
    sender = pre.fund_eoa(10**21)

    tx = Transaction(
        to=None,
        data=initcode_bytes,
        value=value,
        gas_limit=3_000_000,
        sender=sender,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    created = compute_create_address(address=sender, nonce=0)

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={created: Account.NONEXISTENT},
    )


@pytest.mark.valid_from("Amsterdam")
def test_failed_create_tx_no_state_gas_block_observable(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Observe block gasUsed after a failed CREATE tx via coinbase balance.

    TX 1: CREATE tx with EIP-8024 DUPN in initcode that OOGs. The
    failed CREATE must not contribute GAS_NEW_ACCOUNT to
    block_state_gas_used.

    TX 2: Reporter reads BALANCE(COINBASE). Any 112 * cpsb error in
    state gas accounting produces a different coinbase balance, caught
    by state root comparison against the reference implementation.

    Regression test for nethermind bug #15 (bal-devnet-3 block 589).
    """
    # Initcode: PUSH32 + PUSH32 + DUPN(17) → stack underflow → OOG
    initcode = bytes(Op.PUSH32(0x200) + Op.PUSH32(0x37) + Op.DUPN(17))

    sender = pre.fund_eoa(10**21)

    tx_create = Transaction(
        to=None,
        data=initcode,
        value=0,
        gas_limit=3_000_000,
        sender=sender,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    reporter = pre.deploy_contract(
        code=Op.SSTORE(0, Op.BALANCE(Op.COINBASE)),
    )

    tx_reporter = Transaction(
        to=reporter,
        gas_limit=100_000,
        sender=pre.fund_eoa(),
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    created = compute_create_address(address=sender, nonce=0)

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx_create, tx_reporter])],
        post={created: Account.NONEXISTENT},
    )


@pytest.mark.valid_from("Amsterdam")
def test_successful_and_failed_create_txs_in_block(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify block gasUsed with successful and failed CREATE txs.

    Reproduces the exact bal-devnet-3 block 589 pattern:
    TX[0]: CREATE with value, initcode CALLs precompile then STOPs.
           Succeeds — block_state_gas_used includes GAS_NEW_ACCOUNT.
    TX[1]: CREATE with DUPN in initcode, OOGs.
           Fails — block_state_gas_used must NOT include GAS_NEW_ACCOUNT.

    The block gasUsed delta between correct and incorrect clients is
    exactly 131,488 (one GAS_NEW_ACCOUNT). The coinbase observation
    TX makes this directly observable via state root comparison.

    Regression test for nethermind bug #15 (bal-devnet-3 block 589).
    """
    # TX[0]: Successful CREATE — initcode does a CALL then STOPs
    initcode_success = (
        Op.POP(
            Op.CALL(
                gas=10_000,
                address=1,  # ECRECOVER precompile
                value=0,
                args_offset=0,
                args_size=0,
                ret_offset=0,
                ret_size=0,
            )
        )
        + Op.STOP
    )

    sender_0 = pre.fund_eoa(10**21)
    tx0 = Transaction(
        to=None,
        data=bytes(initcode_success),
        value=51_255,
        gas_limit=3_000_000,
        sender=sender_0,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    # TX[1]: Failed CREATE — DUPN causes OOG
    initcode_fail = bytes(Op.PUSH32(0x200) + Op.PUSH32(0x37) + Op.DUPN(17))

    sender_1 = pre.fund_eoa(10**21)
    tx1 = Transaction(
        to=None,
        data=initcode_fail,
        value=0,
        gas_limit=3_000_000,
        sender=sender_1,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    # TX[2]: Coinbase balance reporter
    reporter = pre.deploy_contract(
        code=Op.SSTORE(0, Op.BALANCE(Op.COINBASE)),
    )

    tx_reporter = Transaction(
        to=reporter,
        gas_limit=100_000,
        sender=pre.fund_eoa(),
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    created_0 = compute_create_address(address=sender_0, nonce=0)
    created_1 = compute_create_address(address=sender_1, nonce=0)

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx0, tx1, tx_reporter])],
        post={
            created_0: Account(nonce=1, balance=51_255),
            created_1: Account.NONEXISTENT,
        },
    )


# ── Bug #16: CREATE tx with internal CREATE2 exceeding EIP-7954 ───
#
# bal-devnet-3 block 1031 (2026-04-08): geth forked from canonical
# chain because it computed block gasUsed 131,488 too low.
#
# Scenario:
#   1. CREATE tx (gas_limit=3M < TX_MAX_GAS_LIMIT=16.7M → reservoir=0)
#   2. Constructor does CREATE2 with initcode_size > 65,536 (EIP-7954)
#   3. CREATE2 charges GAS_CREATE state gas (112*cpsb=131,488) BEFORE
#      the size check — state gas spills into gas_left (empty reservoir)
#   4. Size check fails → hard error aborts entire constructor
#   5. 2D block accounting: spilled state gas must still count as state
#      dimension in tx_state_gas, not be absorbed into regular gas
#
# The 131,488 GAS_CREATE was charged as state gas (conceptually) but
# drawn from gas_left (mechanically). Per EIP-8037 line 117:
# "state_gas costs are added to execution_state_gas_used" — the cost
# TYPE determines the dimension, not the SOURCE of gas.
#
# On the live network, geth+bootnode computed gasUsed=25,999,599 while
# reth, nimbus-el, ethrex, and erigon (4 clients) independently computed
# a higher value (diverging at block 1031). However, EELS (the Python
# reference) currently agrees with geth. These fixtures are filled
# against EELS so they currently pass on geth and fail on reth/nimbus-el.
#
# **DISPUTED**: 4/6 live clients disagree with EELS on this scenario.
# The spec may need clarification on whether state gas spilled into
# gas_left retains its "state" classification for 2D block accounting
# after a hard error aborts the frame.
# ───────────────────────────────────────────────────────────────────


@pytest.mark.valid_from("Amsterdam")
def test_create2_oversized_initcode_state_gas_spillover(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Verify GAS_CREATE state gas is correctly tracked when CREATE2
    initcode exceeds EIP-7954 limit and reservoir is empty.

    A CREATE transaction deploys a constructor that attempts a CREATE2
    with initcode larger than max_initcode_size (65,536 bytes). The
    CREATE2 opcode charges GAS_CREATE (112 * cpsb state gas + 9,000
    regular gas) before the size check. With reservoir=0, the state
    gas spills into gas_left.

    The size check fails with a hard error, aborting the constructor.
    The GAS_CREATE state gas must remain in execution_state_gas_used
    per EIP-8037: the cost TYPE (state) determines the accounting
    dimension, not the SOURCE (gas_left due to empty reservoir).

    Geth bug: misclassifies spilled state gas after hard error,
    reducing block gasUsed by exactly 112 * cpsb = 131,488.
    Discovered via bal-devnet-3 block 1031 chain split (2026-04-08).
    """
    # Constructor bytecode:
    #   CALLDATACOPY(0, 0, 0x20000)  — expand memory to 131,072 bytes
    #   CREATE2(value=0, offset=0, size=0x20000, salt=0)
    #   STOP
    #
    # The CREATE2 initcode is 131,072 bytes of zeros (from memory),
    # which exceeds the EIP-7954 max_initcode_size of 65,536.
    oversized_initcode_len = 0x20000  # 131,072 > 65,536

    constructor = (
        # Copy calldata to memory (expands memory)
        Op.CALLDATACOPY(0, 0, oversized_initcode_len)
        # CREATE2 with oversized initcode
        + Op.CREATE2(0, 0, oversized_initcode_len, 0)
        + Op.STOP
    )

    sender = pre.fund_eoa(10**21)

    tx = Transaction(
        to=None,
        data=bytes(constructor),
        value=0,
        gas_limit=3_000_000,  # < TX_MAX_GAS_LIMIT → reservoir=0
        sender=sender,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    created = compute_create_address(address=sender, nonce=0)

    # Constructor aborts due to hard error from CREATE2 size check.
    # No contract is deployed.
    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={created: Account.NONEXISTENT},
    )


@pytest.mark.valid_from("Amsterdam")
def test_create2_oversized_initcode_block_gas_observable(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Observe block gasUsed via coinbase after CREATE2 oversized initcode.

    TX 1: CREATE tx whose constructor does CREATE2 with initcode >
           max_initcode_size. Hard error aborts constructor. The
           GAS_CREATE state gas (131,488) was charged from gas_left
           (empty reservoir) and must count in the state dimension.

    TX 2: Reporter reads BALANCE(COINBASE). Any 112 * cpsb error in
           2D accounting produces a different coinbase balance, caught
           by state root comparison.

    Regression test for geth bug #16 (bal-devnet-3 block 1031).
    """
    oversized_initcode_len = 0x20000  # 131,072 > 65,536

    constructor = (
        Op.CALLDATACOPY(0, 0, oversized_initcode_len)
        + Op.CREATE2(0, 0, oversized_initcode_len, 0)
        + Op.STOP
    )

    sender = pre.fund_eoa(10**21)

    tx_create = Transaction(
        to=None,
        data=bytes(constructor),
        value=0,
        gas_limit=3_000_000,
        sender=sender,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    reporter = pre.deploy_contract(
        code=Op.SSTORE(0, Op.BALANCE(Op.COINBASE)),
    )

    tx_reporter = Transaction(
        to=reporter,
        gas_limit=100_000,
        sender=pre.fund_eoa(),
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    created = compute_create_address(address=sender, nonce=0)

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx_create, tx_reporter])],
        post={created: Account.NONEXISTENT},
    )


@pytest.mark.parametrize(
    "inner_create_size,expect_hard_error",
    [
        pytest.param(
            0x10000,  # 65,536 = exactly at limit → succeeds
            False,
            id="at_limit_succeeds",
        ),
        pytest.param(
            0x10001,  # 65,537 = one byte over → hard error
            True,
            id="one_over_limit_hard_error",
        ),
        pytest.param(
            0x20000,  # 131,072 = well over limit → hard error
            True,
            id="double_limit_hard_error",
        ),
    ],
)
@pytest.mark.valid_from("Amsterdam")
def test_create2_initcode_size_boundary_state_gas(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    inner_create_size: int,
    expect_hard_error: bool,
) -> None:
    """
    Test GAS_CREATE state gas accounting at the EIP-7954 initcode
    size boundary for internal CREATE2.

    At the boundary: CREATE2 succeeds, state gas charged and consumed
    normally (account creation + code deposit).

    Over the boundary: CREATE2 triggers hard error, constructor aborts.
    GAS_CREATE state gas was already charged (pre-state cost) and must
    remain in execution_state_gas_used even though the frame failed.

    In both cases, gas_limit < TX_MAX_GAS_LIMIT so reservoir=0 and
    state gas spills into gas_left. The cost TYPE (state) must
    determine the accounting dimension regardless of SOURCE.
    """
    constructor = (
        Op.CALLDATACOPY(0, 0, inner_create_size)
        + Op.CREATE2(0, 0, inner_create_size, 0)
        + Op.STOP
    )

    sender = pre.fund_eoa(10**21)

    tx = Transaction(
        to=None,
        data=bytes(constructor),
        value=0,
        gas_limit=3_000_000,
        sender=sender,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    created = compute_create_address(address=sender, nonce=0)

    if expect_hard_error:
        # Hard error aborts constructor → no contract deployed
        post = {created: Account.NONEXISTENT}
    else:
        # CREATE2 succeeds, outer constructor deploys (with nonce=2
        # since the inner CREATE2 incremented nonce)
        post = {created: Account(nonce=2)}

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post=post,
    )


@pytest.mark.valid_from("Amsterdam")
def test_block1031_mixed_create_txs_with_internal_create2_failure(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Reproduce bal-devnet-3 block 1031 pattern: mixed successful and
    failed CREATE txs where one constructor has an internal CREATE2
    that exceeds the EIP-7954 initcode size limit.

    Block contains:
      TX[0]: CREATE tx, constructor succeeds (simple contract)
      TX[1]: CREATE tx, constructor does CREATE2 with oversized
             initcode → hard error → constructor fails
      TX[2]: CREATE tx, constructor succeeds (simple contract)
      TX[3]: Coinbase reporter

    The critical test: TX[1]'s internal CREATE2 charges GAS_CREATE
    state gas (112*cpsb) that spills into gas_left. On hard error,
    this must still count as state gas in block_state_gas_used.

    Block gasUsed = max(block_regular_gas, block_state_gas). If the
    spilled state gas is misclassified, block gasUsed differs by
    exactly 112 * cpsb = 131,488.

    Regression test for geth bug #16 (bal-devnet-3 block 1031).
    """
    gas_limit_cap = fork.transaction_gas_limit_cap()
    assert gas_limit_cap is not None

    # TX[0]: Simple successful CREATE — initcode returns 1 byte
    sender_0 = pre.fund_eoa(10**21)
    tx0 = Transaction(
        to=None,
        data=bytes(Op.MSTORE8(0, 0x60) + Op.RETURN(0, 1)),
        value=0,
        gas_limit=3_000_000,
        sender=sender_0,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    # TX[1]: CREATE with internal CREATE2 exceeding max initcode size
    oversized = 0x20000  # 131,072 > 65,536
    constructor_with_create2 = (
        Op.CALLDATACOPY(0, 0, oversized)
        + Op.CREATE2(0, 0, oversized, 0)
        + Op.STOP
    )
    sender_1 = pre.fund_eoa(10**21)
    tx1 = Transaction(
        to=None,
        data=bytes(constructor_with_create2),
        value=0,
        gas_limit=3_000_000,
        sender=sender_1,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    # TX[2]: Another simple successful CREATE
    sender_2 = pre.fund_eoa(10**21)
    tx2 = Transaction(
        to=None,
        data=bytes(Op.MSTORE8(0, 0x00) + Op.RETURN(0, 1)),
        value=0,
        gas_limit=3_000_000,
        sender=sender_2,
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    # TX[3]: Coinbase reporter
    reporter = pre.deploy_contract(
        code=Op.SSTORE(0, Op.BALANCE(Op.COINBASE)),
    )
    tx_reporter = Transaction(
        to=reporter,
        gas_limit=100_000,
        sender=pre.fund_eoa(),
        max_priority_fee_per_gas=1,
        max_fee_per_gas=8,
    )

    created_0 = compute_create_address(address=sender_0, nonce=0)
    created_1 = compute_create_address(address=sender_1, nonce=0)
    created_2 = compute_create_address(address=sender_2, nonce=0)

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx0, tx1, tx2, tx_reporter])],
        post={
            created_0: Account(nonce=1),  # TX[0] succeeded
            created_1: Account.NONEXISTENT,  # TX[1] hard error
            created_2: Account(nonce=1),  # TX[2] succeeded
        },
    )
