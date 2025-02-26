"""Test good and bad EOFCREATE cases."""

import pytest

from ethereum_test_base_types import Account, Storage
from ethereum_test_tools import Alloc, Environment, StateTestFiller, compute_eofcreate_address
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types import Transaction

from .. import EOF_FORK_NAME
from .helpers import (
    slot_code_worked,
    slot_create_address,
    smallest_initcode_subcontainer,
    smallest_runtime_subcontainer,
    value_canary_to_be_overwritten,
    value_code_worked,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7620.md"
REFERENCE_SPEC_VERSION = "52ddbcdddcf72dd72427c319f2beddeb468e1737"

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)


@pytest.mark.parametrize(
    "offset_field",
    [
        pytest.param(True, id="offset"),
        pytest.param(False, id="size"),
    ],
)
@pytest.mark.parametrize(
    ("test_arg", "success"),
    [
        pytest.param(0, True, id="zero"),
        pytest.param(0xFF, True, id="8-bit"),
        pytest.param(0x100, True, id="9-bit"),
        pytest.param(0xFFFF, True, id="16-bit"),
        pytest.param(0x10000, True, id="17-bit"),
        pytest.param(0x1FFFF20, False, id="32-bit-mem-cost"),
        pytest.param(0x2D412E0, False, id="33-bit-mem-cost"),
        pytest.param(0xFFFFFFFF, False, id="32-bit"),
        pytest.param(0x100000000, False, id="33-bit"),
        pytest.param(0x1FFFFFFFF20, False, id="64-bit-mem-cost"),
        pytest.param(0x2D413CCCF00, False, id="65-bit-mem-cost"),
        pytest.param(0xFFFFFFFFFFFFFFFF, False, id="64-bit"),
        pytest.param(0x10000000000000000, False, id="65-bit"),
        pytest.param(0xFFFFFFFFFFFFFFFF, False, id="128-bit"),
        pytest.param(0x10000000000000000, False, id="129-bit"),
        pytest.param(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF, False, id="256-bit"),
    ],
)
def test_eofcreate_memory(
    state_test: StateTestFiller,
    pre: Alloc,
    offset_field: str,
    test_arg: int,
    success: bool,
):
    """
    Tests auxdata sizes in EOFCREATE including multiple offset conditions.

    EOFCREATE either succeeds or fails based on memory access cost, resulting in new address
    or zero in the create address slot.

    The name id of `*-mem-cost` refers to the bit-length of the result of the calculated memory
    expansion cost. Their length choice is designed to cause problems on shorter bit-length
    representations with native integers.

    The `offset_field` param indicates what part of the input data arguments are being tested,
    either the offset of the data in memory or the size of the data in memory.

    The `test_arg` param is the value passed into the field being tested (offset or size),
    intending to trigger integer size bugs for that particular field.
    """
    env = Environment()

    sender = pre.fund_eoa(10**27)

    initial_storage = Storage(
        {
            slot_create_address: value_canary_to_be_overwritten,  # type: ignore
            slot_code_worked: value_canary_to_be_overwritten,  # type: ignore
        }
    )
    calling_contract_address = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(
                        slot_create_address,
                        Op.EOFCREATE[0](
                            value=0,
                            salt=0,
                            input_offset=test_arg if offset_field else 32,
                            input_size=32 if offset_field else test_arg,
                        ),
                    )
                    + Op.SSTORE(slot_code_worked, value_code_worked)
                    + Op.STOP,
                ),
                Section.Container(container=smallest_initcode_subcontainer),
            ]
        ),
        storage=initial_storage,
    )
    destination_contract_address = compute_eofcreate_address(calling_contract_address, 0)

    post = {
        calling_contract_address: Account(
            storage={
                slot_create_address: destination_contract_address,
                slot_code_worked: value_code_worked,
            }
            if success
            else initial_storage,
        ),
        destination_contract_address: Account(code=smallest_runtime_subcontainer)
        if success
        else Account.NONEXISTENT,
    }

    tx = Transaction(sender=sender, to=calling_contract_address, gas_limit=2_000_000_000)

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
