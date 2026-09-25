"""Witness bytecode scenarios for contract creation."""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Bytes,
    ExecutionWitnessCodesExpectation,
    Initcode,
    Op,
    Transaction,
    compute_create_address,
)

pytestmark = pytest.mark.valid_from("Amsterdam")

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


def test_witness_excludes_bytecode_created_in_same_block(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Deploy a contract via CREATE with no prior code access.

    The deployed runtime code should not appear in the execution
    witness.
    """
    runtime_code = bytes.fromhex("deadbeef")
    creator = pre.fund_eoa()
    created_contract = compute_create_address(address=creator, nonce=0)

    create_tx = Transaction(
        sender=creator,
        to=None,
        data=Initcode(deploy_code=runtime_code),
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[create_tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_absent=[Bytes(runtime_code)],
                    )
                ),
            )
        ],
        post={
            creator: Account(nonce=1),
            created_contract: Account(
                nonce=1,
                code=runtime_code,
            ),
        },
    )


def test_witness_keeps_prestate_code_read_even_if_later_created_with_same_hash(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Tx1 reads pre-state code, tx2 deploys the same runtime code hash.

    The pre-state bytecode should appear in executionWitness.codes
    because tx1 CALLs an existing pre-state contract with that code.
    """
    runtime_code = bytes(Op.PUSH1(0x00) + Op.PUSH1(0x00) + Op.RETURN)

    existing_contract = pre.deploy_contract(code=runtime_code)

    reader = pre.fund_eoa()
    creator = pre.fund_eoa()
    created_contract = compute_create_address(address=creator, nonce=0)

    tx1_read_existing_code = Transaction(
        sender=reader,
        to=existing_contract,
        gas_limit=200_000,
    )
    tx2_create_same_code_hash = Transaction(
        sender=creator,
        to=None,
        data=Initcode(deploy_code=runtime_code),
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    tx1_read_existing_code,
                    tx2_create_same_code_hash,
                ],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[Bytes(runtime_code)],
                    )
                ),
            )
        ],
        post={
            reader: Account(nonce=1),
            creator: Account(nonce=1),
            created_contract: Account(
                nonce=1,
                code=runtime_code,
            ),
        },
    )


def test_witness_codes_create2_excludes_new_bytecode(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Deploy a contract via CREATE2.

    The deployed runtime code should not appear in
    executionWitness.codes because it had no pre-state match.
    """
    runtime_code = bytes.fromhex("deadbeef")
    salt = 0
    initcode = Initcode(deploy_code=runtime_code)
    initcode_bytes = bytes(initcode)

    factory_code = (
        Op.MSTORE(0, Op.PUSH32(initcode_bytes))
        + Op.SSTORE(
            0,
            Op.CREATE2(
                value=0,
                offset=32 - len(initcode_bytes),
                size=len(initcode_bytes),
                salt=salt,
            ),
        )
        + Op.STOP
    )
    factory = pre.deploy_contract(code=factory_code)
    sender = pre.fund_eoa()

    created = compute_create_address(
        address=factory,
        nonce=1,
        salt=salt,
        initcode=initcode_bytes,
        opcode=Op.CREATE2,
    )

    tx = Transaction(
        sender=sender,
        to=factory,
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[Bytes(factory_code)],
                        codes_absent=[Bytes(runtime_code)],
                    )
                ),
            )
        ],
        post={
            created: Account(nonce=1, code=runtime_code),
        },
    )


def test_witness_codes_failed_create_includes_factory(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Execute a CREATE whose initcode fails via INVALID.

    The factory contract's code should appear in executionWitness.codes
    because it was read to execute the CREATE attempt, even though the
    creation failed. No new code is deployed.
    """
    failing_initcode = bytes(Op.INVALID)

    factory_code = (
        Op.MSTORE(0, Op.PUSH32(failing_initcode))
        + Op.SSTORE(
            0,
            Op.CREATE(
                offset=32 - len(failing_initcode),
                size=len(failing_initcode),
            ),
        )
        + Op.STOP
    )
    factory = pre.deploy_contract(code=factory_code)
    sender = pre.fund_eoa()

    tx = Transaction(
        sender=sender,
        to=factory,
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[Bytes(factory_code)],
                    )
                ),
            )
        ],
        post={
            factory: Account(
                storage={0: 0},
            ),
        },
    )


