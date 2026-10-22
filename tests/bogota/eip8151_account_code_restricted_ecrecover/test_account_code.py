"""
Tests for the code of the account that ecrecover recovers, under
[EIP-8151: Account Code Restricted ecRecover](https://eips.ethereum.org/EIPS/eip-8151).

The precompile returns the recovered address only when the account holds no
code or a delegation designation; any other code makes it return empty
output, as an invalid signature does.
"""

from typing import Callable

import pytest
from execution_testing import (
    EOA,
    Account,
    Alloc,
    AuthorizationTuple,
    BalAccountExpectation,
    BlockAccessListExpectation,
    CodeGasMeasure,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
)

from .helpers import (
    CONTRACT_CODE,
    INPUT_SIZE,
    OUTPUT_OFFSET,
    SENTINEL,
    fund_signer,
    recover,
    signed_input,
)
from .spec import Spec, ref_spec_8151

REFERENCE_SPEC_GIT_PATH = ref_spec_8151.git_path
REFERENCE_SPEC_VERSION = ref_spec_8151.version

pytestmark = pytest.mark.valid_from("EIP8151")

MARKER = Spec.DELEGATION_MARKER
MARKER_PAYLOAD = Spec.DELEGATED_CODE_LENGTH - len(MARKER)
"""Length of the address after the marker in a delegation designation."""


@pytest.mark.parametrize(
    "make_signer",
    [
        pytest.param(lambda pre: pre.fund_eoa(amount=0), id="absent"),
        pytest.param(lambda pre: pre.fund_eoa(), id="balance-only"),
        pytest.param(
            lambda pre: pre.fund_eoa(nonce=1),
            id="nonce",
            marks=pytest.mark.pre_alloc_mutable,
        ),
        pytest.param(
            lambda pre: pre.fund_eoa(delegation=pre.deploy_contract(Op.STOP)),
            id="delegation-contract",
        ),
        pytest.param(
            lambda pre: pre.fund_eoa(delegation="Self"), id="delegation-self"
        ),
        pytest.param(
            lambda pre: pre.fund_eoa(delegation=Spec.ECRECOVER),
            id="delegation-precompile",
        ),
        pytest.param(
            lambda pre: pre.fund_eoa(delegation=pre.nonexistent_account()),
            id="delegation-absent",
        ),
        pytest.param(
            lambda pre: pre.fund_eoa(code=MARKER + b"\xff" * MARKER_PAYLOAD),
            id="delegation-any-20-bytes",
            marks=pytest.mark.pre_alloc_mutable,
        ),
    ],
)
@pytest.mark.with_all_call_opcodes
def test_permitted_code(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
    make_signer: Callable[[Alloc], EOA],
) -> None:
    """
    Test that ecrecover returns the address of a signer that has no account,
    no code or a delegation designation, whatever the delegation points to.
    """
    signer = make_signer(pre)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(storage.store_next(1, "success"), recover(call_opcode))
        + Op.SSTORE(
            storage.store_next(32, "returndatasize"), Op.RETURNDATASIZE
        )
        + Op.SSTORE(
            storage.store_next(signer, "output"), Op.MLOAD(OUTPUT_OFFSET)
        ),
    )

    tx = Transaction(
        to=caller, data=signed_input(signer), sender=pre.fund_eoa()
    )

    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


