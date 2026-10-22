"""
Helpers for the
[EIP-8151: Account Code Restricted ecRecover](https://eips.ethereum.org/EIPS/eip-8151)
tests.
"""

from execution_testing import EOA, Alloc, Bytecode, Bytes, Op

from ...frontier.precompiles.spec import EcrecoverInput
from .spec import Spec

DIGEST = Bytes(b"account code restricted ecrecover").keccak256()
"""Message hash that every signer signs."""

SENTINEL = 2**256 - 1
"""Word written over the output, so that empty output leaves it in place."""

CONTRACT_CODE = Op.SSTORE(0, 1) + Op.STOP
"""Code other than a delegation designation, so its signer is withheld."""

# Memory layout of the callers: the 128-byte input, then the output word.
INPUT_SIZE = 128
OUTPUT_OFFSET = INPUT_SIZE


def fund_signer(pre: Alloc, *, has_code: bool) -> EOA:
    """
    Fund a signer, giving it code other than a delegation designation when
    `has_code` is set.
    """
    if has_code:
        return pre.fund_eoa(code=CONTRACT_CODE)
    return pre.fund_eoa()


def signed_input(signer: EOA, *, v: int | None = None) -> EcrecoverInput:
    """
    Return the ecrecover input carrying the signer's signature over
    `DIGEST`, with `v` replaced when one is given.
    """
    signed_v, r, s = signer.sign_digest(DIGEST)
    return EcrecoverInput(
        msg_hash=int.from_bytes(DIGEST),
        v=signed_v if v is None else v,
        r=r,
        s=s,
    )


def recover(
    call_opcode: Op = Op.STATICCALL,
    *,
    gas: int | Bytecode = Op.GAS,
    args_offset: int = 0,
    ret_size: int = 32,
) -> Bytecode:
    """
    Call ecrecover on the input at `args_offset`, writing up to `ret_size`
    bytes of output at `OUTPUT_OFFSET`.
    """
    return call_opcode(
        gas=gas,
        address=Spec.ECRECOVER,
        args_offset=args_offset,
        args_size=INPUT_SIZE,
        ret_offset=OUTPUT_OFFSET,
        ret_size=ret_size,
    )
