"""
Test_static_call50000.

Ported from:
state_tests/stStaticCall/static_Call50000Filler.json
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
    "0000000000000000000000002e396fd4f6f2799d61f534b43175f5344c65ecac",
    "000000000000000000000000b00a8701f877b1152cd955e957fcbaf51a15f55f",
]
TX_GAS = [90000000000]
TX_VALUE = [10]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_Call50000Filler.json"],
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
def test_static_call50000(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call50000."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000000,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: lll
    # { (MSTORE 0 (SLOAD 0)) }
    addr_0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.SLOAD(key=0x0)) + Op.STOP,
        storage={0: 1},
        balance=7000,
        nonce=0,
        address=Address("0x6d440cd3e818056e21914c856e3712f4186b06c8"),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 0 (SLOAD 0)) }
    addr_0xbaaf5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.SLOAD(key=0x0)) + Op.STOP,
        storage={0: 1},
        balance=7000,
        nonce=0,
        address=Address("0x7efd7e4e34d1783f5d86b7862a37b3bbbd13deb8"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=Op.GAS,
                address=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLVALUE,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) [[ 0 ]] (STATICCALL 100000 <contract:0xbaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 50000 0 0) ) [[ 1 ]] @i}  # noqa: E501
    addr_0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x3E, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x186A0,
                address=0x7EFD7E4E34D1783F5D86B7862A37B3BBBD13DEB8,
                args_offset=0x0,
                args_size=0xC350,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0x2e396fd4f6f2799d61f534b43175f5344c65ecac"),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (SSTORE 0 (STATICCALL 100000 <contract:0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b> 0 50000 0 0)) ) (SSTORE 32 @i ) }  # noqa: E501
    addr_0xcccf5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x3E, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x186A0,
                address=0x6D440CD3E818056E21914C856E3712F4186B06C8,
                args_offset=0x0,
                args_size=0xC350,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x20, value=Op.MLOAD(offset=0x80))
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0xb00a8701f877b1152cd955e957fcbaf51a15f55f"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                sender: Account(storage={}, code=b"", nonce=1),
                addr_0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={0: 1}, nonce=0
                ),
                addr_0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={0: 0, 1: 50000},
                    balance=0x10000000000009,
                    nonce=0,
                ),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                sender: Account(storage={}, nonce=1),
                addr_0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={0: 1}, balance=7000, nonce=0
                ),
                addr_0xcccf5374fce5edbc8e2a8697c15331677e6ebf0b: Account(
                    storage={0: 1, 32: 50000}, nonce=0
                ),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=target,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
