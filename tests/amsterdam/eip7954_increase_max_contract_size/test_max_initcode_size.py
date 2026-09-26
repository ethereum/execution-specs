"""
Test [EIP-7954: Increase Maximum Contract Size](https://eips.ethereum.org/EIPS/eip-7954).

Tests for the increased maximum initcode size (128 KiB).
"""

from typing import Any, Callable

import pytest
from execution_testing import (
    Account,
    Alloc,
    BalAccountExpectation,
    BlockAccessListExpectation,
    Fork,
    Initcode,
    Op,
    StateTestFiller,
    Transaction,
    TransactionException,
    TransactionReceipt,
    compute_create_address,
    create_op,
    keccak256,
)
from execution_testing import Macros as Om
from execution_testing.forks import Osaka

from .spec import ref_spec_7954

REFERENCE_SPEC_GIT_PATH = ref_spec_7954.git_path
REFERENCE_SPEC_VERSION = ref_spec_7954.version

pytestmark = pytest.mark.valid_from("EIP7954")

SENTINEL = 0xFF
"""Pre-set storage value that only a store which actually ran can replace."""

INITCODE_SIZE_PARAMS = [
    pytest.param(
        lambda _: Osaka.max_initcode_size() + 1, id="over_previous_max"
    ),
    pytest.param(lambda f: f.max_initcode_size() - 1, id="under_max"),
    pytest.param(lambda f: f.max_initcode_size(), id="at_max"),
    pytest.param(lambda f: f.max_initcode_size() + 1, id="over_max"),
]

TX_INITCODE_SIZE_PARAMS = [
    pytest.param(
        lambda _: Osaka.max_initcode_size() + 1, id="over_previous_max"
    ),
    pytest.param(lambda f: f.max_initcode_size() - 1, id="under_max"),
    pytest.param(lambda f: f.max_initcode_size(), id="at_max"),
    pytest.param(
        lambda f: f.max_initcode_size() + 1,
        id="over_max",
        marks=pytest.mark.exception_test,
    ),
]


@pytest.mark.inclusion_test
@pytest.mark.parametrize("initcode_size", TX_INITCODE_SIZE_PARAMS)
def test_max_initcode_size(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode_size: Callable[[Fork], int],
) -> None:
    """Ensure the new max initcode size is enforced for transactions."""
    size = initcode_size(fork)
    initcode = Initcode(
        deploy_code=Op.STOP,
        initcode_length=size,
    )

    alice = pre.fund_eoa()
    create_address = compute_create_address(address=alice, nonce=0)

    tx = Transaction(
        sender=alice,
        to=None,
        data=initcode,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    post: dict[Any, Account | None] = {}
    if size <= fork.max_initcode_size():
        post[create_address] = Account(code=Op.STOP)
    else:
        tx.error = TransactionException.INITCODE_SIZE_EXCEEDED
        post[create_address] = Account.NONEXISTENT

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize("initcode_size", INITCODE_SIZE_PARAMS)
@pytest.mark.with_all_create_opcodes()
def test_max_initcode_size_via_create(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    initcode_size: Callable[[Fork], int],
    create_opcode: Op,
) -> None:
    """Ensure the new max initcode size is enforced via create opcodes."""
    size = initcode_size(fork)
    initcode = Initcode(
        deploy_code=Op.STOP,
        initcode_length=size,
    )
    initcode_bytes = bytes(initcode)

    alice = pre.fund_eoa()

    create_call = create_op(create_opcode, size=Op.CALLDATASIZE)

    factory_code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(0, create_call)
        + Op.STOP
    )

    factory = pre.deploy_contract(factory_code, storage={0: SENTINEL})

    create_address = compute_create_address(
        address=factory,
        nonce=1,
        initcode=initcode,
        opcode=create_opcode,
    )

    tx = Transaction(
        sender=alice,
        to=factory,
        data=initcode_bytes,
        gas_limit=fork.transaction_gas_limit_cap(),
    )

    # An oversized initcode aborts the create opcode before any child frame
    # runs, taking the factory frame down with it, so the sentinel survives.
    created = size <= fork.max_initcode_size()
    post: dict[Any, Account | None] = {
        factory: Account(storage={0: create_address if created else SENTINEL}),
    }
    bal = None
    if created:
        post[create_address] = Account(code=Op.STOP)
    else:
        # The child address is never computed, so it must be missing from
        # the block access list, and the aborted factory frame leaves no
        # changes of its own. The abort is an exceptional halt, so the
        # whole gas allowance burns: a client that merely reverted the
        # factory would leave the same state but refund the rest.
        tx.expected_receipt = TransactionReceipt(
            cumulative_gas_used=tx.gas_limit
        )
        post[create_address] = Account.NONEXISTENT
        bal = BlockAccessListExpectation(
            account_expectations={
                factory: BalAccountExpectation.empty(),
                create_address: None,
            }
        )

    state_test(pre=pre, tx=tx, post=post, expected_block_access_list=bal)


