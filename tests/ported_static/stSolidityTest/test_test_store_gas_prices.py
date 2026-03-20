"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSolidityTest/TestStoreGasPricesFiller.json
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


@pytest.mark.ported_from(
    ["tests/static/state_tests/stSolidityTest/TestStoreGasPricesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_test_store_gas_prices(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x185FBEA9F643C40E33475353B07FA51D0695CA94789492166B67D60FDB6EF7FB
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0x746A528800)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.DIV(
                Op.CALLDATALOAD(offset=0x0),
                0x100000000000000000000000000000000000000000000000000000000,
            )
            + Op.JUMPI(pc=0x2D, condition=Op.EQ(Op.DUP2, 0xC0406226))
            + Op.STOP
            + Op.JUMPDEST
            + Op.PUSH1[0x33]
            + Op.JUMP(pc=0x3D)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x0, value=Op.DUP1)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.GAS
            + Op.SSTORE(key=0x20, value=0x1)
            + Op.SWAP1
            + Op.POP
            + Op.SSTORE(key=0x0, value=Op.SUB(Op.DUP2, Op.GAS))
            + Op.GAS
            + Op.SSTORE(key=0x20, value=0x2)
            + Op.SWAP1
            + Op.POP
            + Op.SSTORE(key=0x1, value=Op.SUB(Op.DUP2, Op.GAS))
            + Op.GAS
            + Op.SSTORE(key=0x20, value=0x2)
            + Op.SWAP1
            + Op.POP
            + Op.SSTORE(key=0x2, value=Op.SUB(Op.DUP2, Op.GAS))
            + Op.GAS
            + Op.SSTORE(key=0x20, value=0x168AA8D53FE6)
            + Op.SWAP1
            + Op.POP
            + Op.SSTORE(key=0x3, value=Op.SUB(Op.DUP2, Op.GAS))
            + Op.GAS
            + Op.SSTORE(key=0x20, value=0x2)
            + Op.SWAP1
            + Op.POP
            + Op.SSTORE(key=0x4, value=Op.SUB(Op.DUP2, Op.GAS))
            + Op.GAS
            + Op.SSTORE(key=0x20, value=0x0)
            + Op.SWAP1
            + Op.POP
            + Op.SSTORE(key=0x5, value=Op.SUB(Op.DUP2, Op.GAS))
            + Op.POP(Op.GAS)
            + Op.PUSH1[0x1]
            + Op.SWAP3
            + Op.SWAP2
            + Op.POP
            + Op.POP
            + Op.JUMP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0xfe58f48415dcf9d527f770e3148b769a76ef83f1"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 22113, 1: 113, 2: 113, 3: 113, 4: 113, 5: 113},
                    code=bytes.fromhex(
                        "7c01000000000000000000000000000000000000000000000000000000006000350463c04062268114602d57005b6033603d565b8060005260206000f35b600060005a600160205590505a81036000555a600260205590505a81036001555a600260205590505a81036002555a65168aa8d53fe660205590505a81036003555a600260205590505a81036004555a600060205590505a81036005555a5060019291505056"  # noqa: E501
                    ),
                )
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex("c0406226"),
        gas_limit=35000000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
