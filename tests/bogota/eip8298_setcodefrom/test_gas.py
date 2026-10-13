"""Test the gas cost and access warming of the `SETCODEFROM` opcode."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BlockAccessListExpectation,
    Bytecode,
    CodeGasMeasure,
    EIPChecklist,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
    TransactionReceipt,
)

from .helpers import (
    RESULT_SLOT,
    SENTINEL,
    SSTORE_MARKER_A,
    SSTORE_MARKER_B,
    adopt_code,
    call_with,
    multi_code,
    word,
)
from .spec import ref_spec_8298

REFERENCE_SPEC_GIT_PATH = ref_spec_8298.git_path
REFERENCE_SPEC_VERSION = ref_spec_8298.version

pytestmark = pytest.mark.valid_from("EIP8298")


def deploy_caller(
    pre: Alloc,
    *,
    adopter: Address,
    source: Address | None,
    gas: int,
    warm: bool = False,
) -> Address:
    """Deploy a caller that stores the result of a `gas`-budgeted call."""
    prewarm = Bytecode()
    if warm:
        assert source is not None, "warm prewarm needs a source address"
        prewarm = Op.POP(Op.BALANCE(source))
    return pre.deploy_contract(
        prewarm
        + Op.SSTORE(RESULT_SLOT, call_with(adopter, source, gas=gas))
        + Op.STOP,
        storage={RESULT_SLOT: SENTINEL},
    )


@pytest.mark.parametrize(
    "delta",
    [
        pytest.param(
            -1,
            id="oog",
            marks=[
                EIPChecklist.Opcode.Test.GasUsage.OutOfGasExecution(),
                EIPChecklist.Opcode.Test.GasUsage.OrderOfOperations.Oog(),
            ],
        ),
        pytest.param(
            0,
            id="exact",
            marks=[
                EIPChecklist.Opcode.Test.GasUsage.Normal(),
                EIPChecklist.Opcode.Test.GasUsage.OrderOfOperations.Exact(),
            ],
        ),
        pytest.param(
            1, id="extra", marks=[EIPChecklist.Opcode.Test.GasUsage.ExtraGas()]
        ),
    ],
)
@pytest.mark.parametrize("warm", [False, True], ids=["cold", "warm"])
@pytest.mark.parametrize(
    "tier", ["nonexistent", "delegated", "valid_unchanged", "valid_changed"]
)
def test_gas_cost(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    tier: str,
    warm: bool,
    delta: int,
) -> None:
    """Verify the exact gas cost of each `SETCODEFROM` cost tier."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    code = adopt_code(
        address_warm=warm,
        source_valid=tier.startswith("valid"),
        code_changed=tier == "valid_changed",
    )
    adopter = pre.deploy_contract(code)
    if tier == "nonexistent":
        source = pre.nonexistent_account()
    elif tier == "delegated":
        source = pre.fund_eoa(delegation=template)
    elif tier == "valid_unchanged":
        source = pre.deploy_contract(code)
    elif tier == "valid_changed":
        source = template
    else:
        raise ValueError(f"unknown tier: {tier}")
    caller = deploy_caller(
        pre,
        adopter=adopter,
        source=source,
        gas=code.gas_cost(fork) + delta,
        warm=warm,
    )
    adopted = tier == "valid_changed" and delta >= 0

    state_test(
        pre=pre,
        post={
            caller: Account(storage={RESULT_SLOT: int(delta >= 0)}),
            adopter: Account(code=SSTORE_MARKER_A if adopted else code),
        },
        # An empty reservoir makes any state gas wrongly charged by
        # SETCODEFROM spill into the budget.
        tx=Transaction(
            sender=pre.fund_eoa(), to=caller, state_gas_reservoir=0
        ),
    )


