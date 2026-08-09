"""
Tests for [EIP-8038: State Access Gas Cost Increase](https://eips.ethereum.org/EIPS/eip-8038).

Covers the EIP-8038 ``EXT*`` "double-read" surcharge: ``EXTCODESIZE`` and
``EXTCODECOPY`` perform two database reads (the account leaf and then the
code) and are therefore charged an extra ``WARM_ACCESS`` on top of the
account-access cost, whereas ``BALANCE`` and ``EXTCODEHASH`` read only the
account leaf and are charged the account-access cost alone.
"""

from typing import Callable

import pytest
from execution_testing import (
    AccessList,
    Account,
    Address,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Environment,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)
from execution_testing.checklists import EIPChecklist

from .spec import ref_spec_8038

REFERENCE_SPEC_GIT_PATH = ref_spec_8038.git_path
REFERENCE_SPEC_VERSION = ref_spec_8038.version

pytestmark = pytest.mark.valid_from("Amsterdam")


# Each parameter carries:
#   - executable: builds the runnable opcode targeting ``target``
#   - cost_metadata: builds the metadata-only opcode for gas computation
#   - extra_stack_items: stack items left by the opcode (for CodeGasMeasure)
#   - code_read_surcharge: whether EIP-8038 adds the extra WARM_ACCESS read
EXT_OPCODES = [
    pytest.param(
        lambda target: Op.EXTCODESIZE(target),
        lambda warm: Op.EXTCODESIZE(address_warm=warm),
        1,
        True,
        id="EXTCODESIZE",
    ),
    pytest.param(
        lambda target: Op.EXTCODECOPY(target, 0, 0, 0),
        lambda warm: Op.EXTCODECOPY(address_warm=warm),
        0,
        True,
        id="EXTCODECOPY",
    ),
    pytest.param(
        lambda target: Op.EXTCODEHASH(target),
        lambda warm: Op.EXTCODEHASH(address_warm=warm),
        1,
        False,
        id="EXTCODEHASH",
    ),
    pytest.param(
        lambda target: Op.BALANCE(target),
        lambda warm: Op.BALANCE(address_warm=warm),
        1,
        False,
        id="BALANCE",
    ),
]


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
@pytest.mark.parametrize(
    "executable,cost_metadata,extra_stack_items,code_read_surcharge",
    EXT_OPCODES,
)
def test_ext_code_opcode_gas(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    warm: bool,
    executable: Callable[[object], Bytecode],
    cost_metadata: Callable[[bool], Bytecode],
    extra_stack_items: int,
    code_read_surcharge: bool,
) -> None:
    """
    Measure the exact gas of an external-code/account-access opcode and
    assert it matches the EIP-8038 schedule.

    ``EXTCODESIZE``/``EXTCODECOPY`` must cost exactly one ``WARM_ACCESS``
    more than ``BALANCE``/``EXTCODEHASH`` at equal warmth (the second,
    code-reading database access).
    """
    del code_read_surcharge  # encoded in `cost_metadata`

    target = pre.deploy_contract(Op.STOP)

    measured_code = executable(target)
    # Subtract the opcode's OWN cold cost (not BALANCE's) so the
    # CodeGasMeasure overhead excludes only the PUSH wrapper; under
    # EIP-8038 EXTCODESIZE/EXTCODECOPY have a higher cold cost than
    # BALANCE because of the code-read surcharge.
    overhead_cost = measured_code.gas_cost(fork) - cost_metadata(
        False
    ).gas_cost(fork)

    code_gas_measure = CodeGasMeasure(
        code=measured_code,
        overhead_cost=overhead_cost,
        extra_stack_items=extra_stack_items,
    )
    measure_address = pre.deploy_contract(code=code_gas_measure)

    # The opcode's own cost is the expected measured gas: it folds the
    # access cost and, for EXTCODESIZE/EXTCODECOPY, the code-read
    # surcharge.
    expected_gas = cost_metadata(warm).gas_cost(fork)

    # Warm the target via the access list when required; the cold case
    # leaves it absent so its first runtime access is cold.
    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        access_list=[AccessList(address=target, storage_keys=[])]
        if warm
        else None,
    )

    post = {measure_address: Account(storage={0: expected_gas})}

    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