@pytest.mark.inclusion_test
@pytest.mark.parametrize(
    "gas_limit_delta",
    [
        pytest.param(
            -1,
            id="below_floor",
            marks=pytest.mark.exception_test,
        ),
        pytest.param(0, id="at_floor"),
        # Slack above the floor separates the gas limit from the gas
        # charged, so the receipt can only match if the floor is priced.
        pytest.param(100_000, id="above_floor"),
    ],
)
def test_max_initcode_size_calldata_floor(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_limit_delta: int,
) -> None:
    """
    Ensure a creation transaction carrying a max-size initcode must cover the
    calldata floor of that initcode, and pays exactly it.
    """
    initcode = Initcode(
        deploy_code=Op.STOP, initcode_length=fork.max_initcode_size()
    )
    alice = pre.fund_eoa()

    floor_gas = fork.transaction_data_floor_cost_calculator()(
        data=initcode, contract_creation=True
    )
    intrinsic_gas = fork.transaction_intrinsic_cost_calculator()(
        calldata=initcode,
        contract_creation=True,
        return_cost_deducted_prior_execution=True,
    )
    # An initcode this large costs more by the floor than by the intrinsic
    # cost, so the floor is the threshold the transaction is held to and the
    # shortfall case is rejected for missing the floor, not the intrinsic.
    assert floor_gas > intrinsic_gas

    tx = Transaction(
        sender=alice,
        to=None,
        data=initcode,
        gas_limit=floor_gas + gas_limit_delta,
    )

    create_address = compute_create_address(address=alice, nonce=0)
    post: dict[Any, Account | None] = {}
    if gas_limit_delta < 0:
        tx.error = TransactionException.INTRINSIC_GAS_BELOW_FLOOR_GAS_COST
        post[create_address] = Account.NONEXISTENT
    else:
        # The deployment spends a fraction of the floor, so the floor is
        # what the sender is charged, spare gas or not.
        tx.expected_receipt = TransactionReceipt(cumulative_gas_used=floor_gas)
        post[create_address] = Account(code=Op.STOP)

    state_test(pre=pre, tx=tx, post=post)


