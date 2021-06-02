from typing import Optional

Bytes = bytes
Bytes32 = bytes
Bytes20 = bytes
Bytes8 = bytes
Root = Bytes32
Hash32 = Bytes32
Address = Bytes20
U256 = int
Uint = int
State = dict[Address, Account]


TX_BASE_COST = 21000
TX_DATA_COST_PER_NON_ZERO = 68
TX_DATA_COST_PER_ZERO = 4

class BlockChain:
    blocks: list[Block]
    state: State

class Account:
    nonce: Uint, 
    balance: Uint,
    code_hash: Hash32,
    storage_root: Root,

class Header:
    parent: Hash32
    ommers_hash: Hash32
    coinbase: Address
    state_root: Root
    transactions_root: Root
    receipt_root: Root
    bloom: Bloom
    difficulty: Uint
    number: Uint
    gas_limit: Uint
    gas_used: Uint
    time: Uint
    extra: Bytes
    mix_digest: Bytes32
    nonce: Bytes8

class Block:
    header: Header
    transactions: list[Transaction]
    ommers: list[Header]

class Transaction:
    nonce: Uint
    gas_price: Uint
    gas: Uint
    to: Optional[Address]
    value: Uint
    data: Bytes
    v: Uint
    r: Uint
    s: Uint

class Bloom:
    pass

def state_transition(chain: Blockchain, block: Block) -> None:
    assert verify_header(block.header)
    process_block(chain, block)

def verify_header(header: Header) -> bool:
    pass

def process_block(chain: BlockChain, block: Block) -> None:
    gas_available = block.header.gas_limit

    for tx in block.transactions:
        assert tx.gas_limit <= gas_available
        receipt, logs, gas_used = process_transaction(chain, block, tx)
        gas_available -= gas_used


def process_transaction(chain: BlockChain, block: Block, tx: Transaction) -> Receipt, Logs, int:
    assert verify_transaction(tx)

    from_address = recover_sender(tx)
    from = get_account(chain.state, from_address) 

    assert from.nonce == tx.nonce
    from.nonce += 1

    cost = tx.gas_limit * tx.gas_price 
    assert cost <= from.balance
    from.balance -= cost

    assert tx.value <= from.balance
    from.balance -= tx.value

    # TODO

def verify_transaction(tx: Transaction) -> bool:
    data_cost = 0

    for byte in tx.data:
        if byte == 0:
            data_cost += TX_DATA_COST_PER_ZERO
        else:
            data_cost += TX_DATA_COST_PER_NON_ZERO

    return TX_BASE_COST + data_cost <= tx.gas_limit

def get_account(state: State, address: Address) -> Account:
    return state[address]

def get_code(state: State, address: Address) -> Account:
    return state[address].code

def recover_sender(tx) -> Address:
    pass