@pytest.mark.parametrize(
    "copy_size", [32, 96], ids=["one_word", "three_words"]
)
def test_extcodecopy_nonzero_composes_additively(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    warm: bool,
    copy_size: int,
) -> None:
    """
    Verify the EIP-8038 ``EXTCODECOPY`` surcharge composes additively.

    With a non-zero copy size, ``EXTCODECOPY`` charges the account-access
    cost, the EIP-8038 code-read ``WARM_ACCESS`` surcharge, the EIP-150
    per-word copy cost (``OPCODE_COPY_PER_WORD`` per word, driven by the
    copied data size), and the memory-expansion cost. The surcharge is a
    flat add-on that does not interact with the copy or memory terms, so
    the measured gas must equal the sum of all four components.
    """
    # Target carries enough code to satisfy the copy; STOP padding keeps
    # it a deployable contract with a non-empty code hash.
    target = pre.deploy_contract(Op.STOP * copy_size)

    # Runnable opcode copying ``copy_size`` bytes of the target's code into
    # memory at offset 0. The metadata mirrors the runtime effect (warmth,
    # copied byte count, and the 0 -> copy_size memory growth) so the
    # opcode model agrees with execution and the overhead reduces to the
    # operand pushes alone.
    measured_code = Op.EXTCODECOPY.with_metadata(
        address_warm=warm,
        data_size=copy_size,
        new_memory_size=copy_size,
        old_memory_size=0,
    )(target, 0, 0, copy_size)

    # Oracle: the same metadata-only opcode. Subtracting its cost from the
    # measured code's cost yields the CodeGasMeasure overhead (the operand
    # PUSHes only), so the stored value equals exactly this opcode cost.
    oracle = Op.EXTCODECOPY.with_metadata(
        address_warm=warm,
        data_size=copy_size,
        new_memory_size=copy_size,
        old_memory_size=0,
    )
    expected_gas = oracle.gas_cost(fork)

    code_gas_measure = CodeGasMeasure(
        code=measured_code,
        overhead_cost=measured_code.gas_cost(fork) - oracle.gas_cost(fork),
        extra_stack_items=0,
    )
    measure_address = pre.deploy_contract(code=code_gas_measure)

    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        access_list=[AccessList(address=target, storage_keys=[])]
        if warm
        else None,
    )

    post = {measure_address: Account(storage={0: expected_gas})}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
def test_extcodehash_empty_account(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    warm: bool,
) -> None:
    """
    Verify ``EXTCODEHASH`` of an empty account is priced without surcharge.

    ``EXTCODEHASH`` reads only the account leaf, so EIP-8038 adds no
    code-read surcharge: the cost is exactly ``COLD_ACCOUNT_ACCESS`` (cold)
    or ``WARM_ACCESS`` (warm) regardless of the target being empty. The
    returned hash of an empty/non-existent account is ``0``.
    """
    # A non-existent (empty) target: never deployed, no balance, no code.
    empty_addr = Address(0xDEAD)

    # EXTCODEHASH reads only the account leaf (no code-read surcharge), so
    # its bare cost is the plain account access.
    expected_gas = Op.EXTCODEHASH(address_warm=warm).gas_cost(fork)

    # Measure the access cost, then store the returned hash so the
    # empty-account 0 result is asserted alongside the pricing. The
    # measured opcode carries the runtime warmth so the overhead reduces
    # to the address PUSH alone.
    #
    # The empty-account hash is 0, which is also the default of an
    # unwritten storage slot: a stranded hash store would leave slot 1 at
    # 0 and pass vacuously (the original defect). Slot 1 is poisoned with
    # a non-zero sentinel before the measured region, so the real store
    # must overwrite it back to 0. If that store is ever stranded, slot 1
    # keeps the sentinel and the assertion fails instead of silently
    # passing.
    # The poison precedes the measured region and the hash store follows
    # it, so neither touches 0xDEAD before the measured access nor
    # perturbs the cold-case gas measurement.
    storage = Storage()
    measured_code = Op.EXTCODEHASH.with_metadata(address_warm=warm)(empty_addr)
    gas_slot = storage.store_next(expected_gas, "extcodehash_empty_gas")
    hash_slot = storage.store_next(0, "extcodehash_empty_hash")
    hash_slot_sentinel = 0xBADC0FFEE
    code = (
        Op.SSTORE(hash_slot, hash_slot_sentinel)
        + CodeGasMeasure(
            code=measured_code,
            overhead_cost=measured_code.gas_cost(fork)
            - Op.EXTCODEHASH(address_warm=warm).gas_cost(fork),
            extra_stack_items=1,
            sstore_key=gas_slot,
        )
        + Op.SSTORE(hash_slot, Op.EXTCODEHASH(empty_addr))
    )
    measure_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        access_list=[AccessList(address=empty_addr, storage_keys=[])]
        if warm
        else None,
    )

    post = {measure_address: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


# The two surcharge opcodes only -- both always pay the second,
# code-reading access, so there is no no-surcharge variant here.
DOUBLE_READ_OPCODES = [Op.EXTCODESIZE, Op.EXTCODECOPY]


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
@pytest.mark.parametrize("opcode", DOUBLE_READ_OPCODES)
def test_ext_code_double_read_empty_account(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    warm: bool,
    opcode: Op,
) -> None:
    """
    Charge the EIP-8038 double-read surcharge on an empty target.

    ``EXTCODESIZE``/``EXTCODECOPY`` add the second, code-reading database
    access unconditionally: the surcharge is charged before the account is
    read, so an empty/non-existent target still costs
    ``COLD_ACCOUNT_ACCESS + WARM_ACCESS`` (cold) or ``2 * WARM_ACCESS``
    (warm), i.e. 3100 / 200, exactly as for a code-bearing target. This
    contrasts with ``EXTCODEHASH``/``BALANCE``, which read only the account
    leaf and carry no surcharge (see ``test_extcodehash_empty_account``). A
    client that skipped the second read for code-less accounts would be
    caught here.
    """
    # Never deployed: no code, no balance, non-existent account.
    empty_addr = pre.nonexistent_account()

    measured_code = opcode(address=empty_addr)
    # Subtract the opcode's OWN cold cost so the CodeGasMeasure overhead is
    # only the operand PUSH wrapper; the surcharge is part of the cold cost.
    overhead_cost = measured_code.gas_cost(fork) - opcode(
        address_warm=False
    ).gas_cost(fork)

    code_gas_measure = CodeGasMeasure(
        code=measured_code,
        overhead_cost=overhead_cost,
        extra_stack_items=opcode.pushed_stack_items,
    )
    measure_address = pre.deploy_contract(code=code_gas_measure)
    expected_gas = opcode(address_warm=warm).gas_cost(fork)

    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        access_list=[AccessList(address=empty_addr, storage_keys=[])]
        if warm
        else None,
    )

    post = {measure_address: Account(storage={0: expected_gas})}

    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
