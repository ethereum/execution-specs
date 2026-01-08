"""
Tests for EIP-214 STATICCALL opcode behavior.

STATICCALL creates a read-only call context where state-modifying operations
are forbidden. This includes CALL with non-zero value to any address.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Op,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Byzantium
from execution_testing.forks.helpers import Fork

from .spec import ref_spec_214

REFERENCE_SPEC_GIT_PATH = ref_spec_214.git_path
REFERENCE_SPEC_VERSION = ref_spec_214.version

pytestmark = [
    pytest.mark.valid_from("Byzantium"),
]


def _issue683_legacy_bytecode() -> bytes:
    """
    Original bytecode from the legacy test, using stack-optimized DUP
    operations.

    Source: https://github.com/dapphub/dapptools/pull/360
    Issue: https://github.com/ethereum/tests/issues/683

    Execution flow:
    1. Outer call (S[0]=0): skip reentry check → store S[0]=1 → STATICCALL
       to self
    2. Inner call (S[0]=1, static ctx): reentry detected → CALL with
       value=1 → reverts
    3. Back in outer: STATICCALL returned 0 (failed) → STOP

    Result: S[0]=1 persists, proving CALL-with-value in static context fails.
    """
    target_code_raw = bytes.fromhex(
        "600080541515601d576001815580818283305afa15601b578081fd5b005b"
        "80818283600160025af15050"
    )

    target_code = (
        # Check if storage[0] != 0 (reentry detection), jump to 0x1d if true
        Op.PUSH1[0x0]  # [0x00]
        + Op.DUP1  # [0x00, 0x00]
        + Op.SLOAD  # [S[0], 0x00]
        + Op.ISZERO  # [S[0]==0, 0x00]
        + Op.ISZERO  # [S[0]!=0, 0x00]
        + Op.PUSH1[0x1D]  # [0x1D, S[0]!=0, 0x00]
        + Op.JUMPI  # [0x00] - jump to 0x1D if S[0]!=0
        # First call: store 1 at slot 0, then STATICCALL to self
        + Op.PUSH1[0x1]  # [0x01, 0x00]
        + Op.DUP2  # [0x00, 0x01, 0x00]
        + Op.SSTORE  # [0x00] - S[0] = 1
        + Op.DUP1  # [0x00, 0x00]
        + Op.DUP2  # [0x00, 0x00, 0x00]
        + Op.DUP3  # [0x00, 0x00, 0x00, 0x00]
        + Op.DUP4  # [0x00, 0x00, 0x00, 0x00, 0x00]
        + Op.ADDRESS  # [ADDR, 0x00, 0x00, 0x00, 0x00, 0x00]
        + Op.GAS  # [GAS, ADDR, 0x00, 0x00, 0x00, 0x00, 0x00]
        + Op.STATICCALL  # [success, 0x00]
        # If STATICCALL failed (returned 0), jump to 0x1b (STOP)
        + Op.ISZERO  # [success==0, 0x00]
        + Op.PUSH1[0x1B]  # [0x1B, success==0, 0x00]
        + Op.JUMPI  # [0x00] - jump to 0x1B if failed
        # If STATICCALL succeeded, REVERT (should not happen)
        + Op.DUP1  # [0x00, 0x00]
        + Op.DUP2  # [0x00, 0x00, 0x00]
        + Op.REVERT  # revert(0, 0)
        # 0x1b: STOP path
        + Op.JUMPDEST  # [0x00]
        + Op.STOP
        # 0x1d: Reentry path - CALL to precompile 0x02 with value=1
        + Op.JUMPDEST  # [0x00] - jumped here because S[0]!=0
        + Op.DUP1  # [0x00, 0x00]
        + Op.DUP2  # [0x00, 0x00, 0x00]
        + Op.DUP3  # [0x00, 0x00, 0x00, 0x00]
        + Op.DUP4  # [0x00, 0x00, 0x00, 0x00, 0x00]
        + Op.PUSH1[0x1]  # [0x01, 0x00, 0x00, 0x00, 0x00, 0x00] - value
        + Op.PUSH1[0x2]  # [0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00] - addr
        + Op.GAS  # [GAS, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00]
        + Op.CALL  # [success, 0x00] - fails in static context
        + Op.POP  # [0x00]
        + Op.POP  # []
    )
    assert bytes(target_code) == target_code_raw
    return bytes(target_code)


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stStaticFlagEnabled/StaticcallForPrecompilesIssue683Filler.yml"
    ],  # noqa: E501
)
def test_staticcall_reentrant_call_with_value_to_precompile_issue683(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
) -> None:
    """
    Regression test for ethereum/tests#683.

    CALL with value inside STATICCALL fails (static context violation).
    Uses the original stack-optimized bytecode to verify exact legacy behavior.
    """
    alice = pre.fund_eoa()

    target_code = _issue683_legacy_bytecode()

    target_balance = 1000
    target = pre.deploy_contract(code=target_code, balance=target_balance)

    tx_value = 100
    tx = Transaction(
        sender=alice,
        to=target,
        gas_limit=1_000_000,
        value=tx_value,
        protected=fork >= Byzantium,
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={
            target: Account(
                balance=target_balance + tx_value,
                storage={0: 1},
            ),
        },
    )


@pytest.mark.with_all_precompiles
@pytest.mark.parametrize(
    "call_value", [0, 2], ids=["zero_value", "nonzero_value"]
)
def test_staticcall_reentrant_call_with_value_to_precompile(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    precompile: Address,
    call_value: int,
) -> None:
    """
    Test CALL to precompile inside STATICCALL with zero and non-zero value.
    source: https://github.com/ethereum/execution-specs/pull/1960#discussion_r2656834142.

    A single contract STATICCALLs itself. On reentry (detected via CALLVALUE=0,
    since STATICCALL doesn't forward value), it attempts CALL to a precompile.

    - call_value=0: CALL succeeds in static context → STATICCALL returns 1
    - call_value>0: CALL violates static context, reverts frame → STATICCALL
      returns 0
    """
    alice = pre.fund_eoa()

    pc_placeholder = 0xFF

    # if CALLVALUE == 0 (inside STATICCALL), jump to reentry path
    entry_check = Op.JUMPI(pc_placeholder, Op.ISZERO(Op.CALLVALUE))

    # STATICCALL to self, store result (0=fail, 1=success), stop
    first_call = Op.SSTORE(0, Op.STATICCALL(address=Op.ADDRESS)) + Op.STOP

    # try CALL with parametrized value (fails in static context if value > 0)
    reentry_path = Op.JUMPDEST + Op.CALL(address=precompile, value=call_value)

    # Calculate actual PC and verify it fits in PUSH1
    pc = len(entry_check) + len(first_call)
    assert len(Op.PUSH1[pc]) == len(Op.PUSH1[pc_placeholder])

    # Rebuild with correct PC
    entry_check = Op.JUMPI(pc, Op.ISZERO(Op.CALLVALUE))

    target_code = bytes(entry_check + first_call + reentry_path)

    target_balance = 1000
    target = pre.deploy_contract(code=target_code, balance=target_balance)

    tx_value = 100
    tx = Transaction(
        sender=alice,
        to=target,
        gas_limit=1_000_000,
        value=tx_value,
        protected=fork >= Byzantium,
    )

    blockchain_test(
        pre=pre,
        blocks=[Block(txs=[tx])],
        post={
            target: Account(
                balance=target_balance + tx_value,
                storage={0: 1 if call_value == 0 else 0},
            ),
        },
    )


@pytest.mark.with_all_precompiles
@pytest.mark.parametrize(
    "call_value", [0, 2], ids=["zero_value", "nonzero_value"]
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stStaticFlagEnabled/CallWithZeroValueToPrecompileFromTransactionFiller.yml",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stStaticFlagEnabled/CallWithNOTZeroValueToPrecompileFromTransactionFiller.yml",
    ],
)
def test_staticcall_call_to_precompile(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    precompile: Address,
    call_value: int,
) -> None:
    """
    Test CALL to precompile inside STATICCALL with zero and non-zero value.

    Contract A STATICCALLs contract B. Contract B attempts to CALL precompile.
    With value = 0, this succeeds. With value > 0, this fails (static context).
    """
    alice = pre.fund_eoa()

    initial_contract_balance = 1000
    marker = 0xFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEED

    # Contract B: attempts CALL to precompile with the parametrized value
    contract_b = pre.deploy_contract(
        code=Op.CALL(gas=100_000, address=precompile, value=call_value),
        balance=initial_contract_balance,
    )

    # Contract A: STATICCALLs contract B and stores the result
    contract_a = pre.deploy_contract(
        code=(
            Op.SSTORE(0, marker)
            + Op.SSTORE(1, Op.STATICCALL(gas=200_000, address=contract_b))
            + Op.SSTORE(2, marker)
        ),
        balance=initial_contract_balance,
    )

    tx_value = 100

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=alice,
                        to=contract_a,
                        gas_limit=500_000,
                        value=tx_value,
                        protected=fork >= Byzantium,
                    )
                ]
            )
        ],
        post={
            contract_a: Account(
                balance=initial_contract_balance + tx_value,
                storage={
                    0: marker,
                    # only succeeds if call_value == 0
                    1: 1 if call_value == 0 else 0,
                    2: marker,
                },
            ),
            contract_b: Account(balance=initial_contract_balance),
        },
    )


@pytest.mark.with_all_precompiles
@pytest.mark.parametrize(
    "call_value", [0, 2], ids=["zero_value", "nonzero_value"]
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stStaticFlagEnabled/CallWithZeroValueToPrecompileFromCalledContractFiller.yml",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stStaticFlagEnabled/CallWithNOTZeroValueToPrecompileFromCalledContractFiller.yml",
    ],
)
def test_staticcall_nested_call_to_precompile(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    precompile: Address,
    call_value: int,
) -> None:
    """
    Test STATICCALL behavior with an extra call depth layer.

    Contract B (target) receives tx and CALLs contract A.
    Contract A STATICCALLs contract C.
    Contract C attempts to CALL the precompile.
    With value = 0, this succeeds. With value > 0, this fails (static context).
    """
    alice = pre.fund_eoa()

    initial_contract_balance = 1000
    marker = 0xFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEED

    # Contract C: attempts CALL to precompile with the parametrized value
    contract_c = pre.deploy_contract(
        code=Op.CALL(gas=100_000, address=precompile, value=call_value),
        balance=initial_contract_balance,
    )

    # Contract A: STATICCALLs contract C, stores markers and result
    contract_a = pre.deploy_contract(
        code=(
            Op.SSTORE(0, marker)
            + Op.SSTORE(1, Op.STATICCALL(gas=200_000, address=contract_c))
            + Op.SSTORE(2, marker)
        ),
        balance=initial_contract_balance,
    )

    # Contract B (target): CALLs contract A, stores markers and result
    contract_b = pre.deploy_contract(
        code=(
            Op.SSTORE(0, marker)
            + Op.SSTORE(1, Op.CALL(gas=300_000, address=contract_a))
            + Op.SSTORE(2, marker)
        ),
        balance=initial_contract_balance,
    )

    tx_value = 100

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=alice,
                        to=contract_b,
                        gas_limit=500_000,
                        value=tx_value,
                        protected=True,
                    )
                ]
            )
        ],
        post={
            contract_a: Account(
                balance=initial_contract_balance,
                storage={
                    0: marker,
                    # only succeeds if call_value == 0
                    1: 1 if call_value == 0 else 0,
                    2: marker,
                },
            ),
            contract_b: Account(
                balance=initial_contract_balance + tx_value,
                storage={
                    0: marker,
                    1: 1,  # CALL to A always succeeds
                    2: marker,
                },
            ),
            contract_c: Account(balance=initial_contract_balance),
        },
    )


@pytest.mark.with_all_precompiles
@pytest.mark.parametrize(
    "call_value", [0, 2], ids=["zero_value", "nonzero_value"]
)
@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stStaticFlagEnabled/CallWithZeroValueToPrecompileFromContractInitializationFiller.yml",
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/stStaticFlagEnabled/CallWithNOTZeroValueToPrecompileFromContractInitializationFiller.yml",
    ],
)
@pytest.mark.parametrize("create_opcode", [Op.CREATE, Op.CREATE2])
def test_staticcall_call_to_precompile_from_contract_init(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
    precompile: Address,
    call_value: int,
    create_opcode: Op,
) -> None:
    """
    Test STATICCALL behavior during contract initialization (CREATE).

    Contract A CREATEs a new contract whose init code STATICCALLs contract B.
    Contract B attempts to CALL the precompile.
    With value = 0, this succeeds. With value > 0, this fails in static
    context.
    """
    alice = pre.fund_eoa()
    marker = 0xFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEED

    contract_initial_balance = 1000

    # Contract B: attempts CALL to precompile with the parametrized value
    contract_b = pre.deploy_contract(
        code=Op.CALL(gas=100_000, address=precompile, value=call_value),
        balance=contract_initial_balance,
    )

    # Init code: stores markers and STATICCALL result during initialization
    # Note: storage written during init but no return means the created
    # contract will have empty code.
    initcode = (
        Op.SSTORE(0, marker)
        + Op.SSTORE(1, Op.STATICCALL(gas=200_000, address=contract_b))
        + Op.SSTORE(2, marker)
    )

    # Contract A: CREATEs new contract using init_code from calldata
    contract_a = pre.deploy_contract(
        code=(
            Op.SSTORE(0, marker)
            + Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
            + Op.SSTORE(
                1,
                create_opcode(value=0, offset=0, size=Op.CALLDATASIZE),
            )
            + Op.SSTORE(2, marker)
        ),
        balance=contract_initial_balance,
    )
    created_contract = compute_create_address(
        nonce=1,
        address=contract_a,
        opcode=create_opcode,
        initcode=initcode,
    )

    tx_value = 100
    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=alice,
                        to=contract_a,
                        gas_limit=4_000_000,
                        value=tx_value,
                        data=bytes(initcode),
                        protected=True,
                    )
                ]
            )
        ],
        post={
            contract_a: Account(
                balance=contract_initial_balance + tx_value,
                storage={0: marker, 1: created_contract, 2: marker},
            ),
            created_contract: Account(
                storage={
                    0: marker,
                    # only succeeds if call_value == 0
                    1: 1 if call_value == 0 else 0,
                    2: marker,
                },
                code=b"",
            ),
            contract_b: Account(balance=contract_initial_balance),
        },
    )
