"""
Test_static_ab_acalls0.

Ported from:
state_tests/stStaticCall/static_ABAcalls0Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
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


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_ABAcalls0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
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
def test_static_ab_acalls0(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_ab_acalls0."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
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
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xFDDB268F64FD5A90F618BBEE0BD38E0C24B0A945),  # noqa: E501
    )
    # Source: lll
    # {  [[ (PC) ]] (STATICCALL 100000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=Op.PC,
            value=Op.STATICCALL(
                gas=0x186A0,
                address=0x9A95017E0DBF52BB87DDFDA883B69D6188D574CA,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xC54C4BE163ADD3CC0EFE5268A599A308DAB12C74),  # noqa: E501
    )
    # Source: lll
    # { [[ (PC) ]] (ADD 1 (STATICCALL 50000 <contract:0x095e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0)) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=Op.PC,
            value=Op.ADD(
                0x1,
                Op.STATICCALL(
                    gas=0xC350,
                    address=0xC54C4BE163ADD3CC0EFE5268A599A308DAB12C74,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            ),
        )
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address(0x9A95017E0DBF52BB87DDFDA883B69D6188D574CA),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 1 (PC)) (STATICCALL 100000 <contract:0x245304eb96065b2a98b57a48a06ae28d285a71b5> 0 0 0 0) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=Op.PC)
        + Op.STATICCALL(
            gas=0x186A0,
            address=0x718A83E869D6F4DEA50A650B9825CBFE683BDF16,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x7A365D98665A08E6ED6C1638C8EA6775FA649048),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 1 (PC)) (STATICCALL 50000 <contract:0x195e7baea6a6c7c4c2dfeb977efac326af552d87> 0 0 0 0) }  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=Op.PC)
        + Op.STATICCALL(
            gas=0xC350,
            address=0x7A365D98665A08E6ED6C1638C8EA6775FA649048,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=23,
        nonce=0,
        address=Address(0x718A83E869D6F4DEA50A650B9825CBFE683BDF16),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr: Account(storage={36: 0}, balance=0xDE0B6B3A76586A0),
                addr_2: Account(storage={38: 0}),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_3: Account(storage={36: 0}, balance=0xDE0B6B3A76586A0),
                addr_4: Account(storage={38: 0}),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_3, left_padding=True),
    ]
    tx_gas = [1000000]
    tx_value = [100000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
