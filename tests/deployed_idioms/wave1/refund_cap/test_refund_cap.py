"""
Archetype 8: refund-cap dependence.

A transaction that clears storage is refunded
`min(gas_used_before_refund // D, refund_counter)`. **`D` was 2 at Berlin
and became 5 at London (EIP-3529)**, and the clear refund itself fell
from 15,000 to 4,800 in the same EIP.

Coverage, CHECKED against the pinned tree rather than assumed:

* **No `tests/london/eip3529*` directory exists.** `tests/london/` holds
  only `eip1559_fee_market_change` and `validation` (a header test), so
  the `//2 -> //5` change itself has no behavioural test.
* Every test that touches the quotient reads it back out of the fork --
  `fork.max_refund_quotient()`, defined as 2 at Genesis and overridden to
  5 in `forks/eips/london/eip_3529.py:31` -- so it moves with the spec and
  cannot fail when the spec does.
* **One partial exception, cited rather than ignored:**
  `tests/amsterdam/eip8038_state_access_gas_cost_increase/
  test_sstore_refunds.py` *does* hardcode `gross // 5`. But it is
  `valid_from("Amsterdam")`, so it covers Amsterdam alone and is blind to
  the quotient on Berlin..Osaka; and it takes the clear-refund *amount*
  from the fork (`code.refund(fork)`), so that term stays untested
  everywhere.

What is left uncovered, and what this file supplies, is therefore the
quotient on **Berlin, London and Osaka**, and the per-clear refund amount
on **every** fork. Deployed code reads neither from a fork: it budgeted
against fixed numbers at deploy time.

Witnessed (CHECKED, `registry/L2-bytecode.jsonl`): *bulk storage clearing
inside a loop* -- **406,604 mainnet addresses from 298,869 distinct
runtime code hashes**, 30.05% of the 994,414 mainnet runtimes scanned.
Exemplar `<address withheld>`. Its recorded
invariant: *"the number of slots a batch can clear within a given
transaction gas limit is determined by the per-slot cost net of refund."*
Dynamically (CHECKED, `registry/L5-dynamic.jsonl`, mainnet blocks
26,250,000-26,259,999): **792,199 of 2,571,532 transactions (30.81%)
receive a refund**, 365,238 of them exactly 4,800 -- one plain clear.
The historically-killed population is the gas tokens (a gas-token contract/a gas-token contract), whose
business model was `refund >= threshold`; L4's `refund-cap` axis records
that narrative but cites **no measured count**, so it is not claimed here.

**How the refund is made observable.** A refund is settled after
execution, so it can change only the ether returned to the sender. Two
senders therefore run bytecode of *identical* gas cost over identical
storage: one clears its slots (`1 -> 0`, refund granted), the other moves
them to another non-zero value (`1 -> 2`, same charge, no refund --
`amsterdam/vm/instructions/storage.py:122-139`). With equal gas limits
and equal starting balances, the difference between their final balances
is **exactly the refund**, and every pricing term they share cancels.
A third transaction in the same block reads both balances with `BALANCE`
and commits the derived quantity to storage.

`gas_limit` is set explicitly, so on Amsterdam
`allocate_evm_gas` (`amsterdam/vm/gas.py:1104`) leaves the state gas
reservoir at **0** for any limit below `TX_MAX_GAS_LIMIT` (16,777,216);
`state_gas_left` is therefore 0 at settlement and
`gas_used_before_refund = tx_gas - gas_left` with no reservoir term.
No slot here is created, so no state gas is charged either.

Measured, not assumed (`tests/tools/test_refund_probe.py`):

```text
fork       gas_used_before_refund   refund    used // refund
Berlin                    271,300   135,650                2
London                    271,300    54,260                5
Cancun                    271,300    54,260                5
Osaka                     271,300    54,260                5
Amsterdam                 620,300   124,060                5
```
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytecode,
    Op,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

GAS_PRICE = 10**9
GAS_LIMIT = 1_000_000

# Enough clears that the counter is far above `used // D` on every fork,
# so the cap is the binding term of the `min`.
CAP_BOUND_SLOTS = 50

# One clear inside a deliberately expensive transaction, so `used // D`
# is far above the counter and the *counter* is the binding term.
COUNTER_BOUND_SLOTS = 1
COUNTER_BOUND_BURN_OFFSET = 245_760  # ~138,000 gas of memory expansion


def _slot_writer(n: int, value: int) -> Bytecode:
    """
    `SSTORE(k, value)` for k in 1..n.

    `PUSH1 value; PUSH1 k; SSTORE` has the same width and the same cost
    for every `value`, which is what makes the clearing and the
    non-clearing twin cost the same to the gas.
    """
    code = Bytecode()
    for k in range(1, n + 1):
        code += Op.PUSH1[value] + Op.PUSH1[k] + Op.SSTORE
    return code


def _ratio_prober(
    clearer_sender: object, twin_sender: object, slot: int
) -> Bytecode:
    """
    Commit `gas_used_before_refund // refund`, which is the divisor `D`.

    Both senders started with `GAS_LIMIT * GAS_PRICE` and spent nothing
    but gas, so `GAS_LIMIT - BALANCE/GAS_PRICE` is each one's `gas_used`.
    The twin received no refund, so its `gas_used` *is*
    `gas_used_before_refund`; the difference between the two balances is
    the refund. Dividing one by the other cancels every price in the
    construction and leaves the rule itself.
    """
    left_clearer = Op.DIV(Op.BALANCE(clearer_sender), GAS_PRICE)
    left_twin = Op.DIV(Op.BALANCE(twin_sender), GAS_PRICE)
    used_before_refund = Op.SUB(GAS_LIMIT, left_twin)
    refund = Op.SUB(left_clearer, left_twin)
    return Op.SSTORE(slot, Op.DIV(used_before_refund, refund)) + Op.STOP


def _refund_prober(
    clearer_sender: object, twin_sender: object, slot: int
) -> Bytecode:
    """Commit the refund itself, in gas units."""
    left_clearer = Op.DIV(Op.BALANCE(clearer_sender), GAS_PRICE)
    left_twin = Op.DIV(Op.BALANCE(twin_sender), GAS_PRICE)
    return Op.SSTORE(slot, Op.SUB(left_clearer, left_twin)) + Op.STOP


def _run(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    *,
    slots: int,
    burn: Bytecode,
    prober_builder: object,
    expected: int,
    label: str,
) -> None:
    """Fill the three-transaction block and assert the committed quantity."""
    initial_storage = {k: 1 for k in range(1, slots + 1)}
    clearer = pre.deploy_contract(
        _slot_writer(slots, 0) + burn + Op.STOP, storage=initial_storage
    )
    twin = pre.deploy_contract(
        _slot_writer(slots, 2) + burn + Op.STOP, storage=initial_storage
    )
    clearer_sender = pre.fund_eoa(amount=GAS_LIMIT * GAS_PRICE)
    twin_sender = pre.fund_eoa(amount=GAS_LIMIT * GAS_PRICE)

    committed = Storage()
    prober = pre.deploy_contract(
        prober_builder(
            clearer_sender, twin_sender, committed.store_next(expected, label)
        )
    )
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        ty=0,
                        sender=clearer_sender,
                        to=clearer,
                        gas_limit=GAS_LIMIT,
                        gas_price=GAS_PRICE,
                    ),
                    Transaction(
                        ty=0,
                        sender=twin_sender,
                        to=twin,
                        gas_limit=GAS_LIMIT,
                        gas_price=GAS_PRICE,
                    ),
                    Transaction(
                        ty=0,
                        sender=pre.fund_eoa(),
                        to=prober,
                        gas_limit=GAS_LIMIT,
                        gas_price=GAS_PRICE,
                    ),
                ]
            )
        ],
        post={prober: Account(storage=committed)},
    )


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Berlin")
def test_refund_is_one_half_of_gas_used_at_berlin(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the pre-EIP-3529 cap returns half of a clearing transaction's gas.

    This is the quotient the gas tokens were built on and the one
    EIP-3529 removed. Fifty clears accrue 750,000 of refund counter
    against 271,300 of gas used, so the cap -- not the counter -- is what
    the sender actually receives, and the measured ratio is exactly 2.
    """
    _run(
        blockchain_test,
        pre,
        slots=CAP_BOUND_SLOTS,
        burn=Bytecode(),
        prober_builder=_ratio_prober,
        expected=2,
        label="refund_divisor",
    )


