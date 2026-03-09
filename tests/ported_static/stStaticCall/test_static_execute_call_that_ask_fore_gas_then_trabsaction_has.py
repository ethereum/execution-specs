"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json
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
        "tests/static/state_tests/stStaticCall/static_ExecuteCallThatAskForeGasThenTrabsactionHasFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "0000000000000000000000003dc16a13cf554533f380cc938a2c1ab04dac534f",
            {
                Address("0xa256ebcc5536cda56e04c39fe9584ecc7594a438"): Account(
                    storage={1: 1}
                )
            },
        ),
        (
            "00000000000000000000000073ef1878a0f2c9629dedc1b1e9be8d77dcf93688",
            {},
        ),
        (
            "000000000000000000000000ce4ccbffaf450ae2126eb96dcd7c891f37764f20",
            {},
        ),
    ],
    ids=["case0", "case1", "case2"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_execute_call_that_ask_fore_gas_then_trabsaction_has(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xDC4EFA209AECDD4C2D5201A419EA27506151B4EC687F14A613229E310932491B
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0x3dc16a13cf554533f380cc938a2c1ab04dac534f"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1C,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.POP(Op.EXTCODESIZE(address=0x1))
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x0)
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0x73ef1878a0f2c9629dedc1b1e9be8d77dcf93688"),  # noqa: E501
    )
    # Source: LLL
    # { [[1]] (STATICCALL 600000 (CALLDATALOAD 0) 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=0x927C0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xa256ebcc5536cda56e04c39fe9584ecc7594a438"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x989680)
    pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0xce4ccbffaf450ae2126eb96dcd7c891f37764f20"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=100000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
