"""
Test_static_callcallcall_000_ooge.

Ported from:
state_tests/stStaticCall/static_callcallcall_000_OOGEFiller.json
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
    ["state_tests/stStaticCall/static_callcallcall_000_OOGEFiller.json"],
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
def test_static_callcallcall_000_ooge(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcallcall_000_ooge."""
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
    # {  [[ 0 ]] (STATICCALL 500000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x7A120,
                address=0xA69F4D8056BB192982BF07D59AD0FF96A15B41D9,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x071587C3E5F2EBF88B2A5B048733778605ADDB28),  # noqa: E501
    )
    # Source: lll
    # {   (MSTORE 3 1) (STATICCALL 300000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) (MSTORE 32 1) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=0xCD0BD482BAEEB001E6F3FFD36BCEB34D32169C93,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xA69F4D8056BB192982BF07D59AD0FF96A15B41D9),  # noqa: E501
    )
    # Source: lll
    # {   (MSTORE 3 1) (STATICCALL 120020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) (MSTORE 32 1) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x1D4D4,
                address=0x9D41CA9233D19D3202BEFCEF33F16AF7201F0EAA,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xCD0BD482BAEEB001E6F3FFD36BCEB34D32169C93),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) (MSTORE 3 1)}
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x3, value=0x1)
        + Op.MSTORE(offset=0x3, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x9D41CA9233D19D3202BEFCEF33F16AF7201F0EAA),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL 600000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x927C0,
                address=0xA69F4D8056BB192982BF07D59AD0FF96A15B41D9,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x9B0CB3CB3655D3173FF7C2CD51319AAF2CCA3CAD),  # noqa: E501
    )
    # Source: lll
    # {   (MSTORE 3 1) (STATICCALL 300000 <contract:0x2000000000000000000000000000000000000002> 0 64 0 64 )(MSTORE 32 1) }  # noqa: E501
    addr_6 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=0xAC6BF72C47193C6FEFC55EFCC14674F8023F39F9,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xA76CE2DE971EA2B78BC19BA706CB135F4FFF2CC2),  # noqa: E501
    )
    # Source: lll
    # {   (MSTORE 3 1) (STATICCALL 120020 <contract:0x2000000000000000000000000000000000000003> 0 64 0 64 )(MSTORE 32 1) }  # noqa: E501
    addr_7 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x3, value=0x1)
        + Op.POP(
            Op.STATICCALL(
                gas=0x1D4D4,
                address=0xF31E5B020AFCCF373BFA588C4D3A199C4F7A46A4,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
        )
        + Op.MSTORE(offset=0x20, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xAC6BF72C47193C6FEFC55EFCC14674F8023F39F9),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)  ) }
    addr_8 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1C, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
        address=Address(0xF31E5B020AFCCF373BFA588C4D3A199C4F7A46A4),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
                addr: Account(storage={0: 1, 1: 0, 2: 0, 3: 0}),
                addr_2: Account(storage={1: 0, 2: 0, 3: 0}),
                addr_3: Account(storage={2: 0, 3: 0}),
                addr_4: Account(storage={3: 0}),
                target: Account(storage={0: 1, 1: 1}),
            },
        },
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={0: 1, 1: 1})},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Hash(addr, left_padding=True),
        Hash(addr_5, left_padding=True),
    ]
    tx_gas = [1720000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
