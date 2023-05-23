"""
Test EIP-4844: Shard Blob Transactions (BLOBHASH Opcode)
EIP: https://eips.ethereum.org/EIPS/eip-4844
"""

import pytest

from typing import List
from ethereum_test_forks import Cancun, forks_from
from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTestFiller,
    Environment,
    TestAddress,
    Transaction,
    Yul,
    add_kzg_version,
    compute_create2_address,
    compute_create_address,
    to_address,
    to_hash_bytes,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

pytestmark = pytest.mark.parametrize("fork", forks_from(Cancun))

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4844.md"
REFERENCE_SPEC_VERSION = "ac003985b9be74ff48bd897770e6d5f2e4318715"

MAX_BLOB_PER_BLOCK = 4
BLOB_COMMITMENT_VERSION_KZG = bytes([0x01])

blobhash_verbatim = "verbatim_{}i_{}o".format(
    Op.BLOBHASH.popped_stack_items, Op.BLOBHASH.pushed_stack_items
)

blobhash_sstore_bytecode = Yul(
    f"""
    {{
       let pos := calldataload(0)
       let end := calldataload(32)
       for {{}} lt(pos, end) {{ pos := add(pos, 1) }}
       {{
        let blobhash := {blobhash_verbatim}(hex"{Op.BLOBHASH.hex()}", pos)
        sstore(pos, blobhash)
       }}
       let blobhash := {blobhash_verbatim}(hex"{Op.BLOBHASH.hex()}", end)
       sstore(end, blobhash)
       return(0, 0)
    }}
    """
)
blobhash_sstore_bytecode_address = to_address(0x100)

blobhash_return_bytecode = Yul(
    f"""
    {{
       let pos := calldataload(0)
       let blobhash := {blobhash_verbatim}(hex"{Op.BLOBHASH.hex()}", pos)
       mstore(0, blobhash)
       return(0, 32)
    }}
    """
)
blobhash_return_bytecode_address = to_address(0x600)

initcode_blobhash_sstore_bytecode = Yul(
    f"""
    {{
       for {{ let pos := 0 }} lt(pos, 10) {{ pos := add(pos, 1) }}
       {{
        let blobhash := {blobhash_verbatim}(hex"{Op.BLOBHASH.hex()}", pos)
        sstore(pos, blobhash)
       }}
       return(0, 0)
    }}
    """
)
tx_created_contract_address = compute_create_address(TestAddress, 0)

call_bytecode = Yul(
    """
    {
        calldatacopy(0, 0, calldatasize())
        pop(call(gas(), 0x100, 0, 0, calldatasize(), 0, 0))
    }
    """
)
call_bytecode_address = to_address(0x200)

delegatecall_bytecode = Yul(
    """
    {
        calldatacopy(0, 0, calldatasize())
        pop(delegatecall(gas(), 0x100, 0, calldatasize(), 0, 0))
    }
    """
)
delegatecall_bytecode_address = to_address(0x300)

callcode_bytecode = Yul(
    f"""
{{
    let pos := calldataload(0)
    let end := calldataload(32)
    for {{ }} lt(pos, end) {{ pos := add(pos, 1) }}
    {{
    mstore(0, pos)
    pop(callcode(gas(), {blobhash_return_bytecode_address}, 0, 0, 32, 0, 32))
    let blobhash := mload(0)
    sstore(pos, blobhash)
    }}

    mstore(0, end)
    pop(callcode(gas(), {blobhash_return_bytecode_address}, 0, 0, 32, 0, 32))
    let blobhash := mload(0)
    sstore(end, blobhash)
    return(0, 0)
}}
        """
)
callcode_bytecode_address = to_address(0x800)

staticcall_bytecode = Yul(
    f"""
{{
    let pos := calldataload(0)
    let end := calldataload(32)
    for {{ }} lt(pos, end) {{ pos := add(pos, 1) }}
    {{
    mstore(0, pos)
    pop(staticcall(gas(), {blobhash_return_bytecode_address}, 0, 32, 0, 32))
    let blobhash := mload(0)
    sstore(pos, blobhash)
    }}

    mstore(0, end)
    pop(staticcall(gas(), {blobhash_return_bytecode_address}, 0, 32, 0, 32))
    let blobhash := mload(0)
    sstore(end, blobhash)
    return(0, 0)
}}
    """
)
staticcall_bytecode_address = to_address(0x700)

create_bytecode = Yul(
    """
    {
        calldatacopy(0, 0, calldatasize())
        pop(create(0, 0, calldatasize()))
    }
    """
)
create_bytecode_address = to_address(0x400)
create_opcode_created_contract = compute_create_address(
    create_bytecode_address, 0
)

