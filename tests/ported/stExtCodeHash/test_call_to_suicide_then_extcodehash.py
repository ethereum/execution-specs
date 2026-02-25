"""
https://github.com/ethereum/tests/issues/652

Ported from:
tests/static/state_tests/stExtCodeHash/callToSuicideThenExtcodehashFiller.json

contract code:
    push1 0x40
    push1 0x00
    push1 0x40
    push1 0x00
    push1 0x00
    push1 0x00
    calldataload
    gas
    callcode
    stop

callee code:
    push1 0x25
    selfdestruct
    stop

callee_1 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x1b562ed9d56d1e40adefed452fdfae7e65e0c551
    push3 0x028488
    callcode
    push1 0x00
    sstore
    push20 0x1b562ed9d56d1e40adefed452fdfae7e65e0c551
    extcodehash
    push1 0x01
    sstore
    stop

callee_2 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x1b562ed9d56d1e40adefed452fdfae7e65e0c551
    push3 0x028488
    call
    push1 0x00
    sstore
    push20 0x1b562ed9d56d1e40adefed452fdfae7e65e0c551
    extcodehash
    push1 0x01
    sstore
    stop

callee_3 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x1b562ed9d56d1e40adefed452fdfae7e65e0c551
    push3 0x028488
    delegatecall
    push1 0x00
    sstore
    push20 0x1b562ed9d56d1e40adefed452fdfae7e65e0c551
    extcodehash
    push1 0x01
    sstore
    stop

callee_4 code:
    push1 0x00
    push1 0x00
    push1 0x00
    push1 0x00
    push20 0x1b562ed9d56d1e40adefed452fdfae7e65e0c551
    push3 0x028488
    staticcall
    push1 0x00
    sstore
    push20 0x1b562ed9d56d1e40adefed452fdfae7e65e0c551
    extcodehash
    push1 0x01
    sstore
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
    ["tests/static/state_tests/stExtCodeHash/callToSuicideThenExtcodehashFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000868ca9cd44e16d9c5e2bddd34f6414eaed74cd7e",
        "00000000000000000000000044e55707ba8597da17fc9ced43d27c4866ddb46a",
        "0000000000000000000000008c019d97297ee7264aac1d8210c9480feedc2ee1",
        "000000000000000000000000a479e3e4f560d6dcfb2cbb3b1ca024a228888515",
    ],
    ids=['case0', 'case1', 'case2', 'case3'],
)
@pytest.mark.pre_alloc_mutable
def test_call_to_suicide_then_extcodehash(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """https://github.com/ethereum/tests/issues/652."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = Address("0xebaf50debf10e08302fe4280c32df010463ca297")
    contract = Address("0x0643600618f0ae5095b4bda2e0f11a79e6d2d541")
    callee = Address("0x1b562ed9d56d1e40adefed452fdfae7e65e0c551")
    callee_1 = Address("0x44e55707ba8597da17fc9ced43d27c4866ddb46a")
    callee_2 = Address("0x868ca9cd44e16d9c5e2bddd34f6414eaed74cd7e")
    callee_3 = Address("0x8c019d97297ee7264aac1d8210c9480feedc2ee1")
    callee_4 = Address("0xa479e3e4f560d6dcfb2cbb3b1ca024a228888515")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x40] + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.GAS + Op.CALLCODE
        + Op.STOP
    ),
        storage={0x1: 0x1122},
    )
    pre[callee] = Account(
        balance=0x14b230ce3,
        nonce=0,
        code=Op.PUSH1[0x25] + Op.SELFDESTRUCT + Op.STOP,
    )
    pre[callee_1] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x1b562ed9d56d1e40adefed452fdfae7e65e0c551]
        + Op.PUSH3[0x28488] + Op.CALLCODE + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH20[0x1b562ed9d56d1e40adefed452fdfae7e65e0c551] + Op.EXTCODEHASH
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_2] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH20[0x1b562ed9d56d1e40adefed452fdfae7e65e0c551]
        + Op.PUSH3[0x28488] + Op.CALL + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH20[0x1b562ed9d56d1e40adefed452fdfae7e65e0c551] + Op.EXTCODEHASH
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_3] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1b562ed9d56d1e40adefed452fdfae7e65e0c551] + Op.PUSH3[0x28488]
        + Op.DELEGATECALL + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH20[0x1b562ed9d56d1e40adefed452fdfae7e65e0c551] + Op.EXTCODEHASH
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[callee_4] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0x1b562ed9d56d1e40adefed452fdfae7e65e0c551] + Op.PUSH3[0x28488]
        + Op.STATICCALL + Op.PUSH1[0x0] + Op.SSTORE
        + Op.PUSH20[0x1b562ed9d56d1e40adefed452fdfae7e65e0c551] + Op.EXTCODEHASH
        + Op.PUSH1[0x1] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        secret_key=Hash(
            "0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869"
        ),
        to=contract,
        data=tx_data,
        gas_limit=300000,
        gas_price=10,
        nonce=0,
        value=1,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