def test_witness_codes_create_then_call_same_block(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Create a contract in tx1 then CALL it in tx2 of the same block.

    The created contract's code should not appear in
    executionWitness.codes because it was written by tx1 thus known
    at tx2 execution time.
    """
    runtime_code = bytes(Op.STOP)

    creator = pre.fund_eoa()
    created = compute_create_address(address=creator, nonce=0)

    caller_code = Op.CALL(address=created) + Op.STOP
    caller = pre.deploy_contract(code=caller_code)

    caller2 = pre.fund_eoa()

    tx1_create = Transaction(
        sender=creator,
        to=None,
        data=Initcode(deploy_code=runtime_code),
        gas_limit=500_000,
    )
    tx2_call = Transaction(
        sender=caller2,
        to=caller,
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx1_create, tx2_call],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[Bytes(bytes(caller_code))],
                        codes_absent=[Bytes(runtime_code)],
                    )
                ),
            )
        ],
        post={
            created: Account(nonce=1, code=runtime_code),
        },
    )


def test_witness_codes_create_same_hash_then_read(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Tx1 deploys a contract, tx2 calls a pre-state contract with same code.

    The pre-state contract's bytecode must not appear in
    executionWitness.codes because the same code hash was already
    written by tx1's CREATE.  A stateless verifier observed
    the bytecode from the CREATE transaction data, so including it
    in the witness is redundant.
    """
    runtime_code = bytes(Op.STOP)

    existing_contract = pre.deploy_contract(code=runtime_code)

    creator = pre.fund_eoa()
    reader = pre.fund_eoa()

    tx1_create = Transaction(
        sender=creator,
        to=None,
        data=Initcode(deploy_code=runtime_code),
        gas_limit=500_000,
    )
    tx2_read = Transaction(
        sender=reader,
        to=existing_contract,
        gas_limit=200_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx1_create, tx2_read],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_absent=[Bytes(runtime_code)],
                    )
                ),
            )
        ],
        post={
            reader: Account(nonce=1),
            creator: Account(nonce=1),
        },
    )


def test_witness_codes_create_then_call_same_tx(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Factory CREATEs a contract and then CALLs it in the same transaction.

    The newly created contract's code should not appear in
    executionWitness.codes because it was read from tx-local code_writes
    and has no pre-state match.
    """
    runtime_code = bytes(Op.STOP)
    initcode = Initcode(deploy_code=runtime_code)
    initcode_bytes = bytes(initcode)

    factory_code = (
        Op.MSTORE(0, Op.PUSH32(initcode_bytes))
        + Op.SSTORE(
            0,
            Op.CREATE(
                offset=32 - len(initcode_bytes),
                size=len(initcode_bytes),
            ),
        )
        + Op.CALL(address=Op.SLOAD(0))
        + Op.STOP
    )
    factory = pre.deploy_contract(code=factory_code)
    sender = pre.fund_eoa()

    created = compute_create_address(address=factory, nonce=1)

    tx = Transaction(
        sender=sender,
        to=factory,
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[Bytes(bytes(factory_code))],
                        codes_absent=[Bytes(runtime_code)],
                    )
                ),
            )
        ],
        post={
            created: Account(nonce=1, code=runtime_code),
        },
    )


def test_witness_codes_initcode_calls_existing_contract(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    CREATE where initcode CALLs a pre-state contract during deployment.

    The called contract's code should appear in executionWitness.codes.
    The initcode itself should not appear because it comes from tx data
    or memory and is never fetched through get_code().
    """
    callee_code = bytes(Op.PUSH1(0x00) + Op.PUSH1(0x00) + Op.RETURN)
    callee = pre.deploy_contract(code=callee_code)

    runtime_code = bytes(Op.STOP)

    initcode_prefix = Op.CALL(address=callee) + Op.POP
    initcode = Initcode(
        deploy_code=runtime_code,
        initcode_prefix=initcode_prefix,
    )
    initcode_bytes = bytes(initcode)

    creator = pre.fund_eoa()
    created = compute_create_address(address=creator, nonce=0)

    tx = Transaction(
        sender=creator,
        to=None,
        data=initcode,
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[Bytes(callee_code)],
                        codes_absent=[Bytes(initcode_bytes)],
                    )
                ),
            )
        ],
        post={
            created: Account(nonce=1, code=runtime_code),
        },
    )


