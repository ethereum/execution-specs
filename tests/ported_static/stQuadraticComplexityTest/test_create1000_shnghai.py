"""
test_create1000_shnghai

Ported from:
state_tests/stQuadraticComplexityTest/Create1000ShnghaiFiller.json
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
    "",
]
TX_GAS = [150000, 250000000]
TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stQuadraticComplexityTest/Create1000ShnghaiFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="-g0",
        ),
        pytest.param(
            0, 1, 0,
            id="-g1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create1000_shnghai(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """test_create1000_shnghai"""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_0 = Address("0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b")
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
        gas_limit=8600000000,
    )

    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffff)
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 1000) [i](+ @i 1) [[ 0 ]] (CREATE 1 0 10) ) [[ 1 ]] @i}
    contract_0 = pre.deploy_contract(
        code=Op.JUMPDEST
        + Op.JUMPI(pc=0x22, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0x3e8)))
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x1, offset=0x0, size=0xa))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0) + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80)) + Op.STOP,
        balance=0xfffffffffffff,
        nonce=0,
        address=Address("0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': -1, 'gas': 0, 'value': -1},
            "network": ['>=Cancun<Osaka'],
            "result": {
        Address("0x010d8b0816e30ff51ba07678c64b272cdeddb807"): Account.NONEXISTENT,  # noqa: E501
        Address("0x014830fe159f418212e5c39b4b2e2ddc7b295395"): Account.NONEXISTENT,  # noqa: E501
        contract_0: Account(storage={0: 0, 1: 0}, nonce=0),
        Address("0x0c6a8f1bf692cb9e4f9d9c5a2785d58edfd42457"): Account.NONEXISTENT,  # noqa: E501
        Address("0x198d23bedd1a9fdbd4adb5760930f6877f5d142f"): Account.NONEXISTENT,  # noqa: E501
        Address("0x266c09580d28c1c576e5c6b9adc926be1fecffb1"): Account.NONEXISTENT,  # noqa: E501
        Address("0xe5dc2e5b40069a91f688e56ea8d12149c5480b42"): Account.NONEXISTENT,  # noqa: E501
        Address("0xfdbd2625737df76e194c99994be160c5f8248dad"): Account.NONEXISTENT,  # noqa: E501
        Address("0xfff043abcbf2b0972c1dca19b2ba3cd682f10e90"): Account.NONEXISTENT,  # noqa: E501
    },
        },
        {
            "indexes": {'data': -1, 'gas': 1, 'value': -1},
            "network": ['>=Cancun<Osaka'],
            "result": {
        Address("0x010d8b0816e30ff51ba07678c64b272cdeddb807"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        Address("0x014830fe159f418212e5c39b4b2e2ddc7b295395"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        contract_0: Account(
                storage={
            0: 0x7981fa24b134deb51d71d250d7b0d9e33c8c5457,
            1: 1000,
        },
                balance=0xffffffffffc21,
                nonce=1000,
            ),
        Address("0x0443d33cbefcfb9dedd1885b4c58b06cb1bb0c09"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        Address("0x0c6a8f1bf692cb9e4f9d9c5a2785d58edfd42457"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        Address("0x198d23bedd1a9fdbd4adb5760930f6877f5d142f"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        Address("0x266c09580d28c1c576e5c6b9adc926be1fecffb1"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        Address("0x38382e1ec7bf834f328feb3170293b1ae558aed0"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        Address("0x49198360b42d89332f8cc121182e071493045c40"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        Address("0x69eada7f1d77ff9bf9c789d44990f9141e39d71f"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        Address("0x901cc1c13f30eb2fc6de17ba1867dcc8c1561d46"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        Address("0xcb78de6453fe67ac38868ac60825f0288e509167"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        Address("0xde8ae395bafe56c8968a2cec0567ec2562598189"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        Address("0xe5dc2e5b40069a91f688e56ea8d12149c5480b42"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        Address("0xfdbd2625737df76e194c99994be160c5f8248dad"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
        Address("0xfff043abcbf2b0972c1dca19b2ba3cd682f10e90"): Account(storage={}, code=b"", balance=1, nonce=1),  # noqa: E501
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
        nonce=0,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
