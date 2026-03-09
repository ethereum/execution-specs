"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCreate2/CREATE2_FirstByte_loopFiller.yml
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
    ["tests/static/state_tests/stCreate2/CREATE2_FirstByte_loopFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "1a8451e6000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ef",  # noqa: E501
            {
                Address("0x09fdd11d68be787a4c43f692a0778befc011cd35"): Account(
                    storage={256: 1}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000ef00000000000000000000000000000000000000000000000000000000000000f0",  # noqa: E501
            {
                Address("0x09fdd11d68be787a4c43f692a0778befc011cd35"): Account(
                    storage={239: 1, 256: 1}
                )
            },
        ),
        (
            "1a8451e600000000000000000000000000000000000000000000000000000000000000f00000000000000000000000000000000000000000000000000000000000000100",  # noqa: E501
            {
                Address("0x09fdd11d68be787a4c43f692a0778befc011cd35"): Account(
                    storage={256: 1}
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2"],
)
@pytest.mark.pre_alloc_mutable
def test_create2_first_byte_loop(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xF79127A3004ABDE26A4CBD80C428CB10F829FA11B54D36E7B326F4F4A5927ACF
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=89128960,
    )

    # Source: Yul
    # {
    #   let start := calldataload(4)
    #   let end := calldataload(36)
    #   // initcode: { mstore8(0, 0x00) return(0, 1) }
    #   mstore(0, 0x600060005360016000f300000000000000000000000000000000000000000000)  # noqa: E501
    #   for { let code := start } lt(code, end) { code := add(code, 1) }
    #   {
    #     mstore8(1, code) // change returned byte in initcode
    #     if iszero(create2(0, 0, 10, 0)) { sstore(code, 1) }
    #   }
    #   sstore(256, 1)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x600060005360016000F300000000000000000000000000000000000000000000,  # noqa: E501
            )
            + Op.CALLDATALOAD(offset=0x24)
            + Op.CALLDATALOAD(offset=0x4)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x38, condition=Op.LT(Op.DUP2, Op.DUP2))
            + Op.SSTORE(key=0x100, value=0x1)
            + Op.STOP
            + Op.JUMPDEST
            + Op.DUP1
            + Op.PUSH1[0x1]
            + Op.SWAP2
            + Op.DUP3
            + Op.MSTORE8
            + Op.JUMPI(
                pc=0x4F,
                condition=Op.ISZERO(
                    Op.CREATE2(
                        value=Op.DUP1, offset=Op.DUP2, size=0xA, salt=0x0
                    ),
                ),
            )
            + Op.JUMPDEST
            + Op.ADD
            + Op.JUMP(pc=0x2A)
            + Op.JUMPDEST
            + Op.SSTORE(key=Op.DUP2, value=Op.DUP2)
            + Op.JUMP(pc=0x4A)
        ),
        nonce=0,
        address=Address("0x09fdd11d68be787a4c43f692a0778befc011cd35"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3B9ACA00)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
