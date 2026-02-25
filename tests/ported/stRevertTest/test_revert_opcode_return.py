"""
Ported from:
tests/static/state_tests/stRevertTest/RevertOpcodeReturnFiller.json

callee code:
    push13 0x72657665727465642064617461
    push1 0x00
    sstore
    push14 0x726576657274206d657373616765
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    revert
    stop

contract code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x0249f0
    call
    push1 0x01
    sstore
    push1 0x00
    mload
    push1 0x02
    sstore
    stop

callee_1 code:
    push13 0x72657665727465642064617461
    push1 0x00
    sstore
    push14 0x726576657274206d657373616765
    push1 0x00
    mstore
    push15 0x0fffffffffffffffffffffffffffff
    push1 0x00
    revert
    stop

callee_2 code:
    push13 0x72657665727465642064617461
    push1 0x00
    sstore
    push14 0x726576657274206d657373616765
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    revert
    stop

callee_3 code:
    push13 0x72657665727465642064617461
    push1 0x00
    sstore
    push14 0x726576657274206d657373616765
    push1 0x00
    mstore
    push1 0x00
    push15 0x0fffffffffffffffffffffffffffff
    revert
    stop

callee_4 code:
    push13 0x72657665727465642064617461
    push1 0x00
    sstore
    push14 0x726576657274206d657373616765
    push1 0x00
    mstore
    push1 0x00
    push1 0x01
    revert
    stop

callee_5 code:
    push13 0x72657665727465642064617461
    push1 0x00
    sstore
    push14 0x726576657274206d657373616765
    push1 0x00
    mstore
    push1 0x00
    push2 0x0100
    revert
    stop
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRevertTest/RevertOpcodeReturnFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit",
    [
        ("0000000000000000000000001963fd2c717f5b4b9fa3d6baf38d66241e1ec005", 800000),
        ("0000000000000000000000001963fd2c717f5b4b9fa3d6baf38d66241e1ec005", 80000),
        ("000000000000000000000000745e52346d8549444323699e9fc383ae89bdd24f", 800000),
        ("000000000000000000000000745e52346d8549444323699e9fc383ae89bdd24f", 80000),
        ("00000000000000000000000050eaca0a040ac6242d0c01cc1ff82f5b95cc10e4", 800000),
        ("00000000000000000000000050eaca0a040ac6242d0c01cc1ff82f5b95cc10e4", 80000),
        ("000000000000000000000000f933d2374d5875de033a8ed9d9c1ce5dea25c78b", 800000),
        ("000000000000000000000000f933d2374d5875de033a8ed9d9c1ce5dea25c78b", 80000),
        ("000000000000000000000000e5b2dfe7f932f2d5eaa7c8fb2e1e9a8b6a846fd7", 800000),
        ("000000000000000000000000e5b2dfe7f932f2d5eaa7c8fb2e1e9a8b6a846fd7", 80000),
        ("000000000000000000000000858f82bbfd84fc9eb91291458511df77311dbd0d", 800000),
        ("000000000000000000000000858f82bbfd84fc9eb91291458511df77311dbd0d", 80000),
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11'],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_return(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x1fc98371f1a058f1a6042e30a141aa8bb67dd1bc")
    callee = Address("0x1963fd2c717f5b4b9fa3d6baf38d66241e1ec005")
    callee_1 = Address("0x50eaca0a040ac6242d0c01cc1ff82f5b95cc10e4")
    callee_2 = Address("0x745e52346d8549444323699e9fc383ae89bdd24f")
    callee_3 = Address("0x858f82bbfd84fc9eb91291458511df77311dbd0d")
    callee_4 = Address("0xe5b2dfe7f932f2d5eaa7c8fb2e1e9a8b6a846fd7")
    callee_5 = Address("0xf933d2374d5875de033a8ed9d9c1ce5dea25c78b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH13[0x72657665727465642064617461] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH14[0x726576657274206d657373616765] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.REVERT + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x249f0]
        + Op.CALL + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x2] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH13[0x72657665727465642064617461] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH14[0x726576657274206d657373616765] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH15[0xfffffffffffffffffffffffffffff] + Op.PUSH1[0x0] + Op.REVERT
        + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH13[0x72657665727465642064617461] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH14[0x726576657274206d657373616765] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.REVERT + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH13[0x72657665727465642064617461] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH14[0x726576657274206d657373616765] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH15[0xfffffffffffffffffffffffffffff] + Op.REVERT
        + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH13[0x72657665727465642064617461] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH14[0x726576657274206d657373616765] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.REVERT + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH13[0x72657665727465642064617461] + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH14[0x726576657274206d657373616765] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH2[0x100] + Op.REVERT + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xe8d4a51000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52"
        ),
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        gas_price=10,
        nonce=0,
        value=0,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
