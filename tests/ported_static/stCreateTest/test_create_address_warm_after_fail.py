"""
Invokes failing CREATE (because initcode fails) and checks.

if the create address is considered warm in the follow up call as required by
EIP-2929.
Addresses taken from https://toolkit.abdk.consulting/ethereum#contract-address

Written primarily by Paweł Bylica (@chfast). Somewhat modified by Ori (@qbzzt)

Ported from:
state_tests/stCreateTest/CreateAddressWarmAfterFailFiller.yml

@manually-enhanced: Do not overwrite. The post-state records the
measured cost of accessing the create address after a failed CREATE,
which is a cold account access. EIP-8038 reprices a cold account
access from 2 600 to 3 000, so each such measurement gains 400 at
Amsterdam. Derive that delta from the fork's gas model so it is
exactly 0 pre-EIP-8037 and tracks parameter changes; do not hardcode
the Amsterdam value.
"""

from typing import NamedTuple

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    CodeGasMeasure,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Bytecode, Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CREATE_RESULT_SLOT = 0
CALL_RESULT_SLOT = 1
FIRST_CREATED_CALL_COST_SLOT = 2


def create_from(*, create_opcode: Op, initcode: Bytecode) -> Bytecode:
    """Place `initcode` at memory 0 and CREATE, or CREATE2, from it."""
    return Op.MSTORE(
        offset=0,
        value=Op.PUSH32[Hash(initcode, right_padding=True)],
    ) + Op.SSTORE(
        CREATE_RESULT_SLOT,
        create_opcode(value=0, offset=0, size=len(initcode)),
    )


class CaseOutcome(NamedTuple):
    """
    The facts a case's post-state follows from.

    `create_result` is what slot 0 records, where `None` stands for the
    probed address itself.
    """

    create_result_stored: bool
    call_result: int
    probed_deployed_code: Bytecode | None
    probed_warm: bool
    entry_nonce_bump: bool


