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

    The factory serves the initcode bytes to itself with EXTCODECOPY
    from a separate template contract holding them as its code:
    without a copy opcode, getting more than 32 bytes into memory
    needs one `PUSH32`+`MSTORE` pair per word, so staging
    arbitrary-length initcode this way is simpler than building it
    inline. The factory is freshly deployed with the default
    pre-alloc nonce of 1, so this call is always its first creation;
    the returned `created` address is derived accordingly with
    `compute_create_address`.

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

    Calling the same deployed contract again with different calldata
    drives `slot` to a new value from a separate transaction or block,
    which is how the cross-transaction and cross-block zero-write tests
    exercise one account without redeploying it.
    """
    return pre.deploy_contract(
        code=Op.SSTORE(slot, Op.CALLDATALOAD(0)) + Op.STOP
    )


def sstore_then_pad(*, slot: int, value: int, total_size: int) -> Bytecode:
    """
    Build code that SSTOREs `value` into `slot`, STOPs, then pads with
    `INVALID` filler bytes out to exactly `total_size` bytes.

    Used to pin code-chunking size boundaries: the write executes and
    reports correctly regardless of how many 31-byte chunks (including
    the account-header/overflow split) the trailing padding spans. The
    filler is `INVALID` rather than zeros so that a client which mis-
    executes past `STOP` (e.g. due to a chunk-metadata bug) fails loudly
    instead of silently falling through.
    """
    prefix = Op.SSTORE(slot, value) + Op.STOP
    assert total_size >= len(prefix), (
        f"total_size {total_size} too small to fit the "
        f"{len(prefix)}-byte SSTORE+STOP prefix"
    )
    return prefix + Op.INVALID * (total_size - len(prefix))
