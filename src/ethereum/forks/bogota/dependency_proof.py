"""
Claim verification and the block's dependency proof, introduced in
[EIP-8141].

Frame transactions declare [`Claim`]s instead of carrying the
signatures and proofs that satisfy them. Each claim resolves to a
[`Dependency`]; the witnesses that satisfy the dependencies of a block's
frame transactions travel in the block's dependency proof. The proof is
in neither the block header nor the block body: it travels in the
execution payload, and the header commits to it through
`dependency_proof_hash`.

Every dependency of a block is verified against the block's pre-state
before any transaction executes, so custom contract verifiers must
already be deployed.

[EIP-8141]: https://eips.ethereum.org/EIPS/eip-8141
[`Claim`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Claim
[`Dependency`]: ref:ethereum.forks.bogota.transactions.frame_transaction.Dependency
"""  # noqa: E501

from typing import Final, FrozenSet, Iterable, Sequence, Tuple

from ethereum_rlp import rlp
from ethereum_rlp.exceptions import RLPException
from ethereum_types.bytes import Bytes
from ethereum_types.numeric import U256, Uint, ulen

from ethereum.crypto.elliptic_curve import (
    SECP256K1N,
    SECP256R1N,
    SECP256R1P,
    is_on_curve_secp256r1,
    secp256k1_recover,
    secp256r1_verify,
)
from ethereum.crypto.hash import Hash32, keccak256
from ethereum.exceptions import InvalidBlock, InvalidSignatureError
from ethereum.state import Address

from . import vm
from .blocks import Header
from .fork_types import ExecutionGas, StateGas
from .state_tracker import TransactionState, get_account, get_code
from .transactions import Transaction
from .transactions.frame_transaction import (
    LEANSPHINCS_SIGNATURE_SIZE,
    LEANSPHINCS_VERIFIER,
    P256_VERIFIER,
    SECP256K1_VERIFIER,
    Dependency,
    FrameTransaction,
    compute_frame_signature_hash,
    resolve_dependency,
)
from .vm.eoa_delegation import is_valid_delegation
from .vm.exceptions import ExceptionalHalt
from .vm.gas import GasCosts, GasMeter, charge_gas_from_meter
from .vm.interpreter import process_call
from .vm.precompiled_contracts.mapping import PRE_COMPILED_CONTRACTS
from .vm.runtime import get_valid_jump_destinations

MAX_DEPENDENCY_PROOF_BYTES: Final[Uint] = Uint(8388608)
"""
Maximum length of a dependency proof. The proof is not part of the RLP
block, so the block size limit of [EIP-7934] does not cover it.

[EIP-7934]: https://eips.ethereum.org/EIPS/eip-7934
"""

DEPENDENCY_PROOF_VERSION_RAW: Final[Bytes] = Bytes(b"\x00")
"""
Version byte of a dependency proof that carries the raw witnesses.
"""


def secp256k1_verifier(verifier_input: Bytes) -> bool:
    """
    Check a [`SECP256K1_VERIFIER`][k1] claim: `key || msg || witness`,
    where the witness is `v || r || s` with a recovery id `v` of 0 or
    1, canonical `r` and low `s`, and the key is the signer's address,
    left-padded.

    [k1]: ref:ethereum.forks.bogota.transactions.frame_transaction.SECP256K1_VERIFIER
    """  # noqa: E501
    if len(verifier_input) != 129:
        return False
    key = verifier_input[0:32]
    msg = Hash32(verifier_input[32:64])
    v = U256(verifier_input[64])
    r = U256.from_be_bytes(verifier_input[65:97])
    s = U256.from_be_bytes(verifier_input[97:129])
    if v > U256(1):
        return False
    if r == U256(0) or r >= SECP256K1N:
        return False
    if s == U256(0) or s > SECP256K1N // U256(2):
        return False
    try:
        public_key = secp256k1_recover(r, s, v, msg)
    except InvalidSignatureError:
        return False
    return key == keccak256(public_key)[12:].rjust(32, b"\x00")