def test_witness_codes_failed_create_after_initcode_read(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    CREATE where initcode CALLs a pre-state contract, then deployment fails.

    The called contract's code should appear in executionWitness.codes
    because code_reads survive rollback (snapshots share the same set).
    No new code is added since the deployment failed.
    """
    callee_code = bytes(Op.PUSH1(0x00) + Op.PUSH1(0x00) + Op.RETURN)
    callee = pre.deploy_contract(code=callee_code)

    # Initcode that calls callee then fails via INVALID opcode
    initcode_body = Op.CALL(address=callee) + Op.POP + Op.INVALID
    initcode = bytes(initcode_body)

    creator = pre.fund_eoa()

    tx = Transaction(
        sender=creator,
        to=None,
        data=initcode,
        gas_limit=500_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[Bytes(callee_code)],
                    )
                ),
            )
        ],
        post={
            creator: Account(nonce=1),
        },
    )


def test_witness_codes_reverted_create_same_hash_then_read(
    pre: Alloc,
    blockchain_test: BlockchainTestFiller,
) -> None:
    """
    Factory CREATEs bytecode A then REVERTs; tx2 calls pre-state contract
    with also bytecode A.

    Said differently, bytecode A was observed by a contract creation execution
    but since the creation fails it isn't tracked cross-tx boundary by the
    state tracker. This means that tx2 access to the pre-state contract's
    code hash doesn't find it thus falls back to fetching the bytecode
    from pre-state and including it in the witness.
    """
    runtime_code = bytes(Op.STOP)

    existing_contract = pre.deploy_contract(code=runtime_code)

    initcode = bytes(Initcode(deploy_code=runtime_code))
    factory_code = (
        Op.MSTORE(0, Op.PUSH32(initcode))
        + Op.CREATE(
            offset=32 - len(initcode),
            size=len(initcode),
        )
        # The runtime_code was observed by the CREATE execution,
        # but since the CREATE fails, it isn't tracked cross-tx
        # boundary by the state tracker. This means that tx2
        # access to the pre-state contract's code hash doesn't
        # find it thus falls back to fetching the bytecode from
        # pre-state and including it in the witness.
        + Op.POP
        + Op.REVERT(offset=0, size=0)
    )
    factory = pre.deploy_contract(code=factory_code)

    sender1 = pre.fund_eoa()
    sender2 = pre.fund_eoa()

    tx1_reverted_create = Transaction(
        sender=sender1,
        to=factory,
        gas_limit=500_000,
    )
    tx2_read = Transaction(
        sender=sender2,
        to=existing_contract,
        gas_limit=200_000,
    )

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[tx1_reverted_create, tx2_read],
                expected_execution_witness_codes=(
                    ExecutionWitnessCodesExpectation(
                        codes_present=[
                            Bytes(bytes(factory_code)),
                            Bytes(runtime_code),
                        ],
                    )
                ),
            )
        ],
        post={
            sender1: Account(nonce=1),
            sender2: Account(nonce=1),
        },
    )
