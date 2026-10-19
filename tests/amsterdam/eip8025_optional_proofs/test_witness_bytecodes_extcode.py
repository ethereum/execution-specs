"""Witness bytecode scenarios for EXTCODE* opcodes."""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    ExecutionWitnessCodesExpectation,
    Fork,
    Op,
    RecipientType,
    Transaction,
)

from .spec import ref_spec_8025

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = ref_spec_8025.git_path
REFERENCE_SPEC_VERSION = ref_spec_8025.version


@pytest.mark.parametrize(
    "extcode_access,target_read",
    [
        pytest.param("extcodesize", True, id="extcodesize"),
        pytest.param("extcodecopy", True, id="extcodecopy"),
        # TODO(zkevm): we will probably change this behavior since copying
        # zero bytes clearly doesn't need to read the code.
        pytest.param(
            "extcodecopy_zero_size", True, id="extcodecopy_zero_size"
        ),
        pytest.param("extcodehash", False, id="extcodehash"),
    ],
)
def test_witness_codes_extcode_contract(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    extcode_access: str,
    target_read: bool,
) -> None:
    """
    EXTCODE* on an existing contract without calling it.

    EXTCODESIZE and EXTCODECOPY call get_code(), which records the code
    read, so the target bytecode appears in executionWitness.codes. This
    holds even when copying zero bytes, because extcodecopy calls
    get_code() before using size for the memory copy. EXTCODEHASH reads
    the value from the account leaf without a code access, so the target
    bytecode does not appear.
    """
    target_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    target = pre.deploy_contract(code=target_code)

    if extcode_access == "extcodesize":
        access = Op.EXTCODESIZE(target) + Op.POP
    elif extcode_access == "extcodecopy":
        access = Op.EXTCODECOPY(target, 0, 0, 32)
    elif extcode_access == "extcodecopy_zero_size":
        access = Op.EXTCODECOPY(target, 0, 0, 0)
    elif extcode_access == "extcodehash":
        access = Op.EXTCODEHASH(target) + Op.POP
    else:
        raise ValueError(f"unknown EXTCODE* access: {extcode_access}")
    caller_code = access + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

    codes_present = [Bytes(caller_code)]
    codes_absent = []
    if target_read:
        codes_present.append(Bytes(target_code))
    else:
        codes_absent.append(Bytes(target_code))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=codes_present,
                        codes_absent=codes_absent,
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )


@pytest.mark.parametrize(
    "extcode_opcode",
    [
        pytest.param("extcodesize", id="extcodesize"),
        pytest.param("extcodecopy", id="extcodecopy"),
    ],
)
def test_witness_codes_extcode_empty_code(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    extcode_opcode: str,
) -> None:
    """
    EXTCODESIZE or EXTCODECOPY on an account with empty code (an EOA).

    The target has EMPTY_CODE_HASH, so get_code() returns early without
    recording a code read.  Nothing should be added to
    executionWitness.codes for the target.
    """
    eoa_target = pre.fund_eoa()

    if extcode_opcode == "extcodesize":
        access = Op.EXTCODESIZE(eoa_target) + Op.POP
    elif extcode_opcode == "extcodecopy":
        access = Op.EXTCODECOPY(eoa_target, 0, 0, 32)
    else:
        raise ValueError(f"unknown EXTCODE* opcode: {extcode_opcode}")
    caller_code = access + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[Bytes(caller_code)],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )


@pytest.mark.parametrize(
    "gas_delta,expect_in_witness",
    [
        pytest.param(
            -1,
            False,
            id="oog",
        ),
        pytest.param(
            0,
            True,
            id="just_enough",
        ),
    ],
)
def test_witness_codes_extcodesize_cold_gas_boundary(
    fork: Fork,
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    gas_delta: int,
    expect_in_witness: bool,
) -> None:
    """
    EXTCODESIZE at the exact gas boundary for cold account access.

    When gas is one short of covering PUSH20 + EXTCODESIZE-cold, the
    opcode OOGs before reaching get_code() and the target code is NOT
    recorded.  With exactly enough gas the code read succeeds and the
    target IS in the witness.  The caller's code appears in both cases
    because it was already read via get_code() when entering the call,
    and code_reads survives transaction rollback.
    """
    target_code = Op.PUSH1(0x42) + Op.POP + Op.STOP
    target = pre.deploy_contract(code=target_code)

    extcodesize_code = Op.EXTCODESIZE(target)
    caller_code = extcodesize_code + Op.POP + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    tx_intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        recipient_type=RecipientType.CONTRACT,
        return_cost_deducted_prior_execution=True,
    )
    gas_limit = tx_intrinsic_gas + extcodesize_code.gas_cost(fork) + gas_delta

    sender = pre.fund_eoa()
    tx = Transaction(
        sender=sender,
        to=caller,
        gas_limit=gas_limit,
    )

    codes_present = [Bytes(caller_code)]
    codes_absent = []
    if expect_in_witness:
        codes_present.append(Bytes(target_code))
    else:
        codes_absent.append(Bytes(target_code))

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=codes_present,
                        codes_absent=codes_absent,
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )


@pytest.mark.with_all_precompiles()
@pytest.mark.parametrize(
    "extcode_opcode",
    [
        pytest.param("extcodesize", id="extcodesize"),
        pytest.param("extcodecopy", id="extcodecopy"),
    ],
)
def test_witness_codes_extcode_precompile(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    precompile: Address,
    extcode_opcode: str,
) -> None:
    """
    Read code metadata of a precompile via EXTCODESIZE or EXTCODECOPY.

    Precompiles have EMPTY_CODE_HASH, so code tracking returns early
    without recording a code read.  The witness must contain only
    the caller and system contract bytecodes — nothing for the
    precompile.
    """
    if extcode_opcode == "extcodesize":
        op = Op.EXTCODESIZE(precompile) + Op.POP
    else:
        op = Op.EXTCODECOPY(precompile, 0, 0, 32)

    caller_code = op + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=caller, gas_limit=500_000)

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[Bytes(caller_code)],
                    )
                ),
            )
        ],
        post={
            sender: Account(nonce=1),
        },
    )
