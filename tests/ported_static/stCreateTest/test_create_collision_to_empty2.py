"""
data0 - create collision to empty, data1 - to empty but nonce, data2 - to...

Ported from:
tests/static/state_tests/stCreateTest/CreateCollisionToEmpty2Filler.json
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
        "tests/static/state_tests/stCreateTest/CreateCollisionToEmpty2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, tx_gas_limit, tx_value, expected_post",
    [
        (
            "0000000000000000000000001000000000000000000000000000000000000000",
            600000,
            0,
            {
                Address("0x1000000000000000000000000000000000000000"): Account(
                    storage={1: 0x13136008B64FF592819B2FA6D43F2835C452020E}
                ),
                Address("0x13136008b64ff592819b2fa6d43f2835c452020e"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "0000000000000000000000001000000000000000000000000000000000000000",
            600000,
            1,
            {
                Address("0x1000000000000000000000000000000000000000"): Account(
                    storage={1: 0x13136008B64FF592819B2FA6D43F2835C452020E}
                ),
                Address("0x13136008b64ff592819b2fa6d43f2835c452020e"): Account(
                    storage={1: 1}
                ),
            },
        ),
        (
            "0000000000000000000000001000000000000000000000000000000000000000",
            54000,
            0,
            {},
        ),
        (
            "0000000000000000000000001000000000000000000000000000000000000000",
            54000,
            1,
            {},
        ),
        (
            "0000000000000000000000002000000000000000000000000000000000000000",
            600000,
            0,
            {},
        ),
        (
            "0000000000000000000000002000000000000000000000000000000000000000",
            600000,
            1,
            {},
        ),
        (
            "0000000000000000000000002000000000000000000000000000000000000000",
            54000,
            0,
            {},
        ),
        (
            "0000000000000000000000002000000000000000000000000000000000000000",
            54000,
            1,
            {},
        ),
        (
            "0000000000000000000000003000000000000000000000000000000000000000",
            600000,
            0,
            {},
        ),
        (
            "0000000000000000000000003000000000000000000000000000000000000000",
            600000,
            1,
            {},
        ),
        (
            "0000000000000000000000003000000000000000000000000000000000000000",
            54000,
            0,
            {},
        ),
        (
            "0000000000000000000000003000000000000000000000000000000000000000",
            54000,
            1,
            {},
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
        "case8",
        "case9",
        "case10",
        "case11",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_collision_to_empty2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    tx_gas_limit: int,
    tx_value: int,
    expected_post: dict,
) -> None:
    """Data0 - create collision to empty, data1 - to empty but nonce,..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )
    callee = Address("0x0bf4c804e0579073baf54ec4ec37cd04f3455c65")
    callee_2 = Address("0x13136008b64ff592819b2fa6d43f2835c452020e")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(balance=0, nonce=2)
    # Source: LLL
    # { (MSTORE 0 0x6001600155) [[1]] (CREATE 0 27 5) }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x6001600155)
            + Op.SSTORE(
                key=0x1, value=Op.CREATE(value=0x0, offset=0x1B, size=0x5)
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[callee_2] = Account(balance=10, nonce=0)
    # Source: LLL
    # { (CALL 80000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0x13880,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1a00000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 0 0x6001600155) [[1]] (CREATE 0 27 5) }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x6001600155)
            + Op.SSTORE(
                key=0x1, value=Op.CREATE(value=0x0, offset=0x1B, size=0x5)
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x2000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 0 0x6001600155) [[1]] (CREATE 0 27 5) }
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x6001600155)
            + Op.SSTORE(
                key=0x1, value=Op.CREATE(value=0x0, offset=0x1B, size=0x5)
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x3000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=bytes.fromhex("1122334455"),
        nonce=0,
        address=Address("0x4b86c4ed99b87f0f396bc0c76885453c343916ed"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=tx_gas_limit,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