def p256_verifier(verifier_input: Bytes) -> bool:
    """
    Check a [`P256_VERIFIER`][p] claim: `key || msg || witness`, where
    the witness is `r || s || qx || qy` with canonical `r` and low `s`,
    and the key is the address of the public key `(qx, qy)`,
    `keccak256(qx || qy)[12:]`, left-padded.

    [p]: ref:ethereum.forks.bogota.transactions.frame_transaction.P256_VERIFIER
    """  # noqa: E501
    if len(verifier_input) != 192:
        return False
    key = verifier_input[0:32]
    msg = Hash32(verifier_input[32:64])
    r = U256.from_be_bytes(verifier_input[64:96])
    s = U256.from_be_bytes(verifier_input[96:128])
    qx = U256.from_be_bytes(verifier_input[128:160])
    qy = U256.from_be_bytes(verifier_input[160:192])
    if r == U256(0) or r >= SECP256R1N:
        return False
    if s == U256(0) or s > SECP256R1N // U256(2):
        return False
    if key != keccak256(verifier_input[128:192])[12:].rjust(32, b"\x00"):
        return False
    # The checks of `P256VERIFY` on the public key.
    if qx >= SECP256R1P or qy >= SECP256R1P:
        return False
    if qx == U256(0) and qy == U256(0):
        return False
    if not is_on_curve_secp256r1(qx, qy):
        return False
    try:
        secp256r1_verify(r, s, qx, qy, msg)
    except InvalidSignatureError:
        return False
    return True


def leansphincs_verifier(verifier_input: Bytes) -> bool:
    """
    Check a [`LEANSPHINCS_VERIFIER`][l] claim: `key || msg || witness`,
    where the key is the 32-byte leanSPHINCS public key and the witness
    a leanSPHINCS signature of `msg` under it.

    No leanSPHINCS implementation is available to this specification
    yet, so no witness satisfies such a claim: the claim is refused
    rather than accepted unchecked.

    [l]: ref:ethereum.forks.bogota.transactions.frame_transaction.LEANSPHINCS_VERIFIER
    """  # noqa: E501
    if ulen(verifier_input) != Uint(64) + LEANSPHINCS_SIGNATURE_SIZE:
        return False
    # No leanSPHINCS implementation to check the signature against.
    return False


def execute_pure_verifier(
    block_env: vm.BlockEnvironment,
    verifier: Address,
    verifier_input: Bytes,
    gas_limit: Uint,
) -> bool:
    """
    Run a custom contract verifier in the pure context and report
    whether the call succeeded, whatever it returned.

    The call has its own access sets, with only the active precompiles
    warm, and draws the verifier's access charge from `gas_limit`. An
    active precompile dispatches directly; any other verifier must
    carry code that is not an [EIP-7702] delegation indicator. Nothing
    the call does survives it: its state is discarded, and the full
    `gas_limit` is charged whatever it consumed.

    [EIP-7702]: https://eips.ethereum.org/EIPS/eip-7702
    """
    tx_state = TransactionState(parent=block_env.state)
    gas_meter = GasMeter(gas_left=ExecutionGas(gas_limit), reservoir=None)
    accessed_addresses = set(PRE_COMPILED_CONTRACTS.keys())

    try:
        if verifier in accessed_addresses:
            charge_gas_from_meter(gas_meter, GasCosts.WARM_ACCESS)
        else:
            charge_gas_from_meter(gas_meter, GasCosts.COLD_ACCOUNT_ACCESS)
            accessed_addresses.add(verifier)
    except ExceptionalHalt:
        return False

    if verifier in PRE_COMPILED_CONTRACTS:
        code = Bytes(b"")
    else:
        code = get_code(tx_state, get_account(tx_state, verifier).code_hash)
        if len(code) == 0 or is_valid_delegation(code):
            return False

    tx_env = vm.TransactionEnvironment(
        origin=vm.FRAME_ENTRY_POINT,
        gas_limit=gas_limit,
        effective_gas_price=Uint(0),
        execution_gas_grant=ExecutionGas(gas_limit),
        state_gas_reservoir=StateGas(Uint(0)),
        calldata_floor=Uint(0),
        access_list_addresses=set(),
        access_list_storage_keys=set(),
        accounts_with_paid_writes=set(),
        state=tx_state,
        blob_versioned_hashes=(),
        authorizations=(),
        index_in_block=None,
        tx_hash=None,
        top_level_context=None,
        frame_context=None,
        is_pure=True,
    )
    evm = vm.Evm(
        # Context
        block_env=block_env,
        tx_env=tx_env,
        parent_evm=None,
        depth=Uint(0),
        # Call Parameters
        caller=vm.FRAME_ENTRY_POINT,
        current_target=verifier,
        value=U256(0),
        call_data=verifier_input,
        should_transfer_value=False,
        is_static=True,
        disable_precompiles=False,
        # Code
        code_address=verifier,
        code=code,
        valid_jump_destinations=get_valid_jump_destinations(code),
        # Machine State
        gas_meter=gas_meter,
        pc=Uint(0),
        stack=[],
        memory=bytearray(),
        return_data=b"",
        # Accrued Effects
        logs=(),
        accounts_to_delete=set(),
        accessed_addresses=accessed_addresses,
        accessed_storage_keys=set(),
        # Outcome
        running=True,
        output=b"",
        error=None,
    )
    process_call(evm)
    return evm.error is None


