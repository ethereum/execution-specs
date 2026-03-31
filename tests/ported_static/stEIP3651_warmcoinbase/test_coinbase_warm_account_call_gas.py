"""
Test_coinbase_warm_account_call_gas.

Ported from:
state_tests/Shanghai/stEIP3651_warmcoinbase/coinbaseWarmAccountCallGasFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/Shanghai/stEIP3651_warmcoinbase/coinbaseWarmAccountCallGasFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
        pytest.param(
            4,
            0,
            0,
            id="d4",
        ),
        pytest.param(
            5,
            0,
            0,
            id="d5",
        ),
        pytest.param(
            6,
            0,
            0,
            id="d6",
        ),
        pytest.param(
            7,
            0,
            0,
            id="d7",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_coinbase_warm_account_call_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_coinbase_warm_account_call_gas."""
    coinbase = Address(0x50228C44ED92561D94511E8518A75AA463BD444B)
    sender = EOA(
        key=0x48DC5A9F099CAAAA557742CA3A990A94BE45B9969126A1BC74E5E8BE5A2B5B47
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: yul
    # berlin
    # {
    #    // Save the coinbase value
    #    let cb := coinbase()
    #
    #    // Minimum gas spent on the measurement, which changes depending on
    #    // the tested opcode
    #    //
    #    // Note that this value can change (mostly down) when Yul rolls out new  # noqa: E501
    #    // optimizations
    #    let measureGas
    #
    #    let gas0, gas1
    #    let retVal
    #
    #    // We can only check the gas of one opcode per transaction,
    #    // because the first check adds the account to the
    #    // 'accessed_addresses' list.
    #    switch calldataload(4)
    #    case 0 {
    #      // EXTCODESIZE
    #      measureGas := 8
    #      gas0 := gas()
    #      retVal := extcodesize(cb)
    #      gas1 := gas()
    #    }
    #    case 1 {
    #      // EXTCODECOPY
    #      measureGas := 5
    #      gas0 := gas()
    # ... (54 more lines)
    target = pre.deploy_contract(  # noqa: F841
        code=Op.COINBASE
        + Op.CALLDATALOAD(offset=0x4)
        + Op.PUSH1[0x0]
        + Op.JUMPI(pc=0xCC, condition=Op.ISZERO(Op.DUP2))
        + Op.JUMPI(pc=0xBA, condition=Op.EQ(0x1, Op.DUP2))
        + Op.POP
        + Op.JUMPI(pc=0xAD, condition=Op.EQ(0x2, Op.DUP1))
        + Op.JUMPI(pc=0xA0, condition=Op.EQ(0x3, Op.DUP1))
        + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x4, Op.DUP1))
        + Op.JUMPI(pc=0x74, condition=Op.EQ(0x5, Op.DUP1))
        + Op.JUMPI(pc=0x5F, condition=Op.EQ(0x6, Op.DUP1))
        + Op.PUSH1[0x7]
        + Op.JUMPI(pc=0x40, condition=Op.EQ)
        + Op.REVERT(offset=Op.DUP1, size=0x0)
        + Op.JUMPDEST
        + Op.PUSH1[0xB]
        + Op.PUSH1[0x0]
        + Op.DUP1 * 3
        + Op.GAS
        + Op.SWAP6
        + Op.PUSH2[0x2710]
        + Op.STATICCALL
        + Op.SWAP2
        + Op.GAS
        + Op.SWAP1
        + Op.JUMPDEST
        + Op.SUB
        + Op.SSTORE(key=0x0, value=Op.SUB)
        + Op.PUSH1[0x0]
        + Op.MSTORE
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0xB]
        + Op.PUSH1[0x0]
        + Op.DUP1 * 3
        + Op.GAS
        + Op.SWAP6
        + Op.PUSH2[0x2710]
        + Op.DELEGATECALL
        + Op.SWAP2
        + Op.GAS
        + Op.SWAP1
        + Op.JUMP(pc=0x51)
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0xB]
        + Op.PUSH1[0x0]
        + Op.DUP1 * 4
        + Op.GAS
        + Op.SWAP7
        + Op.PUSH2[0x2710]
        + Op.CALLCODE
        + Op.SWAP2
        + Op.GAS
        + Op.SWAP1
        + Op.JUMP(pc=0x51)
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0xB]
        + Op.PUSH1[0x0]
        + Op.DUP1 * 4
        + Op.GAS
        + Op.SWAP7
        + Op.PUSH2[0x2710]
        + Op.CALL
        + Op.SWAP2
        + Op.GAS
        + Op.SWAP1
        + Op.JUMP(pc=0x51)
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x8]
        + Op.GAS
        + Op.SWAP2
        + Op.BALANCE
        + Op.SWAP2
        + Op.GAS
        + Op.SWAP1
        + Op.JUMP(pc=0x51)
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x8]
        + Op.GAS
        + Op.SWAP2
        + Op.EXTCODEHASH
        + Op.SWAP2
        + Op.GAS
        + Op.SWAP1
        + Op.JUMP(pc=0x51)
        + Op.JUMPDEST
        + Op.SWAP2
        + Op.PUSH1[0x5]
        + Op.SWAP2
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.DUP1 * 2
        + Op.GAS
        + Op.SWAP4
        + Op.EXTCODECOPY
        + Op.GAS
        + Op.SWAP1
        + Op.JUMP(pc=0x51)
        + Op.JUMPDEST
        + Op.POP * 2
        + Op.PUSH1[0x8]
        + Op.GAS
        + Op.SWAP2
        + Op.EXTCODESIZE
        + Op.SWAP2
        + Op.GAS
        + Op.SWAP1
        + Op.JUMP(pc=0x51),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0xA4A48FC5F3526A9BC06A0136AB0BA1D9574D15BA),  # noqa: E501
    )
    pre[coinbase] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x1),
        Bytes("693c6139") + Hash(0x2),
        Bytes("693c6139") + Hash(0x3),
        Bytes("693c6139") + Hash(0x4),
        Bytes("693c6139") + Hash(0x5),
        Bytes("693c6139") + Hash(0x6),
        Bytes("693c6139") + Hash(0x7),
    ]
    tx_gas = [80000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
    )

    post = {target: Account(storage={0: 100})}

    state_test(env=env, pre=pre, post=post, tx=tx)