# The entry contract's own create fails: EIP-2929 keeps the create
# address warm, and the nonce bump outlives the child frame's failure.
CREATE_FAILED = CaseOutcome(
    create_result_stored=False,
    call_result=0,
    probed_deployed_code=None,
    probed_warm=True,
    entry_nonce_bump=True,
)
# The create succeeds, so slot 0 records the address it deployed to.
CREATE_SUCCEEDED = CaseOutcome(
    create_result_stored=True,
    call_result=0,
    probed_deployed_code=Op.STOP,
    probed_warm=True,
    entry_nonce_bump=True,
)
# A callee ran the create and died out of gas, so its rollback took the
# warmed create address with it and its CALL reports failure.
CALLEE_OUT_OF_GAS = CaseOutcome(
    create_result_stored=False,
    call_result=0,
    probed_deployed_code=None,
    probed_warm=False,
    entry_nonce_bump=False,
)
# A callee ran the create and died out of gas, so its rollback took the
# warmed create address with it and its CALL reports failure.
CONSTRUCTOR_OUT_OF_GAS = CaseOutcome(
    create_result_stored=False,
    call_result=1,
    probed_deployed_code=None,
    probed_warm=True,
    entry_nonce_bump=False,
)
# A callee could not create at all, so it returns normally and its CALL
# reports success, but nothing ever warmed the create address.
CALLEE_COULD_NOT_CREATE = CaseOutcome(
    create_result_stored=False,
    call_result=1,
    probed_deployed_code=None,
    probed_warm=False,
    entry_nonce_bump=False,
)


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateAddressWarmAfterFailFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("value", [0, 1], ids=["v0", "v1"])
@pytest.mark.with_all_create_opcodes
@pytest.mark.parametrize(
    "initcode_outcome",
    [
        "contructor-revert",
        "code-too-big",
        "invalid-opcode",
        "oog-constructor",
        "oog-post-constr",
        "high-nonce",
        "0xef",
        "success",
    ],
)
def test_create_address_warm_after_fail(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    value: int,
    initcode_outcome: str,
    create_opcode: Op,
) -> None:
    """
    Invokes failing CREATE (because initcode fails) and checks
    if the contract address that was supposed to be created is warm after the
    attempt.
    """
    sender = pre.fund_eoa()

    create_attempt: Bytecode
    creator_address: Address | None = None
    creator_nonce = 1
    initcode: Bytecode

    if initcode_outcome == "contructor-revert":
        initcode = Op.REVERT(0, 0)
        create_attempt = create_from(
            create_opcode=create_opcode, initcode=initcode
        )
        outcome = CREATE_FAILED

    elif initcode_outcome == "code-too-big":
        initcode = Op.RETURN(
            offset=0x0,
            size=fork.max_code_size() + 1,
            new_memory_size=fork.max_code_size() + 1,
            code_deposit_size=fork.max_code_size() + 1,
        )
        create_attempt = create_from(
            create_opcode=create_opcode, initcode=initcode
        )
        outcome = CREATE_FAILED

    elif initcode_outcome == "invalid-opcode":
        initcode = Op.INVALID
        create_attempt = create_from(
            create_opcode=create_opcode, initcode=initcode
        )
        outcome = CREATE_FAILED

    elif initcode_outcome in ["oog-constructor", "oog-post-constr"]:
        deploy_size = 10
        initcode = Op.RETURN(
            offset=0,
            size=deploy_size,
            new_memory_size=deploy_size,
            code_deposit_size=deploy_size,
        )
        pre_create_code = Op.MSTORE(
            offset=0,
            value=Op.PUSH32[Hash(initcode, right_padding=True)],
            new_memory_size=32,
        ) + create_opcode(
            value=0,
            offset=0,
            size=len(initcode),
            init_code_size=len(initcode),
            account_new=True,
        )

        initcode_success_gas = pre_create_code.gas_cost(fork) + (
            initcode.gas_cost(fork) * 64 // 63
        )
        callee_code_suffix: Bytecode | Op
        if initcode_outcome == "oog-constructor":
            # Run OOG at the code deposit
            gas = initcode_success_gas - 1
            assert (
                (initcode_success_gas - pre_create_code.gas_cost(fork))
                * 63
                // 64
            ) < initcode.gas_cost(fork)
            callee_code_suffix = Op.STOP
            # Constructor runs out of gas, but the callee does the warming, so
            # is not reverted.
            outcome = CONSTRUCTOR_OUT_OF_GAS

        elif initcode_outcome == "oog-post-constr":
            # Run OOG at the JUMPDEST
            gas = initcode_success_gas
            callee_code_suffix = (
                Op.MSTORE(
                    2**12,
                    1,
                    old_memory_size=32,
                    new_memory_size=2**12,
                )
                + Op.STOP
            )
            assert callee_code_suffix.gas_cost(fork) > (
                gas
                - (pre_create_code.gas_cost(fork) + initcode.gas_cost(fork))
            )
            # Callee runs out of gas, the created contract warming is reverted.
            outcome = CALLEE_OUT_OF_GAS

        else:
            raise Exception(f"invalid initcode_outcome: {initcode_outcome}")

        callee_code = pre_create_code + callee_code_suffix
        creator_address = pre.deploy_contract(code=callee_code)

        create_attempt = Op.SSTORE(
            CALL_RESULT_SLOT,
            Op.CALL(gas=gas, address=creator_address),
        )

    elif initcode_outcome == "high-nonce":
        high_nonce = 2**64 - 1
        deploy_size = 10
        initcode = Op.RETURN(
            offset=0,
            size=deploy_size,
            new_memory_size=deploy_size,
            code_deposit_size=deploy_size,
        )
        pre_create_code = Op.MSTORE(
            offset=0,
            value=Op.PUSH32[Hash(initcode, right_padding=True)],
        ) + create_opcode(
            value=0,
            offset=0,
            size=len(initcode),
            init_code_size=len(initcode),
            account_new=True,
        )
        creator_address = pre.deploy_contract(
            code=pre_create_code + Op.STOP,
            nonce=high_nonce,
        )
        create_attempt = Op.SSTORE(
            CALL_RESULT_SLOT,
            Op.CALL(address=creator_address),
        )
        creator_nonce = high_nonce
        outcome = CALLEE_COULD_NOT_CREATE

    elif initcode_outcome == "0xef":
        initcode = Op.MSTORE8(offset=0, value=0xEF) + Op.RETURN(
            offset=0, size=1
        )
        create_attempt = create_from(
            create_opcode=create_opcode, initcode=initcode
        )
        outcome = CREATE_FAILED

    elif initcode_outcome == "success":
        initcode = Op.RETURN(
            offset=0x0,
            size=0x1,
            new_memory_size=0x1,
            code_deposit_size=0x1,
        )
        create_attempt = create_from(
            create_opcode=create_opcode, initcode=initcode
        )
        outcome = CREATE_SUCCEEDED

    else:
        raise ValueError(f"unhandled case: d={initcode_outcome}")

    call = Op.CALL(
        gas=0,
        address=Op.CALLDATALOAD(0),
        value=Op.CALLVALUE,
        address_warm=outcome.probed_warm,
        value_transfer=bool(value),
        account_new=bool(value) and outcome.probed_deployed_code is None,
    )
    measure_call = CodeGasMeasure(
        code=call,
        extra_stack_items=1,
        sstore_key=FIRST_CREATED_CALL_COST_SLOT,
    )
    entry_contract = pre.deploy_contract(
        code=create_attempt + measure_call + Op.STOP
    )
    if creator_address is None:
        creator_address = entry_contract

    probed_address = compute_create_address(
        address=creator_address,
        nonce=creator_nonce,
        initcode=initcode,
        opcode=create_opcode,
    )

    probed_post: Account | None = (
        Account(code=outcome.probed_deployed_code, balance=value, nonce=1)
        if outcome.probed_deployed_code
        else Account(code=b"", balance=value, nonce=0)
        if value != 0
        else Account.NONEXISTENT
    )

    gas_costs = fork.gas_costs()
    probe_cost = call.gas_cost(fork) - (gas_costs.CALL_STIPEND if value else 0)

    post = {
        sender: Account(nonce=1),
        entry_contract: Account(
            storage={
                CREATE_RESULT_SLOT: (
                    probed_address if outcome.create_result_stored else 0
                ),
                CALL_RESULT_SLOT: outcome.call_result,
                FIRST_CREATED_CALL_COST_SLOT: probe_cost,
            },
            nonce=1 + int(outcome.entry_nonce_bump),
        ),
        probed_address: probed_post,
    }

    tx = Transaction(
        sender=sender,
        to=entry_contract,
        data=Hash(probed_address, left_padding=True),
        state_gas_reservoir=0,
        value=value,
    )

    state_test(pre=pre, post=post, tx=tx)