def verify_dependency(
    block_env: vm.BlockEnvironment,
    dependency: Dependency,
    witness: Bytes,
) -> bool:
    """
    Check whether `witness` satisfies `dependency`: its length must be
    the dependency's witness length, and its verifier must accept
    `key || msg || witness`.
    """
    if ulen(witness) != dependency.witness_len:
        return False
    verifier_input = dependency.key + dependency.msg + witness
    if dependency.verifier == SECP256K1_VERIFIER:
        return secp256k1_verifier(verifier_input)
    if dependency.verifier == P256_VERIFIER:
        return p256_verifier(verifier_input)
    if dependency.verifier == LEANSPHINCS_VERIFIER:
        return leansphincs_verifier(verifier_input)
    return execute_pure_verifier(
        block_env, dependency.verifier, verifier_input, dependency.gas_limit
    )


def transaction_dependencies(tx: FrameTransaction) -> Tuple[Dependency, ...]:
    """
    Return the dependencies a frame transaction's claims resolve to.
    """
    sig_hash = compute_frame_signature_hash(tx)
    return tuple(
        resolve_dependency(claim, tx.sender, sig_hash) for claim in tx.claims
    )


def block_dependencies(
    dependencies: Iterable[Dependency],
) -> Tuple[Dependency, ...]:
    """
    Return the dependencies of a block, deduplicated and sorted: the
    order the dependency proof carries their witnesses in.
    """
    return tuple(sorted(set(dependencies)))


def encode_dependency_proof(witnesses: Sequence[Bytes]) -> Bytes:
    """
    Encode a dependency proof carrying the raw `witnesses`, one per
    dependency of the block in order. A block without dependencies has
    the empty proof.
    """
    if len(witnesses) == 0:
        return Bytes(b"")
    return DEPENDENCY_PROOF_VERSION_RAW + rlp.encode(tuple(witnesses))


def validate_dependency_proof(
    block_env: vm.BlockEnvironment,
    header: Header,
    transactions: Sequence[Transaction],
    dependency_proof: Bytes,
) -> FrozenSet[Dependency]:
    """
    Check the dependency proof received with a block against the
    header's commitment and the claims of the block's transactions,
    and return the dependencies it satisfies.

    Every dependency is verified against the state `block_env` holds,
    which must be the block's pre-state.
    """
    if ulen(dependency_proof) > MAX_DEPENDENCY_PROOF_BYTES:
        raise InvalidBlock("dependency proof too long")
    if header.dependency_proof_hash != keccak256(dependency_proof):
        raise InvalidBlock("dependency proof hash mismatch")

    dependencies = block_dependencies(
        dependency
        for tx in transactions
        if isinstance(tx, FrameTransaction)
        for dependency in transaction_dependencies(tx)
    )

    if len(dependencies) == 0:
        if len(dependency_proof) != 0:
            raise InvalidBlock("dependency proof without dependencies")
        return frozenset()

    if dependency_proof[:1] != DEPENDENCY_PROOF_VERSION_RAW:
        raise InvalidBlock("unknown dependency proof version")
    try:
        decoded = rlp.decode(dependency_proof[1:])
    except RLPException as e:
        raise InvalidBlock("malformed dependency proof") from e
    if isinstance(decoded, bytes):
        raise InvalidBlock("malformed dependency proof")
    witnesses = tuple(Bytes(w) for w in decoded if isinstance(w, bytes))
    if len(witnesses) != len(decoded):
        raise InvalidBlock("malformed dependency proof")
    if len(witnesses) != len(dependencies):
        raise InvalidBlock("dependency proof witness count mismatch")

    for dependency, witness in zip(dependencies, witnesses, strict=True):
        if not verify_dependency(block_env, dependency, witness):
            raise InvalidBlock("dependency proof witness unsatisfied")

    return frozenset(dependencies)
