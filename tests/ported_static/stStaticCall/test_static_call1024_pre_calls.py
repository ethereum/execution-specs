"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_Call1024PreCallsFiller.json
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
        "tests/static/state_tests/stStaticCall/static_Call1024PreCallsFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "0000000000000000000000002806e7553f3585d821f91d679a254abbf002f6f2",
            {
                Address("0x2806e7553f3585d821f91d679a254abbf002f6f2"): Account(
                    storage={0: 1, 2: 1, 3: 1}
                ),
                Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"): Account(
                    storage={0: 1, 1: 1}
                ),
            },
        ),
        (
            "0000000000000000000000007c546b69d5bda111c03c8d7b51b41a8d55b843ca",
            {
                Address("0xc0e4183389eb57f779a986d8c878f89b9401dc8e"): Account(
                    storage={0: 1, 1: 1}
                )
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_call1024_pre_calls(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xCC381C83857B17CA629268ED418E2915A0287B84EFE9CF2204C020302E83CDA0
    )
    callee_2 = Address("0xd9b97c712ebce43f3c19179bbef44b550f9e8bc0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.STATICCALL(
                    gas=0xFFFF,
                    address=0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x3,
                value=Op.STATICCALL(
                    gas=0xFFFF,
                    address=0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=0xFFFFFFFFFFF,
                    address=0x2806E7553F3585D821F91D679A254ABBF002F6F2,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=2024,
        nonce=0,
        address=Address("0x2806e7553f3585d821f91d679a254abbf002f6f2"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0xFFFF,
                    address=0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0xFFFF,
                    address=0xD9B97C712EBCE43F3C19179BBEF44B550F9E8BC0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x0, value=Op.ADD(Op.MLOAD(offset=0x0), 0x1))
            + Op.STATICCALL(
                gas=0xFFFFFFFFFFF,
                address=0x7C546B69D5BDA111C03C8D7B51B41A8D55B843CA,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        balance=2024,
        nonce=0,
        address=Address("0x7c546b69d5bda111c03c8d7b51b41a8d55b843ca"),  # noqa: E501
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
    pre[callee_2] = Account(balance=7000, nonce=0)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=9214364837600034817,
        value=10,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