def test_max_initcode_size_code_opcodes(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Ensure the self code opcodes see a max-size initcode in full while it
    runs.
    """
    max_initcode_size = fork.max_initcode_size()
    logic = (
        Op.SSTORE(0, Op.CODESIZE)
        + Op.CODECOPY(0, 0, Op.CODESIZE)
        + Op.SSTORE(1, Op.SHA3(0, Op.CODESIZE))
        + Op.RETURN(0, 0)
    )
    # The unwritten initcode bytes stay zero, so the factory only stores the
    # leading logic.
    initcode_bytes = bytes(logic).ljust(max_initcode_size, b"\x00")

    factory = pre.deploy_contract(
        Om.MSTORE(bytes(logic), 0)
        + Op.SSTORE(0, Op.CREATE(value=0, offset=0, size=max_initcode_size))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    create_address = compute_create_address(address=factory, nonce=1)

    tx = Transaction(sender=pre.fund_eoa(), to=factory)

    post: dict[Any, Account | None] = {
        factory: Account(storage={0: create_address}),
        create_address: Account(
            code=b"",
            storage={
                0: max_initcode_size,
                1: keccak256(initcode_bytes),
            },
        ),
    }

    state_test(pre=pre, tx=tx, post=post)


def test_max_initcode_size_linear_execution(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """
    Ensure a max-size initcode executes from its first byte to its last
    without a jump.

    The factory assembles the initcode in memory from two copies of a
    `MAX_CODE_SIZE` JUMPDEST contract, overwrites the last word with a
    store and a RETURN, and runs CREATE over it. The child's storage can
    only be set by stepping through every byte before the tail.
    """
    max_code_size = fork.max_code_size()
    max_initcode_size = fork.max_initcode_size()
    assert max_initcode_size == 2 * max_code_size

    source = pre.deploy_contract(Op.JUMPDEST * max_code_size)
    tail = Op.SSTORE(0, 1) + Op.RETURN(0, 0)
    last_word = bytes(Op.JUMPDEST * (32 - len(tail)) + tail)

    factory = pre.deploy_contract(
        Op.EXTCODECOPY(source, 0, 0, max_code_size)
        + Op.EXTCODECOPY(source, max_code_size, 0, max_code_size)
        + Om.MSTORE(last_word, max_initcode_size - 32)
        + Op.SSTORE(0, Op.CREATE(value=0, offset=0, size=max_initcode_size))
        + Op.STOP,
        storage={0: SENTINEL},
    )
    create_address = compute_create_address(address=factory, nonce=1)

    tx = Transaction(sender=pre.fund_eoa(), to=factory)

    post: dict[Any, Account | None] = {
        factory: Account(storage={0: create_address}),
        create_address: Account(code=b"", storage={0: 1}),
    }

    state_test(pre=pre, tx=tx, post=post)


@pytest.mark.parametrize(
    "past_end,valid_jumpdest",
    [
        pytest.param(False, True, id="valid_high_jumpdest"),
        pytest.param(False, False, id="invalid_high_dest"),
        # The tail and its JUMPDEST are in place, but the target is
        # MAX_INITCODE_SIZE itself, one past the last byte.
        pytest.param(True, True, id="invalid_past_end"),
    ],
)
def test_max_initcode_size_high_jumpdest(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    past_end: bool,
    valid_jumpdest: bool,
) -> None:
    """
    Ensure jumpdest analysis reaches the last bytes of a max-size initcode,
    far past the previous initcode limit, and stops at its end.
    """
    max_initcode_size = fork.max_initcode_size()
    tail = Op.JUMPDEST + Op.SSTORE(0, 1) + Op.RETURN(0, 0)
    tail_offset = max_initcode_size - len(tail)
    dest = max_initcode_size if past_end else tail_offset
    push_size = (dest.bit_length() + 7) // 8
    push_op = getattr(Op, f"PUSH{push_size}")

    factory_code = Om.MSTORE(bytes(push_op(dest) + Op.JUMP), 0)
    # Without the tail the jump lands on a zero byte, a STOP that is not a
    # valid jump destination.
    if valid_jumpdest:
        factory_code += Om.MSTORE(bytes(tail), tail_offset)
    factory_code += (
        Op.SSTORE(0, Op.CREATE(value=0, offset=0, size=max_initcode_size))
        + Op.STOP
    )

    factory = pre.deploy_contract(factory_code, storage={0: SENTINEL})
    create_address = compute_create_address(address=factory, nonce=1)

    tx = Transaction(sender=pre.fund_eoa(), to=factory)

    post: dict[Any, Account | None] = {}
    if valid_jumpdest and not past_end:
        post[factory] = Account(storage={0: create_address})
        post[create_address] = Account(storage={0: 1})
    else:
        post[factory] = Account(storage={0: 0})
        post[create_address] = Account.NONEXISTENT

    state_test(pre=pre, tx=tx, post=post)
