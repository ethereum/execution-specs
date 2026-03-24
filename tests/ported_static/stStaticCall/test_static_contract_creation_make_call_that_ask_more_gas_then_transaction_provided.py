"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json
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
        "tests/static/state_tests/stStaticCall/static_contractCreationMakeCallThatAskMoreGasThenTransactionProvidedFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "604060006040600073100000000000000000000000000000000000000161c350fa",  # noqa: E501
            {},
        ),
        (
            "604060006040600073200000000000000000000000000000000000000161c350fa",  # noqa: E501
            {},
        ),
        (
            "604060006040600073300000000000000000000000000000000000000161c350fa",  # noqa: E501
            {},
        ),
        (
            "604060006040600073400000000000000000000000000000000000000161c350fa",  # noqa: E501
            {},
        ),
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_contract_creation_make_call_that_ask_more_gas_then_transaction_provided(  # noqa: E501
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: LLL
    # {(SSTORE 1 1)}
    pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # {(MSTORE 1 1)}
    pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0x2000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
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
        address=Address("0x3000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # { (CALLCODE 1000 0x4000000000000000000000000000000000000004 0 0 0 0 0) }
    pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0x3E8,
                address=0x4000000000000000000000000000000000000004,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0x4000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 1 1) }
    pre.deploy_contract(
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0x4000000000000000000000000000000000000004"),  # noqa: E501
    )
    # Source: LLL
    # { (CALLCODE 1000000 0x4000000000000000000000000000000000000004 0 0 0 0 0) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0xF4240,
                address=0x4000000000000000000000000000000000000004,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0x5000000000000000000000000000000000000001"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x10C8E0)
    # Source: LLL
    # {(STATICCALL 50000 0x1000000000000000000000000000000000000001 0 64 0 64)}
    pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0xC350,
                address=0x1000000000000000000000000000000000000001,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        balance=0x186A0,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data,
        gas_limit=96000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
