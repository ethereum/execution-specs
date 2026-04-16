"""
Callcode inside create contract init to non-existent contract.

Ported from:
state_tests/stCallCodes/callcodeInInitcodeToEmptyContractFiller.json
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
    ["state_tests/stCallCodes/callcodeInInitcodeToEmptyContractFiller.json"],
)
@pytest.mark.valid_from("Cancun")
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
def test_callcode_in_initcode_to_empty_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Callcode inside create contract init to non-existent contract."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x1100000000000000000000000000000000000000)
    contract_1 = Address(0x1000000000000000000000000000000000000000)
    contract_2 = Address(0x2000000000000000000000000000000000000000)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0x2386F26FC10000)
    # Source: lll
    # { (CALL 300000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0x493E0,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x1100000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # {(seq (CREATE 0 0 (lll (seq  [[1]] (CALLCODE 500000 0x1000000000000000000000000000000000000001 1 0 0 0 0)  [[2]] 1  ) 0)   )           )}  # noqa: E501
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x2D]
        + Op.CODECOPY(dest_offset=0x0, offset=0xF, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.CREATE
        + Op.STOP
        + Op.INVALID
        + Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=0x7A120,
                address=0x1000000000000000000000000000000000000001,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0x1)
        + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address(0x1000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # {(seq (CREATE2 0 0 (lll (seq  [[1]] (CALLCODE 500000 0x1000000000000000000000000000000000000001 1 0 0 0 0) [[2]] 1 ) 0)   0)           )}  # noqa: E501
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0x2D]
        + Op.CODECOPY(dest_offset=0x0, offset=0x11, size=Op.DUP1)
        + Op.PUSH1[0x0] * 2
        + Op.CREATE2
        + Op.STOP
        + Op.INVALID
        + Op.SSTORE(
            key=0x1,
            value=Op.CALLCODE(
                gas=0x7A120,
                address=0x1000000000000000000000000000000000000001,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x2, value=0x1)
        + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address(0x2000000000000000000000000000000000000000),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                compute_create_address(address=contract_1, nonce=0): Account(
                    storage={2: 1}
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                Address(0x9F9F2F99F78BFEDCD1F32D936203BD1C0CB00853): Account(
                    storage={2: 1}
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(contract_1, left_padding=True),
        Hash(contract_2, left_padding=True),
    ]
    tx_gas = [1453081]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
