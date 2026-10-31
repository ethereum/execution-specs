"""
Transaction gas limit cap as a WORK CEILING, and its two block-level edges.

Relayers, batchers and multicalls size a batch against the gas they can buy.
The deployed idiom is "the block gas limit is the ceiling; I ask for the gas I
need and I get it". EIP-7825 breaks that with a *per-transaction* cap of
2**24 = 16,777,216, and EIP-8037 then reinterprets the very same constant:

    Osaka      tx.gas > TX_MAX_GAS_LIMIT  ->  transaction INVALID
                                               osaka/transactions.py:582
    Amsterdam  tx.gas > TX_MAX_TOTAL_GAS_LIMIT (2**32-1)  ->  INVALID, and
               TX_MAX_GAS_LIMIT now bounds only the EXECUTION-gas grant:
                   evm_gas   = tx.gas - intrinsic
                   budget    = TX_MAX_GAS_LIMIT - intrinsic
                   execution = min(budget, evm_gas)
                   reservoir = evm_gas - execution
                                               amsterdam/vm/gas.py:1106-1136

So the cap and EIP-8037's state-gas reservoir are the same boundary seen from
two sides, and the intrinsic cost cancels out of the reservoir entirely:

    reservoir == tx.gas - TX_MAX_GAS_LIMIT        for tx.gas >= the cap

The hazard moves across three stages, and the last one is the quiet one:

    Prague      ask for 17.7M, get 17.7M              works
    Osaka       ask for 17.7M, transaction rejected    LOUD failure
    Amsterdam   ask for 17.7M, get 16.76M of execution SILENT truncation

Nothing reverts at Amsterdam. The transaction lands, the batch does less work
than it was sized for, and the extra gas bought state capability the batcher
never asked for.

The ceiling is also *eroded* by anything that raises the intrinsic execution
cost, because the budget is `TX_MAX_GAS_LIMIT - intrinsic.execution`.
EIP-7981 does exactly that, twice over: it reprices access-list entries AND
charges their floor-token surcharge into the execution dimension as well
("on both sides of the gas-used maximum, independently of the existing
per-entry access charges", amsterdam/transactions.py:759-764). Every gas of
that surcharge is a gas of execution capacity no amount of extra `tx.gas`
can buy back.

Asserting raw gas numbers is correct here: 2**24 is the invariant, exactly as
it is for 24,576 in `code_size_gate` and 21,000 in `tests/intrinsic_cost`
(SCHEMA.md 4.1 permits this when the number IS the invariant). Do not repair
a failure by rebasing the constants -- the constants are the assertion.
"""

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytecode,
    Environment,
    Hash,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    TransactionException,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7825.md"
REFERENCE_SPEC_VERSION = "1ed95cbac750539c2aac67c8cbbcc2d77974231c"

CAP = 2**24  # TX_MAX_GAS_LIMIT, amsterdam/vm/gas.py:153

# `GAS` is the first instruction executed, and costs 2, so the recorded
# figure is the top frame's execution grant minus 2.
GAS_OPCODE_COST = 2

# One fresh storage slot: STATE_BYTES_PER_STORAGE_SET 64 * 1,530.
STORAGE_SET = 97_920

# Measured exactly (expansion/tests/tools/test_exp_txcaps_reservoir_probe.py):
# COLD_STORAGE_ACCESS 2,100 + STORAGE_WRITE 10,000 + two PUSH1s.
CHILD_EXEC_COST = 12_106

# A block gas limit comfortably above the cap, so the execution dimension of
# `check_tx_fits_block` can never be the binding one.
BLOCK_ABOVE_CAP = 20_000_000


def _ceiling_meter() -> Bytecode:
    """Record the execution gas this transaction was actually granted."""
    return Op.SSTORE(0, Op.GAS) + Op.STOP


