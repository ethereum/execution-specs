"""
Gas analysis showed this test's gas can go as low as 21053, and still...

Ported from:
state_tests/stQuadraticComplexityTest/Create1000Filler.json
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
    "",
]
TX_GAS = [150000, 250000000]
TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stQuadraticComplexityTest/Create1000Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create1000(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Gas analysis showed this test's gas can go as low as 21053, and..."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_0 = Address("0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=8600000000,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 1000) [i](+ @i 1) [[ 0 ]] (CREATE 1 0 50000) ) [[ 1 ]] @i}  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x23, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0x3E8))
        )
        + Op.SSTORE(
            key=0x0, value=Op.CREATE(value=0x1, offset=0x0, size=0xC350)
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                Address(
                    "0x010d8b0816e30ff51ba07678c64b272cdeddb807"
                ): Account.NONEXISTENT,
                Address(
                    "0x014830fe159f418212e5c39b4b2e2ddc7b295395"
                ): Account.NONEXISTENT,
                contract_0: Account(storage={0: 0, 1: 0}, nonce=0),
                Address(
                    "0x0c6a8f1bf692cb9e4f9d9c5a2785d58edfd42457"
                ): Account.NONEXISTENT,
                Address(
                    "0x198d23bedd1a9fdbd4adb5760930f6877f5d142f"
                ): Account.NONEXISTENT,
                Address(
                    "0x266c09580d28c1c576e5c6b9adc926be1fecffb1"
                ): Account.NONEXISTENT,
                Address(
                    "0xe5dc2e5b40069a91f688e56ea8d12149c5480b42"
                ): Account.NONEXISTENT,
                Address(
                    "0xfdbd2625737df76e194c99994be160c5f8248dad"
                ): Account.NONEXISTENT,
                Address(
                    "0xfff043abcbf2b0972c1dca19b2ba3cd682f10e90"
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                Address(
                    "0x010d8b0816e30ff51ba07678c64b272cdeddb807"
                ): Account.NONEXISTENT,
                Address(
                    "0x014830fe159f418212e5c39b4b2e2ddc7b295395"
                ): Account.NONEXISTENT,
                contract_0: Account(storage={0: 0, 1: 0}, nonce=0),
                Address(
                    "0x0c6a8f1bf692cb9e4f9d9c5a2785d58edfd42457"
                ): Account.NONEXISTENT,
                Address(
                    "0x198d23bedd1a9fdbd4adb5760930f6877f5d142f"
                ): Account.NONEXISTENT,
                Address(
                    "0x266c09580d28c1c576e5c6b9adc926be1fecffb1"
                ): Account.NONEXISTENT,
                Address(
                    "0xe5dc2e5b40069a91f688e56ea8d12149c5480b42"
                ): Account.NONEXISTENT,
                Address(
                    "0xfdbd2625737df76e194c99994be160c5f8248dad"
                ): Account.NONEXISTENT,
                Address(
                    "0xfff043abcbf2b0972c1dca19b2ba3cd682f10e90"
                ): Account.NONEXISTENT,
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
