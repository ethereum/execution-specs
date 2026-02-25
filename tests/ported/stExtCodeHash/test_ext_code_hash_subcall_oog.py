"""
create contract A in a subcall. go OOG in a subcall (revert happens) check EXTCODEHASH of A (in upper call)

Ported from:
tests/static/state_tests/stExtCodeHash/extCodeHashSubcallOOGFiller.yml

contract code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    push3 0x055730
    callcode
    pop
    push1 0x00
    mload
    extcodehash
    push1 0x01
    sstore
    push1 0x00
    mload
    extcodesize
    push1 0x02
    sstore
    ... (22 more instructions)

callee code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xa000000000000000000000000000000000000000
    push3 0x0249f0
    call
    pop
    push1 0x20
    push1 0x00
    return
    stop

callee_1 code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xa000000000000000000000000000000000000000
    push3 0x0249f0
    callcode
    pop
    push1 0x20
    push1 0x00
    return
    stop

callee_2 code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xa000000000000000000000000000000000000000
    push3 0x0249f0
    delegatecall
    pop
    push1 0x20
    push1 0x00
    return
    stop

callee_3 code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xa100000000000000000000000000000000000000
    push3 0x0249f0
    call
    pop
    push1 0x20
    push1 0x00
    return
    stop

callee_4 code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xa100000000000000000000000000000000000000
    push3 0x03d090
    callcode
    pop
    push1 0x20
    push1 0x00
    return
    stop

callee_5 code:
    push1 0x20
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0xa100000000000000000000000000000000000000
    push3 0x0249f0
    delegatecall
    pop
    push1 0x20
    push1 0x00
    return
    stop

callee_6 code:
    push1 0x00
    push1 0x0f
    dup1
    push1 0x1a
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    push1 0x00
    mstore
    push1 0x20
    push1 0x00
    return
    stop
    stop
    invalid
    push5 0x6020602055
    push1 0x00
    mstore
    ... (4 more instructions)

callee_7 code:
    push1 0x00
    push1 0x0f
    dup1
    push1 0x60
    push1 0x00
    codecopy
    push1 0x00
    push1 0x00
    create2
    push1 0x00
    mstore
    push1 0x01
    push1 0x01
    sstore
    push1 0x01
    push1 0x02
    sstore
    push1 0x01
    push1 0x03
    sstore
    ... (46 more instructions)
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
    ["tests/static/state_tests/stExtCodeHash/extCodeHashSubcallOOGFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "0000000000000000000000002000000000000000000000000000000000000000",
        "0000000000000000000000002100000000000000000000000000000000000000",
        "0000000000000000000000002200000000000000000000000000000000000000",
        "0000000000000000000000003000000000000000000000000000000000000000",
        "0000000000000000000000003100000000000000000000000000000000000000",
        "0000000000000000000000003200000000000000000000000000000000000000",
    ],
    ids=['case0', 'case1', 'case2', 'case3', 'case4', 'case5'],
)
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_subcall_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """create contract A in a subcall. go OOG in a subcall (revert happens) check EXTCODEHASH of A (in upper call)."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0x1000000000000000000000000000000000000000")
    callee = Address("0x2000000000000000000000000000000000000000")
    callee_1 = Address("0x2100000000000000000000000000000000000000")
    callee_2 = Address("0x2200000000000000000000000000000000000000")
    callee_3 = Address("0x3000000000000000000000000000000000000000")
    callee_4 = Address("0x3100000000000000000000000000000000000000")
    callee_5 = Address("0x3200000000000000000000000000000000000000")
    callee_6 = Address("0xa000000000000000000000000000000000000000")
    callee_7 = Address("0xa100000000000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.PUSH3[0x55730]
        + Op.CALLCODE + Op.POP + Op.PUSH1[0x0] + Op.MLOAD + Op.EXTCODEHASH
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.EXTCODESIZE
        + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.MLOAD + Op.EXTCODECOPY + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH1[0x3] + Op.SSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH2[0xc350]
        + Op.CALLCODE + Op.PUSH1[0x4] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xa000000000000000000000000000000000000000]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_1] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xa000000000000000000000000000000000000000]
        + Op.PUSH3[0x249f0] + Op.CALLCODE + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa000000000000000000000000000000000000000] + Op.PUSH3[0x249f0]
        + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xa100000000000000000000000000000000000000]
        + Op.PUSH3[0x249f0] + Op.CALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0xa100000000000000000000000000000000000000]
        + Op.PUSH3[0x3d090] + Op.CALLCODE + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_5] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa100000000000000000000000000000000000000] + Op.PUSH3[0x249f0]
        + Op.DELEGATECALL + Op.POP + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN
        + Op.STOP
    ),
    )
    pre[callee_6] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0xf] + Op.DUP1 + Op.PUSH1[0x1a] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.RETURN + Op.STOP + Op.STOP
        + Op.INVALID + Op.PUSH5[0x6020602055] + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH1[0x5] + Op.PUSH1[0x1b] + Op.RETURN + Op.STOP
    ),
    )
    pre[callee_7] = Account(
        balance=0xde0b6b3a7640000,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0xf] + Op.DUP1 + Op.PUSH1[0x60] + Op.PUSH1[0x0]
        + Op.CODECOPY + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CREATE2 + Op.PUSH1[0x0]
        + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x2] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x4] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x5]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x6] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0x7] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x8] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0x9] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xa]
        + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xb] + Op.SSTORE + Op.PUSH1[0x1]
        + Op.PUSH1[0xc] + Op.SSTORE + Op.PUSH1[0x1] + Op.PUSH1[0xd] + Op.SSTORE
        + Op.PUSH1[0x1] + Op.PUSH1[0xe] + Op.SSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.RETURN + Op.STOP + Op.STOP + Op.INVALID + Op.PUSH5[0x6020602055]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x5] + Op.PUSH1[0x1b] + Op.RETURN
        + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=tx_data,
        gas_limit=400000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
