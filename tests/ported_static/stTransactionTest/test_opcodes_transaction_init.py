"""
Verify each opcode family executes inside a creation transaction's init
code, and that its result reaches the deployed contract.

Ported from:
state_tests/stTransactionTest/Opcodes_TransactionInitFiller.json

@manually-enhanced: Do not overwrite. The ported test only checked that
each init code ran to completion, so an opcode returning the wrong
result was invisible. Every arm that produces a value now MSTOREs it and
RETURNs it as the deployed code, making the outcome observable. Cases
are keyed by opcode and parametrized from `fork.valid_opcodes()`, so a
newly-enabled opcode fails here until a case is added. The filler's
`returner` target returned four zero bytes, indistinguishable from an
empty return; it now returns a marker word so the RETURNDATA* arms can
be checked. Sub-calls are sized from the callee's own
`gas_cost(fork)` rather than forwarding everything, which is what lets
the test reach back to Frontier, and the created account's nonce is
derived from EIP-161 rather than pinned at one.
"""

from dataclasses import dataclass, field
from typing import Callable, Generator

import pytest
from _pytest.mark.structures import ParameterSet
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create2_address,
    compute_create_address,
    keccak256,
)
from execution_testing.forks import Fork
from execution_testing.vm import Bytecode, Op, Opcodes

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_VALUE = 100_000
WORD = 32
ALL_ONES = 2**256 - 1
RETURN_MARKER = 0xBEEF
# Markers planted at the exact stack depth each EIP-8024 opcode
# reaches, so surfacing one proves the depth was right.
DUPN_MARKER = 0xA1
SWAPN_MARKER = 0xB2
EXCHANGE_MARKER = 0xC3

# Block context, pinned so the opcodes that read it can be asserted
# rather than merely executed. The block gas limit keeps its default:
# a transaction with no explicit limit is granted exactly that much, so
# lowering it here would make every arm exceed the block.
COINBASE = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
BLOCK_NUMBER = 1
BLOCK_TIMESTAMP = 1_000
PREV_RANDAO = 0x20000
BASE_FEE_PER_GAS = 10
EXCESS_BLOB_GAS = 0
SLOT_NUMBER = 7

# Markers written then read back, so a store or copy that silently did
# nothing is distinguishable from one that worked.
STORE_MARKER = 0xD1CE
MSTORE8_BYTE = 0xAB
RETURNER_MARKER = 0xF00D
SHA3_INPUT = 0x5EED
STORER_BALANCE = 0x1234
CALL_SUCCEEDED = 1
# Two distinct words, so the one left after a POP identifies how many
# items it removed.
POP_TOP = 0xE1
POP_UNDER = 0xE2
JUMP_MARKER = 0x7A

STORER_CODE = Op.SSTORE(key=0x0, value=0x1) + Op.STOP
"""Pre-deployed target whose code EXTCODE* arms read."""
# The ported filler's returner returned four zero bytes, which no
# assertion can distinguish from an empty return; it now returns a
# marker word so RETURNDATASIZE and RETURNDATACOPY are checkable.
RETURNER_CODE = Op.MSTORE(
    offset=0x0, value=RETURNER_MARKER, new_memory_size=WORD
) + Op.RETURN(offset=0x0, size=WORD)
"""Pre-deployed target that returns a known word."""


def _code_word(code: Bytecode) -> int:
    """Return a code's first word, as a COPY into memory would read it."""
    return int.from_bytes(bytes(code)[:WORD].ljust(WORD, b"\x00"), "big")


def _base_nonce(fork: Fork) -> int:
    """Return a newly created contract's starting nonce (EIP-161)."""
    return int(fork.is_eip_enabled(161))


def _hash_word(data: bytes) -> int:
    """Return keccak256 of `data` as a word."""
    return int.from_bytes(bytes(keccak256(data)), "big")


