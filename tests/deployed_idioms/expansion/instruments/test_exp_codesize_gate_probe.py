"""
Measurement instrument: an on-chain code-size gate holding the EIP-170 literal,
and whether the EIP-7954 maximum is reachable at all under EIP-8037.

EIP-7954 moves MAX_CODE_SIZE from 0x6000 (24,576) to 0x10000 (65,536).
Deployed code hardcodes 24,576 (L1-source P26: 338 addresses / 120 runtimes,
hand-measured precision 1.0).

EIP-8037 reprices the code deposit from 200 execution gas per byte to
`COST_PER_STATE_BYTE` = 1,530 STATE gas per byte
(amsterdam/vm/interpreter.py:375-378), and state gas above the 2**24
execution cap comes only from the reservoir. So the two EIPs interact.

`gas_limit` is OMITTED so each fork gets its own implicit limit and a real
reservoir (setting it explicitly yields a zero reservoir).

FAILURES ARE THE MEASUREMENT.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Environment,
    Op,
    StateTestFiller,
    Transaction,
)

EIP170 = 24_576
EIP7954 = 65_536

OUTCOMES = [
    pytest.param(0, 1, id="not_deployed_gate_accepts"),
    pytest.param(EIP170, 1, id="eip170_gate_accepts"),
    pytest.param(EIP170 + 1, 0, id="over_eip170_gate_rejects"),
    pytest.param(EIP7954, 0, id="eip7954_max_gate_rejects"),
    pytest.param(0xFF, 0xFF, id="frame_died"),
]


def _factory(pre: Alloc) -> object:
    return pre.deploy_contract(
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.MSTORE(0x8000, Op.CREATE(0, 0, Op.CALLDATASIZE))
        + Op.SSTORE(1, Op.EXTCODESIZE(Op.MLOAD(0x8000)))
        + Op.SSTORE(
            2, Op.ISZERO(Op.GT(Op.EXTCODESIZE(Op.MLOAD(0x8000)), EIP170))
        )
        + Op.STOP,
        storage={1: 0xFF, 2: 0xFF},
    )


@pytest.mark.parametrize("size,gate", OUTCOMES)
@pytest.mark.parametrize(
    "n", [EIP170, EIP170 + 1], ids=lambda v: f"n{v}"
)
@pytest.mark.valid_from("Osaka")
def test_gate(
    state_test: StateTestFiller, pre: Alloc, n: int, size: int, gate: int
) -> None:
    """Probe: a 60M-gas block, the current mainnet size."""
    factory = _factory(pre)
    tx = Transaction(
        to=factory,
        data=bytes(Op.RETURN(0, n)),
        sender=pre.fund_eoa(amount=10**20),
    )
    state_test(
        env=Environment(gas_limit=60_000_000),
        pre=pre,
        post={factory: Account(storage={1: size, 2: gate})},
        tx=tx,
    )


@pytest.mark.parametrize("size,gate", OUTCOMES)
@pytest.mark.parametrize(
    "block", [60_000_000, 120_000_000], ids=["block_60M", "block_120M"]
)
@pytest.mark.valid_from("Osaka")
def test_reachability(
    state_test: StateTestFiller,
    pre: Alloc,
    block: int,
    size: int,
    gate: int,
) -> None:
    """Probe: is the EIP-7954 maximum deployable at each block gas limit?"""
    factory = _factory(pre)
    tx = Transaction(
        to=factory,
        data=bytes(Op.RETURN(0, EIP7954)),
        sender=pre.fund_eoa(amount=10**20),
    )
    state_test(
        env=Environment(gas_limit=block),
        pre=pre,
        post={factory: Account(storage={1: size, 2: gate})},
        tx=tx,
    )
