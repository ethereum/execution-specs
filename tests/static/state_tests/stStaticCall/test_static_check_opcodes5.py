"""
Ported from:
tests/static/state_tests/stStaticCall/static_CheckOpcodes5Filler.json

callee code:
    push20 0x972f33115b9e8be9c87412a04ce61e6c3a84d15d
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    push20 0x8eeb303e1e7e2bb67d778526e009014a5daead81
    push3 0x0186a0
    delegatecall
    stop

callee_1 code:
    origin
    push20 0xfaa10b404ab607779993c016cd5da73ae1f29d7e
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0x8a6781f0d54ed3cb8963ffc233e98041de8bdadb
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

contract code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x03d090
    call
    push1 0x01
    sstore
    stop

callee_2 code:
    push20 0xdf047446304bc9145d7ba20cd326e1097da151ff
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x00
    push20 0x8eeb303e1e7e2bb67d778526e009014a5daead81
    push3 0x0186a0
    call
    stop

callee_3 code:
    origin
    push20 0xfaa10b404ab607779993c016cd5da73ae1f29d7e
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0x9c40928b20ac4236f0f3920567f28539c2e158b3
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

callee_4 code:
    push20 0xdf047446304bc9145d7ba20cd326e1097da151ff
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x0a
    push20 0x8eeb303e1e7e2bb67d778526e009014a5daead81
    push3 0x0186a0
    call
    stop

callee_5 code:
    push20 0x19473707238ef04c4550e6eee0d12bc0e3a7a02a
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x01
    push20 0x8eeb303e1e7e2bb67d778526e009014a5daead81
    push3 0x0186a0
    callcode
    stop

callee_6 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push2 0xc350
    staticcall
    push1 0x00
    sstore
    stop

callee_7 code:
    origin
    push20 0xfaa10b404ab607779993c016cd5da73ae1f29d7e
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0x09fce828cbd5c5bdc742fe5a63776e2a76a111e5
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

callee_8 code:
    push20 0x3f1afec0e6911ff45e18f4286f10dd905cd18f29
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x00
    push20 0x8eeb303e1e7e2bb67d778526e009014a5daead81
    push3 0x0186a0
    callcode
    stop

callee_9 code:
    origin
    push20 0xfaa10b404ab607779993c016cd5da73ae1f29d7e
    eq
    push1 0x22
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x28
    jump
    jumpdest
    push1 0x01
    push1 0x01
    mstore
    jumpdest
    caller
    push20 0x8eeb303e1e7e2bb67d778526e009014a5daead81
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)
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
    ["tests/static/state_tests/stStaticCall/static_CheckOpcodes5Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value",
    [
        ("0000000000000000000000002c073c9d611d927ca91e4819bbb2dff859a8732b", 50000, 0),
        ("0000000000000000000000002c073c9d611d927ca91e4819bbb2dff859a8732b", 50000, 100),
        ("0000000000000000000000002c073c9d611d927ca91e4819bbb2dff859a8732b", 335000, 0),
        ("0000000000000000000000002c073c9d611d927ca91e4819bbb2dff859a8732b", 335000, 100),
        ("0000000000000000000000007761311ee56479da378519606cc4da58e17251ab", 50000, 0),
        ("0000000000000000000000007761311ee56479da378519606cc4da58e17251ab", 50000, 100),
        ("0000000000000000000000007761311ee56479da378519606cc4da58e17251ab", 335000, 0),
        ("0000000000000000000000007761311ee56479da378519606cc4da58e17251ab", 335000, 100),
        ("0000000000000000000000009c40928b20ac4236f0f3920567f28539c2e158b3", 50000, 0),
        ("0000000000000000000000009c40928b20ac4236f0f3920567f28539c2e158b3", 50000, 100),
        ("0000000000000000000000009c40928b20ac4236f0f3920567f28539c2e158b3", 335000, 0),
        ("0000000000000000000000009c40928b20ac4236f0f3920567f28539c2e158b3", 335000, 100),
        ("0000000000000000000000008a6781f0d54ed3cb8963ffc233e98041de8bdadb", 50000, 0),
        ("0000000000000000000000008a6781f0d54ed3cb8963ffc233e98041de8bdadb", 50000, 100),
        ("0000000000000000000000008a6781f0d54ed3cb8963ffc233e98041de8bdadb", 335000, 0),
        ("0000000000000000000000008a6781f0d54ed3cb8963ffc233e98041de8bdadb", 335000, 100),
        ("00000000000000000000000009fce828cbd5c5bdc742fe5a63776e2a76a111e5", 50000, 0),
        ("00000000000000000000000009fce828cbd5c5bdc742fe5a63776e2a76a111e5", 50000, 100),
        ("00000000000000000000000009fce828cbd5c5bdc742fe5a63776e2a76a111e5", 335000, 0),
        ("00000000000000000000000009fce828cbd5c5bdc742fe5a63776e2a76a111e5", 335000, 100),
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9', 'case10', 'case11', 'case12', 'case13', 'case14', 'case15', 'case16', 'case17', 'case18', 'case19'],
)
@pytest.mark.pre_alloc_mutable
def test_static_check_opcodes5(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x1fe115f5d840cd62e113b09755c50d8f3f358b96")
    callee = Address("0x09fce828cbd5c5bdc742fe5a63776e2a76a111e5")
    callee_1 = Address("0x19473707238ef04c4550e6eee0d12bc0e3a7a02a")
    callee_2 = Address("0x2c073c9d611d927ca91e4819bbb2dff859a8732b")
    callee_3 = Address("0x3f1afec0e6911ff45e18f4286f10dd905cd18f29")
    callee_4 = Address("0x7761311ee56479da378519606cc4da58e17251ab")
    callee_5 = Address("0x8a6781f0d54ed3cb8963ffc233e98041de8bdadb")
    callee_6 = Address("0x8eeb303e1e7e2bb67d778526e009014a5daead81")
    callee_7 = Address("0x972f33115b9e8be9c87412a04ce61e6c3a84d15d")
    callee_8 = Address("0x9c40928b20ac4236f0f3920567f28539c2e158b3")
    callee_9 = Address("0xdf047446304bc9145d7ba20cd326e1097da151ff")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH20[0x972f33115b9e8be9c87412a04ce61e6c3a84d15d] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH20[0x8eeb303e1e7e2bb67d778526e009014a5daead81] + Op.PUSH3[0x186a0]
        + Op.DELEGATECALL + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x8a6781f0d54ed3cb8963ffc233e98041de8bdadb] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0x19473707238ef04c4550e6eee0d12bc0e3a7a02a] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x3d090]
        + Op.CALL + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH20[0xdf047446304bc9145d7ba20cd326e1097da151ff] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x8eeb303e1e7e2bb67d778526e009014a5daead81]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x9c40928b20ac4236f0f3920567f28539c2e158b3] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0x3f1afec0e6911ff45e18f4286f10dd905cd18f29] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH20[0xdf047446304bc9145d7ba20cd326e1097da151ff] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0xa] + Op.PUSH20[0x8eeb303e1e7e2bb67d778526e009014a5daead81]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH20[0x19473707238ef04c4550e6eee0d12bc0e3a7a02a] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0x8eeb303e1e7e2bb67d778526e009014a5daead81]
        + Op.PUSH3[0x186a0] + Op.CALLCODE + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH2[0xc350] + Op.STATICCALL
        + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_7] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x9fce828cbd5c5bdc742fe5a63776e2a76a111e5] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0x972f33115b9e8be9c87412a04ce61e6c3a84d15d] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_8] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH20[0x3f1afec0e6911ff45e18f4286f10dd905cd18f29] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x8eeb303e1e7e2bb67d778526e009014a5daead81]
        + Op.PUSH3[0x186a0] + Op.CALLCODE + Op.STOP
    ),
    )
    pre[callee_9] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x8eeb303e1e7e2bb67d778526e009014a5daead81] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0xdf047446304bc9145d7ba20cd326e1097da151ff] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
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
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
