"""
Tests for the code of the account that ecrecover recovers, under
[EIP-8151: Account Code Restricted ecRecover](https://eips.ethereum.org/EIPS/eip-8151).

The precompile returns the recovered address only when the account holds no
code or a delegation designation; any other code makes it return empty
output, as an invalid signature does.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    BalAccountExpectation,
    BlockAccessListExpectation,
    Bytes,
    CodeGasMeasure,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionReceipt,
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
    "code",
    [
        pytest.param("absent", id="absent"),
        pytest.param("balance-only", id="balance-only"),
        pytest.param("nonce", id="nonce", marks=pytest.mark.pre_alloc_mutable),
        pytest.param("delegation-contract", id="delegation-contract"),
        pytest.param("delegation-self", id="delegation-self"),
        pytest.param("delegation-precompile", id="delegation-precompile"),
        pytest.param("delegation-absent", id="delegation-absent"),
        pytest.param(
            "delegation-any-20-bytes",
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
    code: str,
) -> None:
    """
    Test that ecrecover returns the address of a signer that has no account,
    no code or a delegation designation, whatever the delegation points to.
    """
    if code == "absent":
        signer = pre.fund_eoa(amount=0)
    elif code == "balance-only":
        signer = pre.fund_eoa()
    elif code == "nonce":
        signer = pre.fund_eoa(nonce=1)
    elif code == "delegation-contract":
        signer = pre.fund_eoa(delegation=pre.deploy_contract(Op.STOP))
    elif code == "delegation-self":
        signer = pre.fund_eoa(delegation="Self")
    elif code == "delegation-precompile":
        signer = pre.fund_eoa(delegation=Spec.ECRECOVER)
    elif code == "delegation-absent":
        signer = pre.fund_eoa(delegation=pre.nonexistent_account())
    elif code == "delegation-any-20-bytes":
        signer = pre.fund_eoa(code=Spec.DELEGATION_MARKER + b"\xff" * 20)
    else:
        raise ValueError(f"unknown code: {code}")

    v, r, s = signer.sign_digest(DIGEST)

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(
            storage.store_next(1, "success"),
            call_opcode(
                address=Spec.ECRECOVER,
                args_offset=0,
                args_size=INPUT_SIZE,
                ret_offset=OUTPUT_OFFSET,
                ret_size=32,
            ),
        )
        + Op.SSTORE(
            storage.store_next(32, "returndatasize"), Op.RETURNDATASIZE
        )
        + Op.SSTORE(
            storage.store_next(signer, "output"), Op.MLOAD(OUTPUT_OFFSET)
        ),
    )

    tx = Transaction(
        to=caller,
        data=EcrecoverInput(msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s),
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    "code",
    [
        pytest.param(
            "delegation-marker-22-bytes", id="delegation-marker-22-bytes"
        ),
        pytest.param(
            "delegation-marker-24-bytes", id="delegation-marker-24-bytes"
        ),
        pytest.param("ef0101-23-bytes", id="ef0101-23-bytes"),
        pytest.param("non-ef-23-bytes", id="non-ef-23-bytes"),
        pytest.param("ef-1-byte", id="ef-1-byte"),
        pytest.param("zero-1-byte", id="zero-1-byte"),
        pytest.param("contract", id="contract"),
        pytest.param("max-size", id="max-size"),
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
    code: str,
) -> None:
    """
    Test that ecrecover withholds the address of a signer whose code is not
    a delegation designation, returning empty output as for an invalid
    signature.
    """
    marker = Spec.DELEGATION_MARKER
    length = Spec.DELEGATED_CODE_LENGTH
    if code == "delegation-marker-22-bytes":
        account_code = marker + b"\x11" * (length - len(marker) - 1)
    elif code == "delegation-marker-24-bytes":
        account_code = marker + b"\x11" * (length - len(marker) + 1)
    elif code == "ef0101-23-bytes":
        # Guards a predicate that checks the length and only the 0xEF
        # prefix.
        account_code = bytes.fromhex("ef0101") + b"\x11" * (length - 3)
    elif code == "non-ef-23-bytes":
        account_code = bytes.fromhex("ee0100") + b"\x11" * (length - 3)
    elif code == "ef-1-byte":
        account_code = bytes.fromhex("ef")
    elif code == "zero-1-byte":
        account_code = bytes.fromhex("00")
    elif code == "contract":
        account_code = bytes(CONTRACT_CODE)
    elif code == "max-size":
        account_code = marker + bytes(fork.max_code_size() - len(marker))
    else:
        raise ValueError(f"unknown code: {code}")

    signer = pre.fund_eoa(code=account_code)
    v, r, s = signer.sign_digest(DIGEST)

    # Empty output leaves the sentinel in the output word.
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(
            storage.store_next(1, "success"),
            call_opcode(
                address=Spec.ECRECOVER,
                args_offset=0,
                args_size=INPUT_SIZE,
                ret_offset=OUTPUT_OFFSET,
                ret_size=32,
            ),
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
    _, r, s = signer.sign_digest(DIGEST)
    # Swapping 27 and 28 would recover another address and read it, so only
    # a `v` outside both values is an invalid signature.
    v = 29

    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(
            storage.store_next(1, "success"),
            Op.STATICCALL(
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
    _, r, s = signer.sign_digest(DIGEST)
    v = 29

    balance = Op.BALANCE(signer)
    cold_balance = Op.BALANCE.with_metadata(address_warm=False)
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.SSTORE(
            storage.store_next(1, "success"),
            Op.STATICCALL(
                address=Spec.ECRECOVER,
                args_offset=0,
                args_size=INPUT_SIZE,
                ret_offset=OUTPUT_OFFSET,
                ret_size=32,
            ),
        )
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
        to=caller,
        data=EcrecoverInput(msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s),
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    "signature",
    [
        pytest.param("valid", id="valid"),
        pytest.param("v-29", id="v-29"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_returndatasize_after_rejection(
    state_test: StateTestFiller,
    pre: Alloc,
    signature: str,
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
    permitted_v, permitted_r, permitted_s = permitted.sign_digest(DIGEST)
    signer = pre.fund_eoa(code=CONTRACT_CODE)
    v, r, s = signer.sign_digest(DIGEST)
    if signature == "valid":
        pass
    elif signature == "v-29":
        v = 29
    else:
        raise ValueError(f"unknown signature: {signature}")

    # The first recovery leaves 32 bytes of return data, so the call under
    # test has to clear them.
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, 2 * INPUT_SIZE)
        + Op.POP(
            Op.STATICCALL(
                address=Spec.ECRECOVER,
                args_offset=0,
                args_size=INPUT_SIZE,
                ret_offset=0,
                ret_size=0,
            )
        )
        + Op.SSTORE(
            storage.store_next(32, "recovered_returndatasize"),
            Op.RETURNDATASIZE,
        )
        + Op.SSTORE(
            storage.store_next(1, "success"),
            Op.STATICCALL(
                address=Spec.ECRECOVER,
                args_offset=INPUT_SIZE,
                args_size=INPUT_SIZE,
                ret_offset=0,
                ret_size=0,
            ),
        )
        + Op.SSTORE(
            storage.store_next(0, "returndatasize"), Op.RETURNDATASIZE
        ),
        storage=storage.canary(),
    )

    tx = Transaction(
        to=caller,
        data=bytes(
            EcrecoverInput(
                msg_hash=int.from_bytes(DIGEST),
                v=permitted_v,
                r=permitted_r,
                s=permitted_s,
            )
        )
        + bytes(
            EcrecoverInput(msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s)
        ),
        sender=pre.fund_eoa(),
    )

    state_test(pre=pre, post={caller: Account(storage=storage)}, tx=tx)


@pytest.mark.parametrize(
    "signature",
    [
        pytest.param("valid", id="valid"),
        pytest.param("v-29", id="v-29"),
    ],
)
def test_transaction_to_ecrecover(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    signature: str,
) -> None:
    """
    Test that a transaction sent to ecrecover reads the recovered signer
    only when the signature is valid.
    """
    signer = pre.fund_eoa()
    v, r, s = signer.sign_digest(DIGEST)
    if signature == "valid":
        signer_in_bal: BalAccountExpectation | None = (
            BalAccountExpectation.empty()
        )
    elif signature == "v-29":
        v = 29
        signer_in_bal = None
    else:
        raise ValueError(f"unknown signature: {signature}")

    # The gas used is not checked: with a 128-byte input, the calldata floor
    # exceeds the execution and the standard intrinsic cost together, so it
    # is the same whether the signer is read cold, warm or not at all.
    data = bytes(
        EcrecoverInput(msg_hash=int.from_bytes(DIGEST), v=v, r=r, s=s)
    )
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
                signer: signer_in_bal,
            }
        ),
    )


@pytest.mark.parametrize(
    "authorization",
    [
        pytest.param("applied", id="applied"),
        pytest.param(
            "skipped", id="skipped", marks=pytest.mark.pre_alloc_mutable
        ),
    ],
)
def test_authorization_warms_signer(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    authorization: str,
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
    if authorization == "applied":
        signer = pre.fund_eoa()
        output_word = int.from_bytes(signer)
        post_code = Spec.DELEGATION_MARKER + bytes(delegate)
        post_nonce = int(signer.nonce) + 1
    elif authorization == "skipped":
        signer = pre.fund_eoa(code=CONTRACT_CODE)
        output_word = SENTINEL
        post_code = bytes(CONTRACT_CODE)
        # A skipped authorization leaves the nonce as it was.
        post_nonce = int(signer.nonce)
    else:
        raise ValueError(f"unknown authorization: {authorization}")
    v, r, s = signer.sign_digest(DIGEST)

    # The authority is warmed before its code is checked, so the warm price
    # is enough in both cases.
    storage = Storage()
    caller = pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, INPUT_SIZE)
        + Op.MSTORE(OUTPUT_OFFSET, SENTINEL)
        + Op.SSTORE(
            storage.store_next(1, "success"),
            Op.STATICCALL(
                gas=fork.ecrecover_gas(recovered=True, address_warm=True),
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
        post={
            caller: Account(storage=storage),
            signer: Account(code=post_code, nonce=post_nonce),
        },
        tx=tx,
    )
