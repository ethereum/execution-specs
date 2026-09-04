"""
Tests for [EIP-8246: Remove SELFDESTRUCT balance burn](https://eips.ethereum.org/EIPS/eip-8246).

Further fork-aware EIP-8246 coverage lives in the EIP-6780 selfdestruct
tests (``tests/cancun/eip6780_selfdestruct``).
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BalBalanceChange,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Conditional,
    Fork,
    Hash,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
    compute_create_address,
    keccak256,
)
from execution_testing import (
    Macros as Om,
)
from execution_testing.checklists import EIPChecklist

from ..eip7708_eth_transfer_logs.spec import transfer_log
from .spec import ref_spec_8246

REFERENCE_SPEC_GIT_PATH = ref_spec_8246.git_path
REFERENCE_SPEC_VERSION = ref_spec_8246.version

pytestmark = pytest.mark.valid_from("EIP8246")


@pytest.mark.parametrize("initial_balance", [0, 1])
@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
@pytest.mark.parametrize("post_send_count", [0, 1, 3])
@pytest.mark.parametrize(
    "post_send_opcode", [Op.CALL, Op.CALLCODE, Op.SELFDESTRUCT]
)
@pytest.mark.parametrize(
    "initial_storage",
    [
        pytest.param(False, id="no_storage"),
        pytest.param(True, id="with_storage"),
    ],
)
@pytest.mark.parametrize(
    "transfer_target, transfer_drains_victim",
    [
        pytest.param(Op.ADDRESS, False, id="self"),
        pytest.param(0x01, True, id="precompile"),
        pytest.param(
            Address(keccak256(b"eip-8246-eoa-target")[-20:]),
            True,
            id="eoa",
        ),
    ],
)
@pytest.mark.parametrize(
    "exit_op, execution_success",
    [
        pytest.param(Op.STOP, True, id="success"),
        pytest.param(Op.REVERT(0, 0), False, id="revert"),
        pytest.param(Op.MSTORE(2**32, 0), False, id="oog"),
    ],
)
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior()
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior.Opcode()
@EIPChecklist.Opcode.Test.Terminating.Scenarios.Initcode()
@EIPChecklist.Opcode.Test.Terminating.Rollback.Balance()
def test_selfdestructing_initcode_preserves_balance(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    initial_balance: int,
    post_send_count: int,
    create_opcode: Op,
    post_send_opcode: Op,
    initial_storage: bool,
    transfer_target: Op,
    transfer_drains_victim: bool,
    exit_op: Op,
    execution_success: bool,
) -> None:
    """
    Same-tx SELFDESTRUCT preserves the victim's balance per EIP-8246.

    Test flow:
      selfdestruct_tx
        tx.to = entry_contract
          └─ CALL selfdestruct_contract_factory
              └─ initcode runs:
                  [optional] SSTORE(slot, value)
                  SELFDESTRUCT(transfer_target)   # registers victim
              └─ selfdestruct_contract_factory exits via STOP | REVERT | OOG
          └─ N * post-send to victim (CALL | CALLCODE | donor.SELFDESTRUCT)

        tx finalize
         - victim balance-only per EIP-8246,
         - or NONEXISTENT if EIP-161 cleans up a zero-balance account

      probe_tx
        tx.to = probe_contract
          └─ STORAGE [0] = BALANCE(victim)
             STORAGE [1] = EXTCODEHASH(victim)
             STORAGE [2] = EXTCODESIZE(victim)
             STORAGE [3] = SHA3(EXTCODECOPY(victim, 0, 0, size))
    """
    # Selfdestruct target contract template.
    # Optionally initializes storage to test clearing.
    storage_init = Op.SSTORE(0, 1) if initial_storage else Bytecode()
    selfdestruct_initcode = storage_init + Op.SELFDESTRUCT(transfer_target)

    selfdestruct_template = pre.deploy_contract(code=selfdestruct_initcode)

    # Build selfdestruct target contract via CREATE/CREATE2
    salt = 0
    if create_opcode == Op.CREATE2:
        create_call = create_opcode(
            value=initial_balance,
            size=len(selfdestruct_initcode),
            salt=salt,
        )
    else:
        create_call = create_opcode(
            value=initial_balance,
            size=len(selfdestruct_initcode),
        )

    # Selfdestruct target contract factory
    # Exits via STOP/REVERT/OOG for different scenario
    selfdestruct_contract_factory = pre.deploy_contract(
        code=Op.EXTCODECOPY(
            address=selfdestruct_template, size=len(selfdestruct_initcode)
        )
        + Op.POP(create_call)
        + exit_op
    )

    victim = compute_create_address(
        address=selfdestruct_contract_factory,
        opcode=create_opcode,
        nonce=1,
        salt=salt,
        initcode=selfdestruct_initcode,
    )

    # Post value sending to the victim
    # Ensure the ether transfer is not burned after eip-8246.
    post_send_value = 1
    if post_send_opcode == Op.SELFDESTRUCT:
        donor = pre.deploy_contract(code=Op.SELFDESTRUCT(victim))
        post_send = Op.POP(
            Op.CALL(gas=Op.GAS, address=donor, value=post_send_value)
        )
    else:
        post_send = Op.POP(
            post_send_opcode(gas=Op.GAS, address=victim, value=post_send_value)
        )

    entry_contract = pre.deploy_contract(
        code=Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=selfdestruct_contract_factory,
                value=initial_balance,
            )
        )
        + post_send * post_send_count
    )

    total_balance = initial_balance + post_send_count * post_send_value

    sender = pre.fund_eoa()
    selfdestruct_tx = Transaction(
        sender=sender, to=entry_contract, value=total_balance
    )

    # Balance verification
    #   retained:
    #       selfdestruct-to-self retains balance
    #       selfdestruct-to-others drains balance if not revert / OOG
    #   delivered: post-sends count except for CALLCODE
    retained = 0 if transfer_drains_victim else initial_balance
    delivered = (
        0
        if post_send_opcode == Op.CALLCODE
        else post_send_count * post_send_value
    )

    expected_balance = retained + delivered if execution_success else delivered
    victim_alive = expected_balance > 0

    probe_storage = Storage()
    probe_code = (
        Op.SSTORE(
            probe_storage.store_next(expected_balance),
            Op.BALANCE(Op.CALLDATALOAD(0)),
        )
        + Op.SSTORE(
            probe_storage.store_next(keccak256(b"") if victim_alive else 0),
            Op.EXTCODEHASH(Op.CALLDATALOAD(0)),
        )
        + Op.SSTORE(
            probe_storage.store_next(0),
            Op.EXTCODESIZE(Op.CALLDATALOAD(0)),
        )
        + Op.EXTCODECOPY(
            Op.CALLDATALOAD(0), 0, 0, Op.EXTCODESIZE(Op.CALLDATALOAD(0))
        )
        + Op.SSTORE(
            probe_storage.store_next(keccak256(b"")),
            Op.SHA3(0, Op.EXTCODESIZE(Op.CALLDATALOAD(0))),
        )
        + Op.STOP
    )

    probe_contract = pre.deploy_contract(
        code=probe_code, storage=probe_storage.canary()
    )

    probe_tx = Transaction(
        sender=sender, to=probe_contract, data=Hash(victim, left_padding=True)
    )

    blockchain_test(
        pre=pre,
        post={
            victim: (
                Account.NONEXISTENT
                if not victim_alive
                else Account(
                    balance=expected_balance, nonce=0, code=b"", storage={}
                )
            ),
            probe_contract: Account(storage=probe_storage),
        },
        blocks=[Block(txs=[selfdestruct_tx, probe_tx])],
    )


@pytest.mark.parametrize(
    "value",
    [pytest.param(1, id="kept"), pytest.param(0, id="removed")],
)
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Behavior.Tx()
@EIPChecklist.Opcode.Test.Terminating.Scenarios.TopLevel()
def test_create_transaction_initcode_selfdestruct(
    state_test: StateTestFiller,
    pre: Alloc,
    value: int,
) -> None:
    """
    Depth-0 creation-tx initcode SELFDESTRUCT keeps balance per EIP-8246.

    A creation transaction (``tx.to is None``) whose initcode
    self-destructs to itself exercises the depth-0 create path. A nonzero
    endowment is kept as a balance-only account; a zero endowment is
    removed.
    """
    sender = pre.fund_eoa()
    created = compute_create_address(address=sender, nonce=sender.nonce)

    tx = Transaction(
        sender=sender,
        to=None,
        value=value,
        data=Op.SELFDESTRUCT(Op.ADDRESS),
    )
    post = {
        created: (
            Account(balance=value, nonce=0, code=b"", storage={})
            if value
            else Account.NONEXISTENT
        )
    }
    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "sweep_on_redeploy",
    [
        pytest.param(False, id="selfdestruct_to_self"),
        pytest.param(True, id="sweep_to_origin"),
    ],
)
@EIPChecklist.Opcode.Test.ExecutionContext.Initcode.Reentry()
@EIPChecklist.Opcode.Test.Terminating.Scenarios.Initcode()
def test_create2_redeploy_over_remnant(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    sweep_on_redeploy: bool,
) -> None:
    """
    Case 17 of the EIP and its third security consideration. Because the
    account left behind has nonce zero and no storage, the same factory can
    CREATE2 over it again in a later transaction, and that second deployment
    can spend the balance the first one left there.
    """
    endowment = 5
    deployer = pre.fund_eoa()
    redeployer = pre.fund_eoa()

    if sweep_on_redeploy:
        # Only a redeploy sees a balance above the call value, so the same
        # initcode bytes sweep to the redeployer the second time.
        selfdestruct: Bytecode = Conditional(
            condition=Op.GT(Op.BALANCE(Op.ADDRESS), Op.CALLVALUE),
            if_true=Op.SELFDESTRUCT(Op.ORIGIN),
            if_false=Op.SELFDESTRUCT(Op.ADDRESS),
        )
        redeploy_value = 0
    else:
        selfdestruct = Op.SELFDESTRUCT(Op.ADDRESS)
        redeploy_value = endowment

    initcode = Op.SSTORE(0, 1) + selfdestruct
    factory = pre.deploy_contract(
        code=Om.MSTORE(initcode, 0)
        + Op.SSTORE(
            Op.CALLDATALOAD(0),
            Op.CREATE2(
                value=Op.CALLVALUE, offset=0, size=len(initcode), salt=0
            ),
        )
        + Op.STOP
    )
    created = compute_create_address(
        address=factory, salt=0, initcode=initcode, opcode=Op.CREATE2
    )

    tx1 = Transaction(
        sender=deployer, to=factory, value=endowment, data=Hash(1)
    )
    tx2 = Transaction(
        sender=redeployer, to=factory, value=redeploy_value, data=Hash(2)
    )

    created_post: Account | None
    if sweep_on_redeploy:
        created_post = Account.NONEXISTENT
        final_balance = 0
        tx2_logs = [transfer_log(created, redeployer, endowment)]
    else:
        final_balance = 2 * endowment
        created_post = Account(
            balance=final_balance, nonce=0, code=b"", storage={}
        )
        tx2_logs = [
            transfer_log(redeployer, factory, endowment),
            transfer_log(factory, created, endowment),
        ]
    if fork.is_eip_enabled(7708):
        tx1.expected_receipt = TransactionReceipt(
            logs=[
                transfer_log(deployer, factory, endowment),
                transfer_log(factory, created, endowment),
            ]
        )
        tx2.expected_receipt = TransactionReceipt(logs=tx2_logs)

    expected_bal = None
    if fork.is_eip_enabled(7928):
        expected_bal = BlockAccessListExpectation(
            account_expectations={
                created: BalAccountExpectation(
                    nonce_changes=[],
                    code_changes=[],
                    storage_changes=[],
                    storage_reads=[0],
                    balance_changes=[
                        BalBalanceChange(
                            block_access_index=1, post_balance=endowment
                        ),
                        BalBalanceChange(
                            block_access_index=2, post_balance=final_balance
                        ),
                    ],
                )
            }
        )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(txs=[tx1, tx2], expected_block_access_list=expected_bal)
        ],
        post={
            factory: Account(nonce=3, storage={1: created, 2: created}),
            created: created_post,
        },
    )
