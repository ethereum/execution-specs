"""
Test CreatePreimageLayout dynamic nonce encoding against actual CREATE.

Deploy a contract that loops calling CREATE (empty initcode), computes
the expected address on-chain via CreatePreimageLayout, and reverts on
any mismatch. The post-state check confirms all iterations succeeded.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Conditional,
    CreatePreimageLayout,
    StateTestFiller,
    Transaction,
    While,
)
from execution_testing.vm import Bytecode, Op


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
