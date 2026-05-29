"""
State-test regression for the BLOCKHASH (0x40) opcode recency window.

In a *state test*, nethermind returns a non-zero hash for
``BLOCKHASH(0)`` even when block 0 lies far outside the recency window (256
blocks pre-Prague, 8191 via EIP-2935 from Prague). eels (the reference),
go-ethereum, besu, erigon, evmone and reth all correctly return 0.

Root cause (nethermind, state-test only):
``src/Nethermind/Ethereum.Test.Base/TestBlockhashProvider.cs`` implements::

    number != 0 ? Keccak.Zero : Keccak.Compute(number.ToString())

It performs no recency-window check, and the opcode handler
``InstructionBlockHash`` (in ``EvmInstructions.Environment.cs``) delegates
that check to the provider -- it only rejects ``number >= current``. So
``BLOCKHASH(0)`` returns ``keccak256("0")`` regardless of how ancient block
0 is. Nethermind's *production* ``BlockhashProvider`` does enforce the
window, so this is a state-test tooling bug, not a mainnet consensus bug --
but it makes nethermind diverge under differential state-test fuzzing.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Hash,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

# keccak256(b"0") -- the state-test convention hash for block 0 used by both
# go-ethereum (vmTestBlockHash) and nethermind (TestBlockhashProvider). The
# fuzzer sets env.previousHash to exactly this value so the in-window
# block-0 hash agrees across clients.
KECCAK_OF_BLOCK_0 = Hash(
    0x044852B2A670ADE5407E78FB2863C51DE9FCB96542A07186FE3AEDA6BB8A116D
)


@pytest.mark.valid_from("Frontier")
@pytest.mark.state_test_only
@pytest.mark.parametrize(
    "current_number",
    [
        pytest.param(0x101, id="just_past_256_window"),
        pytest.param(0x2001, id="just_past_8191_window"),
        pytest.param(0x100000, id="far_out_of_window"),
        pytest.param(0xA63CCE, id="fuzzer_discovered_number"),
    ],
)
def test_blockhash_zero_out_of_window(
    state_test: StateTestFiller,
    pre: Alloc,
    current_number: int,
) -> None:
    """
    BLOCKHASH(0) must be 0 when block 0 is outside the recency window.

    At ``current_number`` well past the window, block 0 is ancient, so every
    spec-conformant client returns 0. Nethermind's state-test runner instead
    returns ``keccak256("0")`` because ``TestBlockhashProvider`` skips the
    window check, which is the bug this test guards against.

    Marked ``state_test_only``: the bug lives solely in the state-test code
    path (the production blockhash provider enforces the window), and a state
    test with such a high ``env.number`` cannot be converted into a real
    blockchain-test fixture (no genesis chain up to that height).
    """
    storage = Storage()
    contract = pre.deploy_contract(
        code=(
            # slot 0: the raw hash -- must be zero
            Op.SSTORE(
                storage.store_next(0, "blockhash_0_value"),
                Op.BLOCKHASH(0),
            )
            # slot 1: ISZERO of the hash -- must be 1 (written, so the
            # divergence lands in a non-default slot too)
            + Op.SSTORE(
                storage.store_next(1, "blockhash_0_is_zero"),
                Op.ISZERO(Op.BLOCKHASH(0)),
            )
        )
    )
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=200_000,
        protected=False,  # legacy tx so it fills on pre-EIP-155 forks too
    )

    state_test(
        env=Environment(number=current_number),
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.valid_from("Frontier")
@pytest.mark.valid_until("Cancun")
@pytest.mark.state_test_only
def test_blockhash_zero_in_window_control(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    In-window control: BLOCKHASH(0) returns the block-0 hash at block 1.

    This is the positive counterpart to the out-of-window test. With block 0
    inside the recency window (current block == 1) and ``previousHash`` set
    to the state-test convention value ``keccak256("0")``, all clients --
    including nethermind -- agree on the result, pinning the window boundary.

    Restricted to <= Cancun because EIP-2935 (Prague+) serves BLOCKHASH from
    the history storage contract, which is not pre-populated in a bare state
    test.
    Marked ``state_test_only``: the asserted non-zero hash would not match the
    real genesis hash of a derived blockchain-test fixture.
    """
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(
            storage.store_next(KECCAK_OF_BLOCK_0, "blockhash_0_value"),
            Op.BLOCKHASH(0),
        )
    )
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=200_000,
        protected=False,  # legacy tx so it fills on pre-EIP-155 forks too
    )

    state_test(
        env=Environment(
            number=1,
            block_hashes={0: KECCAK_OF_BLOCK_0},
        ),
        pre=pre,
        post={contract: Account(storage=storage)},
        tx=tx,
    )