def test_extcodesize_empty_account_returns_zero(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    warm: bool,
) -> None:
    """
    Pay the surcharge on an empty target while ``EXTCODESIZE`` returns 0.

    The size returned for an empty/non-existent account is ``0``, which
    confirms the target genuinely has no code: the measured
    ``COLD_ACCOUNT_ACCESS + WARM_ACCESS`` (cold) / ``2 * WARM_ACCESS``
    (warm) cost is therefore unambiguously the surcharge applied to an
    empty account, not an artifact of the target accidentally holding code.
    """
    # Never deployed: no code, no balance, non-existent account.
    empty_addr = pre.nonexistent_account()

    expected_gas = Op.EXTCODESIZE(address_warm=warm).gas_cost(fork)

    # Measure the access cost and, separately, store the returned size so
    # the empty-account 0 result is asserted alongside the pricing. The
    # measured opcode carries the runtime warmth so the overhead reduces to
    # the address PUSH alone.
    storage = Storage()
    measured_code = Op.EXTCODESIZE.with_metadata(address_warm=warm)(empty_addr)
    gas_slot = storage.store_next(expected_gas, "extcodesize_empty_gas")
    size_slot = storage.store_next(0, "extcodesize_empty_size")
    code = CodeGasMeasure(
        code=measured_code,
        overhead_cost=measured_code.gas_cost(fork)
        - Op.EXTCODESIZE(address_warm=warm).gas_cost(fork),
        extra_stack_items=1,
        sstore_key=gas_slot,
    ) + Op.SSTORE(size_slot, Op.EXTCODESIZE(empty_addr))
    measure_address = pre.deploy_contract(code=code)

    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        access_list=[AccessList(address=empty_addr, storage_keys=[])]
        if warm
        else None,
    )

    post = {measure_address: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@EIPChecklist.GasCostChanges.Test.GasUpdatesMeasurement()
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
@pytest.mark.parametrize(
    "copy_size", [32, 96], ids=["one_word", "three_words"]
)
def test_extcodecopy_empty_account_composes_additively(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    fork: Fork,
    warm: bool,
    copy_size: int,
) -> None:
    """
    Compose the surcharge additively when copying from an empty account.

    ``EXTCODECOPY`` of a non-existent source copies zero bytes into memory,
    yet still charges the account-access cost, the EIP-8038 code-read
    ``WARM_ACCESS`` surcharge, the EIP-150 per-word copy cost
    (``OPCODE_COPY_PER_WORD`` per word, driven by the requested size, not
    the source length), and the memory-expansion cost. The measured gas
    must equal the sum of all four components, confirming the surcharge
    composes additively even when there is no code to read.
    """
    # Empty source: never deployed, no code. The copy yields zeros, but the
    # cost is driven by the requested size, identical to a code-bearing
    # source of the same length.
    empty_addr = pre.nonexistent_account()

    oracle = Op.EXTCODECOPY.with_metadata(
        address_warm=warm,
        data_size=copy_size,
        new_memory_size=copy_size,
        old_memory_size=0,
    )
    measured_code = oracle(
        address=empty_addr, dest_offset=0, offset=0, size=copy_size
    )

    expected_gas = oracle.gas_cost(fork)

    code_gas_measure = CodeGasMeasure(
        code=measured_code,
        overhead_cost=measured_code.gas_cost(fork) - oracle.gas_cost(fork),
        extra_stack_items=0,
    )
    measure_address = pre.deploy_contract(code=code_gas_measure)

    tx = Transaction(
        to=measure_address,
        sender=pre.fund_eoa(),
        access_list=[AccessList(address=empty_addr, storage_keys=[])]
        if warm
        else None,
    )

    post = {measure_address: Account(storage={0: expected_gas})}
    state_test(env=env, pre=pre, post=post, tx=tx)
