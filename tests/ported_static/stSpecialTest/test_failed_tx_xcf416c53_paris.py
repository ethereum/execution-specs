"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSpecialTest/failed_tx_xcf416c53_ParisFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stSpecialTest/failed_tx_xcf416c53_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Cancun")
@pytest.mark.pre_alloc_mutable
def test_failed_tx_xcf416c53_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    sender = EOA(
        key=0x0FF8D58222F34F6890DDAA468C023B77D6691ED7D3C4DCDDAE38336212FAF54B
    )
    callee = Address("0x76fae819612a29489a1a43208613d8f8557b8898")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=200000000,
    )

    pre[callee] = Account(balance=10, nonce=0)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.JUMPI(
                pc=Op.PUSH2[0x65],
                condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x97DD3054)),
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MLOAD(offset=0x40)
            + Op.MLOAD(offset=0x60)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x62],
                condition=Op.ISZERO(Op.SLT(Op.DUP3, Op.DUP1)),
            )
            + Op.POP(
                Op.CALL(
                    gas=0x0,
                    address=Op.DUP7,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.ADD(Op.DUP3, 0x1)
            + Op.SWAP2
            + Op.POP
            + Op.JUMP(pc=Op.PUSH2[0x40])
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
        ),
        nonce=0,
        address=Address("0x7e6e9b4ca1b88937abeaec23bc4b6986caf05188"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "97dd30540000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
            "00000000000000000000000000000000000000000000000000000000000002bc"
        ),
        gas_limit=16300000,
        nonce=1,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stSpecialTest/failed_tx_xcf416c53_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Prague")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_failed_tx_xcf416c53_paris_from_prague(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    sender = EOA(
        key=0x0FF8D58222F34F6890DDAA468C023B77D6691ED7D3C4DCDDAE38336212FAF54B
    )
    callee = Address("0x76fae819612a29489a1a43208613d8f8557b8898")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=200000000,
    )

    pre[callee] = Account(balance=10, nonce=0)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.JUMPI(
                pc=Op.PUSH2[0x65],
                condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x97DD3054)),
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MLOAD(offset=0x40)
            + Op.MLOAD(offset=0x60)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x62],
                condition=Op.ISZERO(Op.SLT(Op.DUP3, Op.DUP1)),
            )
            + Op.POP(
                Op.CALL(
                    gas=0x0,
                    address=Op.DUP7,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.ADD(Op.DUP3, 0x1)
            + Op.SWAP2
            + Op.POP
            + Op.JUMP(pc=Op.PUSH2[0x40])
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
        ),
        nonce=0,
        address=Address("0x7e6e9b4ca1b88937abeaec23bc4b6986caf05188"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "97dd30540000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
            "00000000000000000000000000000000000000000000000000000000000002bc"
        ),
        gas_limit=16300000,
        nonce=1,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stSpecialTest/failed_tx_xcf416c53_ParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Osaka")
@pytest.mark.pre_alloc_mutable
def test_failed_tx_xcf416c53_paris_from_osaka(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x68795c4aa09d6f4ed3e5deddf8c2ad3049a601da")
    sender = EOA(
        key=0x0FF8D58222F34F6890DDAA468C023B77D6691ED7D3C4DCDDAE38336212FAF54B
    )
    callee = Address("0x76fae819612a29489a1a43208613d8f8557b8898")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=200000000,
    )

    pre[callee] = Account(balance=10, nonce=0)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.JUMPI(
                pc=Op.PUSH2[0x65],
                condition=Op.ISZERO(Op.EQ(Op.DUP2, 0x97DD3054)),
            )
            + Op.MSTORE(offset=0x40, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x60, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MLOAD(offset=0x40)
            + Op.MLOAD(offset=0x60)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=Op.PUSH2[0x62],
                condition=Op.ISZERO(Op.SLT(Op.DUP3, Op.DUP1)),
            )
            + Op.POP(
                Op.CALL(
                    gas=0x0,
                    address=Op.DUP7,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.ADD(Op.DUP3, 0x1)
            + Op.SWAP2
            + Op.POP
            + Op.JUMP(pc=Op.PUSH2[0x40])
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.JUMPDEST
            + Op.POP
        ),
        nonce=0,
        address=Address("0x7e6e9b4ca1b88937abeaec23bc4b6986caf05188"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "97dd30540000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
            "00000000000000000000000000000000000000000000000000000000000002bc"
        ),
        gas_limit=16300000,
        nonce=1,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
