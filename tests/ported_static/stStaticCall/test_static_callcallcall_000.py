"""
Test_static_callcallcall_000.

Ported from:
state_tests/stStaticCall/static_callcallcall_000Filler.json
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
    ["state_tests/stStaticCall/static_callcallcall_000Filler.json"],
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
def test_static_callcallcall_000(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcallcall_000."""
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
    # {  [[ 0 ]] (STATICCALL 650000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x9EB10,
                address=0x36ACE903A154317B8FA379AAD88A425B7EF025DC,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xFB157BFD4470AB46DFFEC6F8390B747C67F62B38),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 400000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (MSTORE 32 1) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x61A80,
                address=0x3F6D147A714319EF90C47921715DC5F0CCFE3B09,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x36ACE903A154317B8FA379AAD88A425B7EF025DC),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 250000 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 32 1) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x3D090,
                address=0x181B4ED322E192361633CC3C0A418F259AB0CF4B,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x3F6D147A714319EF90C47921715DC5F0CCFE3B09),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) (SSTORE 4 (CALLER)) (SSTORE 7 (CALLVALUE)) (SSTORE 330 (ADDRESS)) (SSTORE 332 (ORIGIN)) (SSTORE 336 (CALLDATASIZE)) (SSTORE 338 (CODESIZE)) (SSTORE 340 (GASPRICE))}  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x3, value=0x1)
        + Op.SSTORE(key=0x4, value=Op.CALLER)
        + Op.SSTORE(key=0x7, value=Op.CALLVALUE)
        + Op.SSTORE(key=0x14A, value=Op.ADDRESS)
        + Op.SSTORE(key=0x14C, value=Op.ORIGIN)
        + Op.SSTORE(key=0x150, value=Op.CALLDATASIZE)
        + Op.SSTORE(key=0x152, value=Op.CODESIZE)
        + Op.SSTORE(key=0x154, value=Op.GASPRICE)
        + Op.STOP,
        nonce=0,
        address=Address(0x181B4ED322E192361633CC3C0A418F259AB0CF4B),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL 350000 <contract:0x2000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x55730,
                address=0xD518EBB39FB88BEB34AD1598FE3CCD3F8E4C4708,
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
    # {  (MSTORE 3 1) (STATICCALL 300000 <contract:0x2000000000000000000000000000000000000002> 0 64 0 64 ) (MSTORE 32 1) }  # noqa: E501
    addr_6 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=0x85EE033B8FF327153F5C82D191B4942102DEBFFC,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xD518EBB39FB88BEB34AD1598FE3CCD3F8E4C4708),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) (STATICCALL 250000 <contract:0x2000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 32 1) }  # noqa: E501
    addr_7 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x3D090,
                address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x85EE033B8FF327153F5C82D191B4942102DEBFFC),  # noqa: E501
    )
    # Source: lll
    # {  (MSTORE 3 1) }
    addr_8 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0x335C5531B84765A7626E6E76688F18B81BE5259C),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr: Account(storage={0: 1}),
                addr_2: Account(storage={}),
                addr_3: Account(storage={}),
                addr_4: Account(
                    storage={
                        3: 0,
                        4: 0,
                        7: 0,
                        330: 0,
                        332: 0,
                        336: 0,
                        338: 0,
                        340: 0,
                    },
                ),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_5: Account(storage={0: 1}),
                addr_6: Account(storage={}),
                addr_7: Account(storage={}),
                addr_8: Account(
                    storage={
                        3: 0,
                        4: 0,
                        7: 0,
                        330: 0,
                        332: 0,
                        336: 0,
                        338: 0,
                        340: 0,
                    },
                ),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_5, left_padding=True),
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
