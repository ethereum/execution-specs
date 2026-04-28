"""
Test_static_call1_mb1024_calldepth.

Ported from:
state_tests/stStaticCall/static_Call1MB1024CalldepthFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_Call1MB1024CalldepthFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
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
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call1_mb1024_calldepth(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call1_mb1024_calldepth."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=892500000000,
    )

    addr = pre.fund_eoa(amount=0xFFFFFFFFFFFFF)  # noqa: F841
    # Source: lll
    # { [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) 0 0 0 0 0)  }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
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
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address(0xB16DBBE237612935E6611C3F5FB7D80EB0046801),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) [[ 0 ]] (+ @@0 1) (if (LT @@0 1024) [[ 1 ]] (STATICCALL (- (GAS) 1005000) <contract:0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 1000000 0 0) [[ 2 ]] 1 )  }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
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
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address(0xA79AE640E38871970F579F62237DFE2705068825),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (MSTORE 0 (+ (MLOAD 0) 1)) (if (LT (MLOAD 0) 1024) (MSTORE 32 (STATICCALL (- (GAS) 1005000) <contract:0xcbbf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 1000000 0 0)) (MSTORE 64 1) )   }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
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
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address(0x583AA587D7D852A5B8448CC4160537D9BD12C889),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(storage={0: 1}),
                addr_2: Account(storage={0: 1, 1: 0}, nonce=0),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                target: Account(storage={0: 1}),
                addr_2: Account(storage={0: 0, 1: 0}, nonce=0),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr_2, left_padding=True),
        Hash(addr_3, left_padding=True),
    ]
    tx_gas = [882500000000]
    tx_value = [10]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
