"""
Test_create2_code_size_limit.

Ported from:
state_tests/stCodeSizeLimit/create2CodeSizeLimitFiller.yml
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
from execution_testing.vm import Op

from tests.ported_static.post_state_resolution import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCodeSizeLimit/create2CodeSizeLimitFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_before("EIP7954")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="valid",
        ),
        pytest.param(
            1,
            0,
            0,
            id="invalid",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2_code_size_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_create2_code_size_limit."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=20000000,
    )

    pre[sender] = Account(balance=0xBEBC200)
    # Source: yul
    # berlin
    # {
    #   mstore(0, calldataload(0))
    #   sstore(0, create2(0, 0, calldatasize(), 0))
    #   sstore(1, 1)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE2(
                value=Op.DUP1, offset=Op.DUP2, size=Op.CALLDATASIZE, salt=0x0
            ),
        )
        + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    # Initcode: PUSH2 <size> PUSH1 0 RETURN. Sizes scale with
    # fork.max_code_size() so pre-7954 forks get the original 0x6000
    # / 0x6001 and Amsterdam+ gets 0x8000 / 0x8001.
    max_code_size = fork.max_code_size()
    tx_data = [
        Bytes(b"\x61" + max_code_size.to_bytes(2) + b"\x60\x00\xf3"),
        Bytes(b"\x61" + (max_code_size + 1).to_bytes(2) + b"\x60\x00\xf3"),
    ]
    tx_gas = [15000000]
    valid_create2_address = compute_create_address(
        address=contract_0,
        salt=0,
        initcode=tx_data[0],
        opcode=Op.CREATE2,
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(
                    storage={
                        0: valid_create2_address,
                        1: 1,
                    },
                ),
                valid_create2_address: Account(storage={}, balance=0, nonce=1),
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=1),
                contract_0: Account(storage={0: 0, 1: 1}),
                valid_create2_address: Account.NONEXISTENT,
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