# ---------------------------------------------------------------------------
# Arm 1: the invariant. More gas buys more work, one for one.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "tx_gas,grant",
    [
        pytest.param(CAP, 16_756_214, id="at_the_future_cap"),
        pytest.param(CAP + 1_000_000, 17_756_214, id="a_million_above_it"),
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Prague")
def test_more_gas_buys_more_execution_before_the_cap(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas: int,
    grant: int,
) -> None:
    """
    Test the execution grant tracks `tx.gas` with no per-transaction ceiling.

    This is the assumption every relayer and batcher is written against, and
    it is asserted on no fork by any existing test. The two points pin the
    1:1 relation: +1,000,000 of `tx.gas` is +1,000,000 of execution gas.
    """
    meter = pre.deploy_contract(_ceiling_meter())
    storage = Storage()
    storage.store_next(grant, f"execution grant for tx.gas={tx_gas}")
    tx = Transaction(
        to=meter, gas_limit=tx_gas, sender=pre.fund_eoa(amount=10**19)
    )
    state_test(
        pre=pre,
        post={meter: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.valid_from("Osaka")
@pytest.mark.valid_until("Osaka")
def test_the_execution_ceiling_at_the_cap_on_osaka(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    Test the most execution gas any Osaka transaction can be granted.

    16,756,214 = 2**24 - 21,000 - 2. Osaka rejects anything above the cap
    outright, which `tests/osaka/eip7825_transaction_gas_limit_cap/
    test_tx_gas_limit.py::test_transaction_gas_limit_cap` already covers; the
    number *below* the rejection -- the batcher's hard ceiling -- is stated
    nowhere, and it is what sizing code has to be written against.
    """
    meter = pre.deploy_contract(_ceiling_meter())
    storage = Storage()
    storage.store_next(16_756_214, "Osaka execution ceiling")
    tx = Transaction(
        to=meter, gas_limit=CAP, sender=pre.fund_eoa(amount=10**19)
    )
    state_test(
        pre=pre,
        post={meter: Account(storage=storage)},
        tx=tx,
    )


# ---------------------------------------------------------------------------
# Arm 2: the violation. More gas buys NOTHING, and nothing reverts.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "tx_gas",
    [
        pytest.param(CAP, id="at_the_cap"),
        pytest.param(CAP + 1_000_000, id="a_million_above"),
        pytest.param(CAP + 8_000_000, id="eight_million_above"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_more_gas_buys_no_execution_from_eip8037(
    state_test: StateTestFiller, pre: Alloc, tx_gas: int
) -> None:
    """
    Test the execution grant is frozen at the cap however much gas is bought.

    All three transactions are VALID -- EIP-8037 raised the validity bound to
    `TX_MAX_TOTAL_GAS_LIMIT` -- and all three are granted the identical
    16,762,214 = 2**24 - 15,000 - 2. Eight million extra gas buys exactly
    zero extra execution, with no exception anywhere for a batcher to catch.
    """
    meter = pre.deploy_contract(_ceiling_meter())
    storage = Storage()
    storage.store_next(
        16_762_214, "EIP-8037 execution ceiling, invariant in tx.gas"
    )
    tx = Transaction(
        to=meter, gas_limit=tx_gas, sender=pre.fund_eoa(amount=10**19)
    )
    state_test(
        pre=pre,
        post={meter: Account(storage=storage)},
        tx=tx,
    )


# ---------------------------------------------------------------------------
# Arm 3: the other side of the same boundary -- the reservoir.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "tx_gas,lands",
    [
        pytest.param(CAP, 0, id="at_the_cap_no_reservoir"),
        pytest.param(CAP + STORAGE_SET - 1, 0, id="one_gas_short"),
        pytest.param(CAP + STORAGE_SET, 1, id="exactly_one_slot"),
        pytest.param(CAP + STORAGE_SET + 1, 1, id="one_gas_over"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_the_reservoir_begins_exactly_at_the_cap(
    state_test: StateTestFiller, pre: Alloc, tx_gas: int, lands: int
) -> None:
    """
    Test the reservoir is exactly `tx.gas - TX_MAX_GAS_LIMIT`, to one gas.

    A child frame is handed exactly 12,106 execution gas -- the measured cost
    of one fresh `SSTORE` -- so it has no slack for the 97,920 state gas to
    spill into (`charge_state_gas_from_meter` draws the reservoir first and
    `gas_left` only for the remainder, amsterdam/vm/gas.py:428-436). The
    write can therefore land only if the reservoir funds it in full.

    It lands at `tx.gas = 2**24 + 97,920` and not at one gas less, which pins
    the reservoir's origin to the EIP-7825 cap itself. The intrinsic cost
    appears on neither side: it cancels out of `evm_gas - execution`, so this
    boundary is immune to the EIP-2780 decomposition that moves every other
    number in this file.

    No gas figure is asserted -- only whether the slot was written.
    """
    writer = pre.deploy_contract(Op.SSTORE(0, 1) + Op.STOP)
    caller = pre.deploy_contract(
        Op.SSTORE(0, Op.CALL(gas=CHILD_EXEC_COST, address=writer)) + Op.STOP,
        storage={0: 0xFF},
    )
    child = Storage()
    child.store_next(lands, "fresh slot written by the child")
    parent = Storage()
    parent.store_next(lands, "child call reported success")
    tx = Transaction(
        to=caller, gas_limit=tx_gas, sender=pre.fund_eoa(amount=10**19)
    )
    state_test(
        pre=pre,
        post={
            writer: Account(storage=child),
            caller: Account(storage=parent),
        },
        tx=tx,
    )


# ---------------------------------------------------------------------------
# Arm 4: EIP-7981 erodes the ceiling, and the surcharge is charged twice.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "keys,grant",
    [
        pytest.param(0, 16_753_814, id="one_address"),
        pytest.param(1, 16_751_914, id="one_address_one_key"),
    ],
)
@pytest.mark.valid_from("Berlin")
@pytest.mark.valid_until("Osaka")
def test_access_list_ceiling_erosion_before_eip7981(
    state_test: StateTestFiller, pre: Alloc, keys: int, grant: int
) -> None:
    """
    Test what an access-list entry costs in execution capacity, pre-EIP-7981.

    Against the no-access-list ceiling of 16,756,214 an address entry costs
    2,400 and a storage key a further 1,900 -- `TX_ACCESS_LIST_ADDRESS` and
    `TX_ACCESS_LIST_STORAGE_KEY` verbatim, with no data surcharge.
    """
    meter = pre.deploy_contract(_ceiling_meter())
    storage = Storage()
    storage.store_next(grant, f"ceiling with 1 address + {keys} keys")
    tx = Transaction(
        ty=1,
        to=meter,
        gas_limit=CAP,
        access_list=[
            AccessList(
                address=Address(0xC0FFEE),
                storage_keys=[Hash(k) for k in range(keys)],
            )
        ],
        sender=pre.fund_eoa(amount=10**19),
    )
    state_test(
        pre=pre,
        post={meter: Account(storage=storage)},
        tx=tx,
    )


@pytest.mark.parametrize(
    "keys,grant",
    [
        pytest.param(0, 16_758_034, id="one_address"),
        pytest.param(1, 16_753_986, id="one_address_one_key"),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_access_list_ceiling_erosion_from_eip7981(
    state_test: StateTestFiller, pre: Alloc, keys: int, grant: int
) -> None:
    """
    Test the EIP-7981 surcharge is levied on the execution side as well.

    Against the no-access-list ceiling of 16,762,214 an address entry now
    costs 4,180 and a storage key 4,048:

        address  2,900 (COLD_ACCOUNT_ACCESS - WARM_ACCESS)
               + 1,280 (ACCESS_LIST_ADDRESS_FLOOR_TOKENS 80 x 16)
        key      2,000 (COLD_STORAGE_ACCESS - WARM_ACCESS)
               + 2,048 (ACCESS_LIST_STORAGE_KEY_FLOOR_TOKENS 128 x 16)

    So an address entry is 74.2% dearer and a storage key 113.1% dearer, and
    the floor-token surcharge is 30.6% of an address entry and **50.6% of a
    storage key** -- more than half the charge is the piece that also appears
    in the calldata floor. Pinning it here catches a double count or its
    accidental removal from either dimension independently, which the
    floor-side tests cannot: they compare the floor against itself.
    """
    meter = pre.deploy_contract(_ceiling_meter())
    storage = Storage()
    storage.store_next(grant, f"ceiling with 1 address + {keys} keys")
    tx = Transaction(
        ty=1,
        to=meter,
        gas_limit=CAP,
        access_list=[
            AccessList(
                address=Address(0xC0FFEE),
                storage_keys=[Hash(k) for k in range(keys)],
            )
        ],
        sender=pre.fund_eoa(amount=10**19),
    )
    state_test(
        pre=pre,
        post={meter: Account(storage=storage)},
        tx=tx,
    )


# ---------------------------------------------------------------------------
# Arm 5: the block-level edge. The cap does NOT let you oversubscribe a block.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "tx_gas,error",
    [
        pytest.param(BLOCK_ABOVE_CAP, None, id="at_the_block_gas_limit"),
        pytest.param(
            BLOCK_ABOVE_CAP + 1,
            TransactionException.GAS_ALLOWANCE_EXCEEDED,
            id="one_gas_over_the_block_gas_limit",
            marks=pytest.mark.exception_test,
        ),
    ],
)
@pytest.mark.valid_from("EIP8037")
def test_the_block_gas_limit_still_bounds_the_whole_tx_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas: int,
    error: TransactionException | None,
) -> None:
    """
    Test the reservoir half of `tx.gas` is still charged against the block.

    `check_tx_fits_block` tests two dimensions (amsterdam/vm/gas.py:1081):

        min(TX_MAX_GAS_LIMIT, tx_gas) > execution_gas_available  -> reject
        tx_gas                        > state_gas_available      -> reject

    The cap softens only the first. In a 20,000,000-gas block the execution
    dimension is satisfied by 16,777,216 whatever `tx.gas` is, yet one gas
    over the block limit is still rejected -- so a batcher that reads
    EIP-7825 as "my execution demand is capped, therefore I may ask for as
    much gas as I like" cannot get the transaction included. The two params
    bracket the boundary from both sides at the block gas limit exactly.
    """
    meter = pre.deploy_contract(Op.SSTORE(0, 1) + Op.STOP)
    storage = Storage()
    storage.store_next(0 if error else 1, "transaction was included")
    tx = Transaction(
        to=meter,
        gas_limit=tx_gas,
        sender=pre.fund_eoa(amount=10**19),
        error=error,
    )
    state_test(
        env=Environment(gas_limit=BLOCK_ABOVE_CAP),
        pre=pre,
        post={meter: Account(storage=storage)},
        tx=tx,
    )
