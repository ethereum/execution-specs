"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_Call1MB1024CalldepthFiller.json
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
        "tests/static/state_tests/stStaticCall/static_Call1MB1024CalldepthFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "000000000000000000000000a79ae640e38871970f579f62237dfe2705068825",
            {
                Address("0xa79ae640e38871970f579f62237dfe2705068825"): Account(
                    storage={0: 1}
                ),
                Address("0xb16dbbe237612935e6611c3f5fb7d80eb0046801"): Account(
                    storage={0: 1}
                ),
            },
        ),
        (
            "000000000000000000000000583aa587d7d852a5b8448cc4160537d9bd12c889",
            {
                Address("0xb16dbbe237612935e6611c3f5fb7d80eb0046801"): Account(
                    storage={0: 1}
                )
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call1_mb1024_calldepth(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )
    callee = Address("0x2ab8257767339461506c0c67824cf17bc77b52ca")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=892500000000,
    )

    pre[callee] = Account(balance=0xFFFFFFFFFFFFF, nonce=0)
    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
            + Op.JUMPI(pc=0x1B, condition=Op.LT(Op.MLOAD(offset=0x0), 0x400))
            + Op.MSTORE(offset=0x40, value=0x1)
            + Op.JUMP(pc=0x45)
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x20,
                value=Op.STATICCALL(
                    gas=Op.SUB(Op.GAS, 0xF55C8),
                    address=0x583AA587D7D852A5B8448CC4160537D9BD12C889,
                    args_offset=0x0,
                    args_size=0xF4240,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0x583aa587d7d852a5b8448cc4160537d9bd12c889"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.JUMPI(pc=0x1B, condition=Op.LT(Op.SLOAD(key=0x0), 0x400))
            + Op.SSTORE(key=0x2, value=0x1)
            + Op.JUMP(pc=0x45)
            + Op.JUMPDEST
            + Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=Op.SUB(Op.GAS, 0xF55C8),
                    address=0xA79AE640E38871970F579F62237DFE2705068825,
                    args_offset=0x0,
                    args_size=0xF4240,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.STOP
        ),
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0xa79ae640e38871970f579f62237dfe2705068825"),  # noqa: E501
    )
    # Source: LLL
    # { [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0)  }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0xb16dbbe237612935e6611c3f5fb7d80eb0046801"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=882500000000,
        value=10,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
