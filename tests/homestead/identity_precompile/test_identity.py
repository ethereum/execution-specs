"""abstract: EIP-2: Homestead Identity Precompile Test Cases."""

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
    keccak256,
)
from ethereum_test_tools import Opcodes as Op


@pytest.mark.with_all_call_opcodes()
@pytest.mark.valid_from("Byzantium")
def test_identity_return_overwrite(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
) -> None:
    """
    Test the return data of the identity precompile overwriting its input.
    """
    code = (
        sum(Op.MSTORE8(offset=i, value=(i + 1)) for i in range(4))  # memory = [1, 2, 3, 4]
        + call_opcode(
            address=4,
            args_offset=0,
            args_size=4,  # args = [1, 2, 3, 4]
            ret_offset=1,
            ret_size=4,
        )  # memory = [1, 1, 2, 3, 4]
        + Op.RETURNDATACOPY(
            dest_offset=0, offset=0, size=Op.RETURNDATASIZE()
        )  # memory correct = [1, 2, 3, 4, 4], corrupt = [1, 1, 2, 3, 4]
        + Op.SSTORE(1, Op.SHA3(offset=0, size=Op.MSIZE))
    )
    contract_address = pre.deploy_contract(
        code=code,
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract_address,
        gas_limit=100_000,
    )

    post = {
        contract_address: Account(
            storage={
                1: keccak256(bytes([1, 2, 3, 4, 4]).ljust(32, b"\0")),
            },
        ),
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.with_all_call_opcodes()
@pytest.mark.valid_from("Byzantium")
def test_identity_return_buffer_modify(
    state_test: StateTestFiller,
    pre: Alloc,
    call_opcode: Op,
) -> None:
    """
    Test the modification of the input range to attempt to modify the return
    buffer.
    """
    env = Environment()
    code = (
        sum(Op.MSTORE8(offset=i, value=(i + 1)) for i in range(4))  # memory = [1, 2, 3, 4]
        + call_opcode(
            address=4,
            args_offset=0,
            args_size=4,  # args = [1, 2, 3, 4]
        )  # memory = [1, 2, 3, 4]
        + Op.MSTORE8(offset=0, value=5)  # memory = [5, 2, 3, 4]
        + Op.MSTORE8(offset=4, value=5)  # memory = [5, 2, 3, 4, 5]
        + Op.RETURNDATACOPY(
            dest_offset=0, offset=0, size=Op.RETURNDATASIZE()
        )  # memory correct = [1, 2, 3, 4, 5], corrupt = [5, 2, 3, 4, 5]
        + Op.SSTORE(1, Op.SHA3(offset=0, size=Op.MSIZE))
    )
    contract_address = pre.deploy_contract(
        code=code,
    )
    tx = Transaction(
        sender=pre.fund_eoa(),
        to=contract_address,
        gas_limit=100_000,
    )

    post = {
        contract_address: Account(
            storage={
                1: keccak256(bytes([1, 2, 3, 4, 5]).ljust(32, b"\0")),
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
