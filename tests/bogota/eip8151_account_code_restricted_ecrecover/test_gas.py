"""
Tests for the account access that ecrecover charges for, under
[EIP-8151: Account Code Restricted ecRecover](https://eips.ethereum.org/EIPS/eip-8151).

A recovery is charged an account access to the recovered address and a code
read on top of the base fee, before the account is read. Without the gas for
these the call runs out of gas: it neither warms the address nor reads the
account, and an address that was already warm stays warm.
"""

from typing import Callable

import pytest
from execution_testing import (
    EOA,
    AccessList,
    Account,
    Alloc,
    BalAccountExpectation,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    CodeGasMeasure,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from ...frontier.precompiles.spec import EcrecoverInput
from .helpers import (
    CONTRACT_CODE,
    DIGEST,
    INPUT_SIZE,
    OUTPUT_OFFSET,
    SENTINEL,
    fund_signer,
    recover,
    signed_input,
)
from .spec import ref_spec_8151

REFERENCE_SPEC_GIT_PATH = ref_spec_8151.git_path
REFERENCE_SPEC_VERSION = ref_spec_8151.version

pytestmark = pytest.mark.valid_from("EIP8151")


@pytest.mark.parametrize(
    "priced_as_recovered,gas_delta,call_succeeds",
    [
        pytest.param(True, 0, True, id="exact"),
        pytest.param(True, -1, False, id="access-minus-one"),
        # The base fee alone, as a caller that forwards the old fixed price.
        pytest.param(False, 0, False, id="base"),
        pytest.param(False, -1, False, id="base-minus-one"),
    ],
)
@pytest.mark.parametrize(
    "signer_has_code",
    [
        pytest.param(False, id="balance-only"),
        pytest.param(True, id="contract", marks=pytest.mark.pre_alloc_mutable),
    ],
)
@pytest.mark.parametrize(
    "address_warm",
    [
        pytest.param(False, id="cold"),
        pytest.param(True, id="access-list"),
    ],
)
@pytest.mark.with_all_call_opcodes
def test_exact_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    address_warm: bool,
    signer_has_code: bool,
    priced_as_recovered: bool,
    gas_delta: int,
    call_succeeds: bool,
) -> None:
    """
    Test that a recovery succeeds with exactly the base fee plus the access
    to the recovered address and the code read, and runs out of gas with one
    less or with the base fee alone.
    """
    signer = fund_signer(pre, has_code=signer_has_code)
    # A withheld address returns empty output, as does a call that runs out
    # of gas, leaving the sentinel.
    if call_succeeds and not signer_has_code:
        output_word = int.from_bytes(signer)
    else:
        output_word = SENTINEL

    # A withheld address is charged like a returned one, code read included;
    # only a failed recovery skips the access.
    call_gas = (
        fork.ecrecover_gas(
            recovered=priced_as_recovered, address_warm=address_warm
        )
        + gas_delta
    )

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(
            storage.store_next(int(call_succeeds), "success"),
            recover(call_opcode, gas=call_gas),
        )
        + Op.SSTORE(
            storage.store_next(output_word, "output"),
            Op.MLOAD(OUTPUT_OFFSET),
        ),
        storage=storage.canary(),
    )

    # An access list warms the signer without reading it.
    tx = Transaction(
        to=caller,
        data=signed_input(signer),
        access_list=(
            [AccessList(address=signer, storage_keys=[])]
            if address_warm
            else None
        ),
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    "gas_delta,call_succeeds",
    [
        pytest.param(0, True, id="exact"),
        pytest.param(-1, False, id="minus-one"),
    ],
)
@pytest.mark.parametrize(
    "v,r,s",
    [
        # A `v` other than 27 or 28 fails before any recovery.
        pytest.param(29, 1, 1, id="v-29"),
        # In-range parameters that recover no key: 5 is not the x-coordinate
        # of any curve point, as 5**3 + 7 is a quadratic non-residue.
        pytest.param(27, 5, 1, id="r-not-on-curve"),
    ],
)
@pytest.mark.with_all_call_opcodes
def test_failed_recovery_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    v: int,
    r: int,
    s: int,
    gas_delta: int,
    call_succeeds: bool,
) -> None:
    """
    Test that a failed recovery pays the base fee before it fails: exactly
    the base fee returns empty output, and one less runs out of gas.
    """
    call_gas = (
        fork.ecrecover_gas(recovered=False, address_warm=False) + gas_delta
    )

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(
            storage.store_next(int(call_succeeds), "success"),
            recover(call_opcode, gas=call_gas),
        )
        + Op.SSTORE(storage.store_next(0, "returndatasize"), Op.RETURNDATASIZE)
        + Op.SSTORE(
            storage.store_next(SENTINEL, "output"), Op.MLOAD(OUTPUT_OFFSET)
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller,
        data=EcrecoverInput(msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s),
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    "priced_as_recovered,gas_delta,call_succeeds",
    [
        pytest.param(True, 0, True, id="exact"),
        pytest.param(True, -1, False, id="access-minus-one"),
        pytest.param(False, -1, False, id="base-minus-one"),
    ],
)
@pytest.mark.parametrize(
    "signer_has_code",
    [
        pytest.param(False, id="balance-only"),
        pytest.param(True, id="contract", marks=pytest.mark.pre_alloc_mutable),
    ],
)
@pytest.mark.with_all_call_opcodes
def test_cold_signer_warmed_only_when_access_paid(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    signer_has_code: bool,
    priced_as_recovered: bool,
    gas_delta: int,
    call_succeeds: bool,
) -> None:
    """
    Test that ecrecover warms a cold signer when the call pays for the
    access, whether the address is then returned or withheld, and leaves it
    cold when the call runs out of gas.
    """
    signer = fund_signer(pre, has_code=signer_has_code)
    call_gas = (
        fork.ecrecover_gas(recovered=priced_as_recovered, address_warm=False)
        + gas_delta
    )

    # A failed frame drops whatever it warmed, so only the call that pays
    # for the access leaves the signer warm.
    balance = Op.BALANCE(signer)
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(
            storage.store_next(int(call_succeeds), "success"),
            recover(call_opcode, gas=call_gas),
        )
        + CodeGasMeasure(
            code=balance,
            overhead_cost=balance.gas_cost(fork)
            - Op.BALANCE.with_metadata(address_warm=False).gas_cost(fork),
            extra_stack_items=1,
            sstore_key=storage.store_next(
                Op.BALANCE.with_metadata(address_warm=call_succeeds).gas_cost(
                    fork
                ),
                "balance_gas",
            ),
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller, data=signed_input(signer), sender=pre.fund_eoa()
    )

    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.with_all_call_opcodes
