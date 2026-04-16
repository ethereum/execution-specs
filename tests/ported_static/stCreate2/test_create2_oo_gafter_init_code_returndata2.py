"""
Call RETURNDATASIZE and RETURNDATACOPY after CREATE2 deploy a contract....

Ported from:
state_tests/stCreate2/Create2OOGafterInitCodeReturndata2Filler.json
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
    ["state_tests/stCreate2/Create2OOGafterInitCodeReturndata2Filler.json"],
)
@pytest.mark.valid_from("Cancun")
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
def test_create2_oo_gafter_init_code_returndata2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Call RETURNDATASIZE and RETURNDATACOPY after CREATE2 deploy a..."""
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
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { (MSTORE 0 0x6460016001556000526005601bf3) (CREATE2 0 18 14 0) [[ 1 ]] (RETURNDATASIZE) (RETURNDATACOPY 0 0 0) [[ 2 ]] (MLOAD 0) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x6460016001556000526005601BF3)
        + Op.POP(Op.CREATE2(value=0x0, offset=0x12, size=0xE, salt=0x0))
        + Op.SSTORE(key=0x1, value=Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x0)
        + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={1: 2},
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": -1, "gas": 0, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(storage={1: 2, 2: 0}),
                compute_create_address(
                    address=contract_0, nonce=0
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": -1, "gas": 1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={1: 0, 2: 0x6460016001556000526005601BF3}
                ),
                Address(0x6878B140F875209C82AB4D5F083B55947299EF6B): Account(
                    code=bytes.fromhex("6001600155")
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes(""),
    ]
    tx_gas = [54000, 95000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