@pytest.mark.parametrize("delta", [-1, 0], ids=["oog", "exact"])
def test_source_in_bal_once_source_gas_paid(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    delta: int,
) -> None:
    """Verify a valid source enters the BAL once the first charge is paid."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    # Priced as an invalid source, so the budget only covers the first
    # charge: one short skips the access, exact fails right after it.
    code = adopt_code(
        address_warm=False, source_valid=False, code_changed=False
    )
    adopter = pre.deploy_contract(code)
    caller = deploy_caller(
        pre, adopter=adopter, source=template, gas=code.gas_cost(fork) + delta
    )

    state_test(
        pre=pre,
        post={
            caller: Account(storage={RESULT_SLOT: 0}),
            adopter: Account(code=code),
        },
        tx=Transaction(
            sender=pre.fund_eoa(), to=caller, state_gas_reservoir=0
        ),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                template: BalAccountExpectation.empty() if delta == 0 else None
            }
        ),
    )


@pytest.mark.parametrize("size", [1, "max"])
def test_gas_independent_of_code_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    size: int | str,
) -> None:
    """Verify an adoption costs the same for any source code size."""
    if size == "max":
        code_size = fork.max_code_size()
    elif size == 1:
        code_size = 1
    else:
        raise ValueError(f"unknown size: {size}")
    source_code = Op.JUMPDEST * (code_size - 1) + Op.STOP
    source = pre.deploy_contract(source_code)
    code = adopt_code(address_warm=False, source_valid=True, code_changed=True)
    adopter = pre.deploy_contract(code)
    caller = deploy_caller(
        pre, adopter=adopter, source=source, gas=code.gas_cost(fork)
    )

    state_test(
        pre=pre,
        post={
            caller: Account(storage={RESULT_SLOT: 1}),
            adopter: Account(code=source_code),
        },
        tx=Transaction(
            sender=pre.fund_eoa(), to=caller, state_gas_reservoir=0
        ),
    )


@pytest.mark.parametrize(
    "source_kind", ["valid", "nonexistent", "delegated_eoa"]
)
def test_source_warm_after_attempt(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    source_kind: str,
) -> None:
    """Verify `source` is warm after any `SETCODEFROM` attempt."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    if source_kind == "valid":
        source = template
    elif source_kind == "nonexistent":
        source = pre.nonexistent_account()
    elif source_kind == "delegated_eoa":
        source = pre.fund_eoa(delegation=template)
    else:
        raise ValueError(f"unknown source_kind: {source_kind}")
    adopter = pre.deploy_contract(
        Op.POP(Op.SETCODEFROM(source))
        + CodeGasMeasure(code=Op.EXTCODEHASH(source), extra_stack_items=1)
        + Op.STOP
    )

    state_test(
        pre=pre,
        post={
            adopter: Account(
                storage={
                    0: Op.EXTCODEHASH(source, address_warm=True).gas_cost(fork)
                }
            ),
        },
        tx=Transaction(sender=pre.fund_eoa(), to=adopter),
    )


def test_delegated_source_target_stays_cold(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Verify a delegated source's target is neither resolved nor warmed."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    delegated = pre.fund_eoa(delegation=template)
    adopter = pre.deploy_contract(
        Op.SSTORE(RESULT_SLOT, Op.SETCODEFROM(delegated))
        + CodeGasMeasure(
            code=Op.EXTCODEHASH(template), extra_stack_items=1, sstore_key=1
        )
        + Op.STOP,
        storage={RESULT_SLOT: SENTINEL},
    )

    state_test(
        pre=pre,
        post={
            adopter: Account(
                storage={
                    RESULT_SLOT: 0,
                    1: Op.EXTCODEHASH(template, address_warm=False).gas_cost(
                        fork
                    ),
                }
            ),
        },
        tx=Transaction(sender=pre.fund_eoa(), to=adopter),
    )


@pytest.mark.parametrize("delta", [-1, 0], ids=["oog", "exact"])
def test_account_write_per_operation(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    delta: int,
) -> None:
    """Verify each code-changing adoption in a frame pays `ACCOUNT_WRITE`."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    template_b = pre.deploy_contract(SSTORE_MARKER_B)
    adopter = pre.deploy_contract(multi_code())
    twin = pre.deploy_contract(multi_code())
    gas = (
        multi_code(
            address_warm=False, source_valid=True, code_changed=True
        ).gas_cost(fork)
        + delta
    )
    caller = pre.deploy_contract(
        Op.MSTORE(0, template)
        + Op.MSTORE(32, twin)
        + Op.MSTORE(64, template_b)
        + Op.SSTORE(
            RESULT_SLOT, Op.CALL(gas=gas, address=adopter, args_size=96)
        )
        + Op.STOP,
        storage={RESULT_SLOT: SENTINEL},
    )

    state_test(
        pre=pre,
        post={
            caller: Account(storage={RESULT_SLOT: int(delta == 0)}),
            adopter: Account(
                code=SSTORE_MARKER_B if delta == 0 else multi_code()
            ),
        },
        tx=Transaction(
            sender=pre.fund_eoa(), to=caller, state_gas_reservoir=0
        ),
    )


@pytest.mark.parametrize("inner_reverts", [True, False])
def test_warmth_reverts_with_frame(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    inner_reverts: bool,
) -> None:
    """Verify source warming is discarded with a reverted frame."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    inner_code = Op.POP(Op.SETCODEFROM(template)) + (
        Op.REVERT(0, 0) if inner_reverts else Op.STOP
    )
    inner = pre.deploy_contract(inner_code)
    outer = pre.deploy_contract(
        Op.POP(call_with(inner))
        + CodeGasMeasure(code=Op.EXTCODEHASH(template), extra_stack_items=1)
        + Op.STOP
    )
    measured = Op.EXTCODEHASH(
        template, address_warm=not inner_reverts
    ).gas_cost(fork)

    state_test(
        pre=pre,
        post={
            outer: Account(storage={0: measured}),
            inner: Account(
                code=inner_code if inner_reverts else SSTORE_MARKER_A
            ),
        },
        tx=Transaction(sender=pre.fund_eoa(), to=outer),
    )