@pytest.mark.valid_from("London")
def test_refund_is_one_fifth_of_gas_used_from_london(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test EIP-3529's cap returns one fifth, on every fork since London.

    The identical construction now commits 5 rather than 2. Pinning both
    sides of the boundary is the point: a fork that moved the divisor in
    *either* direction fails one of this pair, where a conformance test
    that reads the divisor out of the fork can fail for neither.
    """
    _run(
        blockchain_test,
        pre,
        slots=CAP_BOUND_SLOTS,
        burn=Bytecode(),
        prober_builder=_ratio_prober,
        expected=5,
        label="refund_divisor",
    )


@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Berlin")
def test_clear_refund_is_15000_at_berlin(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the other term of the `min`: the clear refund, before EIP-3529.

    One clear inside a transaction expensive enough that `used // 2` is
    far above the counter, so the refund equals the counter exactly. A
    single clear was worth 15,000 gas while costing 5,000 -- a net gain
    of 10,000 per slot, which is the whole of the gas-token trade.
    """
    _run(
        blockchain_test,
        pre,
        slots=COUNTER_BOUND_SLOTS,
        burn=Op.MSTORE(COUNTER_BOUND_BURN_OFFSET, 0),
        prober_builder=_refund_prober,
        expected=15_000,
        label="clear_refund",
    )


@pytest.mark.valid_from("London")
@pytest.mark.valid_until("Osaka")
def test_clear_refund_is_4800_from_london(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the clear refund EIP-3529 left behind: 4,800, not 15,000.

    L5 measured this exact figure as the single commonest refund on
    mainnet -- 365,238 transactions in a 10,000-block window refund
    exactly 4,800 -- so this is the number real transactions settle on.
    Below the cost of the clear (5,000), which is why clearing storage
    stopped being profitable.
    """
    _run(
        blockchain_test,
        pre,
        slots=COUNTER_BOUND_SLOTS,
        burn=Op.MSTORE(COUNTER_BOUND_BURN_OFFSET, 0),
        prober_builder=_refund_prober,
        expected=4_800,
        label="clear_refund",
    )


@pytest.mark.valid_from("EIP8037")
def test_clear_refund_is_11616_from_eip8037(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the clear refund Amsterdam derives from its own write price.

    `REFUND_STORAGE_CLEAR = (STORAGE_WRITE + COLD_STORAGE_ACCESS) *
    4800 // 5000` (`amsterdam/vm/gas.py:98`), i.e. the old 4,800/5,000
    ratio re-applied to the new 12,100 cost: 11,616. Stated as a literal
    here on purpose -- a deployed contract sees the number, not the
    formula, so if the formula's inputs move this test is the alarm.
    """
    _run(
        blockchain_test,
        pre,
        slots=COUNTER_BOUND_SLOTS,
        burn=Op.MSTORE(COUNTER_BOUND_BURN_OFFSET, 0),
        prober_builder=_refund_prober,
        expected=11_616,
        label="clear_refund",
    )
