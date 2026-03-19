"""
Test ported from static filler.

Ported from:
tests/static/state_tests/Shanghai/stEIP3651_warmcoinbase
coinbaseWarmAccountCallGasFiller.yml
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "693c61390000000000000000000000000000000000000000000000000000000000000001",
    "693c61390000000000000000000000000000000000000000000000000000000000000002",
    "693c61390000000000000000000000000000000000000000000000000000000000000003",
    "693c61390000000000000000000000000000000000000000000000000000000000000004",
    "693c61390000000000000000000000000000000000000000000000000000000000000005",
    "693c61390000000000000000000000000000000000000000000000000000000000000006",
    "693c61390000000000000000000000000000000000000000000000000000000000000007",
]

TX_GAS = [80000]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/Shanghai/stEIP3651_warmcoinbase/coinbaseWarmAccountCallGasFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
        pytest.param(2, 0, 0, id="case2"),
        pytest.param(3, 0, 0, id="case3"),
        pytest.param(4, 0, 0, id="case4"),
        pytest.param(5, 0, 0, id="case5"),
        pytest.param(6, 0, 0, id="case6"),
        pytest.param(7, 0, 0, id="case7"),
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
    """Test ported from static filler."""
    coinbase = Address("0x50228c44ed92561d94511e8518a75aa463bd444b")
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

    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    pre[coinbase] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    # Source: Yul
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
    #      extcodecopy(cb, 0, 0, 0)
    # ... (53 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.COINBASE
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
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
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
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
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
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
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
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
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
            + Op.DUP1
            + Op.DUP1
            + Op.GAS
            + Op.SWAP4
            + Op.EXTCODECOPY
            + Op.GAS
            + Op.SWAP1
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.POP
            + Op.POP
            + Op.PUSH1[0x8]
            + Op.GAS
            + Op.SWAP2
            + Op.EXTCODESIZE
            + Op.SWAP2
            + Op.GAS
            + Op.SWAP1
            + Op.JUMP(pc=0x51)
        ),
        balance=0xBA1A9CE0BA1A9CE,
        address=Address("0xa4a48fc5f3526a9bc06a0136ab0ba1d9574d15ba"),  # noqa: E501
    )

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 100},
                    code=bytes.fromhex(
                        "416004356000811560cc578160011460ba57508060021460ad578060031460a05780600414608a578060051460745780600614605f57600714604057600080fd5b600b60008080805a95612710fa915a905b030360005560005260206000f35b50600b60008080805a95612710f4915a906051565b50600b6000808080805a96612710f2915a906051565b50600b6000808080805a96612710f1915a906051565b5060085a9131915a906051565b5060085a913f915a906051565b9160059150600080805a933c5a906051565b505060085a913b915a90605156"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 100},
                    code=bytes.fromhex(
                        "416004356000811560cc578160011460ba57508060021460ad578060031460a05780600414608a578060051460745780600614605f57600714604057600080fd5b600b60008080805a95612710fa915a905b030360005560005260206000f35b50600b60008080805a95612710f4915a906051565b50600b6000808080805a96612710f2915a906051565b50600b6000808080805a96612710f1915a906051565b5060085a9131915a906051565b5060085a913f915a906051565b9160059150600080805a933c5a906051565b505060085a913b915a90605156"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 100},
                    code=bytes.fromhex(
                        "416004356000811560cc578160011460ba57508060021460ad578060031460a05780600414608a578060051460745780600614605f57600714604057600080fd5b600b60008080805a95612710fa915a905b030360005560005260206000f35b50600b60008080805a95612710f4915a906051565b50600b6000808080805a96612710f2915a906051565b50600b6000808080805a96612710f1915a906051565b5060085a9131915a906051565b5060085a913f915a906051565b9160059150600080805a933c5a906051565b505060085a913b915a90605156"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 100},
                    code=bytes.fromhex(
                        "416004356000811560cc578160011460ba57508060021460ad578060031460a05780600414608a578060051460745780600614605f57600714604057600080fd5b600b60008080805a95612710fa915a905b030360005560005260206000f35b50600b60008080805a95612710f4915a906051565b50600b6000808080805a96612710f2915a906051565b50600b6000808080805a96612710f1915a906051565b5060085a9131915a906051565b5060085a913f915a906051565b9160059150600080805a933c5a906051565b505060085a913b915a90605156"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 4, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 100},
                    code=bytes.fromhex(
                        "416004356000811560cc578160011460ba57508060021460ad578060031460a05780600414608a578060051460745780600614605f57600714604057600080fd5b600b60008080805a95612710fa915a905b030360005560005260206000f35b50600b60008080805a95612710f4915a906051565b50600b6000808080805a96612710f2915a906051565b50600b6000808080805a96612710f1915a906051565b5060085a9131915a906051565b5060085a913f915a906051565b9160059150600080805a933c5a906051565b505060085a913b915a90605156"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 5, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 100},
                    code=bytes.fromhex(
                        "416004356000811560cc578160011460ba57508060021460ad578060031460a05780600414608a578060051460745780600614605f57600714604057600080fd5b600b60008080805a95612710fa915a905b030360005560005260206000f35b50600b60008080805a95612710f4915a906051565b50600b6000808080805a96612710f2915a906051565b50600b6000808080805a96612710f1915a906051565b5060085a9131915a906051565b5060085a913f915a906051565b9160059150600080805a933c5a906051565b505060085a913b915a90605156"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 6, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 100},
                    code=bytes.fromhex(
                        "416004356000811560cc578160011460ba57508060021460ad578060031460a05780600414608a578060051460745780600614605f57600714604057600080fd5b600b60008080805a95612710fa915a905b030360005560005260206000f35b50600b60008080805a95612710f4915a906051565b50600b6000808080805a96612710f2915a906051565b50600b6000808080805a96612710f1915a906051565b5060085a9131915a906051565b5060085a913f915a906051565b9160059150600080805a933c5a906051565b505060085a913b915a90605156"  # noqa: E501
                    ),
                )
            },
        },
        {
            "indexes": {"data": 7, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 100},
                    code=bytes.fromhex(
                        "416004356000811560cc578160011460ba57508060021460ad578060031460a05780600414608a578060051460745780600614605f57600714604057600080fd5b600b60008080805a95612710fa915a905b030360005560005260206000f35b50600b60008080805a95612710f4915a906051565b50600b6000808080805a96612710f2915a906051565b50600b6000808080805a96612710f1915a906051565b5060085a9131915a906051565b5060085a913f915a906051565b9160059150600080805a933c5a906051565b505060085a913b915a90605156"  # noqa: E501
                    ),
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=1,
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
