"""
Shared helpers for the EIP-8297 partitioned binary tree EEST suite.
"""

from execution_testing import (
    Address,
    Alloc,
    Bytecode,
    Op,
    compute_create_address,
)

# Canary slot the factory writes to unconditionally after its (POP'd)
# create call, so callers can detect the create failing/OOG-ing before
# reaching that write (otherwise indistinguishable from success, since
# the create's own result is discarded). Chosen far outside any slot the
# caller's own initcode would plausibly write.
FACTORY_CANARY_SLOT = 2**256 - 1


def create_contract_via_factory(
    pre: Alloc,
    initcode: Bytecode,
    *,
    opcode: Op = Op.CREATE,
    salt: int = 0,
    value: int = 0,
) -> tuple[Address, Address]:
    """
    Deploy a factory contract that creates `initcode` via CREATE/CREATE2.

    Stages `initcode` via a template contract plus EXTCODECOPY rather
    than inline `PUSH32`/`MSTORE`, since that scales to arbitrary-length
    initcode. Deployed fresh at nonce 1, so `created` is derived with
    `compute_create_address` on that basis.

    Writes `FACTORY_CANARY_SLOT` (see there) after the (POP'd) create
    call, so callers can detect the create failing before that point.

    Returns `(factory_address, created_address)`.
    """
    template = pre.deploy_contract(code=initcode)

    create_call: Bytecode
    if opcode == Op.CREATE2:
        create_call = Op.CREATE2(
            value=value, offset=0, size=len(initcode), salt=salt
        )
    else:
        create_call = Op.CREATE(value=value, offset=0, size=len(initcode))

    factory = pre.deploy_contract(
        code=Op.EXTCODECOPY(template, 0, 0, len(initcode))
        + Op.POP(create_call)
        + Op.SSTORE(FACTORY_CANARY_SLOT, 1)
        + Op.STOP
    )

    created = compute_create_address(
        address=factory,
        nonce=1,
        salt=salt,
        initcode=initcode,
        opcode=opcode,
    )
    return factory, created


def sstore_from_calldata_contract(pre: Alloc, *, slot: int) -> Address:
    """
    Deploy a contract that SSTOREs its first calldata word into `slot`.

    Calling it again with different calldata drives `slot` to a new
    value without redeploying -- used by the cross-tx/cross-block
    zero-write tests.
    """
    return pre.deploy_contract(
        code=Op.SSTORE(slot, Op.CALLDATALOAD(0)) + Op.STOP
    )


def sstore_then_pad(*, slot: int, value: int, total_size: int) -> Bytecode:
    """
    Build code that SSTOREs `value` into `slot`, STOPs, then pads with
    `INVALID` filler out to exactly `total_size` bytes.

    Filler is `INVALID`, not zeros, so a client that mis-executes past
    `STOP` (e.g. a chunk-metadata bug) fails loudly instead of silently
    falling through. Used to pin code-chunking size boundaries.
    """
    prefix = Op.SSTORE(slot, value) + Op.STOP
    assert total_size >= len(prefix), (
        f"total_size {total_size} too small to fit the "
        f"{len(prefix)}-byte SSTORE+STOP prefix"
    )
    return prefix + Op.INVALID * (total_size - len(prefix))
