"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_ABAcalls1Filler.json
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
    ["tests/static/state_tests/stStaticCall/static_ABAcalls1Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "000000000000000000000000d0a73d84aa7112e8d5179cae211b268d16dafd73",
            {
                Address("0xe7fe01f115e85f0487086659fa9bbf09579b0e3a"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
        (
            "000000000000000000000000c1eb8f73f2e1e269acd146c961210b665078841b",
            {
                Address("0xe7fe01f115e85f0487086659fa9bbf09579b0e3a"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_ab_acalls1(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000000,
    )

    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=Op.PC,
                value=Op.ADD(
                    0x1,
                    Op.STATICCALL(
                        gas=Op.SUB(Op.GAS, 0x186A0),
                        address=0xC1EB8F73F2E1E269ACD146C961210B665078841B,
                        args_offset=0x0,
                        args_size=0x0,
                        ret_offset=0x0,
                        ret_size=0x0,
                    ),
                ),
            )
            + Op.STOP
        ),
        balance=23,
        nonce=0,
        address=Address("0x5e75046384134a4554c3c7061d4637cb978d5699"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=Op.PC)
            + Op.STATICCALL(
                gas=Op.SUB(Op.GAS, 0x186A0),
                address=0x5E75046384134A4554C3C7061D4637CB978D5699,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xc1eb8f73f2e1e269acd146c961210b665078841b"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=Op.PC,
                value=Op.ADD(
                    0x1,
                    Op.STATICCALL(
                        gas=Op.SUB(Op.GAS, 0x186A0),
                        address=0xD0A73D84AA7112E8D5179CAE211B268D16DAFD73,
                        args_offset=0x0,
                        args_size=0x0,
                        ret_offset=0x0,
                        ret_size=0x0,
                    ),
                ),
            )
            + Op.STOP
        ),
        balance=23,
        nonce=0,
        address=Address("0xcc7901b70dcec81d198ac6cf196ef14bca9870be"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=Op.PC,
                value=Op.STATICCALL(
                    gas=Op.SUB(Op.GAS, 0x186A0),
                    address=0xCC7901B70DCEC81D198AC6CF196EF14BCA9870BE,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xd0a73d84aa7112e8d5179cae211b268d16dafd73"),  # noqa: E501
    )
    # Source: LLL
    # { [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0) [[ 1 ]] 1 }
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
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xe7fe01f115e85f0487086659fa9bbf09579b0e3a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=1000000000,
        value=100000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
