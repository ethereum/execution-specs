"""
Test_create1000_shnghai.

Ported from:
state_tests/stQuadraticComplexityTest/Create1000ShnghaiFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stQuadraticComplexityTest/Create1000ShnghaiFiller.json"],
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
def test_create1000_shnghai(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_create1000_shnghai."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_0 = Address(0xBBBF5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=8600000000,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 1000) [i](+ @i 1) [[ 0 ]] (CREATE 1 0 10) ) [[ 1 ]] @i}  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x22, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0x3E8))
        )
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x1, offset=0x0, size=0xA))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
        + Op.STOP,
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address(0xBBBF5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                compute_create_address(
                    address=contract_0, nonce=866
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=780
                ): Account.NONEXISTENT,
                contract_0: Account(storage={0: 0, 1: 0}, nonce=0),
                compute_create_address(
                    address=contract_0, nonce=959
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=393
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=499
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=19
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=327
                ): Account.NONEXISTENT,
                compute_create_address(
                    address=contract_0, nonce=493
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                compute_create_address(address=contract_0, nonce=866): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=contract_0, nonce=780): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                contract_0: Account(
                    storage={
                        0: 0x7981FA24B134DEB51D71D250D7B0D9E33C8C5457,
                        1: 1000,
                    },
                    balance=0xFFFFFFFFFFC21,
                    nonce=1000,
                ),
                compute_create_address(address=contract_0, nonce=733): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=contract_0, nonce=959): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=contract_0, nonce=393): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=contract_0, nonce=499): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=contract_0, nonce=36): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=contract_0, nonce=568): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=contract_0, nonce=66): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=contract_0, nonce=981): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=contract_0, nonce=693): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=contract_0, nonce=390): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=contract_0, nonce=19): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=contract_0, nonce=327): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
                compute_create_address(address=contract_0, nonce=493): Account(
                    storage={}, code=b"", balance=1, nonce=1
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [150000, 250000000]
    tx_value = [10]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
