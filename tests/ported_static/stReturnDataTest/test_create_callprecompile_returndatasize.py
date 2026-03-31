"""
Test_create_callprecompile_returndatasize.

Ported from:
state_tests/stReturnDataTest/create_callprecompile_returndatasizeFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    Fork,
)
from execution_testing.vm import Op

from execution_testing.forks import Amsterdam

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stReturnDataTest/create_callprecompile_returndatasizeFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_callprecompile_returndatasize(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test_create_callprecompile_returndatasize."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x834185262E53584684BF2B72C64E510013C235D0F45E462DB65900455DF45A35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    # Source: lll
    # { (seq (MSTORE 0 0x0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff) (RETURN 0 32)) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF,  # noqa: E501
        )
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.STOP,
        nonce=0,
        address=Address(0x9898DD5E5C526B55EC49B1047E298705C13279F1),  # noqa: E501
    )
    # Source: lll
    # { (seq (CREATE 0 0 (lll (seq (mstore 0 0x112233) (CALL 0x9000 4 0 0 32 0 32) (SSTORE 0 (RETURNDATASIZE)) (RETURN 0 32) (STOP) ) 0)) (SSTORE 0 (RETURNDATASIZE)) (STOP) )}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x23]
        + Op.CODECOPY(dest_offset=0x0, offset=0x15, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.POP(Op.CREATE)
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.STOP * 2
        + Op.INVALID
        + Op.MSTORE(offset=0x0, value=0x112233)
        + Op.POP(
            Op.CALL(
                gas=0x9000,
                address=0x4,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x20,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.STOP * 2,
        storage={0: 1},
        nonce=0,
        address=Address(0xA2412B1E2A1E23E8FD87F52566C8A89F48682676),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
    )

    post = {target: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
