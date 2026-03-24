"""
Test checks that the returndata buffer is changed when a subcall REVERTs. ...

Ported from:
tests/static/state_tests/stRevertTest
RevertOpcodeInCallsOnNonEmptyReturnDataFiller.json
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
        "tests/static/state_tests/stRevertTest/RevertOpcodeInCallsOnNonEmptyReturnDataFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, expected_post",
    [
        (
            "000000000000000000000000e73611b5b479b30c93ac377aeb3bfb199764f3c3",
            860000,
            {
                Address("0x172a8f572404293aa810685dfdc6f740c300cc4b"): Account(
                    storage={10: 1}
                ),
                Address("0xe73611b5b479b30c93ac377aeb3bfb199764f3c3"): Account(
                    storage={2: 1}
                ),
            },
        ),
        (
            "000000000000000000000000e73611b5b479b30c93ac377aeb3bfb199764f3c3",
            28000,
            {
                Address("0x172a8f572404293aa810685dfdc6f740c300cc4b"): Account(
                    storage={10: 255}
                )
            },
        ),
        (
            "000000000000000000000000c9da6cd8413f64323f12cd44c99671f280f15e1c",
            860000,
            {
                Address("0x172a8f572404293aa810685dfdc6f740c300cc4b"): Account(
                    storage={10: 1}
                ),
                Address("0xc9da6cd8413f64323f12cd44c99671f280f15e1c"): Account(
                    storage={2: 1}
                ),
            },
        ),
        (
            "000000000000000000000000c9da6cd8413f64323f12cd44c99671f280f15e1c",
            28000,
            {
                Address("0x172a8f572404293aa810685dfdc6f740c300cc4b"): Account(
                    storage={10: 255}
                )
            },
        ),
        (
            "000000000000000000000000f20ccaf271beaa36e7cf4c9ced2867fac9558f14",
            860000,
            {
                Address("0x172a8f572404293aa810685dfdc6f740c300cc4b"): Account(
                    storage={10: 1}
                ),
                Address("0xf20ccaf271beaa36e7cf4c9ced2867fac9558f14"): Account(
                    storage={2: 1}
                ),
            },
        ),
        (
            "000000000000000000000000f20ccaf271beaa36e7cf4c9ced2867fac9558f14",
            28000,
            {
                Address("0x172a8f572404293aa810685dfdc6f740c300cc4b"): Account(
                    storage={10: 255}
                )
            },
        ),
        (
            "0000000000000000000000006bacdfa8216dbb2a09819f8739e57ae3574c9fff",
            860000,
            {
                Address("0x172a8f572404293aa810685dfdc6f740c300cc4b"): Account(
                    storage={10: 1}
                ),
                Address("0x6bacdfa8216dbb2a09819f8739e57ae3574c9fff"): Account(
                    storage={0: 1}
                ),
                Address("0xea519c47889074e6378b0d83747f2c3ea0b9cbc9"): Account(
                    storage={5: 1}
                ),
            },
        ),
        (
            "0000000000000000000000006bacdfa8216dbb2a09819f8739e57ae3574c9fff",
            28000,
            {
                Address("0x172a8f572404293aa810685dfdc6f740c300cc4b"): Account(
                    storage={10: 255}
                )
            },
        ),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_revert_opcode_in_calls_on_non_empty_return_data(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Test checks that the returndata buffer is changed when a subcall..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0xC)
            + Op.RETURN(offset=0x0, size=0x40)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x127eaf7e31d691a8393b7a2f84a6e94372190c01"),  # noqa: E501
    )
    # Source: LLL
    # { (CALL 0 <contract:0xffff5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[10]] (CALL 260000 (CALLDATALOAD 0) 0 0 0 0 0)}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x0,
                    address=0x127EAF7E31D691A8393B7A2F84A6E94372190C01,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0xA,
                value=Op.CALL(
                    gas=0x3F7A0,
                    address=Op.CALLDATALOAD(offset=0x0),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        storage={0xA: 0xFF},
        balance=1,
        nonce=0,
        address=Address("0x172a8f572404293aa810685dfdc6f740c300cc4b"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x0,
                    address=0x127EAF7E31D691A8393B7A2F84A6E94372190C01,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x186A0,
                    address=0xEA519C47889074E6378B0D83747F2C3EA0B9CBC9,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=Op.RETURNDATASIZE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x6bacdfa8216dbb2a09819f8739e57ae3574c9fff"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=0x1, value=0xC)
            + Op.REVERT(offset=0x0, size=0x1)
            + Op.SSTORE(key=0x3, value=0xD)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0x93a599bde9a3b6390afdb06952aa5ec0b8c44f3b"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x0,
                    address=0x127EAF7E31D691A8393B7A2F84A6E94372190C01,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0xC350,
                    address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=Op.RETURNDATASIZE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0xc9da6cd8413f64323f12cd44c99671f280f15e1c"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x0,
                    address=0x127EAF7E31D691A8393B7A2F84A6E94372190C01,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0xC350,
                    address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=Op.RETURNDATASIZE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0xe73611b5b479b30c93ac377aeb3bfb199764f3c3"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x0,
                    address=0x127EAF7E31D691A8393B7A2F84A6E94372190C01,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x4,
                value=Op.CALL(
                    gas=0xC350,
                    address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x5, value=Op.RETURNDATASIZE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0xea519c47889074e6378b0d83747f2c3ea0b9cbc9"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x0,
                    address=0x127EAF7E31D691A8393B7A2F84A6E94372190C01,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.DELEGATECALL(
                    gas=0xC350,
                    address=0x93A599BDE9A3B6390AFDB06952AA5EC0B8C44F3B,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x2, value=Op.RETURNDATASIZE)
            + Op.STOP
        ),
        balance=1,
        nonce=0,
        address=Address("0xf20ccaf271beaa36e7cf4c9ced2867fac9558f14"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
