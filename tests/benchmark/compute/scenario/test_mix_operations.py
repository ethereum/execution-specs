"""Benchmark mixed operations."""

import random
from dataclasses import dataclass

import pytest
from execution_testing import (
    Alloc,
    BenchmarkTestFiller,
    Bytecode,
    Fork,
    Op,
    Transaction,
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
    ids=lambda x: x.hex(),
)
def test_jumpdest_analysis(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    pattern: Bytecode | RandomInitcode,
    gas_benchmark_value: int,
    tx_gas_limit: int,
) -> None:
    """
    Benchmark jumpdest analysis of CREATE initcode.

    Each CREATE runs a max-size initcode that jumps straight to its last byte,
    so its cost is almost all analysis. Tiled patterns repeat with a period the
    branch predictor learns; ``RandomInitcode`` does not repeat.
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
        tx_data = b""
    else:
        # Tile a small calldata window to fill the initcode: cheap, but the
        # period is learnable.
        tx_data_len = 1024
        tx_data = bytes(pattern) * (tx_data_len // len(pattern))
        tx_data += (tx_data_len - len(tx_data)) * bytes(Op.JUMPDEST)
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
    overhead = len(setup) + len(Op.JUMPDEST) + len(Op.JUMP(len(setup)))
    iterations = (fork.max_code_size() - overhead) // len(attack_block)
    loop_contract = pre.deploy_contract(
        code=setup
        + Op.JUMPDEST
        + attack_block * iterations
        + Op.JUMP(len(setup))
    )

    create = Op.CREATE.with_metadata(init_code_size=initcode_size)
    if create.state_cost(fork) > 0:
        # Pre-fund the CREATE targets so creation skips NEW_ACCOUNT. Each
        # transaction runs out of gas and reverts, so every transaction reuses
        # the same targets and one transaction's gas bounds how many there are.
        create_cost = create.execution_cost(fork)
        tx_budget = min(gas_benchmark_value, tx_gas_limit)
        for nonce in range(1, tx_budget // create_cost + 2):
            pre.fund_address(
                compute_create_address(address=loop_contract, nonce=nonce), 1
            )

    benchmark_test(
        tx=Transaction(
            to=loop_contract,
            data=tx_data,
            gas_limit=gas_benchmark_value,
            sender=pre.fund_eoa(),
        )
    )
