"""
Tests for [EIP-7666: EVM-ify the identity precompile](https://eips.ethereum.org/EIPS/eip-7666).

The identity precompile is retired: seven bytes of EVM code at its
address return the calldata unchanged, observable as ordinary code and
charged ordinary EVM gas.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Fork,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    keccak256,
)

from .helpers import IDENTITY, compare_call_costs
from .spec import Spec, ref_spec_7666

REFERENCE_SPEC_GIT_PATH = ref_spec_7666.git_path
REFERENCE_SPEC_VERSION = ref_spec_7666.version

pytestmark = pytest.mark.valid_from("EIP7666")


def test_replacement_code_observable(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """
    The retired address holds exactly the specified seven bytes of
    code, sized and hashed like any contract.
    """
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(
            storage.store_next(len(Spec.EVM_CODE)), Op.EXTCODESIZE(IDENTITY)
        )
        + Op.SSTORE(
            storage.store_next(keccak256(Spec.EVM_CODE)),
            Op.EXTCODEHASH(IDENTITY),
        )
    )
    tx = Transaction(sender=pre.fund_eoa(), to=contract)
    state_test(pre=pre, tx=tx, post={contract: Account(storage=storage)})


def test_called_like_any_contract(
    state_test: StateTestFiller, pre: Alloc
) -> None:
    """
    A call to the retired address costs exactly as much as a call to a
    twin contract holding the same code: the address is neither warm at
    the start of the transaction nor priced as a precompile.
    """
    twin = pre.deploy_contract(code=Spec.EVM_CODE)
    storage = Storage()
    contract = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1), compare_call_costs(twin))
    )
    tx = Transaction(sender=pre.fund_eoa(), to=contract)
    state_test(pre=pre, tx=tx, post={contract: Account(storage=storage)})


@pytest.mark.parametrize(
    "size",
    [
        pytest.param(0, id="empty"),
        pytest.param(1, id="single_byte"),
        pytest.param(32, id="one_word"),
        pytest.param(33, id="word_plus_one"),
        pytest.param(96, id="three_words"),
    ],
)
def test_identity_equivalence(
    state_test: StateTestFiller, pre: Alloc, fork: Fork, size: int
) -> None:
    """
    The replacement returns its calldata unchanged: the returndata size
    matches the input size and the round-tripped bytes are identical.
    """
    data = Bytes(bytes(range(1, size + 1)) if size else b"")
    storage = Storage()
    code = (
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
        + Op.SSTORE(
            storage.store_next(1),
            Op.CALL(address=IDENTITY, args_size=Op.CALLDATASIZE),
        )
        + Op.SSTORE(storage.store_next(size), Op.RETURNDATASIZE)
    )
    if size:
        code += Op.RETURNDATACOPY(0x100, 0, Op.RETURNDATASIZE)
        first_word = int.from_bytes(bytes(data[:32]).ljust(32, b"\x00"), "big")
        code += Op.SSTORE(storage.store_next(first_word), Op.MLOAD(0x100))
        last_offset = 0x100 + size - 32 if size >= 32 else 0x100
        last_word = int.from_bytes(
            bytes(data[-32:]).ljust(32, b"\x00")
            if size < 32
            else bytes(data[size - 32 : size]),
            "big",
        )
        code += Op.SSTORE(storage.store_next(last_word), Op.MLOAD(last_offset))
    contract = pre.deploy_contract(code=code)
    tx = Transaction(sender=pre.fund_eoa(), to=contract, data=data)
    state_test(pre=pre, tx=tx, post={contract: Account(storage=storage)})
