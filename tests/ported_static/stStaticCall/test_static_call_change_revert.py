"""
Test_static_call_change_revert.

Ported from:
state_tests/stStaticCall/static_callChangeRevertFiller.json
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
    ["state_tests/stStaticCall/static_callChangeRevertFiller.json"],
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
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_change_revert(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_call_change_revert."""
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
    # {  (CALL 350000 (CALLDATALOAD 0) 0 0 0 0 0)  }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0x55730,
            address=Op.CALLDATALOAD(offset=0x0),
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x492BB18ADCE7DA2BED3592742FB4E3DF9086FB4C),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 1 1)  }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0xC031FC0AA7B61A5D7D962AFEE8838DEC6948ABB7),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 1 1) (SSTORE 1 (SLOAD 1)) }
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1)
        + Op.SSTORE(key=0x1, value=Op.SLOAD(key=0x1))
        + Op.STOP,
        nonce=0,
        address=Address(0x47C4ED3D93429CB8304737E2327B522E8928C9F3),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000001> 1 0 0 0 0) [[ 1 ]] (STATICCALL 100000 <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) [[ 2 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000001> 1 0 0 0 0) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x186A0,
                address=0xC031FC0AA7B61A5D7D962AFEE8838DEC6948ABB7,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x186A0,
                address=0xC031FC0AA7B61A5D7D962AFEE8838DEC6948ABB7,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x186A0,
                address=0xC031FC0AA7B61A5D7D962AFEE8838DEC6948ABB7,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xE6F1FDAA1C99007971C641E10AF3A8FAC0B641C8),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000001> 1 0 0 0 0) [[ 1 ]] (STATICCALL 100000 <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) [[ 2 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000001> 1 0 0 0 0) (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x186A0,
                address=0xC031FC0AA7B61A5D7D962AFEE8838DEC6948ABB7,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x186A0,
                address=0xC031FC0AA7B61A5D7D962AFEE8838DEC6948ABB7,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x186A0,
                address=0xC031FC0AA7B61A5D7D962AFEE8838DEC6948ABB7,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPDEST
        + Op.JUMPI(
            pc=0x8F, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x73)
        + Op.JUMPDEST
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xEA22EC955AC71D8E4380541212BD20818D704567),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000002> 1 0 0 0 0) [[ 1 ]] (STATICCALL 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) [[ 2 ]] (CALL 100000 <contract:0x1000000000000000000000000000000000000002> 1 0 0 0 0) }  # noqa: E501
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=0x186A0,
                address=0x47C4ED3D93429CB8304737E2327B522E8928C9F3,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x186A0,
                address=0x47C4ED3D93429CB8304737E2327B522E8928C9F3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.CALL(
                gas=0x186A0,
                address=0x47C4ED3D93429CB8304737E2327B522E8928C9F3,
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x2C004389EDAAE817E664B6D660F46735756B56D3),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr: Account(storage={0: 1, 1: 1, 2: 1}),
                addr_2: Account(balance=2),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_3: Account(storage={0: 0, 1: 0, 2: 0}),
                addr_2: Account(balance=0),
            },
        },
        {
            "indexes": {"data": 2, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr_4: Account(storage={0: 1, 1: 0, 2: 1}),
                addr_5: Account(balance=2),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_3, left_padding=True),
        Hash(addr_4, left_padding=True),
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
