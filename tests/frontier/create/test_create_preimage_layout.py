"""State test for `CreatePreimageLayout` address computation."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Conditional,
    CreatePreimageLayout,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    While,
    compute_create_address,
)


@pytest.mark.parametrize(
    "nonce",
    [
        pytest.param(0, id="nonce-0"),
        pytest.param(1, id="nonce-1"),
        pytest.param(2, id="nonce-2"),
        pytest.param(127, id="nonce-127"),
        pytest.param(128, id="nonce-128"),
        pytest.param(255, id="nonce-255"),
        pytest.param(256, id="nonce-256"),
        pytest.param(3515, id="nonce-3515"),
        pytest.param(65535, id="nonce-65535"),
        pytest.param(16777215, id="nonce-16777215"),
    ],
)
def test_create_preimage_layout_address(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    nonce: int,
) -> None:
    """
    Test `CreatePreimageLayout` by executing the bytecode in the EVM and
    verifying the computed address matches `compute_create_address`.
    """
    sender = pre.fund_eoa()
    sender_int = int.from_bytes(sender, "big")

    layout = CreatePreimageLayout(
        sender_address=sender_int,
        nonce=nonce,
    )
    # Write preimage to memory, hash it, mask to 20-byte address, store
    code = layout + Op.SSTORE(0, layout.address_op())
    contract = pre.deploy_contract(code)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=500_000,
        protected=fork.supports_protected_txs(),
    )

    expected_address = compute_create_address(address=sender, nonce=nonce)
    post = {
        contract: Account(storage={0: int.from_bytes(expected_address, "big")})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


NONCE_COUNT = 16


@pytest.mark.parametrize(
    "sender_index",
    [
        pytest.param(0, id="sender-0"),
        pytest.param(1337, id="sender-1"),
        pytest.param(7702, id="sender-2"),
    ],
)
def test_create_preimage_layout_multiple_nonces(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    sender_index: int,
) -> None:
    """
    Test `CreatePreimageLayout` with a fixed sender and linearly
    increasing nonces from 0 to NONCE_COUNT-1.
    """
    sender = pre.fund_eoa()
    sender_int = int.from_bytes(sender, "big") + sender_index
    sender_address = sender_int.to_bytes(20, "big")

    code = Bytecode()
    for nonce in range(NONCE_COUNT):
        layout = CreatePreimageLayout(
            sender_address=sender_int,
            nonce=nonce,
        )
        code += layout + Op.SSTORE(nonce, layout.address_op())
    contract = pre.deploy_contract(code)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1_000_000,
        protected=fork.supports_protected_txs(),
    )

    expected_storage = {
        nonce: int.from_bytes(
            compute_create_address(address=sender_address, nonce=nonce),
            "big",
        )
        for nonce in range(NONCE_COUNT)
    }
    post = {contract: Account(storage=expected_storage)}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.parametrize(
    "nonce",
    [
        pytest.param(0, id="nonce-0"),
        pytest.param(1, id="nonce-1"),
        pytest.param(2, id="nonce-2"),
        pytest.param(127, id="nonce-127"),
        pytest.param(128, id="nonce-128"),
        pytest.param(255, id="nonce-255"),
        pytest.param(256, id="nonce-256"),
        pytest.param(3515, id="nonce-3515"),
        pytest.param(65535, id="nonce-65535"),
    ],
)
def test_create_preimage_layout_dynamic_nonce(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
    nonce: int,
) -> None:
    """
    Test `CreatePreimageLayout` with a dynamic nonce passed via
    calldata, verifying the computed address matches
    `compute_create_address`.
    """
    sender = pre.fund_eoa()
    sender_int = int.from_bytes(sender, "big")

    layout = CreatePreimageLayout(
        sender_address=sender_int,
        nonce=Op.CALLDATALOAD(0),
    )
    code = layout + Op.SSTORE(0, layout.address_op())
    contract = pre.deploy_contract(code)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=nonce.to_bytes(32, "big"),
        gas_limit=1_000_000,
        protected=fork.supports_protected_txs(),
    )

    expected_address = compute_create_address(address=sender, nonce=nonce)
    post = {
        contract: Account(storage={0: int.from_bytes(expected_address, "big")})
    }

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


DYNAMIC_NONCE_COUNT = 16


def test_create_preimage_layout_increment_nonce(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """
    Test `CreatePreimageLayout.increment_nonce_op` by computing
    addresses for nonces 0..DYNAMIC_NONCE_COUNT-1 using a single
    layout with nonce incrementing in the EVM.
    """
    sender = pre.fund_eoa()
    sender_int = int.from_bytes(sender, "big")
    sender_address = sender_int.to_bytes(20, "big")

    layout = CreatePreimageLayout(
        sender_address=sender_int,
        nonce=Op.CALLDATALOAD(0),
    )
    # Initial setup + first address
    code = layout + Op.SSTORE(0, layout.address_op())
    # Increment and compute for nonces 1..N-1
    for i in range(1, DYNAMIC_NONCE_COUNT):
        code += layout.increment_nonce_op()
        code += Op.SSTORE(i, layout.address_op())
    contract = pre.deploy_contract(code)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=(0).to_bytes(32, "big"),
        gas_limit=5_000_000,
        protected=fork.supports_protected_txs(),
    )

    expected_storage = {
        n: int.from_bytes(
            compute_create_address(address=sender_address, nonce=n),
            "big",
        )
        for n in range(DYNAMIC_NONCE_COUNT)
    }
    post = {contract: Account(storage=expected_storage)}

    state_test(env=Environment(), pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Osaka")
def test_create_address_dynamic_nonce(
    pre: Alloc,
    state_test: StateTestFiller,
) -> None:
    """
    Verify CreatePreimageLayout dynamic nonce encoding matches CREATE.

    A contract calls CREATE(value=0, offset=0, size=0) in a loop,
    computes the expected address using the dynamic nonce RLP encoder,
    and reverts if any computed address differs from the actual one.

    The loop runs from nonce 1 to 260, crossing the RLP encoding
    boundary at nonce 128 (1-byte to 2-byte encoding) and at
    256 where it has to change the 0x80 prefix to 0x81.
    """
    iterations = 260

    # Memory[0:32] is used as the loop counter.
    # Layout starts at offset 32 to avoid conflict.
    layout = CreatePreimageLayout(
        sender_address=Op.ADDRESS,
        nonce=Op.PUSH1(1),
        offset=32,
    )

    # Build the loop body: check address, revert on mismatch,
    # increment nonce, decrement counter.
    body = (
        Conditional(
            condition=Op.EQ(
                layout.address_op(),
                Op.CREATE(value=0, offset=0, size=0),
            ),
            if_false=Op.REVERT(0, 0),
        )
        + layout.increment_nonce_op()
        + Op.MSTORE(0, Op.SUB(Op.MLOAD(0), 1))
    )

    code: Bytecode = layout
    code += Op.MSTORE(0, iterations)
    code += While(body=body, condition=Op.MLOAD(0))
    code += Op.SSTORE(0, 1)
    code += Op.STOP

    contract = pre.deploy_contract(code=code)
    sender = pre.fund_eoa()

    tx = Transaction(
        to=contract,
        gas_limit=15_000_000,
        sender=sender,
    )

    post = {contract: Account(storage={0: 1})}

    state_test(pre=pre, tx=tx, post=post)


# Address with first and last byte zero to exercise edge cases
# in the 20-byte address portion of the CREATE preimage.
DEPLOYER_ADDRESS = Address(0x00112233445566778899AABBCCDDEEFF11223300)

BOUNDARY_ITERATIONS = 10


@pytest.mark.parametrize(
    "starting_nonce",
    [
        pytest.param(1, id="nonce_1_initial_value"),
        pytest.param(127, id="nonce_127_max_single_byte"),
        pytest.param(255, id="nonce_max_1_byte_value"),
        pytest.param(256**2 - 1, id="nonce_max_2_byte_value"),
        pytest.param(256**3 - 1, id="nonce_max_3_byte_value"),
        pytest.param(256**4 - 1, id="nonce_max_4_byte_value"),
        pytest.param(256**5 - 1, id="nonce_max_5_byte_value"),
        pytest.param(256**6 - 1, id="nonce_max_6_byte_value"),
        pytest.param(256**7 - 1, id="nonce_max_7_byte_value"),
    ],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.valid_from("Osaka")
def test_create_address_nonce_boundary(
    pre: Alloc,
    state_test: StateTestFiller,
    starting_nonce: int,
) -> None:
    """
    Verify CreatePreimageLayout at RLP encoding size boundaries.

    Deploy a contract at an address whose first and last bytes are
    zero, with a prestate nonce set to ``starting_nonce``.  Run
    CREATE in a loop for a small number of iterations, verifying
    each computed address matches the actual one.

    Each boundary value is the last nonce before the RLP encoding
    grows by one byte.
    """
    # EVM does not allow nonces higher than 8 bytes, so a PUSH8 will always fit
    nonce_push = Op.PUSH8(starting_nonce)

    layout = CreatePreimageLayout(
        sender_address=Op.ADDRESS,
        nonce=nonce_push,
        offset=32,
    )

    body = (
        Conditional(
            condition=Op.EQ(
                layout.address_op(),
                Op.CREATE(value=0, offset=0, size=0),
            ),
            if_false=Op.REVERT(0, 0),
        )
        + layout.increment_nonce_op()
        + Op.MSTORE(0, Op.SUB(Op.MLOAD(0), 1))
    )

    code: Bytecode = layout
    code += Op.MSTORE(0, BOUNDARY_ITERATIONS)
    code += While(body=body, condition=Op.MLOAD(0))
    code += Op.SSTORE(0, 1)
    code += Op.STOP

    pre.deploy_contract(
        code=code,
        address=DEPLOYER_ADDRESS,
        nonce=starting_nonce,
    )
    sender = pre.fund_eoa()

    tx = Transaction(
        to=DEPLOYER_ADDRESS,
        gas_limit=15_000_000,
        sender=sender,
    )

    post = {DEPLOYER_ADDRESS: Account(storage={0: 1})}

    state_test(pre=pre, tx=tx, post=post)
