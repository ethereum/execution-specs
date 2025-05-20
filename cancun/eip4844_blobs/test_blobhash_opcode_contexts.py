"""
abstract: Tests `BLOBHASH` opcode in [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844)
    Test case for `BLOBHASH` opcode calls across different contexts
    in [EIP-4844: Shard Blob Transactions](https://eips.ethereum.org/EIPS/eip-4844).

"""  # noqa: E501

from enum import Enum
from typing import Iterable, List

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Hash,
    StateTestFiller,
    Transaction,
    add_kzg_version,
    compute_create_address,
)
from ethereum_test_tools import Opcodes as Op

from .spec import Spec, ref_spec_4844

REFERENCE_SPEC_GIT_PATH = ref_spec_4844.git_path
REFERENCE_SPEC_VERSION = ref_spec_4844.version

pytestmark = pytest.mark.valid_from("Cancun")


class BlobhashContext(Enum):
    """
    A utility class for mapping common EVM opcodes in different contexts
    to specific bytecode (with BLOBHASH), addresses and contracts.
    """

    BLOBHASH_SSTORE = "blobhash_sstore"
    BLOBHASH_RETURN = "blobhash_return"
    CALL = "call"
    DELEGATECALL = "delegatecall"
    CALLCODE = "callcode"
    STATICCALL = "staticcall"
    CREATE = "create"
    CREATE2 = "create2"
    INITCODE = "initcode"

    def code(self, *, indexes=Iterable[int]):
        """
        Map opcode context to bytecode that utilizes the BLOBHASH opcode.

        Args:
            indexes: The indexes to request using the BLOBHASH opcode

        """
        match self:
            case BlobhashContext.BLOBHASH_SSTORE:
                return (
                    sum(Op.SSTORE(index, Op.BLOBHASH(index=index)) for index in indexes) + Op.STOP
                )
            case BlobhashContext.BLOBHASH_RETURN:
                return Op.MSTORE(
                    offset=0, value=Op.BLOBHASH(index=Op.CALLDATALOAD(offset=0))
                ) + Op.RETURN(offset=0, size=32)
            case BlobhashContext.INITCODE:
                return (
                    sum(Op.SSTORE(index, Op.BLOBHASH(index=index)) for index in indexes) + Op.STOP
                )
            case _:
                raise ValueError(f"Invalid context: {self}")

    def deploy_contract(
        self,
        *,
        pre: Alloc,
        indexes=Iterable[int],
    ) -> Address:
        """
        Deploy a contract with the given context and indexes.

        Args:
            pre: The pre state to deploy the contract on
            indexes: The indexes to request using the BLOBHASH opcode

        """
        match self:
            case BlobhashContext.BLOBHASH_SSTORE | BlobhashContext.BLOBHASH_RETURN:
                return pre.deploy_contract(self.code(indexes=indexes))
            case BlobhashContext.CALL | BlobhashContext.CALLCODE | BlobhashContext.STATICCALL:
                blobhash_return_address = BlobhashContext.BLOBHASH_RETURN.deploy_contract(
                    pre=pre, indexes=indexes
                )
                call_opcode = (
                    Op.CALL
                    if self == BlobhashContext.CALL
                    else (Op.CALLCODE if self == BlobhashContext.CALLCODE else Op.STATICCALL)
                )
                bytecode = (
                    sum(
                        Op.MSTORE(offest=0, value=index)
                        + Op.POP(
                            call_opcode(
                                address=blobhash_return_address,
                                args_offset=0,
                                args_size=32,
                                ret_offset=32,
                                ret_size=32,
                            )
                        )
                        + Op.SSTORE(index, Op.MLOAD(offset=32))
                        for index in indexes
                    )
                    + Op.STOP
                )
                return pre.deploy_contract(bytecode)
            case BlobhashContext.DELEGATECALL:
                blobhash_sstore_address = pre.deploy_contract(
                    BlobhashContext.BLOBHASH_SSTORE.code(indexes=indexes)
                )
                bytecode = Op.POP(
                    Op.DELEGATECALL(
                        address=blobhash_sstore_address, args_offset=0, args_size=Op.CALLDATASIZE()
                    )
                )
                return pre.deploy_contract(bytecode)
            case BlobhashContext.CREATE | BlobhashContext.CREATE2:
                initcode = BlobhashContext.INITCODE.code(indexes=indexes)
                initcode_address = pre.deploy_contract(initcode)
                create_opcode = Op.CREATE if self == BlobhashContext.CREATE else Op.CREATE2
                create_bytecode = Op.EXTCODECOPY(
                    address=initcode_address, dest_offset=0, offset=0, size=len(initcode)
                ) + Op.POP(create_opcode(value=0, offset=0, size=len(initcode), salt=0))
                return pre.deploy_contract(create_bytecode)

            case _:
                raise ValueError(f"Invalid context: {self}")


@pytest.fixture()
def simple_blob_hashes(
    max_blobs_per_block: int,
) -> List[Hash]:
    """Return a simple list of blob versioned hashes ranging from bytes32(1 to 4)."""
    return add_kzg_version(
        [(1 << x) for x in range(max_blobs_per_block)],
        Spec.BLOB_COMMITMENT_VERSION_KZG,
    )


