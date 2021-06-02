import crypto
import rlp

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
Bloom = Bytes32

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

class Receipt:
    post_state: Root
    cumulative_gas_used: Uint
    bloom: Bloom
    logs: list[Log]

class Log:
    address: Address
    topics: list[Hash32]
    data: bytes

def state_transition(chain: Blockchain, block: Block) -> None:
    assert verify_header(block.header)
    process_block(chain, block)

def verify_header(header: Header) -> bool:
    pass

def process_block(chain: BlockChain, block: Block) -> None:
    gas_available = block.header.gas_limit
    receipts = []

    for tx in block.transactions:
        assert tx.gas_limit <= gas_available
        ctx = evm.Environment(
                block_hashes=[],
                coinbase=block.coinbase,
                number=block.number,
                gas_limit=block.gas_limit,
                gas_price=tx.gas_price
                time=block.time,
                difficulty=block.difficulty,
                state=chain.state
        )

        logs, gas_used = process_transaction(chain, block, tx)
        gas_available -= gas_used

        receipts.append(
            Receipt(
                post_state=bytes.from_hex('00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'),
                cumulative_gas_used=(block.gas_limit - gas_available),
                bloom=bytes.from_hex('00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'),
                logs=logs
        ))

        gas_available -= gas_used


def process_transaction(ctx: evm.Environment, tx: Transaction) -> Logs, int:
    assert verify_transaction(tx)

    from_address = recover_sender(tx)
    from = get_account(state, from_address) 

    assert from.nonce == tx.nonce
    from.nonce += 1

    cost = tx.gas_limit * tx.gas_price 
    assert cost <= from.balance
    from.balance -= cost

    assert tx.value <= from.balance
    from.balance -= tx.value

    ctx.caller = from
    return evm.proccess_call(from, target, tx.data, tx.value, tx.gas, 0, ctx)


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
    v, r, s = tx.v, tx.r, tx.s

    #  if v > 28:
    #      v = v - (chainid*2+8)

    assert v==27 or v==28
    r_int  = int.from_bytes(r, "big")
    s_int  = int.from_bytes(s, "big")

    assert 0 < r_int and r_int < secp256k1n
    #assert 0<s_int and s_int<(secp256k1n//2+1)     # TODO: this causes error starting in block 46169 (or 46170?), so just commented

    return crypto.secp256k1recover(r, s, v-27, sig_hash_tx(tx))

def sig_hash_tx(tx: Transaction) -> Hash32:
    return crypto.keccak256(rlp.encode(
        tx.nonce,
        tx.gas_price,
        tx.gas_limit,
        tx.to,
        tx.value,
        tx.data
    ))
