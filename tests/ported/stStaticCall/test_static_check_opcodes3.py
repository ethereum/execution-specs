"""
Ported from:
tests/static/state_tests/stStaticCall/static_CheckOpcodes3Filler.json

callee code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x0186a0
    staticcall
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    eq
    push1 0x24
    jumpi
    push1 0x02
    push1 0x01
    sstore
    push1 0x2a
    ... (7 more instructions)

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
    push20 0x8113f9fc0868700534ecbecf1120a812cb1af0ac
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
    calldataload
    push3 0x0186a0
    staticcall
    push1 0x01
    sstore
    stop

callee_2 code:
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
    push20 0xe541572ce4b4ccbb2b92aab0fb852f018d51c512
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

callee_3 code:
    push20 0x4af0c90f8f7b7834e7e7bd57dda960412f9650f9
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    push20 0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35
    push3 0x0186a0
    delegatecall
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    eq
    push1 0x4e
    jumpi
    push1 0x02
    push1 0x01
    ... (9 more instructions)

callee_4 code:
    push20 0xa131950507c8977b0de1790c8e76a1a28dd92805
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x01
    push20 0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35
    push3 0x0186a0
    call
    push1 0x00
    mstore
    push1 0x01
    push1 0x01
    mstore
    push1 0x01
    push1 0x02
    mstore
    stop

callee_5 code:
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
    push20 0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

callee_6 code:
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
    push20 0xba044a82b25080bc96678b9fa77678e014605c48
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

callee_7 code:
    push20 0xb93cf5121157d61ab42345f5a5e9815b19cec2cc
    push1 0x20
    mstore
    push1 0x00
    push1 0x00
    push1 0x40
    push1 0x20
    push1 0x00
    push20 0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35
    push3 0x0186a0
    callcode
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    eq
    push1 0x50
    jumpi
    push1 0x02
    ... (10 more instructions)

callee_8 code:
    push20 0x6d797b6a2c5f22885c4068990f19ae845d698a79
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x01
    push20 0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35
    push3 0x0186a0
    callcode
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    eq
    push1 0x50
    jumpi
    push1 0x02
    ... (10 more instructions)

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
    push20 0x9b68a6b37af295c7fd23aa2269db8c875c2b86b4
    eq
    push1 0x4b
    jumpi
    ... (41 more instructions)

callee_10 code:
    push20 0xa131950507c8977b0de1790c8e76a1a28dd92805
    push1 0x00
    mstore
    push1 0x00
    push1 0x00
    push1 0x20
    push1 0x00
    push1 0x00
    push20 0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35
    push3 0x0186a0
    call
    push1 0x00
    mstore
    push1 0x00
    mload
    push1 0x01
    eq
    push1 0x50
    jumpi
    push1 0x02
    ... (10 more instructions)
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
    ["tests/static/state_tests/stStaticCall/static_CheckOpcodes3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_value",
    [
        ("000000000000000000000000f697c2d8963df21523b18e96caaf6c7703a1882e", 0),
        ("000000000000000000000000f697c2d8963df21523b18e96caaf6c7703a1882e", 100),
        ("0000000000000000000000009b68a6b37af295c7fd23aa2269db8c875c2b86b4", 0),
        ("0000000000000000000000009b68a6b37af295c7fd23aa2269db8c875c2b86b4", 100),
        ("000000000000000000000000ba044a82b25080bc96678b9fa77678e014605c48", 0),
        ("000000000000000000000000ba044a82b25080bc96678b9fa77678e014605c48", 100),
        ("000000000000000000000000e541572ce4b4ccbb2b92aab0fb852f018d51c512", 0),
        ("000000000000000000000000e541572ce4b4ccbb2b92aab0fb852f018d51c512", 100),
        ("0000000000000000000000008113f9fc0868700534ecbecf1120a812cb1af0ac", 0),
        ("0000000000000000000000008113f9fc0868700534ecbecf1120a812cb1af0ac", 100),
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5', 'case6', 'case7', 'case8', 'case9'],
)
@pytest.mark.pre_alloc_mutable
def test_static_check_opcodes3(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_value: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xfaa10b404ab607779993c016cd5da73ae1f29d7e")
    contract = Address("0x50f628d871a69f2db31e98d7fbf8ae6f1fc0d55c")
    callee = Address("0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35")
    callee_1 = Address("0x4af0c90f8f7b7834e7e7bd57dda960412f9650f9")
    callee_2 = Address("0x6d797b6a2c5f22885c4068990f19ae845d698a79")
    callee_3 = Address("0x8113f9fc0868700534ecbecf1120a812cb1af0ac")
    callee_4 = Address("0x9b68a6b37af295c7fd23aa2269db8c875c2b86b4")
    callee_5 = Address("0xa131950507c8977b0de1790c8e76a1a28dd92805")
    callee_6 = Address("0xb93cf5121157d61ab42345f5a5e9815b19cec2cc")
    callee_7 = Address("0xba044a82b25080bc96678b9fa77678e014605c48")
    callee_8 = Address("0xe541572ce4b4ccbb2b92aab0fb852f018d51c512")
    callee_9 = Address("0xef6a70e5546ca5339758b2f3b819780625c233c3")
    callee_10 = Address("0xf697c2d8963df21523b18e96caaf6c7703a1882e")

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
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x186a0] + Op.STATICCALL
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH1[0x1] + Op.EQ
        + Op.PUSH1[0x24] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x2a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
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
        + Op.PUSH20[0x8113f9fc0868700534ecbecf1120a812cb1af0ac] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0x4af0c90f8f7b7834e7e7bd57dda960412f9650f9] + Op.EQ
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
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x186a0] + Op.STATICCALL
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0xe541572ce4b4ccbb2b92aab0fb852f018d51c512] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0x6d797b6a2c5f22885c4068990f19ae845d698a79] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH20[0x4af0c90f8f7b7834e7e7bd57dda960412f9650f9] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH20[0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35] + Op.PUSH3[0x186a0]
        + Op.DELEGATECALL + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x1] + Op.EQ + Op.PUSH1[0x4e] + Op.JUMPI + Op.PUSH1[0x2]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x54] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH20[0xa131950507c8977b0de1790c8e76a1a28dd92805] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x1] + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.MSTORE
        + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0xa131950507c8977b0de1790c8e76a1a28dd92805] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.ORIGIN + Op.PUSH20[0xfaa10b404ab607779993c016cd5da73ae1f29d7e] + Op.EQ
        + Op.PUSH1[0x22] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x28] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLER
        + Op.PUSH20[0xba044a82b25080bc96678b9fa77678e014605c48] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0xb93cf5121157d61ab42345f5a5e9815b19cec2cc] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x0] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_7] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH20[0xb93cf5121157d61ab42345f5a5e9815b19cec2cc] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x20]
        + Op.PUSH1[0x0] + Op.PUSH20[0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35]
        + Op.PUSH3[0x186a0] + Op.CALLCODE + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.EQ + Op.PUSH1[0x50] + Op.JUMPI + Op.PUSH1[0x2]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x56] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_8] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH20[0x6d797b6a2c5f22885c4068990f19ae845d698a79] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH20[0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35]
        + Op.PUSH3[0x186a0] + Op.CALLCODE + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.EQ + Op.PUSH1[0x50] + Op.JUMPI + Op.PUSH1[0x2]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x56] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.JUMPDEST + Op.STOP
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
        + Op.PUSH20[0x9b68a6b37af295c7fd23aa2269db8c875c2b86b4] + Op.EQ
        + Op.PUSH1[0x4b] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x51] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.ADDRESS
        + Op.PUSH20[0xef6a70e5546ca5339758b2f3b819780625c233c3] + Op.EQ
        + Op.PUSH1[0x74] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x7a] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.CALLVALUE + Op.PUSH1[0x1] + Op.EQ
        + Op.PUSH1[0x8a] + Op.JUMPI + Op.PUSH1[0x2] + Op.PUSH1[0x1] + Op.SSTORE
        + Op.PUSH1[0x90] + Op.JUMP + Op.JUMPDEST + Op.PUSH1[0x1] + Op.PUSH1[0x1]
        + Op.MSTORE + Op.JUMPDEST + Op.STOP
    ),
    )
    pre[callee_10] = Account(
        balance=10,
        nonce=0,
        code=(
        Op.PUSH20[0xa131950507c8977b0de1790c8e76a1a28dd92805] + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x2e5dc1c94af89d7c115126fcebad7a5c50f5fe35]
        + Op.PUSH3[0x186a0] + Op.CALL + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.MLOAD + Op.PUSH1[0x1] + Op.EQ + Op.PUSH1[0x50] + Op.JUMPI + Op.PUSH1[0x2]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x56] + Op.JUMP + Op.JUMPDEST
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.MSTORE + Op.JUMPDEST + Op.STOP
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
        gas_limit=335000,
        gas_price=10,
        nonce=0,
        value=tx_value,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
