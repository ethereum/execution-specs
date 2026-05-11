"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/VMTests/vmIOandFlowOperations/returnFiller.yml
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
    ["state_tests/VMTests/vmIOandFlowOperations/returnFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="return",
        ),
        pytest.param(
            1,
            0,
            0,
            id="returnInfBuff",
        ),
        pytest.param(
            2,
            0,
            0,
            id="returnBigBuff",
        ),
        pytest.param(
            3,
            0,
            0,
            id="returnOffset",
        ),
        pytest.param(
            4,
            0,
            0,
            id="returnOld",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_return(
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
    contract_3 = Address(0x0000000000000000000000000000000000001003)
    contract_4 = Address(0x0000000000000000000000000000000000001004)
    contract_5 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
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

    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: lll
    # {
    #    [0] 0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    #    [[0xFF]] 0x600D
    #    (return 0x00 0x40)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,  # noqa: E501
        )
        + Op.SSTORE(key=0xFF, value=0x600D)
        + Op.RETURN(offset=0x0, size=0x40)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001000),  # noqa: E501
    )
    # Source: lll
    # {
    #    [0] 0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    #    [[0xFF]] 0x600D
    #    (return 0x00 (- 0 1))
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,  # noqa: E501
        )
        + Op.SSTORE(key=0xFF, value=0x600D)
        + Op.RETURN(offset=0x0, size=Op.SUB(0x0, 0x1))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001001),  # noqa: E501
    )
    # Source: lll
    # {
    #    [0] 0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    #    [[0xFF]] 0x600D
    #    (return 0x05 0x20)
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,  # noqa: E501
        )
        + Op.SSTORE(key=0xFF, value=0x600D)
        + Op.RETURN(offset=0x5, size=0x20)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001003),  # noqa: E501
    )
    # Source: raw
    # 0x6001608052600060805111601b57600160005260206000f3602b565b602760005260206000f360026080525b00  # noqa: E501
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x80, value=0x1)
        + Op.JUMPI(pc=0x1B, condition=Op.GT(Op.MLOAD(offset=0x80), 0x0))
        + Op.MSTORE(offset=0x0, value=0x1)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.JUMP(pc=0x2B)
        + Op.JUMPDEST
        + Op.MSTORE(offset=0x0, value=0x27)
        + Op.RETURN(offset=0x0, size=0x20)
        + Op.MSTORE(offset=0x80, value=0x2)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001004),  # noqa: E501
    )
    # Source: lll
    # {
    #     ; read 0x40 bytes of return data
    #     (delegatecall 0xffffff (+ 0x1000 $4) 0 0 0x00 0x40)
    #
    #     [[0]] @0x00
    #     [[1]] @0x20
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.DELEGATECALL(
                gas=0xFFFFFF,
                address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)),
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x20))
        + Op.STOP,
        storage={255: 2989},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    # Source: lll
    # {
    #    [0] 0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
    #    [[0xFF]] 0x600D
    #    (return 0x00 0x1000)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,  # noqa: E501
        )
        + Op.SSTORE(key=0xFF, value=0x600D)
        + Op.RETURN(offset=0x0, size=0x1000)
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000001002),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0, 2], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_5: Account(
                    storage={
                        0: 0x123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF,  # noqa: E501
                        1: 0,
                        255: 24589,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_5: Account(storage={255: 2989})},
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_5: Account(
                    storage={
                        0: 0xABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0000000000,  # noqa: E501
                        1: 0,
                        255: 24589,
                    },
                ),
            },
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {contract_5: Account(storage={0: 39, 255: 2989})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("693c6139") + Hash(0x0),
        Bytes("693c6139") + Hash(0x1),
        Bytes("693c6139") + Hash(0x2),
        Bytes("693c6139") + Hash(0x3),
        Bytes("693c6139") + Hash(0x4),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_5,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