def _jump_over_revert(conditional: bool) -> Bytecode:
    """
    Jump past a REVERT to reach a marker push.

    The target is derived from the code it skips, and a jump landing
    anywhere else either reverts or faults on a non-JUMPDEST, so the
    marker surviving into the deployed code is the proof. Valid only
    with an empty `prefix`, which puts this body at offset 0.
    """
    revert = Op.REVERT(offset=0x0, size=0x0)
    jump = (
        Op.JUMPI(pc=Op.PUSH1(data_placeholder="target"), condition=1)
        if conditional
        else Op.JUMP(pc=Op.PUSH1(data_placeholder="target"))
    )
    code = jump + revert + Op.JUMPDEST + Op.PUSH1[JUMP_MARKER]
    code.substitute(target=len(jump) + len(revert))
    return code


@dataclass(frozen=True)
class Targets:
    """What an init-code body may need beyond the opcode itself."""

    storer: Address
    """Contract whose code performs `sstore(0, 1)`."""
    returner: Address
    """Contract that returns a known word."""
    fork: Fork
    """Lets a body size a sub-call from its callee's own cost."""


@dataclass(frozen=True)
class Context:
    """Runtime facts an expected value may depend on."""

    created: Address
    sender: Address
    init_code: Bytecode
    fork: Fork
    env: Environment


@dataclass(frozen=True)
class Case:
    """
    One opcode exercised inside a creation transaction's init code.

    `expected` is the word the deployed contract must hold. Unless
    `terminates` is set, the scaffold supplies the MSTORE/RETURN that
    puts it there, so `body` need only leave it on the stack. A callable
    body receives the pre-deployed `Targets`.
    """

    body: Bytecode | Callable[[Targets], Bytecode]
    expected: int | Callable[[Context], int] | None = None
    prefix: Bytecode = field(default_factory=Bytecode)
    terminates: bool = False
    """`body` ends the frame itself; the scaffold adds no RETURN."""
    discarded: bool = False
    """The created account must not exist once the frame ends."""
    creations: int = 0
    """Contracts the init code creates, which raise its own nonce."""
    extra: Callable[[Context], dict] | None = None
    """Further post-state entries, given the runtime context."""


def _stack(depth: int) -> tuple[Bytecode, int]:
    """
    Push `depth` distinct non-zero words, deepest first.

    Return the pushed code and the deepest value, which is what a
    correct `DUP<depth>` or `SWAP<depth - 1>` must surface.
    """
    values = [0xA0 + i for i in range(depth)]
    code = Bytecode()
    for value in values:
        code += Op.PUSH1[value]
    return code, values[0]


def _dup_op(n: int) -> Opcodes:
    """Return the `DUP<n>` opcode."""
    return getattr(Op, f"DUP{n}")


def _swap_op(n: int) -> Opcodes:
    """Return the `SWAP<n>` opcode."""
    return getattr(Op, f"SWAP{n}")


def _push_op(n: int) -> Opcodes:
    """Return the `PUSH<n>` opcode."""
    return getattr(Op, f"PUSH{n}")


def _dup_case(n: int) -> Case:
    """DUP<n> must reach exactly `n` items down the stack."""
    prep, deepest = _stack(n)
    return Case(_dup_op(n), deepest, prefix=prep)


def _swap_case(n: int) -> Case:
    """SWAP<n> must exchange the top with the item `n` below it."""
    prep, deepest = _stack(n + 1)
    return Case(_swap_op(n), deepest, prefix=prep)


def _push_case(n: int) -> Case:
    """PUSH<n> must place its whole immediate on the stack."""
    value = int.from_bytes(bytes(range(1, n + 1)), "big")
    return Case(_push_op(n)[value], value)


def _address_word(address: Address) -> int:
    """Return an address as the word an opcode would push."""
    return int.from_bytes(bytes(address), "big")


