"""
Test_create_init_code_size_limit.

Ported from:
state_tests/Shanghai/stEIP3860_limitmeterinitcode/createInitCodeSizeLimitFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
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
    [
        "state_tests/Shanghai/stEIP3860_limitmeterinitcode/createInitCodeSizeLimitFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
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
def test_create_init_code_size_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_create_init_code_size_limit."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB)
    contract_1 = Address(0x000000000000000000000000000000000000C0DE)
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

    pre[sender] = Account(balance=0xBEBC200, nonce=1)
    # Source: yul
    # berlin
    # {
    #   // :yul { codecopy(0x00, 0x00, 0x0a) return(0x00, 0x0a) }
    #   mstore(0, 0x600a80600080396000f300000000000000000000000000000000000000000000)  # noqa: E501
    #   // get initcode size from calldata
    #   let initcode_size := calldataload(0)
    #   let gas_before := gas()
    #   let create_result := create(0, 0, initcode_size)
    #   sstore(10, sub(gas_before, gas()))
    #   sstore(0, create_result)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SHL(0xB0, 0x600A80600080396000F3)
        + Op.PUSH1[0x0]
        + Op.SWAP1
        + Op.DUP2
        + Op.MSTORE
        + Op.CALLDATALOAD
        + Op.GAS
        + Op.SWAP1
        + Op.PUSH1[0x0]
        + Op.DUP1
        + Op.CREATE
        + Op.SWAP1
        + Op.GAS
        + Op.SWAP1
        + Op.SSTORE(key=0xA, value=Op.SUB)
        + Op.PUSH1[0x0]
        + Op.SSTORE
        + Op.STOP,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000C0DE),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   mstore(0, calldataload(0))
    #   let call_result := call(10000000, 0xc0de, 0, 0, calldatasize(), 0, 0)
    #   sstore(0, call_result)
    #   sstore(1, 1)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x989680,
                address=contract_1,
                value=Op.DUP1,
                args_offset=Op.DUP2,
                args_size=Op.CALLDATASIZE,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.STOP,
        nonce=1,
        address=Address(0xBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=2),
                contract_0: Account(storage={0: 1, 1: 1}),
                contract_1: Account(
                    storage={
                        0: compute_create_address(address=contract_1, nonce=1),
                        10: 46323,
                    },
                ),
                compute_create_address(address=contract_1, nonce=1): Account(
                    storage={},
                    code=bytes.fromhex("600a80600080396000f3"),
                    balance=0,
                    nonce=1,
                ),
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                sender: Account(nonce=2),
                contract_0: Account(storage={0: 0, 1: 1}, nonce=1),
                contract_1: Account(storage={}),
                Address(
                    0x682327124C5D2DC0CD2158BA65D37AC3D2140C91
                ): Account.NONEXISTENT,
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(0xC000),
        Hash(0xC001),
    ]
    tx_gas = [15000000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
