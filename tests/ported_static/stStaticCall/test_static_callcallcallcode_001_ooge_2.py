"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcallcallcode_001_OOGE_2Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/static_callcallcallcode_001_OOGE_2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "000000000000000000000000071587c3e5f2ebf88b2a5b048733778605addb28",
            {
                Address("0x071587c3e5f2ebf88b2a5b048733778605addb28"): Account(
                    storage={0: 1}
                ),
                Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
        (
            "000000000000000000000000ed9009abb678fb6e7898148dc46fa339ea580cbd",
            {
                Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"): Account(
                    storage={0: 1, 1: 1}
                ),
                Address("0xed9009abb678fb6e7898148dc46fa339ea580cbd"): Account(
                    storage={0: 1}
                ),
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcallcallcode_001_ooge_2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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

    pre.deploy_contract(
        code=(
            Op.SSTORE(
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
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x071587c3e5f2ebf88b2a5b048733778605addb28"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0x493E0,
                address=0xA7C64824C59E4295A3868A2B275AD46B38F7846D,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x2db6829f13013d6280c5be4f6a5e87de274a3c47"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPDEST
            + Op.JUMPI(
                pc=0x1C,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.POP(Op.EXTCODESIZE(address=0x1))
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x0)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x609e4dfe6190235b9a0362084c741d9ec330fb1e"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x3, value=0x1)
            + Op.MSTORE(offset=0x3, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x9d41ca9233d19d3202befcef33f16af7201f0eaa"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0x1D4D4,
                address=0x609E4DFE6190235B9A0362084C741D9EC330FB1E,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xa7c64824c59e4295a3868a2b275ad46b38f7846d"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.STATICCALL(
                gas=0x493E0,
                address=0xFEE7D85F02F84CE8917FA8300FEA57FF41AD47D7,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xbda9155e6214fe759004e6fcbe736289ef800528"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (CALL (GAS) (CALLDATALOAD 0) (CALLVALUE) 0 0 0 0) [[ 1 ]] 1 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
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
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    pre.deploy_contract(
        code=(
            Op.SSTORE(
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
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xed9009abb678fb6e7898148dc46fa339ea580cbd"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0x1D4D4,
                address=0x9D41CA9233D19D3202BEFCEF33F16AF7201F0EAA,
                value=0x0,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xfee7d85f02f84ce8917fa8300fea57ff41ad47d7"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=1720000,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