# Every opcode valid on a fork must appear here. `valid_opcodes()`
# drives the parametrization, so a newly-enabled opcode fails this test
# until a case is added; there is no opt-out.
CASES: dict[Opcodes, Case] = {
    # --- Arithmetic. Operands chosen so the answer is self-evident.
    Op.ADD: Case(Op.ADD(2, 3), 5),
    Op.MUL: Case(Op.MUL(3, 4), 12),
    Op.SUB: Case(Op.SUB(5, 3), 2),
    Op.DIV: Case(Op.DIV(12, 4), 3),
    Op.SDIV: Case(Op.SDIV(12, 4), 3),
    Op.MOD: Case(Op.MOD(7, 3), 1),
    Op.SMOD: Case(Op.SMOD(7, 3), 1),
    Op.ADDMOD: Case(Op.ADDMOD(5, 3, 4), 0),
    Op.MULMOD: Case(Op.MULMOD(5, 3, 4), 3),
    Op.EXP: Case(Op.EXP(2, 10), 1024),
    Op.SIGNEXTEND: Case(Op.SIGNEXTEND(0, 0xFF), ALL_ONES),
    # --- Comparison and bitwise.
    Op.LT: Case(Op.LT(1, 2), 1),
    Op.GT: Case(Op.GT(2, 1), 1),
    Op.SLT: Case(Op.SLT(1, 2), 1),
    Op.SGT: Case(Op.SGT(2, 1), 1),
    Op.EQ: Case(Op.EQ(3, 3), 1),
    Op.ISZERO: Case(Op.ISZERO(0), 1),
    Op.AND: Case(Op.AND(0xF0, 0x3C), 0x30),
    Op.OR: Case(Op.OR(0xF0, 0x3C), 0xFC),
    Op.XOR: Case(Op.XOR(0xF0, 0x3C), 0xCC),
    Op.NOT: Case(Op.NOT(0), ALL_ONES),
    Op.BYTE: Case(Op.BYTE(31, 0xAB), 0xAB),
    Op.SHL: Case(Op.SHL(1, 1), 2),
    Op.SHR: Case(Op.SHR(1, 2), 1),
    Op.SAR: Case(Op.SAR(1, 2), 1),
    Op.CLZ: Case(Op.CLZ(1), 255),
    # --- Frame identity. A creation frame has no calldata, and the
    # account already holds the transaction's value while init runs.
    Op.ADDRESS: Case(Op.ADDRESS, lambda c: _address_word(c.created)),
    Op.ORIGIN: Case(Op.ORIGIN, lambda c: _address_word(c.sender)),
    Op.CALLER: Case(Op.CALLER, lambda c: _address_word(c.sender)),
    Op.CALLVALUE: Case(Op.CALLVALUE, TX_VALUE),
    Op.CALLDATASIZE: Case(Op.CALLDATASIZE, 0),
    Op.CODESIZE: Case(Op.CODESIZE, lambda c: len(c.init_code)),
    Op.SELFBALANCE: Case(Op.SELFBALANCE, TX_VALUE),
    # The current block is not yet on the chain, so it hashes to zero.
    # Asking for an ancestor instead reaches into `block_hashes`, which
    # a single-block state test does not populate.
    Op.BLOCKHASH: Case(Op.BLOCKHASH(block_number=Op.NUMBER), 0),
    # A legacy transaction carries no blobs.
    Op.BLOBHASH: Case(Op.BLOBHASH(index=0), 0),
    # --- Round-trips, so a read that wrongly yields zero is
    # distinguishable from a correct one.
    Op.SLOAD: Case(Op.SLOAD(0x0), 42, prefix=Op.SSTORE(key=0x0, value=42)),
    Op.MLOAD: Case(Op.MLOAD(0x40), 7, prefix=Op.MSTORE(offset=0x40, value=7)),
    Op.TLOAD: Case(Op.TLOAD(0x0), 99, prefix=Op.TSTORE(key=0x0, value=99)),
    Op.MCOPY: Case(
        Op.MLOAD(0x80),
        7,
        prefix=Op.MSTORE(offset=0x40, value=7)
        + Op.MCOPY(dest_offset=0x80, offset=0x40, size=WORD),
    ),
    Op.MSIZE: Case(Op.MSIZE, 0x60, prefix=Op.MSTORE(offset=0x40, value=0)),
    Op.PUSH0: Case(Op.PUSH0, 0),
    # --- Reading other accounts, against their known code and balance.
    Op.EXTCODESIZE: Case(
        lambda t: Op.EXTCODESIZE(address=t.storer), len(STORER_CODE)
    ),
    Op.EXTCODEHASH: Case(
        lambda t: Op.EXTCODEHASH(address=t.storer),
        _hash_word(bytes(STORER_CODE)),
    ),
    Op.BALANCE: Case(lambda t: Op.BALANCE(address=t.storer), STORER_BALANCE),
    # --- A call reports success as its stack result.
    Op.CALL: Case(
        lambda t: Op.CALL(
            address=t.returner, gas=RETURNER_CODE.gas_cost(t.fork)
        ),
        CALL_SUCCEEDED,
    ),
    Op.CALLCODE: Case(
        lambda t: Op.CALLCODE(
            address=t.returner, gas=RETURNER_CODE.gas_cost(t.fork)
        ),
        CALL_SUCCEEDED,
    ),
    Op.DELEGATECALL: Case(
        lambda t: Op.DELEGATECALL(
            address=t.returner, gas=RETURNER_CODE.gas_cost(t.fork)
        ),
        CALL_SUCCEEDED,
    ),
    Op.STATICCALL: Case(
        lambda t: Op.STATICCALL(
            address=t.returner, gas=RETURNER_CODE.gas_cost(t.fork)
        ),
        CALL_SUCCEEDED,
    ),
    # --- Hashing a word we planted.
    Op.SHA3: Case(
        Op.SHA3(offset=0x1C0, size=WORD),
        _hash_word(SHA3_INPUT.to_bytes(WORD, "big")),
        prefix=Op.MSTORE(offset=0x1C0, value=SHA3_INPUT),
    ),
    Op.CHAINID: Case(Op.CHAINID, 1),
    # --- Jumps must clear the REVERT they skip over.
    Op.JUMP: Case(_jump_over_revert(conditional=False), JUMP_MARKER),
    Op.JUMPI: Case(_jump_over_revert(conditional=True), JUMP_MARKER),
    # A creation frame has no calldata: the transaction's `data` is this
    # init code, and it is code here, not input. An implementation that
    # also exposed it as calldata would read a non-zero word.
    Op.CALLDATALOAD: Case(Op.CALLDATALOAD(offset=0x0), 0),
    # POP must remove exactly the top item, leaving the one beneath.
    Op.POP: Case(
        Op.POP,
        POP_UNDER,
        prefix=Op.PUSH1[POP_UNDER] + Op.PUSH1[POP_TOP],
    ),
    # --- Stores and copies, each read back out of the location it
    # wrote, so an operation that did nothing fails.
    Op.MSTORE: Case(
        Op.MLOAD(0x100),
        STORE_MARKER,
        prefix=Op.MSTORE(offset=0x100, value=STORE_MARKER),
    ),
    # MSTORE8 writes one byte, which lands in the word's high end.
    Op.MSTORE8: Case(
        Op.MLOAD(0x120),
        MSTORE8_BYTE << 248,
        prefix=Op.MSTORE8(offset=0x120, value=MSTORE8_BYTE),
    ),
    Op.SSTORE: Case(
        Op.SLOAD(0x2),
        STORE_MARKER,
        prefix=Op.SSTORE(key=0x2, value=STORE_MARKER),
    ),
    Op.TSTORE: Case(
        Op.TLOAD(0x2),
        STORE_MARKER,
        prefix=Op.TSTORE(key=0x2, value=STORE_MARKER),
    ),
    # A creation frame has no calldata, so the copy must clear the
    # marker already sitting at the destination.
    Op.CALLDATACOPY: Case(
        Op.MLOAD(0x140),
        0,
        prefix=Op.MSTORE(offset=0x140, value=STORE_MARKER)
        + Op.CALLDATACOPY(dest_offset=0x140, offset=0x0, size=WORD),
    ),
    Op.CODECOPY: Case(
        Op.MLOAD(0x160),
        lambda c: _code_word(c.init_code),
        prefix=Op.CODECOPY(dest_offset=0x160, offset=0x0, size=WORD),
    ),
    Op.EXTCODECOPY: Case(
        lambda t: Op.EXTCODECOPY(
            address=t.storer, dest_offset=0x180, offset=0x0, size=WORD
        )
        + Op.MLOAD(0x180),
        _code_word(STORER_CODE),
    ),
    Op.RETURNDATASIZE: Case(
        lambda t: Op.POP(Op.CALL(address=t.returner)) + Op.RETURNDATASIZE,
        WORD,
    ),
    Op.RETURNDATACOPY: Case(
        lambda t: Op.POP(Op.CALL(address=t.returner))
        + Op.RETURNDATACOPY(dest_offset=0x1A0, offset=0x0, size=WORD)
        + Op.MLOAD(0x1A0),
        RETURNER_MARKER,
    ),
    # --- Block context, each read back against the pinned environment.
    Op.COINBASE: Case(Op.COINBASE, _address_word(COINBASE)),
    Op.NUMBER: Case(Op.NUMBER, BLOCK_NUMBER),
    Op.TIMESTAMP: Case(Op.TIMESTAMP, BLOCK_TIMESTAMP),
    Op.PREVRANDAO: Case(Op.PREVRANDAO, PREV_RANDAO),
    Op.BASEFEE: Case(Op.BASEFEE, BASE_FEE_PER_GAS),
    Op.GASLIMIT: Case(Op.GASLIMIT, lambda c: int(c.env.gas_limit)),
    Op.SLOTNUM: Case(Op.SLOTNUM, SLOT_NUMBER),
    Op.BLOBBASEFEE: Case(
        Op.BLOBBASEFEE,
        lambda c: c.fork.blob_gas_price_calculator()(
            excess_blob_gas=EXCESS_BLOB_GAS
        ),
    ),
    # --- EIP-8024 immediate-operand stack ops. DUPN[n] copies the
    # n-th item up, SWAPN[n] swaps the top with the one n below it, and
    # EXCHANGE[a, b] swaps two items beneath the top.
    Op.DUPN: Case(
        Op.DUPN[17],
        DUPN_MARKER,
        prefix=Op.PUSH1[DUPN_MARKER] + Op.PUSH0 * 16,
    ),
    Op.SWAPN: Case(
        Op.SWAPN[17],
        SWAPN_MARKER,
        prefix=Op.PUSH1[SWAPN_MARKER] + Op.PUSH0 * 17,
    ),
    Op.EXCHANGE: Case(
        Op.EXCHANGE[1, 2] + Op.POP,
        EXCHANGE_MARKER,
        prefix=Op.PUSH1[EXCHANGE_MARKER] + Op.PUSH0 * 2,
    ),
    # --- Frames that end themselves.
    Op.RETURN: Case(
        Op.MSTORE(offset=0x0, value=RETURN_MARKER)
        + Op.RETURN(offset=0x0, size=WORD),
        RETURN_MARKER,
        terminates=True,
    ),
    Op.REVERT: Case(
        Op.REVERT(offset=0x0, size=0x0), terminates=True, discarded=True
    ),
    Op.SELFDESTRUCT: Case(
        Op.SELFDESTRUCT(address=Op.ORIGIN),
        terminates=True,
        discarded=True,
    ),
    # --- Creating from within init code bumps this account's own nonce
    # and leaves the nested account behind.
    Op.CREATE: Case(
        Op.CREATE(value=0x0, offset=0x0, size=0x0),
        lambda c: _address_word(
            compute_create_address(
                address=c.created, nonce=_base_nonce(c.fork)
            )
        ),
        creations=1,
        extra=lambda c: {
            compute_create_address(
                address=c.created, nonce=_base_nonce(c.fork)
            ): Account(nonce=_base_nonce(c.fork))
        },
    ),
    Op.CREATE2: Case(
        Op.CREATE2(value=0x0, offset=0x0, size=0x0, salt=0x0),
        lambda c: _address_word(
            compute_create2_address(address=c.created, salt=0x0, initcode=b"")
        ),
        creations=1,
        extra=lambda c: {
            compute_create2_address(
                address=c.created, salt=0x0, initcode=b""
            ): Account(nonce=_base_nonce(c.fork))
        },
    ),
    # --- Arms with no value of their own: they must simply run.
    Op.STOP: Case(Op.STOP),
    Op.JUMPDEST: Case(Op.JUMPDEST),
    Op.PC: Case(Op.POP(Op.PC)),
    Op.GAS: Case(Op.POP(Op.GAS)),
    Op.GASPRICE: Case(Op.POP(Op.GASPRICE)),
    Op.LOG0: Case(Op.LOG0(offset=0x0, size=0x0)),
    Op.LOG1: Case(Op.LOG1(offset=0x0, size=0x0, topic_1=0x0)),
    Op.LOG2: Case(Op.LOG2(offset=0x0, size=0x0, topic_1=0x0, topic_2=0x0)),
    Op.LOG3: Case(
        Op.LOG3(offset=0x0, size=0x0, topic_1=0x0, topic_2=0x0, topic_3=0x0)
    ),
    Op.LOG4: Case(
        Op.LOG4(
            offset=0x0,
            size=0x0,
            topic_1=0x0,
            topic_2=0x0,
            topic_3=0x0,
            topic_4=0x0,
        )
    ),
    # Reaching other accounts.
}
CASES.update({_push_op(n): _push_case(n) for n in range(1, 33)})
CASES.update({_dup_op(n): _dup_case(n) for n in range(1, 17)})
CASES.update({_swap_op(n): _swap_case(n) for n in range(1, 17)})