def test_delegation_target_not_read(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that recovering a delegated signer reads only the signer's raw
    code, leaving the delegation target out of the block access list.
    """
    target = pre.deploy_contract(Op.STOP)
    signer = pre.fund_eoa(delegation=target)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(storage.store_next(1, "success"), recover())
        + Op.SSTORE(
            storage.store_next(signer, "output"), Op.MLOAD(OUTPUT_OFFSET)
        )
    )

    tx = Transaction(
        to=caller, data=signed_input(signer), sender=pre.fund_eoa()
    )

    # Nothing else touches the target, so any read of it would be the
    # recovery's.
    state_test(
        pre=pre,
        post={caller: Account(storage=storage)},
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                signer: BalAccountExpectation.empty(),
                target: None,
            }
        ),
    )


def test_delegation_target_stays_cold(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that recovering a delegated signer leaves the delegation target
    cold.
    """
    target = pre.deploy_contract(Op.STOP)
    signer = pre.fund_eoa(delegation=target)

    balance = Op.BALANCE(target)
    cold_balance = Op.BALANCE.with_metadata(address_warm=False)
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(storage.store_next(1, "success"), recover())
        + Op.SSTORE(
            storage.store_next(signer, "output"), Op.MLOAD(OUTPUT_OFFSET)
        )
        + CodeGasMeasure(
            code=balance,
            overhead_cost=balance.gas_cost(fork) - cold_balance.gas_cost(fork),
            extra_stack_items=1,
            sstore_key=storage.store_next(
                cold_balance.gas_cost(fork), "target_balance_gas"
            ),
        )
    )

    tx = Transaction(
        to=caller, data=signed_input(signer), sender=pre.fund_eoa()
    )

    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    "account_code",
    [
        pytest.param(
            MARKER + b"\x11" * (MARKER_PAYLOAD - 1),
            id="delegation-marker-22-bytes",
        ),
        pytest.param(
            MARKER + b"\x11" * (MARKER_PAYLOAD + 1),
            id="delegation-marker-24-bytes",
        ),
        # Guards a predicate that checks the length and only the 0xEF
        # prefix.
        pytest.param(
            bytes.fromhex("ef0101") + b"\x11" * MARKER_PAYLOAD,
            id="ef0101-23-bytes",
        ),
        pytest.param(
            bytes.fromhex("ee0100") + b"\x11" * MARKER_PAYLOAD,
            id="non-ef-23-bytes",
        ),
        pytest.param(bytes.fromhex("ef"), id="ef-1-byte"),
        pytest.param(bytes.fromhex("00"), id="zero-1-byte"),
        pytest.param(bytes(CONTRACT_CODE), id="contract"),
        # The largest code the fork allows, built from the fork below.
        pytest.param(None, id="max-size"),
    ],
)
# Giving an account code is a pre-state only a filled test can hold.
@pytest.mark.pre_alloc_mutable
@pytest.mark.with_all_call_opcodes
def test_rejected_code(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    call_opcode: Op,
    account_code: bytes | None,
) -> None:
    """
    Test that ecrecover withholds the address of a signer whose code is not
    a delegation designation, returning empty output as for an invalid
    signature.
    """
    if account_code is None:
        account_code = MARKER + bytes(fork.max_code_size() - len(MARKER))
    signer = pre.fund_eoa(code=account_code)

    # Empty output leaves the sentinel in the output word.
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(storage.store_next(1, "success"), recover(call_opcode))
        + Op.SSTORE(storage.store_next(0, "returndatasize"), Op.RETURNDATASIZE)
        + Op.SSTORE(
            storage.store_next(SENTINEL, "output"), Op.MLOAD(OUTPUT_OFFSET)
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller, data=signed_input(signer), sender=pre.fund_eoa()
    )

    state_test(
        pre=pre,
        post={
            caller: Account(storage=storage),
            signer: Account(code=account_code),
        },
        tx=tx,
    )


