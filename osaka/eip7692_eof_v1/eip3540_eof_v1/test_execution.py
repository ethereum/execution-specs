"""
Execution of basic EOF containers.
"""

import pytest

from ethereum_test_base_types import Storage
from ethereum_test_tools import Account, Alloc, Environment, StateTestFiller, Transaction
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "8dcb0a8c1c0102c87224308028632cc986a61183"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)

EXPECTED_STORAGE = (bytes.fromhex("EF"), bytes.fromhex("BADDCAFE"))
"""Expected storage (key => value) to be produced by the EOF containers"""


@pytest.mark.parametrize(
    "container",
    (
        Container(
            name="store_from_push",
            sections=[Section.Code(Op.SSTORE(*EXPECTED_STORAGE) + Op.STOP)],
        ),
        Container(
            name="store_with_data",
            sections=[
                Section.Code(Op.SSTORE(Op.DATALOADN[0], Op.DATALOADN[32]) + Op.STOP),
                Section.Data(
                    EXPECTED_STORAGE[0].rjust(32, b"\x00") + EXPECTED_STORAGE[1].rjust(32, b"\x00")
                ),
            ],
        ),
    ),
    ids=lambda x: x.name,
)
def test_eof_execution(
    state_test: StateTestFiller,
    pre: Alloc,
    container: Container,
):
    """
    Test simple contracts that are expected to succeed on call.
    """
    env = Environment()

    storage = Storage()
    sender = pre.fund_eoa()
    container_address = pre.deploy_contract(container)
    caller_contract = Op.SSTORE(
        storage.store_next(1), Op.CALL(Op.GAS, container_address, 0, 0, 0, 0, 0)
    )
    caller_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        to=caller_address,
        gas_limit=1_000_000,
        gas_price=10,
        protected=False,
        sender=sender,
    )

    post = {
        caller_address: Account(storage=storage),
        container_address: Account(storage=dict([EXPECTED_STORAGE])),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
