"""
SELFBALANCE tests inside CALL, DELEGATECALL, and CALLCODE.

Ported from:
tests/static/state_tests/stSelfBalance/selfBalanceCallTypesFiller.json
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
    ["tests/static/state_tests/stSelfBalance/selfBalanceCallTypesFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "0000000000000000000000000000000000000000000000000000000000000001",
            {
                Address("0x76bac61ee2056f42f6cc29f5400adae3e5705237"): Account(
                    storage={33: 4352}
                ),
                Address("0x84bf87fbef135afea15330fdf5847eb504cff901"): Account(
                    storage={
                        0: 0xA590BBF1B07B00FED987724E1DB1BF206C2BC37C,
                        1: 0x76BAC61EE2056F42F6CC29F5400ADAE3E5705237,
                        2: 0x8537CE29429EA557E3903C255EE6554DD8D21D26,
                        3: 0xE1CE93B3251FB38AE74D41AF9F865978C572CF63,
                    }
                ),
                Address("0x8537ce29429ea557e3903c255ee6554dd8d21d26"): Account(
                    storage={49: 5}
                ),
                Address("0xa590bbf1b07b00fed987724e1db1bf206c2bc37c"): Account(
                    storage={17: 1}
                ),
                Address("0xe1ce93b3251fb38ae74d41af9f865978c572cf63"): Account(
                    storage={65: 4864, 66: 4863, 67: 1}
                ),
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000002",
            {
                Address("0x84bf87fbef135afea15330fdf5847eb504cff901"): Account(
                    storage={
                        0: 0xA590BBF1B07B00FED987724E1DB1BF206C2BC37C,
                        1: 0x76BAC61EE2056F42F6CC29F5400ADAE3E5705237,
                        2: 0x8537CE29429EA557E3903C255EE6554DD8D21D26,
                        3: 0xE1CE93B3251FB38AE74D41AF9F865978C572CF63,
                        17: 1,
                        33: 8192,
                        49: 5,
                        65: 8192,
                        66: 8191,
                        67: 1,
                    }
                )
            },
        ),
        (
            "0000000000000000000000000000000000000000000000000000000000000003",
            {
                Address("0x84bf87fbef135afea15330fdf5847eb504cff901"): Account(
                    storage={
                        0: 0xA590BBF1B07B00FED987724E1DB1BF206C2BC37C,
                        1: 0x76BAC61EE2056F42F6CC29F5400ADAE3E5705237,
                        2: 0x8537CE29429EA557E3903C255EE6554DD8D21D26,
                        3: 0xE1CE93B3251FB38AE74D41AF9F865978C572CF63,
                        17: 1,
                        33: 8192,
                        49: 5,
                        65: 8192,
                        66: 8191,
                        67: 1,
                    }
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2"],
)
@pytest.mark.pre_alloc_mutable
def test_self_balance_call_types(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """SELFBALANCE tests inside CALL, DELEGATECALL, and CALLCODE."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x897B12D02D588D8A4FE16FF831CBD4459C6F62F8C845B0CCDD31CAF068C84A26
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
        code=Op.SSTORE(key=0x21, value=Op.SELFBALANCE) + Op.STOP,
        balance=4352,
        nonce=0,
        address=Address("0x76bac61ee2056f42f6cc29f5400adae3e5705237"),  # noqa: E501
    )
    # Source: LLL
    # {(set 'i 0) (while @@ @i {(when (eq 0x01 $0x0) (call allgas @@ @i 0 0 0 0 0)) (when (eq 0x02 $0x0) (delegatecall allgas @@ @i 0 0 0 0)) (when (eq 0x03 $0x0) (callcode allgas @@ @i 0 0 0 0 0)) [i]:(+ @i 1)})}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x80, value=0x0)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x75,
                condition=Op.ISZERO(Op.SLOAD(key=Op.MLOAD(offset=0x80))),
            )
            + Op.JUMPI(
                pc=0x2C,
                condition=Op.ISZERO(Op.EQ(0x1, Op.CALLDATALOAD(offset=0x0))),
            )
            + Op.POP(
                Op.CALL(
                    gas=Op.SUB(Op.GAS, 0x15),
                    address=Op.SLOAD(key=Op.MLOAD(offset=0x80)),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x49,
                condition=Op.ISZERO(Op.EQ(0x2, Op.CALLDATALOAD(offset=0x0))),
            )
            + Op.POP(
                Op.DELEGATECALL(
                    gas=Op.SUB(Op.GAS, 0x15),
                    address=Op.SLOAD(key=Op.MLOAD(offset=0x80)),
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x68,
                condition=Op.ISZERO(Op.EQ(0x3, Op.CALLDATALOAD(offset=0x0))),
            )
            + Op.POP(
                Op.CALLCODE(
                    gas=Op.SUB(Op.GAS, 0x15),
                    address=Op.SLOAD(key=Op.MLOAD(offset=0x80)),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x5)
            + Op.JUMPDEST
            + Op.STOP
        ),
        storage={
            0x0: 0xA590BBF1B07B00FED987724E1DB1BF206C2BC37C,
            0x1: 0x76BAC61EE2056F42F6CC29F5400ADAE3E5705237,
            0x2: 0x8537CE29429EA557E3903C255EE6554DD8D21D26,
            0x3: 0xE1CE93B3251FB38AE74D41AF9F865978C572CF63,
        },
        balance=8192,
        nonce=0,
        address=Address("0x84bf87fbef135afea15330fdf5847eb504cff901"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.GAS
            + Op.SELFBALANCE
            + Op.GAS
            + Op.SWAP1
            + Op.POP
            + Op.SWAP1
            + Op.SUB
            + Op.PUSH1[0x2]
            + Op.SWAP1
            + Op.SSTORE(key=0x31, value=Op.SUB)
            + Op.STOP
        ),
        balance=4608,
        nonce=0,
        address=Address("0x8537ce29429ea557e3903c255ee6554dd8d21d26"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x11,
                value=Op.EQ(Op.SELFBALANCE, Op.BALANCE(address=Op.ADDRESS)),
            )
            + Op.STOP
        ),
        balance=4096,
        nonce=0,
        address=Address("0xa590bbf1b07b00fed987724e1db1bf206c2bc37c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3635C9ADC5DEA00000)
    pre.deploy_contract(
        code=(
            Op.SELFBALANCE
            + Op.SSTORE(key=0x41, value=Op.DUP1)
            + Op.POP(
                Op.CALL(
                    gas=0x0,
                    address=0x0,
                    value=0x1,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SELFBALANCE
            + Op.SSTORE(key=0x42, value=Op.DUP1)
            + Op.SWAP1
            + Op.SSTORE(key=0x43, value=Op.SUB)
            + Op.STOP
        ),
        balance=4864,
        nonce=0,
        address=Address("0xe1ce93b3251fb38ae74d41af9f865978c572cf63"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=1000000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
