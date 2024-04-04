"""
tests for selfdestruct interaction with revert
"""

from itertools import count
from typing import Dict, SupportsBytes

import pytest

from ethereum_test_forks import Cancun
from ethereum_test_tools import (
    Account,
    Address,
    Environment,
    Initcode,
    StateTestFiller,
    Storage,
    TestAddress,
    Transaction,
    YulCompiler,
    compute_create_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-6780.md"
REFERENCE_SPEC_VERSION = "2f8299df31bb8173618901a03a8366a3183479b0"

SELFDESTRUCT_ENABLE_FORK = Cancun


@pytest.fixture
def entry_code_address() -> Address:
    """Address where the entry code will run."""
    return compute_create_address(TestAddress, 0)


@pytest.fixture
def recursive_revert_contract_address() -> Address:
    """Address where the recursive revert contract address exists"""
    return Address(0xDEADBEEF)


@pytest.fixture
def env() -> Environment:
    """Default environment for all tests."""
    return Environment(
        fee_recipient="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
    )


@pytest.fixture
def selfdestruct_recipient_address() -> Address:
    """List of possible addresses that can receive a SELFDESTRUCT operation."""
    return Address(0x1234)


@pytest.fixture
def selfdestruct_on_outer_call() -> int:
    """Whether to selfdestruct the target contract in the outer call scope"""
    return 0


@pytest.fixture
def recursive_revert_contract_code(
    yul: YulCompiler,
    selfdestruct_on_outer_call: int,
    selfdestruct_with_transfer_contract_code: SupportsBytes,
    selfdestruct_with_transfer_contract_address: Address,
) -> SupportsBytes:
    """
    Contract code that:
        Given selfdestructable contract A, transfer value to A and call A.selfdestruct.
        Then, recurse into a new call which transfers value to A,
        call A.selfdestruct, and reverts.
    """
    optional_outer_call_code_1 = ""
    optional_outer_call_code_2 = ""
    optional_outer_call_code = f"""
        mstore(0, 1)
        pop(call(gaslimit(), {selfdestruct_with_transfer_contract_address}, 1, 0, 32, 0, 0))"""
    if selfdestruct_on_outer_call == 1:
        optional_outer_call_code_1 = optional_outer_call_code
    elif selfdestruct_on_outer_call == 2:
        optional_outer_call_code_2 = optional_outer_call_code

    """Contract code which calls selfdestructable contract, and also makes use of revert"""
    return yul(
        f"""
        {{
            let operation := calldataload(0)
            let op_outer_call := 0
            let op_inner_call := 1

            switch operation
            case 0 /* outer call */ {{
                // transfer value to contract and make it selfdestruct
                {optional_outer_call_code_1}

                // transfer value to the selfdestructed contract
                mstore(0, 0)
                pop(call(gaslimit(), {selfdestruct_with_transfer_contract_address}, 1, 0, 32, 0, 0))

                // recurse into self
                mstore(0, op_inner_call)
                pop(call(gaslimit(), address(), 0, 0, 32, 0, 0))

                // store the selfdestructed contract's balance for verification
                sstore(1, balance({selfdestruct_with_transfer_contract_address}))

                // transfer value to contract and make it selfdestruct
                {optional_outer_call_code_2}

                return(0, 0)
            }}
            case 1 /* inner call */ {{
                // trigger previously-selfdestructed contract to self destruct
                // and then revert

                mstore(0, 1)
                pop(call(gaslimit(), {selfdestruct_with_transfer_contract_address}, 1, 0, 32, 0, 0))
                revert(0, 0)
            }}
            default {{
                stop()
            }}
        }}
        """  # noqa: E272, E201, E202, E221, E501
    )


@pytest.fixture
def selfdestruct_with_transfer_contract_address(entry_code_address: Address) -> Address:
    """Contract address for contract that can selfdestruct and receive value"""
    res = compute_create_address(entry_code_address, 1)
    return res


@pytest.fixture
def selfdestruct_with_transfer_contract_code(
    yul: YulCompiler, selfdestruct_recipient_address: Address
) -> SupportsBytes:
    """Contract that can selfdestruct and receive value"""
    return yul(
        f"""
        {{
            let operation := calldataload(0)

            switch operation
            case 0 /* no-op used for transferring value to this contract */ {{
                let times_called := sload(0)
                times_called := add(times_called, 1)
                sstore(0, times_called)
                return(0, 0)
            }}
            case 1 /* trigger the contract to selfdestruct */ {{
                let times_called := sload(1)
                times_called := add(times_called, 1)
                sstore(1, times_called)
                selfdestruct({selfdestruct_recipient_address})
            }}
            default /* unsupported operation */ {{
                stop()
            }}
        }}
        """  # noqa: E272, E201, E202, E221
    )


@pytest.fixture
def selfdestruct_with_transfer_contract_initcode(
    selfdestruct_with_transfer_contract_code: SupportsBytes,
) -> SupportsBytes:
    """Initcode for selfdestruct_with_transfer_contract_code"""
    return Initcode(deploy_code=selfdestruct_with_transfer_contract_code)


@pytest.fixture
def selfdestruct_with_transfer_initcode_copy_from_address() -> Address:
    """Address of a pre-existing contract we use to simply copy initcode from."""
    return Address(0xABCD)


@pytest.fixture
def pre(
    recursive_revert_contract_address: Address,
    recursive_revert_contract_code: SupportsBytes,
    selfdestruct_with_transfer_initcode_copy_from_address: Address,
    selfdestruct_with_transfer_contract_initcode: SupportsBytes,
    selfdestruct_with_transfer_contract_address: Address,
    yul: YulCompiler,
) -> Dict[Address, Account]:
    """Prestate for test_selfdestruct_not_created_in_same_tx_with_revert"""
    return {
        TestAddress: Account(balance=100_000_000_000_000_000_000),
        selfdestruct_with_transfer_initcode_copy_from_address: Account(
            code=selfdestruct_with_transfer_contract_initcode
        ),
        recursive_revert_contract_address: Account(code=recursive_revert_contract_code, balance=3),
    }


@pytest.mark.parametrize(
    "selfdestruct_on_outer_call",
    [0, 1, 2],
    ids=[
        "no_outer_selfdestruct",
        "outer_selfdestruct_before_inner_call",
        "outer_selfdestruct_after_inner_call",
    ],
)
@pytest.mark.valid_from("Cancun")
def test_selfdestruct_created_in_same_tx_with_revert(  # noqa SC200
    state_test: StateTestFiller,
    env: Environment,
    pre: Dict[Address, Account],
    entry_code_address: Address,
    selfdestruct_on_outer_call: int,
    selfdestruct_with_transfer_contract_code: SupportsBytes,
    selfdestruct_with_transfer_contract_initcode: SupportsBytes,
    selfdestruct_with_transfer_contract_address: Address,
    selfdestruct_recipient_address: Address,
    selfdestruct_with_transfer_initcode_copy_from_address: Address,
    recursive_revert_contract_address: Address,
    recursive_revert_contract_code: SupportsBytes,
):
    """
    Given:
        Contract A which has methods to receive balance and selfdestruct, and was created in current tx
    Test the following call sequence:
         Transfer value to A and call A.selfdestruct.
         Recurse into a new call from transfers value to A, calls A.selfdestruct, and reverts.
    """  # noqa: E501
    entry_code = Op.EXTCODECOPY(
        selfdestruct_with_transfer_initcode_copy_from_address,
        0,
        0,
        len(bytes(selfdestruct_with_transfer_contract_initcode)),
    )

    entry_code += Op.SSTORE(
        0,
        Op.CREATE(
            0, 0, len(bytes(selfdestruct_with_transfer_contract_initcode))  # Value  # Offset
        ),
    )

    entry_code += Op.CALL(
        Op.GASLIMIT(),
        recursive_revert_contract_address,
        0,  # value
        0,  # arg offset
        0,  # arg length
        0,  # ret offset
        0,  # ret length
    )

    post: Dict[Address, Account] = {
        entry_code_address: Account(
            code="0x", storage=Storage({0: selfdestruct_with_transfer_contract_address})
        ),
        selfdestruct_with_transfer_initcode_copy_from_address: Account(
            code=selfdestruct_with_transfer_contract_initcode,
        ),
        recursive_revert_contract_address: Account(
            code=recursive_revert_contract_code,
            storage=Storage({1: 1}),
        ),
    }

    if selfdestruct_on_outer_call > 0:
        post[selfdestruct_with_transfer_contract_address] = Account.NONEXISTENT  # type: ignore
        post[selfdestruct_recipient_address] = Account(
            balance=1 if selfdestruct_on_outer_call == 1 else 2,
        )
    else:
        post[selfdestruct_with_transfer_contract_address] = Account(
            balance=1,
            code=selfdestruct_with_transfer_contract_code,
            storage=Storage(
                {
                    # 2 value transfers (1 in outer call, 1 in reverted inner call)
                    0: 1,
                    # 1 selfdestruct in reverted inner call
                    1: 0,
                }
            ),
        )
        post[selfdestruct_recipient_address] = Account.NONEXISTENT  # type: ignore

    nonce = count()
    tx = Transaction(
        ty=0x0,
        value=0,
        data=entry_code,
        chain_id=0x0,
        nonce=next(nonce),
        to=None,
        gas_limit=100_000_000,
        gas_price=10,
        protected=False,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.fixture
def pre_with_selfdestructable(  # noqa: SC200
    recursive_revert_contract_address: Address,
    recursive_revert_contract_code: SupportsBytes,
    selfdestruct_with_transfer_initcode_copy_from_address: Address,
    selfdestruct_with_transfer_contract_initcode: SupportsBytes,
    selfdestruct_with_transfer_contract_address: Address,
    yul: YulCompiler,
) -> Dict[Address, Account]:
    """Preset for selfdestruct_not_created_in_same_tx_with_revert"""
    return {
        TestAddress: Account(balance=100_000_000_000_000_000_000),
        selfdestruct_with_transfer_initcode_copy_from_address: Account(
            code=selfdestruct_with_transfer_contract_initcode
        ),
        recursive_revert_contract_address: Account(code=recursive_revert_contract_code, balance=2),
    }


@pytest.mark.parametrize(
    "selfdestruct_on_outer_call",
    [0, 1, 2],
    ids=[
        "no_outer_selfdestruct",
        "outer_selfdestruct_before_inner_call",
        "outer_selfdestruct_after_inner_call",
    ],
)
@pytest.mark.valid_from("Cancun")
def test_selfdestruct_not_created_in_same_tx_with_revert(
    state_test: StateTestFiller,
    env: Environment,
    entry_code_address: Address,
    selfdestruct_on_outer_call: int,
    selfdestruct_with_transfer_contract_code: SupportsBytes,
    selfdestruct_with_transfer_contract_address: Address,
    selfdestruct_recipient_address: Address,
    recursive_revert_contract_address: Address,
    recursive_revert_contract_code: SupportsBytes,
):
    """
    Same test as selfdestruct_created_in_same_tx_with_revert except selfdestructable contract
    is pre-existing
    """
    entry_code = Op.CALL(
        Op.GASLIMIT(),
        recursive_revert_contract_address,
        0,  # value
        0,  # arg offset
        0,  # arg length
        0,  # ret offset
        0,  # ret length
    )

    pre: Dict[Address, Account] = {
        TestAddress: Account(balance=100_000_000_000_000_000_000),
        selfdestruct_with_transfer_contract_address: Account(
            code=selfdestruct_with_transfer_contract_code
        ),
        recursive_revert_contract_address: Account(
            code=bytes(recursive_revert_contract_code), balance=2
        ),
    }

    post: Dict[Address, Account] = {
        entry_code_address: Account(code="0x"),
    }

    if selfdestruct_on_outer_call > 0:
        post[selfdestruct_with_transfer_contract_address] = Account(
            balance=1 if selfdestruct_on_outer_call == 1 else 0,
            code=selfdestruct_with_transfer_contract_code,
            storage=Storage(
                {
                    # 2 value transfers: 1 in outer call, 1 in reverted inner call
                    0: 1,
                    # 1 selfdestruct in reverted inner call
                    1: 1,
                }
            ),
        )
        post[selfdestruct_recipient_address] = Account(
            balance=1 if selfdestruct_on_outer_call == 1 else 2
        )
    else:
        post[selfdestruct_with_transfer_contract_address] = Account(
            balance=1,
            code=selfdestruct_with_transfer_contract_code,
            storage=Storage(
                {
                    # 2 value transfers: 1 in outer call, 1 in reverted inner call
                    0: 1,
                    # 2 selfdestructs: 1 in outer call, 1 in reverted inner call # noqa SC100
                    1: 0,
                }
            ),
        )
        post[selfdestruct_recipient_address] = Account.NONEXISTENT  # type: ignore

    nonce = count()
    tx = Transaction(
        ty=0x0,
        value=0,
        data=entry_code,
        chain_id=0x0,
        nonce=next(nonce),
        to=None,
        gas_limit=100_000_000,
        gas_price=10,
        protected=False,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