def test_access_oog_preserves_prior_warmth(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
) -> None:
    """
    Test that a signer warmed by the access list is still warm after an
    ecrecover call runs out of gas for the access.
    """
    signer = pre.fund_eoa()

    balance = Op.BALANCE(signer)
    warm_balance = Op.BALANCE.with_metadata(address_warm=True)
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(
            storage.store_next(0, "success"),
            recover(
                call_opcode,
                gas=fork.ecrecover_gas(recovered=True, address_warm=True) - 1,
            ),
        )
        # A failed frame drops only what it added; the caller's warm set
        # is left as it was.
        + CodeGasMeasure(
            code=balance,
            overhead_cost=balance.gas_cost(fork)
            - Op.BALANCE.with_metadata(address_warm=False).gas_cost(fork),
            extra_stack_items=1,
            sstore_key=storage.store_next(
                warm_balance.gas_cost(fork), "balance_gas"
            ),
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller,
        data=signed_input(signer),
        access_list=[AccessList(address=signer, storage_keys=[])],
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


def test_repeated_recovery(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that recovering a signer again in the same transaction costs the
    warm price, and that the signer is cold again in the next transaction
    of the block.

    The input is identical every time, so an implementation that caches the
    precompile result by input must still price each call by warmth.
    """
    signer = pre.fund_eoa()
    cold_gas = fork.ecrecover_gas(recovered=True, address_warm=False)
    warm_gas = fork.ecrecover_gas(recovered=True, address_warm=True)

    first_storage = Storage()
    first_caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(
            first_storage.store_next(1, "cold_call"), recover(gas=cold_gas)
        )
        + Op.SSTORE(
            first_storage.store_next(1, "warm_call"), recover(gas=warm_gas)
        )
        + Op.SSTORE(
            first_storage.store_next(signer, "output"),
            Op.MLOAD(OUTPUT_OFFSET),
        ),
        storage=first_storage.canary(),
    )

    # The warm price runs out of gas before the cold call warms the signer.
    second_storage = Storage()
    second_caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(
            second_storage.store_next(0, "warm_call"), recover(gas=warm_gas)
        )
        + Op.SSTORE(
            second_storage.store_next(1, "cold_call"), recover(gas=cold_gas)
        )
        + Op.SSTORE(
            second_storage.store_next(signer, "output"),
            Op.MLOAD(OUTPUT_OFFSET),
        ),
        storage=second_storage.canary(),
    )

    data = signed_input(signer)
    sender = pre.fund_eoa()
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(to=first_caller, data=data, sender=sender),
                    Transaction(to=second_caller, data=data, sender=sender),
                ]
            )
        ],
        post={
            first_caller: Account(storage=first_storage),
            second_caller: Account(storage=second_storage),
        },
    )


@pytest.mark.parametrize(
    "recoverer_exit,frame_succeeds",
    [
        pytest.param(Op.STOP, True, id="success"),
        pytest.param(Op.REVERT(0, 0), False, id="revert"),
        pytest.param(Op.INVALID, False, id="invalid"),
    ],
)
@pytest.mark.parametrize(
    "warm_on_entry",
    [
        pytest.param(False, id="cold"),
        pytest.param(True, id="access-list"),
    ],
)
def test_warmth_after_recovering_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    warm_on_entry: bool,
    recoverer_exit: Bytecode,
    frame_succeeds: bool,
) -> None:
    """
    Test that a signer warmed by a recovery stays warm for the caller only
    when the frame that recovered it succeeds, and that a signer already
    warm before that frame stays warm whatever its outcome.

    A revert or an exceptional halt restores the warm set to what it was on
    entry to the frame, so a signer the frame warmed is cold again and the
    warm price runs out of gas. The read itself stays in the block access
    list either way, which also shows the recovery in a failed frame was
    paid.
    """
    signer = pre.fund_eoa()

    recoverer = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.POP(
            recover(
                gas=fork.ecrecover_gas(
                    recovered=True, address_warm=warm_on_entry
                ),
                ret_size=0,
            )
        )
        + recoverer_exit
    )

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(
            storage.store_next(int(frame_succeeds), "recoverer_success"),
            Op.CALL(address=recoverer, args_offset=0, args_size=INPUT_SIZE),
        )
        + Op.SSTORE(
            storage.store_next(
                int(frame_succeeds or warm_on_entry), "warm_price_call"
            ),
            recover(gas=fork.ecrecover_gas(recovered=True, address_warm=True)),
        ),
        storage=storage.canary(),
    )

    # An access list warms the signer without reading it.
    tx = Transaction(
        to=caller,
        data=signed_input(signer),
        access_list=(
            [AccessList(address=signer, storage_keys=[])]
            if warm_on_entry
            else None
        ),
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={caller: Account(storage=storage)},
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={signer: BalAccountExpectation.empty()}
        ),
    )


@pytest.mark.parametrize(
    "warmed_as",
    [
        pytest.param("sender", id="sender"),
        pytest.param(
            "coinbase",
            id="coinbase",
            marks=pytest.mark.execute(
                pytest.mark.skip(
                    reason="requires env.fee_recipient as block coinbase"
                )
            ),
        ),
        pytest.param("executing-account", id="executing-account"),
    ],
)
def test_signer_warmed_by_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    warmed_as: str,
) -> None:
    """
    Test that a signer the transaction has already warmed is recovered for
    the warm price: the sender, the block coinbase, and a delegated account
    recovering its own signature.
    """
    # The signer, and so the expected output, depends on the case, so the
    # output slot is filled in once the signer exists.
    storage = Storage()
    success_slot = storage.store_next(1, "success")
    output_slot = storage.store_next(0, "output")
    recovering_code = (
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(
            success_slot,
            recover(gas=fork.ecrecover_gas(recovered=True, address_warm=True)),
        )
        + Op.SSTORE(output_slot, Op.MLOAD(OUTPUT_OFFSET))
    )

    # Each case warms the signer a different way, so each builds its own
    # transaction shape.
    env = Environment()
    if warmed_as == "sender":
        signer = pre.fund_eoa()
        sender = signer
        to = pre.deploy_contract(recovering_code)
        storage_owner = to
    elif warmed_as == "coinbase":
        signer = pre.fund_eoa()
        sender = pre.fund_eoa()
        to = pre.deploy_contract(recovering_code)
        storage_owner = to
        env = Environment(fee_recipient=signer)
    elif warmed_as == "executing-account":
        # The delegation designation keeps the signer's address returned,
        # and the code runs as the signer, the call target.
        signer = pre.fund_eoa(delegation=pre.deploy_contract(recovering_code))
        sender = pre.fund_eoa()
        to = signer
        storage_owner = signer
    else:
        raise ValueError(f"unknown warmed_as: {warmed_as}")
    storage[output_slot] = signer

    tx = Transaction(to=to, data=signed_input(signer), sender=sender)

    state_test(
        env=env,
        pre=pre,
        post={storage_owner: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.parametrize(
    "recoverer_exit,frame_succeeds",
    [
        pytest.param(Op.RETURN(0, 32), True, id="success"),
        pytest.param(Op.REVERT(0, 32), False, id="revert"),
    ],
)
@pytest.mark.parametrize(
    "make_signer",
    [
        # A signer with no account is read as an account with empty code.
        pytest.param(lambda pre: pre.fund_eoa(amount=0), id="absent"),
        pytest.param(lambda pre: pre.fund_eoa(), id="balance-only"),
        pytest.param(
            lambda pre: pre.fund_eoa(code=CONTRACT_CODE),
            id="contract",
            marks=pytest.mark.pre_alloc_mutable,
        ),
    ],
)
def test_bal_records_recovered_signer(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    make_signer: Callable[[Alloc], EOA],
    recoverer_exit: Bytecode,
    frame_succeeds: bool,
) -> None:
    """
    Test that a recovery puts the signer in the block access list, whether
    the address is returned or withheld, and keeps it there when the caller
    reverts.
    """
    signer = make_signer(pre)

    # The recoverer hands the precompile call's result back either way.
    recoverer = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(
            0,
            recover(
                gas=fork.ecrecover_gas(recovered=True, address_warm=False)
            ),
        )
        + recoverer_exit
    )

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(
            storage.store_next(int(frame_succeeds), "recoverer_success"),
            Op.CALL(address=recoverer, args_offset=0, args_size=INPUT_SIZE),
        )
        + Op.RETURNDATACOPY(0, 0, 32)
        + Op.SSTORE(storage.store_next(1, "success"), Op.MLOAD(0)),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller, data=signed_input(signer), sender=pre.fund_eoa()
    )

    # The read is recorded when the access is paid for, and a revert does
    # not remove it.
    state_test(
        pre=pre,
        post={caller: Account(storage=storage)},
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={signer: BalAccountExpectation.empty()}
        ),
    )


@pytest.mark.parametrize(
    "priced_as_recovered",
    [
        pytest.param(True, id="access-minus-one"),
        pytest.param(False, id="base-minus-one"),
    ],
)
@pytest.mark.parametrize(
    "access_listed,read_first",
    [
        pytest.param(False, False, id="cold"),
        pytest.param(True, False, id="access-list"),
        pytest.param(False, True, id="balance"),
    ],
)
def test_bal_after_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    access_listed: bool,
    read_first: bool,
    priced_as_recovered: bool,
) -> None:
    """
    Test that an ecrecover call that runs out of gas does not read the
    signer, which reaches the block access list only through another read.
    """
    signer = pre.fund_eoa()
    call_gas = (
        fork.ecrecover_gas(
            recovered=priced_as_recovered,
            address_warm=access_listed or read_first,
        )
        - 1
    )

    # Only the BALANCE case reads the signer outside ecrecover; access list
    # entries are not added to the block access list by themselves.
    storage = Storage()
    caller = pre.deploy_contract(
        (Op.POP(Op.BALANCE(signer)) if read_first else Bytecode())
        + Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(storage.store_next(0, "success"), recover(gas=call_gas))
        + Op.SSTORE(
            storage.store_next(SENTINEL, "output"), Op.MLOAD(OUTPUT_OFFSET)
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller,
        data=signed_input(signer),
        access_list=(
            [AccessList(address=signer, storage_keys=[])]
            if access_listed
            else None
        ),
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={caller: Account(storage=storage)},
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                signer: BalAccountExpectation.empty() if read_first else None
            }
        ),
    )
