"""
Ori Pomerantz qbzzt1@gmail.com

Ported from:
state_tests/VMTests/vmTests/sha3Filler.yml
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "693c61390000000000000000000000000000000000000000000000000000000000000000",
    "693c61390000000000000000000000000000000000000000000000000000000000000001",
    "693c61390000000000000000000000000000000000000000000000000000000000000002",
    "693c61390000000000000000000000000000000000000000000000000000000000000003",
    "693c61390000000000000000000000000000000000000000000000000000000000000004",
    "693c61390000000000000000000000000000000000000000000000000000000000000005",
    "693c61390000000000000000000000000000000000000000000000000000000000000006",
    "693c61390000000000000000000000000000000000000000000000000000000000000007",
    "693c61390000000000000000000000000000000000000000000000000000000000000008",
    "693c61390000000000000000000000000000000000000000000000000000000000000009",
    "693c6139000000000000000000000000000000000000000000000000000000000000000a",
    "693c6139000000000000000000000000000000000000000000000000000000000000000b",
    "693c6139000000000000000000000000000000000000000000000000000000000000000c",
    "693c6139000000000000000000000000000000000000000000000000000000000000000d",
    "693c61390000000000000000000000000000000000000000000000000000000000000010",
    "693c6139000000000000000000000000000000000000000000000000000000000000000e",
    "693c6139000000000000000000000000000000000000000000000000000000000000000f",
]
TX_GAS = [16777216]
TX_VALUE = [1]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/VMTests/vmTests/sha3Filler.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="sha3_nodata",
        ),
        pytest.param(
            1, 0, 0,
            id="sha3_five_0s",
        ),
        pytest.param(
            2, 0, 0,
            id="sha3_ten_0s",
        ),
        pytest.param(
            3, 0, 0,
            id="sha3_0xFFFFF_0s",
        ),
        pytest.param(
            4, 0, 0,
            id="sha3_highmem",
        ),
        pytest.param(
            5, 0, 0,
            id="sha3_huge_buffer",
        ),
        pytest.param(
            6, 0, 0,
            id="sha3_neg1_neg1",
        ),
        pytest.param(
            7, 0, 0,
            id="sha3_neg1_2",
        ),
        pytest.param(
            8, 0, 0,
            id="sha3_0x1000000_2",
        ),
        pytest.param(
            9, 0, 0,
            id="sha3_960_1",
        ),
        pytest.param(
            10, 0, 0,
            id="sha3_992_1",
        ),
        pytest.param(
            11, 0, 0,
            id="sha3_1024_1",
        ),
        pytest.param(
            12, 0, 0,
            id="sha3_1984_1",
        ),
        pytest.param(
            13, 0, 0,
            id="sha3_2016_1",
        ),
        pytest.param(
            14, 0, 0,
            id="sha3_2016_32",
        ),
        pytest.param(
            15, 0, 0,
            id="sha3_2048_1",
        ),
        pytest.param(
            16, 0, 0,
            id="sha3_1024_0",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_sha3(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x0000000000000000000000000000000000001000")
    contract_1 = Address("0x0000000000000000000000000000000000001001")
    contract_2 = Address("0x0000000000000000000000000000000000001002")
    contract_3 = Address("0x0000000000000000000000000000000000001003")
    contract_4 = Address("0x0000000000000000000000000000000000001004")
    contract_5 = Address("0x0000000000000000000000000000000000001005")
    contract_6 = Address("0x0000000000000000000000000000000000001006")
    contract_7 = Address("0x0000000000000000000000000000000000001007")
    contract_8 = Address("0x0000000000000000000000000000000000001008")
    contract_9 = Address("0x0000000000000000000000000000000000001009")
    contract_10 = Address("0x000000000000000000000000000000000000100a")
    contract_11 = Address("0x000000000000000000000000000000000000100b")
    contract_12 = Address("0x000000000000000000000000000000000000100c")
    contract_13 = Address("0x000000000000000000000000000000000000100d")
    contract_14 = Address("0x000000000000000000000000000000000000100e")
    contract_15 = Address("0x000000000000000000000000000000000000100f")
    contract_16 = Address("0x0000000000000000000000000000000000001010")
    contract_17 = Address("0xcccccccccccccccccccccccccccccccccccccccc")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # {
    #     [[0]] (sha3 0 0)
    # }
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x0, size=0x0)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001000"),  # noqa: E501
    )
    # Source: lll
    # {
    #     [[0]] (sha3 4 5)
    # }
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x4, size=0x5)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001001"),  # noqa: E501
    )
    # Source: lll
    # {
    #     [[0]] (sha3 10 10)
    # }
    contract_2 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0xa, size=0xa)) + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001002"),  # noqa: E501
    )
    # Source: lll
    # {
    #     [[0]] (sha3 1000 0xFFFFF)
    # }
    contract_3 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x3e8, size=0xfffff)) + Op.STOP,  # noqa: E501
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001003"),  # noqa: E501
    )
    # Source: lll
    # {
    #     ; The result here is zero, because we run out of gas
    #     [[0]] (sha3 0xfffffffff  100)
    # }
    contract_4 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0xfffffffff, size=0x64))
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001004"),  # noqa: E501
    )
    # Source: lll
    # {
    #     ; The result here is zero, because we run out of gas
    #     [[0]] (sha3 10000 0xfffffffff)
    # }
    contract_5 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x2710, size=0xfffffffff))
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001005"),  # noqa: E501
    )
    # Source: lll
    # {
    #     (def 'neg1 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
    #     [[0]] (sha3 neg1 neg1)
    # }
    contract_6 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, size=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001006"),  # noqa: E501
    )
    # Source: lll
    # {
    #     (def 'neg1 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
    #     [[0]] (sha3 neg1 2)
    # }
    contract_7 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, size=0x2))  # noqa: E501
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001007"),  # noqa: E501
    )
    # Source: lll
    # {
    #     [[0]] (sha3 0x1000000 2)
    # }
    contract_8 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x1000000, size=0x2)) + Op.STOP,  # noqa: E501
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001008"),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[ 0 ]] (sha3 960 1)
    # }
    contract_9 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x3c0, size=0x1)) + Op.STOP,  # noqa: E501
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001009"),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[ 0 ]] (sha3 992 1)
    # }
    contract_10 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x3e0, size=0x1)) + Op.STOP,  # noqa: E501
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100a"),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[ 0 ]] (sha3 1024 1)
    # }
    contract_11 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x400, size=0x1)) + Op.STOP,  # noqa: E501
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100b"),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[ 0 ]] (sha3 1984 1)
    # }
    contract_12 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x7c0, size=0x1)) + Op.STOP,  # noqa: E501
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100c"),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[ 0 ]] (sha3 2016 1)
    # }
    contract_13 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x7e0, size=0x1)) + Op.STOP,  # noqa: E501
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100d"),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[ 0 ]] (sha3 2048 1)
    # }
    contract_14 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x800, size=0x1)) + Op.STOP,  # noqa: E501
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100e"),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[ 0 ]] (sha3 1024 0)
    # }
    contract_15 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x400, size=0x0)) + Op.STOP,  # noqa: E501
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000100f"),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[ 0 ]] (sha3 2016 32)
    # }
    contract_16 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.SHA3(offset=0x7e0, size=0x20)) + Op.STOP,  # noqa: E501
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000001010"),  # noqa: E501
    )
    # Source: lll
    # {
    #     (call (- 0 1) (+ 0x1000 $4) 0
    #        0x0F 0x10   ; arg offset and length to get the 0x1234...f0 value
    #        0x20 0x40)  ; return offset and length
    # }
    contract_17 = pre.deploy_contract(
        code=Op.CALL(gas=Op.SUB(0x0, 0x1), address=Op.ADD(0x1000, Op.CALLDATALOAD(offset=0x4)), value=0x0, args_offset=0xf, args_size=0x10, ret_offset=0x20, ret_size=0x40)
        + Op.STOP,
        balance=0xba1a9ce0ba1a9ce,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x100000000000)

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': [0], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_0: Account(
                storage={
            0: 0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470,
        },
            ),
    },
        },
        {
            "indexes": {'data': [1], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_1: Account(
                storage={
            0: 0xc41589e7559804ea4a2080dad19d876a024ccb05117835447d72ce08c1d020ec,
        },
            ),
    },
        },
        {
            "indexes": {'data': [2], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_2: Account(
                storage={
            0: 0x6bd2dd6bd408cbee33429358bf24fdc64612fbf8b1b4db604518f40ffd34b607,
        },
            ),
    },
        },
        {
            "indexes": {'data': [3], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_3: Account(
                storage={
            0: 0xbe6f1b42b34644f918560a07f959d23e532dea5338e4b9f63db0caeb608018fa,
        },
            ),
    },
        },
        {
            "indexes": {'data': [4], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_4: Account(storage={0: 0})},
        },
        {
            "indexes": {'data': [5], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_5: Account(storage={0: 0})},
        },
        {
            "indexes": {'data': [6], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_6: Account(storage={0: 0})},
        },
        {
            "indexes": {'data': [7], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_7: Account(storage={0: 0})},
        },
        {
            "indexes": {'data': [8], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {contract_8: Account(storage={0: 0})},
        },
        {
            "indexes": {'data': [9], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_9: Account(
                storage={
            0: 0xbc36789e7a1e281436464229828f817d6612f7b477d66591ff96a9e064bcc98a,
        },
            ),
    },
        },
        {
            "indexes": {'data': [10], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_10: Account(
                storage={
            0: 0xbc36789e7a1e281436464229828f817d6612f7b477d66591ff96a9e064bcc98a,
        },
            ),
    },
        },
        {
            "indexes": {'data': [11], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_11: Account(
                storage={
            0: 0xbc36789e7a1e281436464229828f817d6612f7b477d66591ff96a9e064bcc98a,
        },
            ),
    },
        },
        {
            "indexes": {'data': [12], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_12: Account(
                storage={
            0: 0xbc36789e7a1e281436464229828f817d6612f7b477d66591ff96a9e064bcc98a,
        },
            ),
    },
        },
        {
            "indexes": {'data': [13], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_13: Account(
                storage={
            0: 0xbc36789e7a1e281436464229828f817d6612f7b477d66591ff96a9e064bcc98a,
        },
            ),
    },
        },
        {
            "indexes": {'data': [15], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_14: Account(
                storage={
            0: 0xbc36789e7a1e281436464229828f817d6612f7b477d66591ff96a9e064bcc98a,
        },
            ),
    },
        },
        {
            "indexes": {'data': [16], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_15: Account(
                storage={
            0: 0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470,
        },
            ),
    },
        },
        {
            "indexes": {'data': [14], 'gas': -1, 'value': -1},
            "network": ['>=Cancun'],
            "result": {
        contract_16: Account(
                storage={
            0: 0x290decd9548b62a8d60345a988386fc84ba6bc95484008f6362f93160ef3e563,
        },
            ),
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_17,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