def opcodes_by_fork(fork: Fork) -> Generator[ParameterSet, None, None]:
    """Yield every opcode this fork enables, identified by its name."""
    for opcode in fork.valid_opcodes():
        yield pytest.param(opcode, id=opcode._name_.lower())


@pytest.mark.ported_from(
    ["state_tests/stTransactionTest/Opcodes_TransactionInitFiller.json"],
)
@pytest.mark.valid_from("Frontier")
@pytest.mark.parametrize_by_fork("opcode", opcodes_by_fork)
def test_opcodes_transaction_init(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    opcode: Opcodes,
) -> None:
    """Run one opcode inside a creation transaction's init code."""
    case = CASES.get(opcode)
    assert case is not None, (
        f"{opcode._name_} is valid on this fork but has no case; "
        "add one to CASES"
    )

    sender = pre.fund_eoa()
    targets = Targets(
        storer=pre.deploy_contract(code=STORER_CODE, balance=STORER_BALANCE),
        returner=pre.deploy_contract(code=RETURNER_CODE),
        fork=fork,
    )
    body = case.body if isinstance(case.body, Bytecode) else case.body(targets)
    created = compute_create_address(address=sender, nonce=0)

    if case.terminates:
        init_code = case.prefix + body
    elif case.expected is None:
        init_code = case.prefix + body + Op.RETURN(offset=0x0, size=0x0)
    else:
        init_code = (
            case.prefix
            + Op.MSTORE(offset=0x0, value=body)
            + Op.RETURN(offset=0x0, size=WORD)
        )

    env = Environment.for_fork(
        fork,
        fee_recipient=COINBASE,
        number=BLOCK_NUMBER,
        timestamp=BLOCK_TIMESTAMP,
        prev_randao=PREV_RANDAO,
        base_fee_per_gas=BASE_FEE_PER_GAS,
        excess_blob_gas=EXCESS_BLOB_GAS,
        slot_number=SLOT_NUMBER,
        # Pre-merge, opcode 0x44 reads the difficulty instead.
        **(
            {}
            if fork.header_prev_randao_required()
            else {"difficulty": PREV_RANDAO}
        ),
    )
    context = Context(
        created=created,
        sender=sender,
        init_code=init_code,
        fork=fork,
        env=env,
    )
    deployed_code = b""
    if case.expected is not None:
        value = (
            case.expected(context)
            if callable(case.expected)
            else case.expected
        )
        deployed_code = value.to_bytes(WORD, "big")

    tx = Transaction(
        sender=sender,
        to=None,
        data=init_code,
        value=TX_VALUE,
        protected=fork.supports_protected_txs(),
    )

    post: dict[Address, Account | None] = {sender: Account(nonce=1)}
    post[created] = (
        Account.NONEXISTENT
        if case.discarded
        else Account(
            code=deployed_code,
            # EIP-161 starts a new contract's nonce at one; before it,
            # at zero.
            nonce=_base_nonce(fork) + case.creations,
        )
    )
    if case.extra is not None:
        post.update(case.extra(context))

    state_test(env=env, pre=pre, post=post, tx=tx)
