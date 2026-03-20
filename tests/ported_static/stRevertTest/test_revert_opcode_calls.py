"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRevertTest/RevertOpcodeCallsFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "000000000000000000000000ceb48d108c874b5b014acdd1a2466d65a3d01de6",
    "000000000000000000000000737f82ed94146e759790d925492df5a8ced35885",
    "0000000000000000000000006b8268ac8921e6a6e59a4b1d51a76f4e807e17af",
    "000000000000000000000000bf3fc188d9c8d699ffa12f0369e3b2bcf8428f7c",
]

TX_GAS = [460000, 83622]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRevertTest/RevertOpcodeCallsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(0, 1, 0, id="case1"),
        pytest.param(1, 0, 0, id="case2"),
        pytest.param(1, 1, 0, id="case3"),
        pytest.param(2, 0, 0, id="case4"),
        pytest.param(2, 1, 0, id="case5"),
        pytest.param(3, 0, 0, id="case6"),
        pytest.param(3, 1, 0, id="case7"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: LLL
    # {  [[10]] (CALL 260000 (CALLDATALOAD 0) 0 0 0 0 0)}
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0xA,
                value=Op.CALL(
                    gas=0x3F7A0,
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
        balance=1,
        nonce=0,
        address=Address("0x1ada72179309fd8a562e308928e38763a543ed6c"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x4,
                value=Op.CALL(
                    gas=0xC350,
                    address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x5, value=0xE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x652761b88018ea027f6f27e456fe55c2dc5d6a91"),  # noqa: E501
    )
    callee_1 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=0xE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x6b8268ac8921e6a6e59a4b1d51a76f4e807e17af"),  # noqa: E501
    )
    callee_2 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0xC350,
                    address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=0xE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x737f82ed94146e759790d925492df5a8ced35885"),  # noqa: E501
    )
    callee_3 = pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0xC)
            + Op.REVERT(offset=0x0, size=0x1)
            + Op.SSTORE(key=0x3, value=0xD)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b"),  # noqa: E501
    )
    callee_4 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x186A0,
                    address=0x652761B88018EA027F6F27E456FE55C2DC5D6A91,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=0xE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0xbf3fc188d9c8d699ffa12f0369e3b2bcf8428f7c"),  # noqa: E501
    )
    callee_5 = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0xC350,
                    address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=0xE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0xceb48d108c874b5b014acdd1a2466d65a3d01de6"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={10: 1},
                    code=bytes.fromhex(
                        "600060006000600060006000356203f7a0f1600a5500"
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600455600e60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f4600055600e60025500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f2600055600e60025500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60015560016000fd600d60035500")
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6000600060006000600073652761b88018ea027f6f27e456fe55c2dc5d6a91620186a0f1600055600e60025500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    storage={2: 14},
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600055600e60025500"  # noqa: E501
                    ),
                ),
            },
        },
        {
            "indexes": {"data": 0, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006000356203f7a0f1600a5500"
                    )
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600455600e60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f4600055600e60025500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f2600055600e60025500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60015560016000fd600d60035500")
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6000600060006000600073652761b88018ea027f6f27e456fe55c2dc5d6a91620186a0f1600055600e60025500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600055600e60025500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={10: 1},
                    code=bytes.fromhex(
                        "600060006000600060006000356203f7a0f1600a5500"
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600455600e60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f4600055600e60025500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    storage={2: 14},
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f2600055600e60025500"  # noqa: E501
                    ),
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60015560016000fd600d60035500")
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6000600060006000600073652761b88018ea027f6f27e456fe55c2dc5d6a91620186a0f1600055600e60025500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600055600e60025500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006000356203f7a0f1600a5500"
                    )
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600455600e60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f4600055600e60025500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f2600055600e60025500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60015560016000fd600d60035500")
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6000600060006000600073652761b88018ea027f6f27e456fe55c2dc5d6a91620186a0f1600055600e60025500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600055600e60025500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={10: 1},
                    code=bytes.fromhex(
                        "600060006000600060006000356203f7a0f1600a5500"
                    ),
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600455600e60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    storage={2: 14},
                    code=bytes.fromhex(
                        "60006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f4600055600e60025500"  # noqa: E501
                    ),
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f2600055600e60025500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60015560016000fd600d60035500")
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6000600060006000600073652761b88018ea027f6f27e456fe55c2dc5d6a91620186a0f1600055600e60025500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600055600e60025500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 2, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006000356203f7a0f1600a5500"
                    )
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600455600e60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f4600055600e60025500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f2600055600e60025500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60015560016000fd600d60035500")
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6000600060006000600073652761b88018ea027f6f27e456fe55c2dc5d6a91620186a0f1600055600e60025500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600055600e60025500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={10: 1},
                    code=bytes.fromhex(
                        "600060006000600060006000356203f7a0f1600a5500"
                    ),
                ),
                callee: Account(
                    storage={5: 14},
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600455600e60055500"  # noqa: E501
                    ),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f4600055600e60025500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f2600055600e60025500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60015560016000fd600d60035500")
                ),
                callee_4: Account(
                    storage={0: 1, 2: 14},
                    code=bytes.fromhex(
                        "6000600060006000600073652761b88018ea027f6f27e456fe55c2dc5d6a91620186a0f1600055600e60025500"  # noqa: E501
                    ),
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600055600e60025500"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 3, "gas": 1, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    code=bytes.fromhex(
                        "600060006000600060006000356203f7a0f1600a5500"
                    )
                ),
                callee: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600455600e60055500"  # noqa: E501
                    )
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "60006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f4600055600e60025500"  # noqa: E501
                    )
                ),
                callee_2: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f2600055600e60025500"  # noqa: E501
                    )
                ),
                callee_3: Account(
                    code=bytes.fromhex("600c60015560016000fd600d60035500")
                ),
                callee_4: Account(
                    code=bytes.fromhex(
                        "6000600060006000600073652761b88018ea027f6f27e456fe55c2dc5d6a91620186a0f1600055600e60025500"  # noqa: E501
                    )
                ),
                callee_5: Account(
                    code=bytes.fromhex(
                        "600060006000600060007393a599bde9a3b6390afdb06952aa5ec0b8c44f3b61c350f1600055600e60025500"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
