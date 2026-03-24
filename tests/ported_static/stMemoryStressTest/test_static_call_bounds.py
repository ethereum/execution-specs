"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemoryStressTest/static_CALL_BoundsFiller.json
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
        "tests/static/state_tests/stMemoryStressTest/static_CALL_BoundsFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, expected_post",
    [
        (150000, {}),
        (16777216, {}),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_static_call_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xEF111BBDAB3A1622936AFDFC9BBEC4B5BC05B4FA4B1EF0CE2A55CEF552F7650E
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
    )
    # Source: LLL
    # {  (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xfffffff 0 0xfffffff) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0xffffffff 0 0xffffffff) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xfffffff 0 0xfffffff 0) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffff 0 0xffffffff 0) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffff 0 0xffffffffffffffff 0) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffff 0) (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0)  }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.STATICCALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                    args_offset=0x0,
                    args_size=0xFFFFFFF,
                    ret_offset=0x0,
                    ret_size=0xFFFFFFF,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                    args_offset=0x0,
                    args_size=0xFFFFFFFF,
                    ret_offset=0x0,
                    ret_size=0xFFFFFFFF,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                    args_offset=0xFFFFFFF,
                    args_size=0x0,
                    ret_offset=0xFFFFFFF,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                    args_offset=0xFFFFFFFF,
                    args_size=0x0,
                    ret_offset=0xFFFFFFFF,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                    args_offset=0xFFFFFFFFFFFFFFFF,
                    args_size=0x0,
                    ret_offset=0xFFFFFFFFFFFFFFFF,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.STATICCALL(
                    gas=0x7FFFFFFFFFFFFFF,
                    address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                    args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    args_size=0x0,
                    ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                    ret_size=0x0,
                ),
            )
            + Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=0xCC704D60C46B9C08AAB4D15281184441AC7ED35C,
                args_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                args_size=0x0,
                ret_offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x7f91c742985ac295da40f3771a1be98f99f6a357"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.ADD(0x1, Op.SLOAD(key=0x0)))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xcc704d60c46b9c08aab4d15281184441ac7ed35c"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=tx_gas_limit,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
