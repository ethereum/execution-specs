"""
An on-chain validator holding the EIP-170 literal 24,576, against EIP-7954.

Deployed code hardcodes the EIP-170 contract-size limit. L1-source pattern
P26 ("EIP-170/3860 code-size limit encoded as a constant") measures the
literal at **338 mainnet addresses / 120 distinct runtime code hashes**,
exact count mode, hand-measured precision 1.0 on a seeded random sample
(registry/L1-source.jsonl). Named exemplars, read as source:

    <address withheld>  a deployed Vyper contract:38
    <address withheld>  a deployed Vyper contract:38
        `def deployFromBytecode(_bytecode: Bytes[24576]) -> address`
        -- a factory whose input buffer IS the EIP-170 limit
    <address withheld>  DexConstraintPoly.sol:201
    <address withheld>  FastExitHandler.sol:1088
        -- the 49,152 EIP-3860 initcode form

EIP-7954 moves `MAX_CODE_SIZE` from 0x6000 (24,576) to 0x10000 (65,536)
(amsterdam/vm/interpreter.py:80). From that fork a 24,577-byte contract is a
perfectly valid deployment that every one of those validators refuses.

**The angle the official suite does not take.** `tests/amsterdam/
eip7954_increase_max_contract_size/` is 1,666 lines and thorough, but every
size in it comes from `fork.max_code_size()` or `Osaka.max_code_size()`
(test_max_code_size.py:38-42). The limit is never a literal *inside EVM
bytecode*, so nothing in it can observe a contract making the wrong decision
about a valid deployment -- which is the actual deployed harm. The gate here
is three opcodes with 24,576 pushed as an immediate, and its verdict is a
committed storage effect.

**A second, cross-EIP result this archetype is the only place to see.**
EIP-8037 reprices the code deposit from 200 execution gas per byte to
`COST_PER_STATE_BYTE` = 1,530 **state** gas per byte
(amsterdam/vm/interpreter.py:375-378), and state gas above the EIP-7825 cap
comes only from the reservoir, which is `tx.gas - 2**24` and so bounded by
the block gas limit. A maximum-size EIP-7954 contract therefore needs

    65,536 x 1,530 = 100,270,080  state gas for the code
       120 x 1,530 =     183,600  state gas for the account
                     -----------
                     100,453,680

and is **measured deployable in a 120,000,000-gas block and not in a
60,000,000-gas one** -- today's mainnet block gas limit. The headline new
capability of EIP-7954 is unreachable on mainnet as configured today, and no
single-EIP test suite can see that, because neither EIP is wrong on its own.

Asserting the raw constants is correct here: 24,576 and 65,536 ARE the
invariant (SCHEMA.md 4.1).
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Environment,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7954.md"
REFERENCE_SPEC_VERSION = "2e62d6a88aa596e4efbf3592cda7706f8a51dac3"

EIP170_LIMIT = 24_576  # 0x6000, the literal deployed code holds
EIP7954_LIMIT = 65_536  # 0x10000

MAINNET_BLOCK_GAS_LIMIT = 60_000_000

SENTINEL = 0xFF
"""Pre-set storage, so a frame that never ran is distinguishable from a 0."""


def _factory_with_an_eip170_gate() -> Bytecode:
    """
    Deploy whatever initcode arrives as calldata, then validate the result.

    Slot 0 records the deployed code size; slot 1 records the gate's verdict,
    1 meaning "this contract is acceptable". The literal 24,576 is a PUSH
    immediate in the bytecode -- the deployed shape, not a fork lookup.
    """
    return (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.MSTORE(0x8000, Op.CREATE(0, 0, Op.CALLDATASIZE))
        + Op.SSTORE(0, Op.EXTCODESIZE(Op.MLOAD(0x8000)))
        + Op.SSTORE(
            1,
            Op.ISZERO(
                Op.GT(Op.EXTCODESIZE(Op.MLOAD(0x8000)), EIP170_LIMIT)
            ),
        )
        + Op.STOP
    )


def _initcode_returning(n: int) -> bytes:
    """Initcode depositing `n` zero bytes, i.e. `n` STOPs."""
    return bytes(Op.RETURN(0, n))


def _run(
    state_test: StateTestFiller,
    pre: Alloc,
    *,
    n: int,
    size: int,
    gate: int,
    block_gas_limit: int = MAINNET_BLOCK_GAS_LIMIT,
) -> None:
    """
    Deploy `n` bytes through the gated factory and assert both committed
    effects.

    `gas_limit` is deliberately OMITTED: EIP-8037 defines the reservoir as
    `tx.gas` above `TX_MAX_GAS_LIMIT`, and an explicit `gas_limit` yields a
    ZERO reservoir, which would make every Amsterdam deposit here fail for
    the wrong reason.
    """
    factory = pre.deploy_contract(
        _factory_with_an_eip170_gate(), storage={0: SENTINEL, 1: SENTINEL}
    )
    storage = Storage()
    storage.store_next(size, f"EXTCODESIZE of the CREATE result for n={n}")
    storage.store_next(gate, "the EIP-170 gate's verdict")
    tx = Transaction(
        to=factory,
        data=_initcode_returning(n),
        sender=pre.fund_eoa(amount=10**20),
    )
    state_test(
        env=Environment(gas_limit=block_gas_limit),
        pre=pre,
        post={factory: Account(storage=storage)},
        tx=tx,
    )


# ---------------------------------------------------------------------------
# Arm 1: the invariant. Every deployable contract passes the gate.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "n,size,gate",
    [
        pytest.param(EIP170_LIMIT, EIP170_LIMIT, 1, id="at_eip170"),
        pytest.param(EIP170_LIMIT + 1, 0, 1, id="one_byte_over_eip170"),
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_the_eip170_gate_never_rejects_a_live_contract(
    state_test: StateTestFiller, pre: Alloc, n: int, size: int, gate: int
) -> None:
    """
    Test the gate is sound while 24,576 is the protocol limit.

    Pinned from both sides: 24,576 bytes deploy and the gate accepts them;
    24,577 bytes do not deploy at all, so the gate's verdict of 1 on an empty
    address is vacuous rather than wrong. On these forks the validator can
    never refuse a contract that exists -- which is precisely why 338
    addresses were willing to encode the constant.
    """
    _run(state_test, pre, n=n, size=size, gate=gate)


# ---------------------------------------------------------------------------
# Arm 2: the violation. A valid contract is rejected by deployed code.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "n,size,gate",
    [
        pytest.param(EIP170_LIMIT, EIP170_LIMIT, 1, id="at_eip170_still_ok"),
        pytest.param(
            EIP170_LIMIT + 1, EIP170_LIMIT + 1, 0, id="one_byte_over_eip170"
        ),
    ],
)
@pytest.mark.valid_from("EIP7954")
def test_the_eip170_gate_rejects_a_live_contract_from_eip7954(
    state_test: StateTestFiller, pre: Alloc, n: int, size: int, gate: int
) -> None:
    """
    Test one byte over EIP-170 now deploys AND is refused by the validator.

    Both effects are asserted in the same transaction: `EXTCODESIZE` reports
    24,577, so the contract is live and callable, and the gate commits 0, so
    the factory refuses to register it. Nothing reverts. The 24,576 param is
    the control -- the gate's behaviour there is unchanged, so the failure is
    localised to the single byte that crossed the old limit.
    """
    _run(state_test, pre, n=n, size=size, gate=gate)


# ---------------------------------------------------------------------------
# Arm 3: the new limit, and whether a mainnet-sized block can reach it.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "n,size,gate",
    [
        pytest.param(EIP7954_LIMIT, EIP7954_LIMIT, 0, id="at_eip7954_limit"),
        pytest.param(EIP7954_LIMIT + 1, 0, 1, id="one_byte_over_eip7954"),
    ],
)
@pytest.mark.valid_from("EIP7954")
def test_the_new_limit_is_pinned_from_both_sides(
    state_test: StateTestFiller, pre: Alloc, n: int, size: int, gate: int
) -> None:
    """
    Test 65,536 deploys and 65,537 does not, in a block large enough to pay.

    Needs a 120,000,000-gas block: see arm 4 for why, which is the point.
    """
    _run(state_test, pre, n=n, size=size, gate=gate, block_gas_limit=120_000_000)


@pytest.mark.parametrize(
    "block_gas_limit,size,gate",
    [
        pytest.param(
            MAINNET_BLOCK_GAS_LIMIT, 0, 1, id="mainnet_60M_cannot_deploy_it"
        ),
        pytest.param(
            120_000_000, EIP7954_LIMIT, 0, id="120M_can_deploy_it"
        ),
    ],
)
@pytest.mark.valid_from("EIP7954")
def test_the_eip7954_maximum_needs_more_than_a_mainnet_block(
    state_test: StateTestFiller,
    pre: Alloc,
    block_gas_limit: int,
    size: int,
    gate: int,
) -> None:
    """
    Test a maximum-size contract is undeployable at the current block limit.

    The deposit costs 100,270,080 state gas plus 183,600 for the account,
    and the reservoir that funds it is `tx.gas - 2**24`, itself bounded by
    the block's state-gas budget (`check_tx_fits_block`,
    amsterdam/vm/gas.py:1084). At 60,000,000 the largest reachable reservoir
    is 60,000,000 - 16,777,216 = 43,222,784, plus at most one execution
    grant's worth of spill -- far short of 100,453,680. The CREATE returns
    zero and the gate then "accepts" an empty address, so a factory sees
    success-shaped nothing.

    Both arms are asserted, because a one-sided test here would read as "the
    limit is unreachable" rather than "the limit is reachable but not in a
    block this size", and those have opposite implications for whether this
    is an EIP bug or a parameter choice.
    """
    _run(
        state_test,
        pre,
        n=EIP7954_LIMIT,
        size=size,
        gate=gate,
        block_gas_limit=block_gas_limit,
    )
