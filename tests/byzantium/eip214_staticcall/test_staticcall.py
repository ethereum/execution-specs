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

    Original bytecode from: https://github.com/dapphub/dapptools/pull/360
    Issue: https://github.com/ethereum/tests/issues/683
    """
    alice = pre.fund_eoa()

    target_code = bytes.fromhex(
        "600080541515601d576001815580818283305afa15601b578081fd5b005b"
        "80818283600160025af15050"
    )

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
