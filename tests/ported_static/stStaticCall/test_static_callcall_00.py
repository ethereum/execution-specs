"""
Test_static_callcall_00.

Ported from:
state_tests/stStaticCall/static_callcall_00Filler.json
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
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcall_00Filler.json"],
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
def test_static_callcall_00(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcall_00."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
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
        address=Address(0xC0E4183389EB57F779A986D8C878F89B9401DC8E),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL 350000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x55730,
                address=0x620B442C84D5068E6B57D390A1AC99130205406E,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x2F9EC0AFCB4EDCD7D38C6A48F5E36038263CA3CD),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 250000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x3D090,
            address=0x33F368F0B54063613CF5944941E8E0E4EEB64697,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x620B442C84D5068E6B57D390A1AC99130205406E),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 2 1) (SSTORE 4 (CALLER)) (SSTORE 7 (CALLVALUE)) (SSTORE 230 (ADDRESS)) (SSTORE 232 (ORIGIN)) (SSTORE 236 (CALLDATASIZE)) (SSTORE 238 (CODESIZE)) (SSTORE 240 (GASPRICE))}  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x2, value=0x1)
        + Op.SSTORE(key=0x4, value=Op.CALLER)
        + Op.SSTORE(key=0x7, value=Op.CALLVALUE)
        + Op.SSTORE(key=0xE6, value=Op.ADDRESS)
        + Op.SSTORE(key=0xE8, value=Op.ORIGIN)
        + Op.SSTORE(key=0xEC, value=Op.CALLDATASIZE)
        + Op.SSTORE(key=0xEE, value=Op.CODESIZE)
        + Op.SSTORE(key=0xF0, value=Op.GASPRICE)
        + Op.STOP,
        nonce=0,
        address=Address(0x33F368F0B54063613CF5944941E8E0E4EEB64697),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL 350000 <contract:0x2000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x55730,
                address=0xDCC76191E9F918ECFE9FBA5414884D5EE621AE00,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xBF23F3306533431B2EE5E4CA95E0A0834C090105),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 250000 <contract:0x2000000000000000000000000000000000000002> 0 64 0 64 ) }  # noqa: E501
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x3D090,
            address=0x29736372C0FAB51DB4556614EF27D74A89ACFE21,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xDCC76191E9F918ECFE9FBA5414884D5EE621AE00),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 0 1) (MSTORE 32 (CALLER)) (MSTORE 64 (CALLVALUE)) (MSTORE 96 (ADDRESS)) (MSTORE 128 (ORIGIN)) (MSTORE 160 (CALLDATASIZE)) (MSTORE 192 (CODESIZE)) (MSTORE 224 (GASPRICE))}  # noqa: E501
    addr_6 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x1)
        + Op.MSTORE(offset=0x20, value=Op.CALLER)
        + Op.MSTORE(offset=0x40, value=Op.CALLVALUE)
        + Op.MSTORE(offset=0x60, value=Op.ADDRESS)
        + Op.MSTORE(offset=0x80, value=Op.ORIGIN)
        + Op.MSTORE(offset=0xA0, value=Op.CALLDATASIZE)
        + Op.MSTORE(offset=0xC0, value=Op.CODESIZE)
        + Op.MSTORE(offset=0xE0, value=Op.GASPRICE)
        + Op.STOP,
        nonce=0,
        address=Address(0x29736372C0FAB51DB4556614EF27D74A89ACFE21),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 1, 1: 1}),
                addr: Account(storage={0: 1}),
                addr_3: Account(
                    storage={
                        2: 0,
                        4: 0,
                        7: 0,
                        230: 0,
                        232: 0,
                        236: 0,
                        238: 0,
                        240: 0,
                    },
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                target: Account(storage={0: 1, 1: 1}),
                addr_4: Account(storage={0: 1}),
                addr_6: Account(
                    storage={
                        2: 0,
                        4: 0,
                        7: 0,
                        230: 0,
                        232: 0,
                        236: 0,
                        238: 0,
                        240: 0,
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_4, left_padding=True),
    ]
    tx_gas = [3000000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
