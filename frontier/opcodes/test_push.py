"""
A State test for the set of `PUSH*` opcodes.
Ported from: https://github.com/ethereum/tests/blob/4f65a0a7cbecf4442415c226c65e089acaaf6a8b/src/GeneralStateTestsFiller/VMTests/vmTests/pushFiller.yml.
"""  # noqa: E501

import pytest

from ethereum_test_forks import Fork, Frontier, Homestead
from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools import Opcodes as Op


def get_input_for_push_opcode(opcode: Op) -> bytes:
    """
    Get a sample input for the `PUSH*` opcode.

    The input is a portion of an excerpt from the Ethereum yellow paper.
    """
    ethereum_state_machine = b"Ethereum is a transaction-based state machine."
    input_size = opcode.data_portion_length
    return ethereum_state_machine[0:input_size]


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/VMTests/vmTests/pushFiller.yml",
    ],
    pr=["https://github.com/ethereum/execution-spec-tests/pull/975"],
)
@pytest.mark.parametrize(
    "push_opcode",
    [getattr(Op, f"PUSH{i}") for i in range(1, 33)],  # Dynamically parametrize PUSH opcodes
    ids=lambda op: str(op),
)
@pytest.mark.valid_from("Frontier")
def test_push(state_test: StateTestFiller, fork: Fork, pre: Alloc, push_opcode: Op):
    """
    The set of `PUSH*` opcodes pushes data onto the stack.

    In this test, we ensure that the set of `PUSH*` opcodes writes
    a portion of an excerpt from the Ethereum yellow paper to
    storage.
    """
    # Input used to test the `PUSH*` opcode.
    excerpt = get_input_for_push_opcode(push_opcode)

    env = Environment()

    """
     **               Bytecode explanation              **
     +---------------------------------------------------+
     | Bytecode      | Stack        | Storage            |
     |---------------------------------------------------|
     | PUSH* excerpt | excerpt      |                    |
     | PUSH1 0       | 0 excerpt    |                    |
     | SSTORE        |              | [0]: excerpt       |
     +---------------------------------------------------+
    """

    contract_code = push_opcode(excerpt) + Op.PUSH1(0) + Op.SSTORE
    contract = pre.deploy_contract(contract_code)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        gas_limit=500_000,
        protected=False if fork in [Frontier, Homestead] else True,
    )

    post = {}
    post[contract] = Account(storage={0: int.from_bytes(excerpt, byteorder="big")})

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/VMTests/vmTests/pushFiller.yml",
    ],
    pr=["https://github.com/ethereum/execution-spec-tests/pull/975"],
)
@pytest.mark.parametrize(
    "push_opcode",
    [getattr(Op, f"PUSH{i}") for i in range(1, 33)],
    ids=lambda op: str(op),
)
@pytest.mark.parametrize("stack_height", range(1024, 1026))
@pytest.mark.valid_from("Frontier")
def test_stack_overflow(
    state_test: StateTestFiller, fork: Fork, pre: Alloc, push_opcode: Op, stack_height: int
):
    """A test to ensure that the stack overflows when the stack limit of 1024 is exceeded."""
    env = Environment()

    # Input used to test the `PUSH*` opcode.
    excerpt = get_input_for_push_opcode(push_opcode)

    """
    Essentially write a n-byte message to storage by pushing [1024,1025] times to stack. This
    simulates a "jump" over the stack limit of 1024.

    The message is UTF-8 encoding of excerpt (say 0x45 for PUSH1). Within the stack limit,
    the message is written to the to the storage at the same offset (0x45 for PUSH1).
    The last iteration will overflow the stack and the storage slot will be empty.

     **               Bytecode explanation              **
     +---------------------------------------------------+
     | Bytecode      | Stack        | Storage            |
     |---------------------------------------------------|
     | PUSH* excerpt | excerpt      |                    |
     | PUSH1 0       | 0 excerpt    |                    |
     | SSTORE        |              | [0]: excerpt       |
     +---------------------------------------------------+
    """
    contract_code = push_opcode(excerpt) * stack_height + Op.SSTORE
    contract = pre.deploy_contract(contract_code)

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract,
        gas_limit=500_000,
        protected=False if fork in [Frontier, Homestead] else True,
    )

    post = {}
    key = int.from_bytes(excerpt, "big")

    # Storage should ONLY have the message if stack does not overflow.
    value = key if stack_height <= 1024 else 0

    post[contract] = Account(storage={key: value})

    state_test(env=env, pre=pre, post=post, tx=tx)
