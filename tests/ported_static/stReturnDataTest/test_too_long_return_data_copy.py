"""
Test RETURNDATACOPY bounds against the length a callee returned.

The original tests were written by Ori Pomerantz (qbzzt1@gmail.com).

Ported from:
state_tests/stReturnDataTest/tooLongReturnDataCopyFiller.yml

@manually-enhanced: Do not overwrite. Parametrized on the returned length,
the copied range and the callee's exit, with the outcome derived from
whether the copied range fits in the return data. The calldata selector,
gas price and gas limit are dropped.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

UNTOUCHED = 0x60A7
SUCCESS = 0xDEAD


@pytest.mark.ported_from(
    ["state_tests/stReturnDataTest/tooLongReturnDataCopyFiller.yml"],
)
@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    "callee_reverts", [False, True], ids=["return", "revert"]
)
@pytest.mark.parametrize(
    "returned_length, copy_offset, copy_length",
    [
        (0x0, 0x0, 0x0),
        (0x0, 0x0, 0x1),
        (0x10, 0x0, 0x8),
        (0x10, 0x0, 0x10),
        (0x10, 0x0, 0x11),
        (0x10, 0x1, 0xF),
        (0x10, 0x1, 0x10),
        (0x10, 0x8, 0x8),
        (0x10, 0x9, 0x8),
        (0x10, 0x10, 0x8),
        (0x10, 0x10, 0x10),
        (0x10, 0x20, 0x10),
    ],
)
def test_too_long_return_data_copy(
    state_test: StateTestFiller,
    pre: Alloc,
    returned_length: int,
    copy_offset: int,
    copy_length: int,
    callee_reverts: bool,
) -> None:
    """
    Copy a range of the data a callee returned or reverted with.

    The copy succeeds only when `copy_offset + copy_length` fits within
    `returned_length`; otherwise RETURNDATACOPY halts the frame and the
    target's storage keeps its pre-set value. A successful run also shows
    that the other copy opcodes may read past the end of their source.
    """
    sender = pre.fund_eoa()

    returning_callee = pre.deploy_contract(
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.MSTORE(
            offset=0x0,
            value=0x1F1E1D1C1B1A191817161514131211100F0E0D0C0B0A090807060504030201FF,  # noqa: E501
        )
        + Op.SSTORE(key=0x0, value=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.RETURN,
    )
    reverting_callee = pre.deploy_contract(
        code=Op.CALLDATALOAD(offset=0x0)
        + Op.MSTORE(
            offset=0x0,
            value=0x1F1E1D1C1B1A191817161514131211100F0E0D0C0B0A090807060504030201FF,  # noqa: E501
        )
        + Op.SSTORE(key=0x0, value=Op.DUP1)
        + Op.PUSH1[0x0]
        + Op.REVERT,
    )
    # Calldata: returned length, copy offset, copy length, callee address.
    target = pre.deploy_contract(
        # Ask the callee to return (or revert with) `returned_length` bytes.
        code=Op.MSTORE(offset=0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.POP(
            Op.CALL(
                address=Op.CALLDATALOAD(offset=0x60),
                args_offset=0,
                args_size=0x20,
                ret_offset=0,
                ret_size=0x100,
            )
        )
        # Halts the frame if the copied range overruns the return data.
        + Op.RETURNDATACOPY(
            dest_offset=0x100,
            offset=Op.CALLDATALOAD(offset=0x20),
            size=Op.CALLDATALOAD(offset=0x40),
        )
        # The other copy opcodes may read past the end of their source.
        + Op.EXTCODECOPY(
            address=returning_callee,
            dest_offset=0,
            offset=0,
            size=Op.ADD(0x20, Op.EXTCODESIZE(address=returning_callee)),
        )
        + Op.CALLDATACOPY(
            dest_offset=0, offset=0, size=Op.ADD(0x20, Op.CALLDATASIZE)
        )
        + Op.CODECOPY(dest_offset=0, offset=0, size=Op.ADD(0x20, Op.CODESIZE))
        + Op.SSTORE(key=0x0, value=SUCCESS)
        + Op.STOP,
        storage={0: UNTOUCHED},
    )

    callee = reverting_callee if callee_reverts else returning_callee
    succeeds = copy_offset + copy_length <= returned_length
    post = {target: Account(storage={0: SUCCESS if succeeds else UNTOUCHED})}

    tx = Transaction(
        sender=sender,
        to=target,
        data=Hash(returned_length)
        + Hash(copy_offset)
        + Hash(copy_length)
        + Hash(callee, left_padding=True),
    )

    state_test(pre=pre, post=post, tx=tx)
