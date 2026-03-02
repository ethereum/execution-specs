"""State test for `CreatePreimageLayout` address computation."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    CreatePreimageLayout,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
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
