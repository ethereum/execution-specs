"""
Test_static_return_bounds.

Ported from:
state_tests/stStaticCall/static_RETURN_BoundsFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stStaticCall/static_RETURN_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_static_return_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_return_bounds."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(
        amount=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: lll
    # { (RETURN 0 0) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0x0) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (RETURN 0xfffffff 0) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFF, size=0x0) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {  (RETURN 0xffffffff 0)  }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFFF, size=0x0) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (RETURN 0xffffffffffffffff 0) }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFFFFFFFFFFF, size=0x0) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (RETURN 0xfffffffffffffffffffffffffff 0) }
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFF, size=0x0)
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (RETURN 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0)  }  # noqa: E501
    addr_6 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(
            offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            size=0x0,
        )
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (RETURN 0 0xfffffff) }
    addr_7 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0xFFFFFFF) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {  (RETURN 0 0xffffffff)  }
    addr_8 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0xFFFFFFFF) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (RETURN 0 0xffffffffffffffff) }
    addr_9 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0xFFFFFFFFFFFFFFFF) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (RETURN 0 0xfffffffffffffffffffffffffff) }
    addr_10 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (RETURN 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)  }  # noqa: E501
    addr_11 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(
            offset=0x0,
            size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        )
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (RETURN 0xfffffff 0xfffffff) }
    addr_12 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFF, size=0xFFFFFFF) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # {  (RETURN 0xffffffff 0xffffffff)  }
    addr_13 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFFF, size=0xFFFFFFFF) + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (RETURN 0xffffffffffffffff 0xffffffffffffffff) }
    addr_14 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFFFFFFFFFFF, size=0xFFFFFFFFFFFFFFFF)
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (RETURN 0xfffffffffffffffffffffffffff 0xfffffffffffffffffffffffffff) }
    addr_15 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(
            offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFF,
        )
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { (RETURN 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)  }  # noqa: E501
    addr_16 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(
            offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
        )
        + Op.STOP,
        nonce=0,
    )
    # Source: lll
    # { [[1]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) [[2]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) [[3]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000003> 0 0 0 0) [[4]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000004> 0 0 0 0) [[5]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000005> 0 0 0 0) [[6]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[7]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[8]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[9]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[10]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[11]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[12]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[13]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[14]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[15]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[16]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0)}  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x2,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x3,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x4,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x5,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x6,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x7,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x8,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x9,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0xA,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0xB,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0xC,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0xD,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0xE,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0xF,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(
            key=0x10,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=addr_6,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=15000000,
        value=1,
    )

    post = {
        target: Account(
            storage={
                1: 1,
                2: 1,
                3: 1,
                4: 1,
                5: 1,
                6: 1,
                7: 1,
                8: 1,
                9: 1,
                10: 1,
                11: 1,
                12: 1,
                13: 1,
                14: 1,
                15: 1,
                16: 1,
            },
            balance=1,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
