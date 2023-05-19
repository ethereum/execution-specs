
"""
Test EIP-4844: Shard Blob Transactions (DATAHASH Opcode)
EIP: https://eips.ethereum.org/EIPS/eip-4844
"""
# import itertools

import pytest

# from copy import copy
from typing import Dict, List

from ethereum_test_forks import Cancun, Fork, forks_from
from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTestFiller,
    # CodeGasMeasure,
    Environment,
    # StateTest,
    TestAddress,
    Transaction,
    Yul,
    compute_create2_address,
    compute_create_address,
    # test_from,
    to_address,
    to_hash_bytes,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

pytestmark = pytest.mark.parametrize("fork", forks_from(Cancun))

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-4844.md"
REFERENCE_SPEC_VERSION = "ac003985b9be74ff48bd897770e6d5f2e4318715"

DATAHASH_GAS_COST = 3
MAX_BLOB_PER_BLOCK = 4
BLOB_COMMITMENT_VERSION_KZG = bytes([0x01])

env = Environment(  # Global state test environment
    coinbase="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
    difficulty=0x20000,
    gas_limit=300000000,
    number=1,
    timestamp=1000,
)

datahash_verbatim = "verbatim_{}i_{}o".format(
    Op.DATAHASH.popped_stack_items, Op.DATAHASH.pushed_stack_items
)

datahash_sstore_bytecode = Yul(
    f"""
    {{
       let pos := calldataload(0)
       let end := calldataload(32)
       for {{}} lt(pos, end) {{ pos := add(pos, 1) }}
       {{
        let datahash := {datahash_verbatim}(hex"{Op.DATAHASH.hex()}", pos)
        sstore(pos, datahash)
       }}
       let datahash := {datahash_verbatim}(hex"{Op.DATAHASH.hex()}", end)
       sstore(end, datahash)
       return(0, 0)
    }}
    """
)
datahash_sstore_bytecode_address = to_address(0x100)

datahash_return_bytecode = Yul(
    f"""
    {{
       let pos := calldataload(0)
       let datahash := {datahash_verbatim}(hex"{Op.DATAHASH.hex()}", pos)
       mstore(0, datahash)
       return(0, 32)
    }}
    """
)
datahash_return_bytecode_address = to_address(0x600)

initcode_datahash_sstore_bytecode = Yul(
    f"""
    {{
       for {{ let pos := 0 }} lt(pos, 10) {{ pos := add(pos, 1) }}
       {{
        let datahash := {datahash_verbatim}(hex"{Op.DATAHASH.hex()}", pos)
        sstore(pos, datahash)
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
    pop(callcode(gas(), {datahash_return_bytecode_address}, 0, 0, 32, 0, 32))
    let datahash := mload(0)
    sstore(pos, datahash)
    }}

    mstore(0, end)
    pop(callcode(gas(), {datahash_return_bytecode_address}, 0, 0, 32, 0, 32))
    let datahash := mload(0)
    sstore(end, datahash)
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
    pop(staticcall(gas(), {datahash_return_bytecode_address}, 0, 32, 0, 32))
    let datahash := mload(0)
    sstore(pos, datahash)
    }}

    mstore(0, end)
    pop(staticcall(gas(), {datahash_return_bytecode_address}, 0, 32, 0, 32))
    let datahash := mload(0)
    sstore(end, datahash)
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
    initcode_datahash_sstore_bytecode.assemble(),
)

b_hashes: List[bytes] = [
    to_hash_bytes(1 << x) for x in range(MAX_BLOB_PER_BLOCK)
]

tx = Transaction(  # Transaction template
    nonce=0,
    data=to_hash_bytes(0),
    gas_limit=3000000,
    max_fee_per_gas=10,
    max_fee_per_data_gas=10,
    access_list=[],
)


@pytest.fixture(
    params=[
        'BLOBHASH_on_top_level_call_stack',
        'BLOBHASH_on_max_value',
    ]
)
def opcode_context(request):
    opcode = request.param
    opcode_contexts = {
        'BLOBHASH_on_top_level_call_stack': {
            'pre':
            {
                TestAddress: Account(balance=1000000000000000000000),
                datahash_sstore_bytecode_address: Account(
                    code=datahash_sstore_bytecode
                ),
            },
            'tx': tx.with_fields(
                ty=3,
                to=datahash_sstore_bytecode_address,
                max_priority_fee_per_gas=10,
                blob_commitment_version_kzg=BLOB_COMMITMENT_VERSION_KZG,
                blob_versioned_hashes=b_hashes[:1],
            ),
            'post':
            {
                datahash_sstore_bytecode_address: Account(
                    storage={
                        0: BLOB_COMMITMENT_VERSION_KZG 
                        + b_hashes[0][1:]
                    }
                ),
            },
        },
        'BLOBHASH_on_max_value': {
            'pre':
            {
                TestAddress: Account(balance=1000000000000000000000),
                datahash_sstore_bytecode_address: Account(
                    code=datahash_sstore_bytecode
                ),
            },
            'tx': tx.with_fields(
                ty=3,
                data=to_hash_bytes(2**256 - 1) + to_hash_bytes(2**256 - 1),
                to=datahash_sstore_bytecode_address,
                max_priority_fee_per_gas=10,
                blob_commitment_version_kzg=BLOB_COMMITMENT_VERSION_KZG,
                blob_versioned_hashes=b_hashes[:1],
            ),
            'post':
            {
                datahash_sstore_bytecode_address: Account(storage={}),
            },
        },
    }
    context = opcode_contexts.get(opcode)
    if context is None:
        return None
    context['opcode'] = opcode
    return context


def test_datahash_opcode_contexts(
    opcode_context: Dict,
    blockchain_test: BlockchainTestFiller,
    fork: Fork
):
    print(opcode_context['pre'])
    blockchain_test(
        pre=opcode_context['pre'],
        post=opcode_context['post'],
        blocks=[Block(
            txs=[opcode_context['tx']]
        )],
        genesis_environment=env,
        tag=opcode_context['opcode'],
    )