def test_invalid_v_reads_no_account(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test that an invalid `v` on a real signer's signature fails before the
    signer's account is read, so the signer stays out of the block access
    list.
    """
    signer = pre.fund_eoa()

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(storage.store_next(1, "success"), recover())
        + Op.SSTORE(
            storage.store_next(SENTINEL, "output"), Op.MLOAD(OUTPUT_OFFSET)
        ),
    )

    # Swapping 27 and 28 would recover another address and read it, so only
    # a `v` outside both values is an invalid signature.
    tx = Transaction(
        to=caller, data=signed_input(signer, v=29), sender=pre.fund_eoa()
    )

    state_test(
        pre=pre,
        post={caller: Account(storage=storage)},
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={signer: None}
        ),
    )


def test_invalid_v_leaves_signer_cold(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Test that an invalid `v` on a real signer's signature leaves the signer
    cold.
    """
    signer = pre.fund_eoa()

    balance = Op.BALANCE(signer)
    cold_balance = Op.BALANCE.with_metadata(address_warm=False)
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(storage.store_next(1, "success"), recover())
        + CodeGasMeasure(
            code=balance,
            overhead_cost=balance.gas_cost(fork) - cold_balance.gas_cost(fork),
            extra_stack_items=1,
            sstore_key=storage.store_next(
                cold_balance.gas_cost(fork), "balance_gas"
            ),
        ),
    )

    tx = Transaction(
        to=caller, data=signed_input(signer, v=29), sender=pre.fund_eoa()
    )

    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    "v",
    [
        pytest.param(None, id="valid"),
        pytest.param(29, id="v-29"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_returndatasize_after_rejection(
    state_test: StateTestFiller,
    pre: Alloc,
    v: int | None,
) -> None:
    """
    Test that the return data after a withheld address is the same as after
    an invalid signature, even when a recovery just filled the return data
    buffer.

    Some verifiers, such as Solady's `ECDSA.recover`, detect a failed
    recovery from `RETURNDATASIZE` alone, so they treat a rejection the
    same way as a failed recovery only if the sizes match.
    """
    permitted = pre.fund_eoa()
    signer = pre.fund_eoa(code=CONTRACT_CODE)

    # The first recovery leaves 32 bytes of return data, so the call under
    # test has to clear them.
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, 2 * INPUT_SIZE)
        + Op.POP(recover(ret_size=0))
        + Op.SSTORE(
            storage.store_next(32, "recovered_returndatasize"),
            Op.RETURNDATASIZE,
        )
        + Op.SSTORE(
            storage.store_next(1, "success"),
            recover(args_offset=INPUT_SIZE, ret_size=0),
        )
        + Op.SSTORE(
            storage.store_next(0, "returndatasize"), Op.RETURNDATASIZE
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller,
        data=bytes(signed_input(permitted)) + bytes(signed_input(signer, v=v)),
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    "v,signer_read",
    [
        pytest.param(None, True, id="valid"),
        pytest.param(29, False, id="v-29"),
    ],
)
def test_transaction_to_ecrecover(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    v: int | None,
    signer_read: bool,
) -> None:
    """
    Test that a transaction sent to ecrecover reads the recovered signer
    only when the signature is valid.
    """
    signer = pre.fund_eoa()

    # The gas used is not checked: with a 128-byte input, the calldata floor
    # exceeds the execution and the standard intrinsic cost together, so it
    # is the same whether the signer is read cold, warm or not at all.
    data = bytes(signed_input(signer, v=v))
    standard_cost = fork.transaction_intrinsic_cost_calculator()(
        calldata=data, return_cost_deducted_prior_execution=True
    )
    floor_cost = fork.transaction_data_floor_cost_calculator()(data=data)
    cold_recovery = fork.ecrecover_gas(recovered=True, address_warm=False)
    assert floor_cost > standard_cost + cold_recovery

    tx = Transaction(
        to=Spec.ECRECOVER,
        data=data,
        sender=pre.fund_eoa(),
        expected_receipt=TransactionReceipt(status=1),
    )

    state_test(
        pre=pre,
        post={},
        tx=tx,
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                Spec.ECRECOVER: BalAccountExpectation.empty(),
                signer: BalAccountExpectation.empty() if signer_read else None,
            }
        ),
    )


@pytest.mark.parametrize(
    "signer_has_code",
    [
        pytest.param(False, id="applied"),
        pytest.param(True, id="skipped", marks=pytest.mark.pre_alloc_mutable),
    ],
)
def test_authorization_warms_signer(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    signer_has_code: bool,
) -> None:
    """
    Test that an authorization warms its authority for ecrecover, whether
    it is applied or skipped because the authority has code other than a
    delegation designation.

    Authorizations are applied before execution, so ecrecover sees the
    state they leave: a new delegation returns the address and a skipped
    authorization leaves the code that withholds it.
    """
    delegate = pre.deploy_contract(Op.STOP)
    signer = fund_signer(pre, has_code=signer_has_code)
    if signer_has_code:
        # A skipped authorization leaves the code and the nonce as they
        # were.
        output_word = SENTINEL
        signer_post = Account(code=bytes(CONTRACT_CODE), nonce=signer.nonce)
    else:
        output_word = int.from_bytes(signer)
        signer_post = Account(
            code=MARKER + bytes(delegate), nonce=int(signer.nonce) + 1
        )

    # The authority is warmed before its code is checked, so the warm price
    # is enough in both cases.
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(
            storage.store_next(1, "success"),
            recover(gas=fork.ecrecover_gas(recovered=True, address_warm=True)),
        )
        + Op.SSTORE(
            storage.store_next(output_word, "output"),
            Op.MLOAD(OUTPUT_OFFSET),
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller,
        data=signed_input(signer),
        authorization_list=[
            AuthorizationTuple(
                address=delegate,
                nonce=signer.nonce,
                signer=signer,
            ),
        ],
        sender=pre.fund_eoa(),
    )

    state_test(
        pre=pre,
        post={caller: Account(storage=storage), signer: signer_post},
        tx=tx,
    )
