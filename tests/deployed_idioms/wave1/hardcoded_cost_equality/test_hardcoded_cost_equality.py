"""
Archetype 3: hardcoded cost-equality for a storage write.

A contract that quotes a fee, bills a relayer, or gates work on
affordability has to know what its own storage writes cost. No opcode
reports it, so deployed code writes the EIP-2200 schedule down as a literal
and keeps it forever:

```text
20,000   a storage write that creates a slot   (SSTORE_SET)
 5,000   a storage write that replaces a value (SSTORE_RESET, cold)
```

The invariant is **equality**: the constant equals the charge the EVM
actually takes. This is one of the two archetypes in the corpus where
asserting a raw gas number *is* the invariant, so SCHEMA.md 4.1's
prohibition does not apply -- it says "unless the gas number IS the
invariant". **Do not repair a failure here by rebasing the constants. The
constants are the assertion.** A test asserting `gasUsed == 45038` protects
nothing because the number is incidental to what that test is about; these
numbers are not incidental, they are what a deployed contract wrote into
immutable code and then multiplied by a gas price to move ether.

## Deployed witnesses for the 20,000 constant (CHECKED)

**a deployed rollup `Bridge`**, mainnet `<address withheld>`,
`contracts/bridge/Bridge.sol`. The clearest instance in the corpus, because
the constant flows directly into an ether transfer:

```solidity
46:  /// @dev The amount of gas not to charge fee per cache operation.
47:  uint256 private constant _GAS_REFUND_PER_CACHE_OPERATION = 20_000;
...
288:  uint256 refund = stats.numCacheOps * _GAS_REFUND_PER_CACHE_OPERATION;
291:  stats.gasUsedInFeeCalc = uint32(
292:      GAS_OVERHEAD + gasStart + _messageCalldataCost(_message.data.length)
293:          - gasleft()
294:  );
296:  uint256 gasCharged = refund.max(stats.gasUsedInFeeCalc) - refund;
297:  uint256 maxFee = gasCharged * _message.fee / _message.gasLimit;
298:  uint256 baseFee = gasCharged * block.basefee;
...
303:  msg.sender.sendEtherAndVerify(fee, _SEND_ETHER_GAS_LIMIT);
```

If 20,000 under-states the real charge, `gasCharged` is too small and the
relayer is **under-paid in ether**. Nothing reverts. The identifier appears
in 18 verified source files across **21 mainnet addresses**.

**a deployed rollup a rollup execution manager**, mainnet
`<address withheld>`,
`contracts/optimistic-ethereum/OVM/execution/a rollup execution manager.sol`:

```solidity
67:  uint256 constant NUISANCE_GAS_SLOAD = 20000;
68:  uint256 constant NUISANCE_GAS_SSTORE = 20000;
...
1686:     _useNuisanceGas(NUISANCE_GAS_SSTORE);   // first write to a slot only
```

`NUISANCE_GAS_SSTORE` is debited from a budget that gates execution, so here
the same constant drives a sufficiency decision rather than a price. 6 files,
**26 mainnet addresses**.

Both counts are distinct mainnet (`chain_id = 1`) addresses whose verified
source set contains the identifier, measured over the Sourcify v2 export; see
README.md for the query. The 5,000 constant is **not** separately witnessed
here -- see "Witness scope" in README.md. It is asserted on the same footing
as `tests/stipend_fallback`'s 2,300: a protocol constant, not a budget this
corpus chose.

## What the schedule actually does to the two constants

Measured from inside the EVM (`tests/tools/test_storage_cost_probe.py`,
CHECKED, six forks) as the `GAS` delta across one `SSTORE`:

```text
fork            create a slot    replace a value     clear a value
Berlin                 22,100              5,000             5,000
London                 22,100              5,000             5,000
Cancun                 22,100              5,000             5,000
Prague                 22,100              5,000             5,000
Osaka                  22,100              5,000             5,000
Amsterdam             110,020             12,100            12,100
```

The two constants have opposite histories, which is why both are tested:

* **5,000 is exactly right** for five consecutive forks. EIP-2929 split the
  flat 5,000 into `COLD_STORAGE_ACCESS 2,100` plus
  `COLD_STORAGE_WRITE 5,000 - COLD_STORAGE_ACCESS 2,100`, deliberately
  preserving the cold total, so a contract holding 5,000 stayed correct
  through the largest access-cost reprice in Ethereum's history. EELS still
  carries the figure under that name -- `COLD_STORAGE_WRITE: Final[Uint] =
  Uint(5000)`, osaka/vm/gas.py:49, consumed as
  `COLD_STORAGE_WRITE - COLD_STORAGE_ACCESS` in
  osaka/vm/instructions/storage.py. A corpus that only asserted inequalities
  would never have recorded that this equality held.
* **20,000 has been wrong since Berlin**, by the 2,100 cold surcharge
  EIP-2929 added on top of `STORAGE_SET` -- a 10.5% under-quote sitting in
  deployed code for five forks with no test failing anywhere, because
  nothing asserts the equality. a deployed rollup under-pays its relayers by that margin
  today.

At EIP-8037 both break at once, in the same direction, much harder:

```text
constant   real cost (Amsterdam)   under-quote
20,000              110,020             5.50x   = 2,100 + 10,000 + 97,920
 5,000               12,100             2.42x   = 2,100 + 10,000
```

`110,020 = COLD_STORAGE_ACCESS 2,100 + STORAGE_WRITE 10,000 +
STATE_BYTES_PER_STORAGE_SET 64 * COST_PER_STATE_BYTE 1,530`
(amsterdam/vm/gas.py:47-53, :78, :82).

Read the second row twice. 12,100 involves **no state gas at all**, so it is
not reachable by reasoning about the reservoir, and it is the row that hits
the archetype-2 population: a contract that only ever updates values it
already created -- one that "never needs to write new state" -- is still
mispriced by 7,100 gas per write.

## Why `gasleft()` is the right instrument, and the only one

The charge is taken by the `SSTORE` itself, so the only way a contract can
observe it is a `GAS` reading on each side -- which is exactly what deployed
self-metering code does (`gasStart ... - gasleft()` in the a deployed rollup excerpt
above). The 17 gas of instrument overhead between the two readings is
derived, not fitted:

```text
after the first GAS is charged and its value pushed:
  PUSH1 <mem offset>                    3
  MSTORE                                3 + 3   (one word of expansion)
  PUSH1 <sstore value>                  3
  PUSH1 <sstore key>                    3
  SSTORE                                C       <- the quantity under test
  GAS                                   2       (charged before it pushes)
                                      -----
                                        C + 17
```

Cross-check: the Osaka reading is 22,117 and `2,100 + 20,000 + 17 = 22,117`,
so the derivation and the measurement agree exactly rather than one being
inferred from the other.

## What a failure means

The gas cost of a storage write moved, and every deployed contract that
prices a fee, bills a relayer, or gates a batch on one of these two
constants is now wrong by the delta -- silently, because a bad quote
produces a bad price, not a revert.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# The EIP-2200 schedule as deployed code writes it down. These are the
# constants under test, not parameters of the test.
HARDCODED_SSTORE_SET = 20_000
HARDCODED_SSTORE_RESET = 5_000

# Gas spent between the two `GAS` readings, exclusive of the SSTORE.
# Derived in the module docstring, cross-checked against the Osaka reading.
INSTRUMENT_OVERHEAD = 17

# Measured per fork band (tests/tools/test_storage_cost_probe.py, CHECKED).
REAL_SET_THROUGH_OSAKA = 22_100
REAL_RESET_THROUGH_OSAKA = 5_000
REAL_SET_FROM_EIP8037 = 110_020
REAL_RESET_FROM_EIP8037 = 12_100

# Kept clear of 0x00 and 0x01, which `Storage.store_next` allocates to the
# two labelled markers.
SLOT_FRESH = 0x80
SLOT_EXISTING = 0x81

CREATING_WRITE = "creating_write"
REPLACING_WRITE = "replacing_write"


def _meter(
    write: Bytecode,
    storage: Storage,
    real_cost: int,
    quoted: int,
    label: str,
) -> Bytecode:
    """
    Build a self-metering write and record both the charge and the verdict.

    Two markers, because they fail differently and both are wanted:

    * the **charge** pins the exact number, so a reprice in either direction
      fails the test. This is the equality assertion, and it is the whole
      point of the archetype.
    * the **verdict** records whether the contract's own quote covered the
      charge. It is the readable form of the invariant: a maintainer facing
      a failure sees `quote_20000_covers_creating_write: want 0x1, got 0x0`
      rather than only a changed integer.
    """
    return (
        Op.MSTORE(0, Op.GAS)
        + write
        + Op.MSTORE(0x20, Op.GAS)
        + Op.MSTORE(0x40, Op.SUB(Op.MLOAD(0), Op.MLOAD(0x20)))
        + Op.SSTORE(
            storage.store_next(
                real_cost + INSTRUMENT_OVERHEAD, f"charge_for_{label}"
            ),
            Op.MLOAD(0x40),
        )
        + Op.SSTORE(
            storage.store_next(
                int(real_cost <= quoted), f"quote_{quoted}_covers_{label}"
            ),
            Op.ISZERO(Op.GT(Op.MLOAD(0x40), quoted + INSTRUMENT_OVERHEAD)),
        )
        + Op.STOP
    )


def _run(
    state_test: StateTestFiller,
    pre: Alloc,
    real_cost: int,
    quoted: int,
    label: str,
) -> None:
    """Fill one metered write; the label selects which write is metered."""
    creating = label == CREATING_WRITE
    write = (
        Op.SSTORE(SLOT_FRESH, 1)
        if creating
        else Op.SSTORE(SLOT_EXISTING, 2)
    )

    storage = Storage()
    subject = pre.deploy_contract(
        _meter(write, storage, real_cost, quoted, label),
        storage={SLOT_EXISTING: 1},
    )
    # State the written slots too, so the post condition is complete and
    # "nothing else moved" is part of the assertion.
    if creating:
        storage[SLOT_FRESH] = 1
        storage[SLOT_EXISTING] = 1
    else:
        storage[SLOT_EXISTING] = 2

    tx = Transaction(to=subject, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(pre=pre, post={subject: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_hardcoded_5000_equals_a_replacing_write_through_osaka(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the hardcoded 5,000 is the exact charge for replacing a value.

    The equality that held, asserted on the forks where it holds. A contract
    quoting 5,000 for a non-creating storage write was correct on Berlin,
    London, Cancun, Prague and Osaka, and stayed correct *through* EIP-2929
    because that EIP split the charge (`2,100 + 2,900`) while preserving its
    cold total.

    Pinning it here is what makes the Amsterdam break below a measured
    change rather than an unverified claim about the past -- and if a future
    fork restores the old figure, this test starts applying again instead of
    the corpus going quiet.
    """
    _run(
        state_test,
        pre,
        REAL_RESET_THROUGH_OSAKA,
        HARDCODED_SSTORE_RESET,
        REPLACING_WRITE,
    )


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_hardcoded_20000_already_under_quotes_a_creating_write(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the hardcoded 20,000 has been 2,100 short since Berlin.

    The equality that did *not* hold, asserted so the corpus records a
    pre-existing break instead of discovering it only at Amsterdam.
    EIP-2929 added `COLD_STORAGE_ACCESS` on top of `STORAGE_SET` without
    reducing the latter, so a deployed rollup's `_GAS_REFUND_PER_CACHE_OPERATION` and
    a deployed rollup's `NUISANCE_GAS_SSTORE` have both under-quoted by 10.5% for
    five forks.

    The `quote_20000_covers_creating_write` marker records 0, which is the
    committed form of that statement: a test that asserted only the number
    would make this look like a measurement, where it is in fact a finding.
    """
    _run(
        state_test,
        pre,
        REAL_SET_THROUGH_OSAKA,
        HARDCODED_SSTORE_SET,
        CREATING_WRITE,
    )


@pytest.mark.parametrize(
    "real_cost,quoted,label",
    [
        pytest.param(
            REAL_SET_FROM_EIP8037,
            HARDCODED_SSTORE_SET,
            CREATING_WRITE,
            id="set_quoted_20000_costs_110020",
        ),
        pytest.param(
            REAL_RESET_FROM_EIP8037,
            HARDCODED_SSTORE_RESET,
            REPLACING_WRITE,
            id="reset_quoted_5000_costs_12100",
        ),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_hardcoded_storage_costs_both_break_from_eip8037(
    state_test: StateTestFiller,
    pre: Alloc,
    real_cost: int,
    quoted: int,
    label: str,
) -> None:
    """
    Test both hardcoded constants under-quote once EIP-8037 is active.

    A creating write costs 110,020 against a quote of 20,000 (5.50x); a
    replacing write costs 12,100 against a quote of 5,000 (2.42x). Both
    `quote_covers` markers record 0.

    The replacing case is the one worth reading twice: it involves no state
    gas at all, so it is not reachable by reasoning about the reservoir.
    `STORAGE_WRITE` is simply 10,000 where the old
    `COLD_STORAGE_WRITE - COLD_STORAGE_ACCESS` term was 2,900.
    """
    _run(state_test, pre, real_cost, quoted, label)