@pytest.mark.parametrize(
    "test_case",
    [
        "on_top_level_call_stack",
        "on_max_value",
        "on_CALL",
        "on_DELEGATECALL",
        "on_STATICCALL",
        "on_CALLCODE",
        "on_CREATE",
        "on_CREATE2",
    ],
    ids=lambda x: x,
)
def test_blobhash_opcode_contexts(
    pre: Alloc,
    test_case: str,
    max_blobs_per_block: int,
    simple_blob_hashes: List[bytes],
    fork: Fork,
    state_test: StateTestFiller,
):
    """
    Tests that the `BLOBHASH` opcode functions correctly when called in different contexts.

    - `BLOBHASH` opcode on the top level of the call stack.
    - `BLOBHASH` opcode on the max value.
    - `BLOBHASH` opcode on `CALL`, `DELEGATECALL`, `STATICCALL`, and `CALLCODE`.
    - `BLOBHASH` opcode on Initcode.
    - `BLOBHASH` opcode on `CREATE` and `CREATE2`.
    - `BLOBHASH` opcode on transaction types 0, 1 and 2.
    """
    tx_to: Address
    post: dict[Address, Account]

    match test_case:
        case "on_top_level_call_stack":
            blobhash_sstore_address = BlobhashContext.BLOBHASH_SSTORE.deploy_contract(
                pre=pre, indexes=range(max_blobs_per_block + 1)
            )
            tx_to = blobhash_sstore_address
            post = {
                blobhash_sstore_address: Account(
                    storage=dict(
                        zip(
                            range(len(simple_blob_hashes)),
                            simple_blob_hashes,
                            strict=False,
                        )
                    )
                ),
            }
        case "on_max_value":
            blobhash_sstore_address = BlobhashContext.BLOBHASH_SSTORE.deploy_contract(
                pre=pre, indexes=[2**256 - 1]
            )
            tx_to = blobhash_sstore_address
            post = {
                blobhash_sstore_address: Account(storage={}),
            }
        case "on_CALL" | "on_DELEGATECALL" | "on_STATICCALL" | "on_CALLCODE":
            call_context: BlobhashContext
            match test_case:
                case "on_CALL":
                    call_context = BlobhashContext.CALL
                case "on_DELEGATECALL":
                    call_context = BlobhashContext.DELEGATECALL
                case "on_STATICCALL":
                    call_context = BlobhashContext.STATICCALL
                case "on_CALLCODE":
                    call_context = BlobhashContext.CALLCODE
            call_address = call_context.deploy_contract(
                pre=pre, indexes=range(max_blobs_per_block + 1)
            )
            tx_to = call_address
            post = {
                call_address: Account(
                    storage=dict(
                        zip(
                            range(len(simple_blob_hashes)),
                            simple_blob_hashes,
                            strict=False,
                        )
                    )
                ),
            }
        case "on_CREATE" | "on_CREATE2":
            create_context: BlobhashContext
            opcode: Op
            match test_case:
                case "on_CREATE":
                    create_context = BlobhashContext.CREATE
                    opcode = Op.CREATE
                case "on_CREATE2":
                    create_context = BlobhashContext.CREATE2
                    opcode = Op.CREATE2
            factory_address = create_context.deploy_contract(
                pre=pre, indexes=range(max_blobs_per_block + 1)
            )
            created_contract_address = compute_create_address(
                address=factory_address,
                nonce=1,  # the create contract will have nonce 1 for its first create
                salt=0,
                initcode=BlobhashContext.INITCODE.code(indexes=range(max_blobs_per_block + 1)),
                opcode=opcode,
            )
            tx_to = factory_address
            post = {
                created_contract_address: Account(
                    storage=dict(
                        zip(range(len(simple_blob_hashes)), simple_blob_hashes, strict=False)
                    )
                ),
            }
        case _:
            raise Exception(f"Unknown test case {test_case}")

    state_test(
        pre=pre,
        tx=Transaction(
            ty=Spec.BLOB_TX_TYPE,
            to=tx_to,
            gas_limit=500_000,
            max_fee_per_blob_gas=fork.min_base_fee_per_blob_gas() * 10,
            blob_versioned_hashes=simple_blob_hashes,
            sender=pre.fund_eoa(),
        ),
        post=post,
    )


@pytest.mark.with_all_tx_types(selector=lambda x: x != 3)
def test_blobhash_opcode_contexts_tx_types(
    pre: Alloc,
    tx_type: int,
    state_test: StateTestFiller,
):
    """
    Tests that the `BLOBHASH` opcode functions correctly when called in different contexts.

    - `BLOBHASH` opcode on the top level of the call stack.
    - `BLOBHASH` opcode on the max value.
    - `BLOBHASH` opcode on `CALL`, `DELEGATECALL`, `STATICCALL`, and `CALLCODE`.
    - `BLOBHASH` opcode on Initcode.
    - `BLOBHASH` opcode on `CREATE` and `CREATE2`.
    - `BLOBHASH` opcode on transaction types 0, 1 and 2.
    """
    blobhash_sstore_address = BlobhashContext.BLOBHASH_SSTORE.deploy_contract(pre=pre, indexes=[0])
    tx_kwargs = {
        "ty": tx_type,
        "to": blobhash_sstore_address,
        "sender": pre.fund_eoa(),
        "gas_limit": 500_000,
    }
    if tx_type == 4:
        signer = pre.fund_eoa(amount=0)
        tx_kwargs["authorization_list"] = [
            AuthorizationTuple(
                signer=signer,
                address=Address(0),
                nonce=0,
            )
        ]

    state_test(
        pre=pre,
        tx=Transaction(**tx_kwargs),
        post={
            blobhash_sstore_address: Account(storage={0: 0}),
        },
    )
