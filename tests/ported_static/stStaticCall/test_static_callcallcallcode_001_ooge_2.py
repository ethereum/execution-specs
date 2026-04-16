"""
Test_static_callcallcallcode_001_ooge_2.

Ported from:
state_tests/stStaticCall/static_callcallcallcode_001_OOGE_2Filler.json
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
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_callcallcallcode_001_OOGE_2Filler.json"],
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
def test_static_callcallcallcode_001_ooge_2(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_callcallcallcode_001_ooge_2."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xDE0B6B3A7640000)

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
    # {  (SSTORE 3 1) (MSTORE 3 1)}
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x3, value=0x1)
        + Op.MSTORE(offset=0x3, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x9D41CA9233D19D3202BEFCEF33F16AF7201F0EAA),  # noqa: E501
    )
    # Source: lll
    # {  (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)  ) }
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
        address=Address(0x609E4DFE6190235B9A0362084C741D9EC330FB1E),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 120020 <contract:0x1000000000000000000000000000000000000003> 0 0 64 0 64 ) }  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x1D4D4,
            address=0x9D41CA9233D19D3202BEFCEF33F16AF7201F0EAA,
            value=0x0,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xFEE7D85F02F84CE8917FA8300FEA57FF41AD47D7),  # noqa: E501
    )
    # Source: lll
    # {  (CALLCODE 120020 <contract:0x2000000000000000000000000000000000000003> 0 0 64 0 64 ) }  # noqa: E501
    addr_7 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x1D4D4,
            address=0x609E4DFE6190235B9A0362084C741D9EC330FB1E,
            value=0x0,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xA7C64824C59E4295A3868A2B275AD46B38F7846D),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 300000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) }  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x493E0,
            address=0xFEE7D85F02F84CE8917FA8300FEA57FF41AD47D7,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xBDA9155E6214FE759004E6FCBE736289EF800528),  # noqa: E501
    )
    # Source: lll
    # {  (STATICCALL 300000 <contract:0x2000000000000000000000000000000000000002> 0 64 0 64 ) }  # noqa: E501
    addr_6 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x493E0,
            address=0xA7C64824C59E4295A3868A2B275AD46B38F7846D,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x2DB6829F13013D6280C5BE4F6A5E87DE274A3C47),  # noqa: E501
    )
    # Source: lll
    # {  [[ 0 ]] (STATICCALL 500000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x7A120,
                address=0xBDA9155E6214FE759004E6FCBE736289EF800528,
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
    # {  [[ 0 ]] (STATICCALL 500000 <contract:0x2000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.STATICCALL(
                gas=0x7A120,
                address=0x2DB6829F13013D6280C5BE4F6A5E87DE274A3C47,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xED9009ABB678FB6E7898148DC46FA339EA580CBD),  # noqa: E501
    )

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
    )

    post = {target: Account(storage={0: 1, 1: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
