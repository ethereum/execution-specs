"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/mloadFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
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
    ["state_tests/VMTests/vmIOandFlowOperations/mloadFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="mload",
        ),
        pytest.param(
            1,
            0,
            0,
            id="mloadOOG",
        ),
        pytest.param(
            2,
            0,
            0,
            id="mloadOOG",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_mload(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x0000000000000000000000000000000000001000)
    contract_1 = Address(0x0000000000000000000000000000000000001001)
    contract_2 = Address(0x0000000000000000000000000000000000001002)
    contract_3 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
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

    # Source: lll
    # {
    #      [0] 0x0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffff  # noqa: E501
    #      [[0]] (mload 0)
    #
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF,  # noqa: E501
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: lll
    # {
    #      [[0]] (mload 0x0fffffff)
    #
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0xFFFFFFF)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001001),  # noqa: E501
    )
    # Source: lll
    # {
    #      [[0]] (mload 7489573)
    #
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x724825)) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001002),  # noqa: E501
    )
    # Source: lll
    # {
    #     (delegatecall (gas) (+ 0x1000 $4) 0 0 0 0)
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=Op.GAS,
            address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        storage={0: 2989},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_3: Account(
                    storage={
                        0: 0x111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF,  # noqa: E501
                    },
                ),
            },
        },
        {
            "indexes": {"data": [1, 2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_3: Account(storage={0: 2989})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x1),
        Bytes("693c6139") + Hash(0x2),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_3,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
