"""Benchmark mixed operations."""

import random
from dataclasses import dataclass

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Bytecode,
    Fork,
    JumpLoopGenerator,
    Op,
    compute_create_address,
)


@dataclass(frozen=True)
class RandomInitcode:
    """Non-repeating random initcode over an opcode alphabet (fixed seed)."""

    alphabet: tuple[Op, ...]
    weights: tuple[int, ...] | None = None

    def code(self, size: int) -> bytes:
        """Return ``size`` pseudo-random bytes over the alphabet."""
        rng = random.Random(0)
        values = [bytes(op)[0] for op in self.alphabet]
        return bytes(rng.choices(values, weights=self.weights, k=size))


@pytest.mark.parametrize(
    "pattern",
    [
        # Periodic tiles: the branch predictor learns the period, so these
        # measure analysis with the predictor warm.
        Op.STOP,
        Op.JUMPDEST,
        Op.PUSH1[bytes(Op.JUMPDEST)],
        Op.PUSH2[bytes(Op.JUMPDEST + Op.JUMPDEST)],
        Op.PUSH1[bytes(Op.JUMPDEST)] + Op.JUMPDEST,
        Op.PUSH2[bytes(Op.JUMPDEST + Op.JUMPDEST)] + Op.JUMPDEST,
        Op.SWAPN[bytes(Op.JUMPDEST)],
        Op.DUPN[bytes(Op.JUMPDEST)],
        Op.EXCHANGE[bytes(Op.JUMPDEST)],
        # Non-repeating random initcode defeats the predictor. The alphabets
        # straddle the thresholds analysis loops branch on (0x5b JUMPDEST,
        # 0x60 PUSH1); the weighted variant makes PUSH1 half of all bytes, so
        # the PUSH1 threshold is a 50/50 branch.
        pytest.param(
            RandomInitcode((Op.STOP, Op.JUMPDEST, Op.PUSH1)),
            id="random_stop_jumpdest_push1",
        ),
        pytest.param(
            RandomInitcode((Op.STOP, Op.JUMPDEST)),
            id="random_stop_jumpdest",
        ),
        pytest.param(
            RandomInitcode((Op.JUMPDEST, Op.PUSH1)),
            id="random_jumpdest_push1",
        ),
        pytest.param(
            RandomInitcode(
                (Op.STOP, Op.JUMPDEST, Op.PUSH1), weights=(1, 1, 2)
            ),
            id="random_stop_jumpdest_2push1",
        ),
    ],
    ids=lambda x: x.hex() if isinstance(x, Bytecode) else None,
)
def test_jumpdest_analysis(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    pattern: Bytecode | RandomInitcode,
    gas_benchmark_value: int,
    fixed_opcode_count: float | None,
) -> None:
    """
    Benchmark jumpdest analysis of CREATE initcode.

    Each transaction fills a max-size initcode and CREATEs it in a loop up to
    the gas limit; the initcode jumps to its last byte, forcing a full analysis
    with almost no execution, and the returned address is mixed in so every
    analysis is of new code. Periodic ``pattern`` tiles run with the branch
    predictor warm; a ``RandomInitcode`` fills the initcode with non-repeating
    bytes the predictor cannot learn, raising mispredictions.

    In gas-driven mode every CREATE target is pre-funded with 1 wei so it is
    already alive and the creation skips ``NEW_ACCOUNT``, isolating the
    analysis cost. In fill these are genesis pre-allocation; on-chain the
    analysis is gated behind that per-account charge.
    """
    initcode_size = fork.max_initcode_size()

    if isinstance(pattern, RandomInitcode):
        # Deploy the random bytes as two max-size contracts and EXTCODECOPY
        # them in; no calldata, whose floor would exceed small gas budgets.
        chunk = fork.max_code_size()
        assert initcode_size % chunk == 0
        full = pattern.code(initcode_size)
        code_prepare_initcode = Bytecode()
        for offset in range(0, initcode_size, chunk):
            source = pre.deploy_contract(code=full[offset : offset + chunk])
            code_prepare_initcode += Op.EXTCODECOPY(
                address=source, dest_offset=offset, size=chunk
            )
        tx_kwargs: dict = {}
    else:
        # Tile a small calldata window to fill the initcode: cheap, but the
        # period is learnable.
        tx_data = bytes(pattern) * (1024 // len(pattern))
        tx_data += (1024 - len(tx_data)) * bytes(Op.JUMPDEST)
        assert initcode_size % len(tx_data) == 0
        code_prepare_initcode = sum(
            (
                Op.CALLDATACOPY(
                    dest_offset=i * len(tx_data),
                    offset=0,
                    size=Op.CALLDATASIZE,
                )
                for i in range(initcode_size // len(tx_data))
            ),
            Bytecode(),
        )
        tx_kwargs = {"data": tx_data}

    # Jump to the last byte, forcing a full analysis, and make it a JUMPDEST.
    initcode_prefix = Op.JUMP(initcode_size - 1)
    code_prepare_initcode += Op.MSTORE(
        0, Op.PUSH32[bytes(initcode_prefix).ljust(32, bytes(Op.JUMPDEST))]
    )
    code_prepare_initcode += Op.MSTORE(
        initcode_size - 32, Op.PUSH32[bytes(Op.JUMPDEST) * 32]
    )

    # Mix the returned address into the initcode so each analysis is unique.
    attack_block = (
        Op.PUSH1[len(initcode_prefix)]
        + Op.MSTORE
        + Op.CREATE(value=Op.PUSH0, offset=Op.PUSH0, size=Op.MSIZE)
    )
    setup = code_prepare_initcode + Op.CREATE(
        value=Op.PUSH0, offset=Op.PUSH0, size=Op.MSIZE
    )
    code_generator = JumpLoopGenerator(
        setup=setup, attack_block=attack_block, tx_kwargs=tx_kwargs
    )

    if fixed_opcode_count is None:
        # Pre-fund every address the loop will CREATE so it is already alive
        # and the creation skips NEW_ACCOUNT. Each transaction OOGs and
        # reverts, rolling back the CREATEs, so the targets stay deployable and
        # are reused by every transaction and block (a one-time cost) and the
        # loop nonce restarts at 1. Distinct targets are therefore bounded by
        # one transaction's gas (each CREATE costs at least create_cost), not
        # the whole budget; the range carries one spare. The fixed-opcode-count
        # mode creates from a different account, so skip it.
        create_cost = Op.CREATE.with_metadata(
            init_code_size=initcode_size
        ).execution_cost(fork)
        tx_budget = min(
            gas_benchmark_value,
            fork.transaction_gas_limit_cap() or gas_benchmark_value,
        )
        loop_contract = code_generator.deploy_contracts_once(
            pre=pre, fork=fork
        )
        for nonce in range(1, tx_budget // create_cost + 2):
            pre.fund_address(
                compute_create_address(address=loop_contract, nonce=nonce), 1
            )

    benchmark_test(code_generator=code_generator)
