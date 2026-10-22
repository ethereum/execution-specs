"""
Tests for the account access that ecrecover charges for, under
[EIP-8151: Account Code Restricted ecRecover](https://eips.ethereum.org/EIPS/eip-8151).

A recovery is charged an account access to the recovered address and a code
read on top of the base fee, before the account is read. Without the gas for
these the call runs out of gas: it neither warms the address nor reads the
account, and an address that was already warm stays warm.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Alloc,
    BalAccountExpectation,
    Block,
    BlockAccessListExpectation,
    BlockchainTestFiller,
    Bytecode,
    Bytes,
    CodeGasMeasure,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

from ...frontier.precompiles.spec import EcrecoverInput
from .spec import Spec, ref_spec_8151

REFERENCE_SPEC_GIT_PATH = ref_spec_8151.git_path
REFERENCE_SPEC_VERSION = ref_spec_8151.version

pytestmark = pytest.mark.valid_from("EIP8151")

DIGEST = Bytes(b"account code restricted ecrecover").keccak256()
SENTINEL = 2**256 - 1
CONTRACT_CODE = Op.SSTORE(0, 1) + Op.STOP

# Memory layout of the callers: the 128-byte input, then the output word.
INPUT_SIZE = 128
OUTPUT_OFFSET = INPUT_SIZE


@pytest.mark.parametrize(
    "gas",
    [
        pytest.param("exact", id="exact"),
        pytest.param("access-minus-one", id="access-minus-one"),
        pytest.param("base", id="base"),
        pytest.param("base-minus-one", id="base-minus-one"),
    ],
)
@pytest.mark.parametrize(
    "code",
    [
        pytest.param("balance-only", id="balance-only"),
        pytest.param(
            "contract", id="contract", marks=pytest.mark.pre_alloc_mutable
        ),
    ],
)
@pytest.mark.parametrize(
    "warmth",
    [
        pytest.param("cold", id="cold"),
        pytest.param("access-list", id="access-list"),
    ],
)
@pytest.mark.with_all_call_opcodes
def test_exact_gas_boundary(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    warmth: str,
    code: str,
    gas: str,
) -> None:
    """
    Test that a recovery succeeds with exactly the base fee plus the access
    to the recovered address and the code read, and runs out of gas with one
    less or with the base fee alone.
    """
    if code == "balance-only":
        signer = pre.fund_eoa()
        output_word = int.from_bytes(signer)
    elif code == "contract":
        # A withheld address returns empty output, leaving the sentinel.
        signer = pre.fund_eoa(code=CONTRACT_CODE)
        output_word = SENTINEL
    else:
        raise ValueError(f"unknown code: {code}")
    v, r, s = signer.sign_digest(DIGEST)

    # An access list warms the signer without reading it.
    if warmth == "cold":
        address_warm = False
        access_list = None
    elif warmth == "access-list":
        address_warm = True
        access_list = [AccessList(address=signer, storage_keys=[])]
    else:
        raise ValueError(f"unknown warmth: {warmth}")

    # A withheld address is charged like a returned one, code read included;
    # only a failed recovery skips the access.
    exact_gas = fork.ecrecover_gas(recovered=True, address_warm=address_warm)
    if gas == "exact":
        call_gas = exact_gas
        success = 1
    elif gas == "access-minus-one":
        call_gas = exact_gas - 1
        success = 0
        output_word = SENTINEL
    elif gas == "base":
        # The base fee alone, as a caller that forwards the old fixed price.
        call_gas = fork.ecrecover_gas(
            recovered=False, address_warm=address_warm
        )
        success = 0
        output_word = SENTINEL
    elif gas == "base-minus-one":
        call_gas = (
            fork.ecrecover_gas(recovered=False, address_warm=address_warm) - 1
        )
        success = 0
        output_word = SENTINEL
    else:
        raise ValueError(f"unknown gas: {gas}")

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(
            storage.store_next(success, "success"),
            call_opcode(
                gas=call_gas,
                address=Spec.ECRECOVER,
                args_offset=0,
                args_size=INPUT_SIZE,
                ret_offset=OUTPUT_OFFSET,
                ret_size=32,
            ),
        )
        + Op.SSTORE(
            storage.store_next(output_word, "output"),
            Op.MLOAD(OUTPUT_OFFSET),
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller,
        data=EcrecoverInput(msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s),
        access_list=access_list,
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    "gas",
    [
        pytest.param("exact", id="exact"),
        pytest.param("access-minus-one", id="access-minus-one"),
        pytest.param("base-minus-one", id="base-minus-one"),
    ],
)
@pytest.mark.with_all_call_opcodes
def test_cold_signer_warmed_only_when_access_paid(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    gas: str,
) -> None:
    """
    Test that ecrecover warms a cold signer when the call pays for the
    access, and leaves it cold when the call runs out of gas.
    """
    signer = pre.fund_eoa()
    v, r, s = signer.sign_digest(DIGEST)

    # A failed frame drops whatever it warmed, so only the call that pays
    # for the access leaves the signer warm.
    exact_gas = fork.ecrecover_gas(recovered=True, address_warm=False)
    if gas == "exact":
        call_gas = exact_gas
        success = 1
        address_warm = True
    elif gas == "access-minus-one":
        call_gas = exact_gas - 1
        success = 0
        address_warm = False
    elif gas == "base-minus-one":
        call_gas = fork.ecrecover_gas(recovered=False, address_warm=False) - 1
        success = 0
        address_warm = False
    else:
        raise ValueError(f"unknown gas: {gas}")

    balance = Op.BALANCE(signer)
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(
            storage.store_next(success, "success"),
            call_opcode(
                gas=call_gas,
                address=Spec.ECRECOVER,
                args_offset=0,
                args_size=INPUT_SIZE,
                ret_offset=OUTPUT_OFFSET,
                ret_size=32,
            ),
        )
        + CodeGasMeasure(
            code=balance,
            overhead_cost=balance.gas_cost(fork)
            - Op.BALANCE.with_metadata(address_warm=False).gas_cost(fork),
            extra_stack_items=1,
            sstore_key=storage.store_next(
                Op.BALANCE.with_metadata(address_warm=address_warm).gas_cost(
                    fork
                ),
                "balance_gas",
            ),
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller,
        data=EcrecoverInput(msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s),
        sender=pre.fund_eoa(),
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
    v, r, s = signer.sign_digest(DIGEST)

    balance = Op.BALANCE(signer)
    warm_balance = Op.BALANCE.with_metadata(address_warm=True)
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(
            storage.store_next(0, "success"),
            call_opcode(
                gas=fork.ecrecover_gas(recovered=True, address_warm=True) - 1,
                address=Spec.ECRECOVER,
                args_offset=0,
                args_size=INPUT_SIZE,
                ret_offset=OUTPUT_OFFSET,
                ret_size=32,
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
        data=EcrecoverInput(msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s),
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
    v, r, s = signer.sign_digest(DIGEST)
    cold_gas = fork.ecrecover_gas(recovered=True, address_warm=False)
    warm_gas = fork.ecrecover_gas(recovered=True, address_warm=True)

    def recover(gas: int) -> Bytecode:
        return Op.STATICCALL(
            gas=gas,
            address=Spec.ECRECOVER,
            args_offset=0,
            args_size=INPUT_SIZE,
            ret_offset=OUTPUT_OFFSET,
            ret_size=32,
        )

    first_storage = Storage()
    first_caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(
            first_storage.store_next(1, "cold_call"), recover(cold_gas)
        )
        + Op.SSTORE(
            first_storage.store_next(1, "warm_call"), recover(warm_gas)
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
            second_storage.store_next(0, "warm_call"), recover(warm_gas)
        )
        + Op.SSTORE(
            second_storage.store_next(1, "cold_call"), recover(cold_gas)
        )
        + Op.SSTORE(
            second_storage.store_next(signer, "output"),
            Op.MLOAD(OUTPUT_OFFSET),
        ),
        storage=second_storage.canary(),
    )

    data = EcrecoverInput(msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s)
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
    "recoverer_outcome",
    [
        pytest.param("success", id="success"),
        pytest.param("revert", id="revert"),
        pytest.param("invalid", id="invalid"),
    ],
)
def test_warmth_after_recovering_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    recoverer_outcome: str,
) -> None:
    """
    Test that a signer warmed by a recovery stays warm for the caller only
    when the frame that recovered it succeeds.

    A revert or an exceptional halt restores the warm set, so the warm price
    then runs out of gas. The read itself stays in the block access list
    either way, which also shows the recovery in a failed frame was paid.
    """
    signer = pre.fund_eoa()
    v, r, s = signer.sign_digest(DIGEST)

    if recoverer_outcome == "success":
        recoverer_exit: Bytecode = Op.STOP
        recoverer_success = 1
        signer_warm = True
    elif recoverer_outcome == "revert":
        recoverer_exit = Op.REVERT(0, 0)
        recoverer_success = 0
        signer_warm = False
    elif recoverer_outcome == "invalid":
        recoverer_exit = Op.INVALID
        recoverer_success = 0
        signer_warm = False
    else:
        raise ValueError(f"unknown recoverer outcome: {recoverer_outcome}")

    recoverer = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.POP(
            Op.STATICCALL(
                gas=fork.ecrecover_gas(recovered=True, address_warm=False),
                address=Spec.ECRECOVER,
                args_offset=0,
                args_size=INPUT_SIZE,
                ret_offset=0,
                ret_size=0,
            )
        )
        + recoverer_exit
    )

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(
            storage.store_next(recoverer_success, "recoverer_success"),
            Op.CALL(address=recoverer, args_offset=0, args_size=INPUT_SIZE),
        )
        + Op.SSTORE(
            storage.store_next(int(signer_warm), "warm_price_call"),
            Op.STATICCALL(
                gas=fork.ecrecover_gas(recovered=True, address_warm=True),
                address=Spec.ECRECOVER,
                args_offset=0,
                args_size=INPUT_SIZE,
                ret_offset=OUTPUT_OFFSET,
                ret_size=32,
            ),
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller,
        data=EcrecoverInput(msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s),
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
            Op.STATICCALL(
                gas=fork.ecrecover_gas(recovered=True, address_warm=True),
                address=Spec.ECRECOVER,
                args_offset=0,
                args_size=INPUT_SIZE,
                ret_offset=OUTPUT_OFFSET,
                ret_size=32,
            ),
        )
        + Op.SSTORE(output_slot, Op.MLOAD(OUTPUT_OFFSET))
    )

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
    v, r, s = signer.sign_digest(DIGEST)

    tx = Transaction(
        to=to,
        data=EcrecoverInput(msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s),
        sender=sender,
    )

    state_test(
        env=env,
        pre=pre,
        post={storage_owner: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.parametrize(
    "caller_outcome",
    [
        pytest.param("success", id="success"),
        pytest.param("revert", id="revert"),
    ],
)
@pytest.mark.parametrize(
    "code",
    [
        pytest.param("balance-only", id="balance-only"),
        pytest.param(
            "contract", id="contract", marks=pytest.mark.pre_alloc_mutable
        ),
    ],
)
def test_bal_records_recovered_signer(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    code: str,
    caller_outcome: str,
) -> None:
    """
    Test that a recovery puts the signer in the block access list, whether
    the address is returned or withheld, and keeps it there when the caller
    reverts.
    """
    if code == "balance-only":
        signer = pre.fund_eoa()
    elif code == "contract":
        signer = pre.fund_eoa(code=CONTRACT_CODE)
    else:
        raise ValueError(f"unknown code: {code}")
    v, r, s = signer.sign_digest(DIGEST)

    call = Op.STATICCALL(
        gas=fork.ecrecover_gas(recovered=True, address_warm=False),
        address=Spec.ECRECOVER,
        args_offset=0,
        args_size=INPUT_SIZE,
        ret_offset=OUTPUT_OFFSET,
        ret_size=32,
    )
    # The recoverer hands the precompile call's result back either way.
    if caller_outcome == "success":
        recoverer_exit = Op.RETURN(0, 32)
        recoverer_success = 1
    elif caller_outcome == "revert":
        recoverer_exit = Op.REVERT(0, 32)
        recoverer_success = 0
    else:
        raise ValueError(f"unknown caller outcome: {caller_outcome}")
    recoverer = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE) + Op.MSTORE(0, call) + recoverer_exit
    )

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(
            storage.store_next(recoverer_success, "recoverer_success"),
            Op.CALL(address=recoverer, args_offset=0, args_size=INPUT_SIZE),
        )
        + Op.RETURNDATACOPY(0, 0, 32)
        + Op.SSTORE(storage.store_next(1, "success"), Op.MLOAD(0)),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller,
        data=EcrecoverInput(msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s),
        sender=pre.fund_eoa(),
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
    "gas",
    [
        pytest.param("access-minus-one", id="access-minus-one"),
        pytest.param("base-minus-one", id="base-minus-one"),
    ],
)
@pytest.mark.parametrize(
    "warmth",
    [
        pytest.param("cold", id="cold"),
        pytest.param("access-list", id="access-list"),
        pytest.param("balance", id="balance"),
    ],
)
def test_bal_after_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    warmth: str,
    gas: str,
) -> None:
    """
    Test that an ecrecover call that runs out of gas does not read the
    signer, which reaches the block access list only through another read.
    """
    signer = pre.fund_eoa()
    v, r, s = signer.sign_digest(DIGEST)

    # Only the BALANCE case reads the signer outside ecrecover; access list
    # entries are not added to the block access list by themselves.
    if warmth == "cold":
        address_warm = False
        access_list = None
        prior_read = Bytecode()
        signer_in_bal: BalAccountExpectation | None = None
    elif warmth == "access-list":
        address_warm = True
        access_list = [AccessList(address=signer, storage_keys=[])]
        prior_read = Bytecode()
        signer_in_bal = None
    elif warmth == "balance":
        address_warm = True
        access_list = None
        prior_read = Op.POP(Op.BALANCE(signer))
        signer_in_bal = BalAccountExpectation.empty()
    else:
        raise ValueError(f"unknown warmth: {warmth}")

    if gas == "access-minus-one":
        call_gas = (
            fork.ecrecover_gas(recovered=True, address_warm=address_warm) - 1
        )
    elif gas == "base-minus-one":
        call_gas = (
            fork.ecrecover_gas(recovered=False, address_warm=address_warm) - 1
        )
    else:
        raise ValueError(f"unknown gas: {gas}")

    storage = Storage()
    caller = pre.deploy_contract(
        prior_read
        + Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(
            storage.store_next(0, "success"),
            Op.STATICCALL(
                gas=call_gas,
                address=Spec.ECRECOVER,
                args_offset=0,
                args_size=INPUT_SIZE,
                ret_offset=OUTPUT_OFFSET,
                ret_size=32,
            ),
        )
        + Op.SSTORE(
            storage.store_next(SENTINEL, "output"), Op.MLOAD(OUTPUT_OFFSET)
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller,
        data=EcrecoverInput(msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s),
        access_list=access_list,
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={caller: Account(storage=storage)},
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={signer: signer_in_bal}
        ),
    )