@pytest.mark.parametrize("delta", [-1, 0, 1], ids=["oog", "exact", "extra"])
def test_initcode_adoption_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    delta: int,
) -> None:
    """
    Verify an adopting creation pays account creation and the `RETURN`
    memory expansion but no deposit, and fails one gas short.
    """
    template = pre.deploy_contract(SSTORE_MARKER_A)
    initcode = Op.POP(
        Op.SETCODEFROM(
            template, address_warm=False, source_valid=True, code_changed=True
        )
    ) + Op.RETURN(0, 32, new_memory_size=32)
    gas_used = (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=initcode,
            contract_creation=True,
            return_cost_deducted_prior_execution=True,
        )
        + fork.transaction_top_frame_state_gas(contract_creation=True)
        + initcode.gas_cost(fork)
    )
    floor = fork.transaction_data_floor_cost_calculator()(
        data=initcode, contract_creation=True
    )
    assert floor < gas_used, "the calldata floor must not bind"
    created = delta >= 0
    gas_limit = gas_used + delta
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=None,
        data=initcode,
        gas_limit=gas_limit,
        state_gas_reservoir=0,
        # Running out of gas consumes the whole limit.
        expected_receipt=TransactionReceipt(
            cumulative_gas_used=gas_used if created else gas_limit
        ),
    )

    state_test(
        pre=pre,
        post={
            tx.created_contract: (
                Account(code=SSTORE_MARKER_A, nonce=1)
                if created
                else Account.NONEXISTENT
            )
        },
        tx=tx,
    )


@pytest.mark.with_all_precompiles
@pytest.mark.parametrize("delta", [-1, 0], ids=["oog", "exact"])
def test_precompile_source(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    precompile: Address,
    delta: int,
) -> None:
    """Verify a precompile is an always-warm, invalid source."""
    code = adopt_code(
        address_warm=True, source_valid=False, code_changed=False
    )
    adopter = pre.deploy_contract(code)
    caller = deploy_caller(
        pre,
        adopter=adopter,
        source=precompile,
        gas=code.gas_cost(fork) + delta,
    )

    state_test(
        pre=pre,
        post={
            caller: Account(storage={RESULT_SLOT: int(delta == 0)}),
            adopter: Account(code=code),
        },
        tx=Transaction(
            sender=pre.fund_eoa(), to=caller, state_gas_reservoir=0
        ),
        expected_block_access_list=BlockAccessListExpectation(
            account_expectations={
                precompile: (
                    BalAccountExpectation.empty() if delta == 0 else None
                )
            }
        ),
    )


@pytest.mark.parametrize("delta", [-1, 0], ids=["oog", "exact"])
def test_self_source_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    delta: int,
) -> None:
    """Verify adopting from the current account is a warm, unchanged hash."""
    code = (
        Op.SETCODEFROM(
            Op.ADDRESS,
            address_warm=True,
            source_valid=True,
            code_changed=False,
        )
        + Op.STOP
    )
    adopter = pre.deploy_contract(code)
    caller = deploy_caller(
        pre, adopter=adopter, source=None, gas=code.gas_cost(fork) + delta
    )

    state_test(
        pre=pre,
        post={
            caller: Account(storage={RESULT_SLOT: int(delta == 0)}),
            adopter: Account(code=code),
        },
        tx=Transaction(
            sender=pre.fund_eoa(), to=caller, state_gas_reservoir=0
        ),
    )


@pytest.mark.parametrize("delta", [-1, 0], ids=["oog", "exact"])
def test_account_write_on_written_account(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    delta: int,
) -> None:
    """Verify adopting into an account the tx already wrote pays in full."""
    template = pre.deploy_contract(SSTORE_MARKER_A)
    code = adopt_code(address_warm=False, source_valid=True, code_changed=True)
    adopter = pre.deploy_contract(code)
    calldata = word(template)
    gas_limit = (
        fork.transaction_intrinsic_cost_calculator()(
            calldata=calldata,
            sends_value=True,
            return_cost_deducted_prior_execution=True,
        )
        + fork.transaction_top_frame_execution_gas(sends_value=True)
        + fork.transaction_top_frame_state_gas(sends_value=True)
        + code.gas_cost(fork)
        + delta
    )
    floor = fork.transaction_data_floor_cost_calculator()(
        data=calldata, sends_value=True
    )
    assert floor < gas_limit, "the calldata floor must not bind"
    adopted = delta == 0

    state_test(
        pre=pre,
        post={
            adopter: Account(
                code=SSTORE_MARKER_A if adopted else code, balance=int(adopted)
            ),
        },
        tx=Transaction(
            sender=pre.fund_eoa(),
            to=adopter,
            value=1,
            data=calldata,
            gas_limit=gas_limit,
            state_gas_reservoir=0,
        ),
    )