create2_bytecode = Yul(
    """
    {
        calldatacopy(0, 0, calldatasize())
        pop(create2(0, 0, calldatasize(), 0))
    }
    """
)
create2_bytecode_address = to_address(0x500)
create2_opcode_created_contract = compute_create2_address(
    create2_bytecode_address,
    0,
    initcode_blobhash_sstore_bytecode.assemble(),
)

# Blob versioned hashes ranging from 1-4
b_hashes: List[bytes] = add_kzg_version(
    [(1 << x) for x in range(MAX_BLOB_PER_BLOCK)],
    BLOB_COMMITMENT_VERSION_KZG,
)

# Blob transaction template
tx_type_3 = Transaction(
    ty=3,
    data=to_hash_bytes(0),
    gas_limit=3000000,
    max_fee_per_gas=10,
    max_priority_fee_per_gas=10,
    max_fee_per_data_gas=10,
    access_list=[],
    blob_commitment_version_kzg=BLOB_COMMITMENT_VERSION_KZG,
    blob_versioned_hashes=b_hashes,
)


def create_opcode_context(pre, tx, post):
    return {'pre': pre, 'tx': tx, 'post': post}


opcode_contexts = {
    'BLOBHASH_on_top_level_call_stack': create_opcode_context(
        {
            TestAddress: Account(balance=1000000000000000000000),
            blobhash_sstore_bytecode_address: Account(
                code=blobhash_sstore_bytecode
            ),
        },
        tx_type_3.with_fields(
            to=blobhash_sstore_bytecode_address,
            blob_versioned_hashes=b_hashes[:1],
        ),
        {
            blobhash_sstore_bytecode_address: Account(
                storage={
                    0: b_hashes[0]
                }
            ),
        },
    ),
    'BLOBHASH_on_max_value': create_opcode_context(
        {
            TestAddress: Account(balance=1000000000000000000000),
            blobhash_sstore_bytecode_address: Account(
                code=blobhash_sstore_bytecode
            ),
        },
        tx_type_3.with_fields(
            data=to_hash_bytes(2**256 - 1) + to_hash_bytes(2**256 - 1),
            to=blobhash_sstore_bytecode_address,
        ),
        {
            blobhash_sstore_bytecode_address: Account(storage={}),
        },
    ),
    'BLOBHASH_on_CALL': create_opcode_context(
        {
            TestAddress: Account(balance=1000000000000000000000),
            call_bytecode_address: Account(code=call_bytecode),
            blobhash_sstore_bytecode_address: Account(
                code=blobhash_sstore_bytecode
            ),
        },
        tx_type_3.with_fields(
            data=to_hash_bytes(1) + to_hash_bytes(1),
            to=call_bytecode_address,
            blob_versioned_hashes=b_hashes[:2],
        ),
        {
            blobhash_sstore_bytecode_address: Account(
                storage={
                    1: b_hashes[1]
                }
            ),
        },
    ),
    'BLOBHASH_on_DELEGATECALL': create_opcode_context(
        {
            TestAddress: Account(balance=1000000000000000000000),
            delegatecall_bytecode_address: Account(
                code=delegatecall_bytecode
            ),
            blobhash_sstore_bytecode_address: Account(
                code=blobhash_sstore_bytecode
            ),
        },
        tx_type_3.with_fields(
            data=to_hash_bytes(0) + to_hash_bytes(3),
            to=delegatecall_bytecode_address,
        ),
        {
            delegatecall_bytecode_address: Account(
                storage={
                    k: v for (k, v) in zip(range(len(b_hashes)), b_hashes)
                }
            ),
        },
    ),
    'BLOBHASH_on_STATICCALL': create_opcode_context(
        {
            TestAddress: Account(balance=1000000000000000000000),
            staticcall_bytecode_address: Account(code=staticcall_bytecode),
            blobhash_return_bytecode_address: Account(
                code=blobhash_return_bytecode
            ),
        },
        tx_type_3.with_fields(
            data=to_hash_bytes(0) + to_hash_bytes(3),
            to=staticcall_bytecode_address,
        ),
        {
            staticcall_bytecode_address: Account(
                storage={
                    k: v for (k, v) in zip(range(len(b_hashes)), b_hashes)
                }
            ),
        },
    ),
    'BLOBHASH_on_CALLCODE': create_opcode_context(
        {
            TestAddress: Account(balance=1000000000000000000000),
            callcode_bytecode_address: Account(code=callcode_bytecode),
            blobhash_return_bytecode_address: Account(
                code=blobhash_return_bytecode
            ),
        },
        tx_type_3.with_fields(
            data=to_hash_bytes(0) + to_hash_bytes(3),
            to=callcode_bytecode_address,
        ),
        {
            callcode_bytecode_address: Account(
                storage={
                    k: v for (k, v) in zip(range(len(b_hashes)), b_hashes)
                }
            ),
        },
    ),
    'BLOBHASH_on_INITCODE': create_opcode_context( 
        {
            TestAddress: Account(balance=1000000000000000000000),
        },
        tx_type_3.with_fields(
            data=initcode_blobhash_sstore_bytecode,
            to=None,
        ),
        {
            tx_created_contract_address: Account(
                storage={
                    k: v for (k, v) in zip(range(len(b_hashes)), b_hashes)
                }
            ),
        },
    ),
    'BLOBHASH_on_CREATE': create_opcode_context( 
        {
            TestAddress: Account(balance=1000000000000000000000),
            create_bytecode_address: Account(code=create_bytecode),
        },
        tx_type_3.with_fields(
            data=initcode_blobhash_sstore_bytecode,
            to=create_bytecode_address,
        ),
        {
            create_opcode_created_contract: Account(
                storage={
                    k: v for (k, v) in zip(range(len(b_hashes)), b_hashes)
                }
            ),
        },
    ),
    'BLOBHASH_on_CREATE2': create_opcode_context( 
        {
            TestAddress: Account(balance=1000000000000000000000),
            create2_bytecode_address: Account(code=create2_bytecode),
        },
        tx_type_3.with_fields(
            data=initcode_blobhash_sstore_bytecode,
            to=create2_bytecode_address,
        ),
        {
            create2_opcode_created_contract: Account(
                storage={
                    k: v for (k, v) in zip(range(len(b_hashes)), b_hashes)
                }
            ),
        },
    ),
    'BLOBHASH_on_type_2_tx': create_opcode_context(
        {
            TestAddress: Account(balance=1000000000000000000000),
            blobhash_sstore_bytecode_address: Account(
                code=blobhash_sstore_bytecode
            ),
        },
        Transaction(
            ty=2,
            data=to_hash_bytes(0),
            to=blobhash_sstore_bytecode_address,
            gas_limit=3000000,
            max_fee_per_gas=10,
            max_priority_fee_per_gas=10,
            access_list=[],
        ),
        {
            blobhash_sstore_bytecode_address: Account(storage={0: 0}),
        },
    ),
    'BLOBHASH_on_type_1_tx': create_opcode_context(
        {
            TestAddress: Account(balance=1000000000000000000000),
            blobhash_sstore_bytecode_address: Account(
                code=blobhash_sstore_bytecode
            ),
        },
        Transaction(
            ty=1,
            data=to_hash_bytes(0),
            to=blobhash_sstore_bytecode_address,
            gas_limit=3000000,
            gas_price=10,
            access_list=[],
        ),
        {
            blobhash_sstore_bytecode_address: Account(storage={0: 0}),
        },
    ),
    'BLOBHASH_on_type_0_tx': create_opcode_context(
        {
            TestAddress: Account(balance=1000000000000000000000),
            blobhash_sstore_bytecode_address: Account(
                code=blobhash_sstore_bytecode
            ),
        },
        Transaction(
            ty=0,
            data=to_hash_bytes(0),
            to=blobhash_sstore_bytecode_address,
            gas_limit=3000000,
            gas_price=10,
            access_list=[],
        ),
        {
            blobhash_sstore_bytecode_address: Account(storage={0: 0}),
        },
    ),
}


@pytest.fixture
def env():
    """
    Fixture for environment setup.
    """
    return Environment(
        coinbase="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
        difficulty=0x20000,
        gas_limit=300000000,
        number=1,
        timestamp=1000,
    )


@pytest.fixture(params=opcode_contexts.values(), ids=opcode_contexts.keys())
def context(request):
    """
    Fixture that is parameterized to each value of the opcode_contexts
    dictionary, with each key being used as the test ID.
    """
    return request.param


@pytest.fixture
def pre(context):
    """
    Fixture for the pre state of the given context.
    """
    return context['pre']


@pytest.fixture
def tx(context):
    """
    Fixture of the transaction for the given context.
    """
    return context['tx']


@pytest.fixture
def post(context):
    """
    Fixture for the post state of the given context.
    """
    return context['post']


def test_blobhash_opcode_contexts(
    pre,
    tx,
    post,
    env: Environment,
    blockchain_test: BlockchainTestFiller
):
    """
    Test function for each opcode context, in the opcode_contexts dictionary.
    """
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        blocks=[Block(
            txs=[tx]
        )],
        post=post,
    )
