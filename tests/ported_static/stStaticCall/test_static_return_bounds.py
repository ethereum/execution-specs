"""
test_static_return_bounds

Ported from:
state_tests/stStaticCall/static_RETURN_BoundsFiller.json
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
    ["state_tests/stStaticCall/static_RETURN_BoundsFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_return_bounds(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_static_return_bounds"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x50eadfb1030587ab3a993a6ecc073041fc3b45e119daa31a13d78c7e209631a5
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: lll
    # { [[1]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) [[2]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) [[3]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000003> 0 0 0 0) [[4]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000004> 0 0 0 0) [[5]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000005> 0 0 0 0) [[6]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[7]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[8]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[9]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[10]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[11]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[12]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[13]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[14]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[15]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[16]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0)}
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x5efbf04d8e1cc5b6b3719b16b5744a09bacfc18b, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x2, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0xc7aa750fe05c7e38475a49fe98a301024d0c1d54, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x3, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0xff6b6d23be161344e86eb7b174acedd4b1dc6dc7, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x4, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x7bbcf24c83493c4e733cb54079b51873d3211ad2, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x5, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x7a4461ac9f9cd13f40f9514a7c60e23a71c1dff3, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x6, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x7, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x8, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x9, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xa, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xb, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xc, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xd, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xe, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0xf, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.SSTORE(key=0x10, value=Op.STATICCALL(gas=0x7ffffffffffffff, address=0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0xdaaed08adba0dd97804c34dd17b55766d54fc392"),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0 0) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0x0) + Op.STOP,
        nonce=0,
        address=Address("0x5efbf04d8e1cc5b6b3719b16b5744a09bacfc18b"),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0xfffffff 0) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.RETURN(offset=0xfffffff, size=0x0) + Op.STOP,
        nonce=0,
        address=Address("0xc7aa750fe05c7e38475a49fe98a301024d0c1d54"),  # noqa: E501
    )
    # Source: lll
    # {  (RETURN 0xffffffff 0)  }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.RETURN(offset=0xffffffff, size=0x0) + Op.STOP,
        nonce=0,
        address=Address("0xff6b6d23be161344e86eb7b174acedd4b1dc6dc7"),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0xffffffffffffffff 0) }
    addr_0x1000000000000000000000000000000000000004 = pre.deploy_contract(
        code=Op.RETURN(offset=0xffffffffffffffff, size=0x0) + Op.STOP,
        nonce=0,
        address=Address("0x7bbcf24c83493c4e733cb54079b51873d3211ad2"),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0xfffffffffffffffffffffffffff 0) }
    addr_0x1000000000000000000000000000000000000005 = pre.deploy_contract(
        code=Op.RETURN(offset=0xfffffffffffffffffffffffffff, size=0x0) + Op.STOP,
        nonce=0,
        address=Address("0x7a4461ac9f9cd13f40f9514a7c60e23a71c1dff3"),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0)  }
    addr_0x1000000000000000000000000000000000000006 = pre.deploy_contract(
        code=Op.RETURN(offset=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63"),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0 0xfffffff) }
    addr_0x1000000000000000000000000000000000000007 = pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0xfffffff) + Op.STOP,
        nonce=0,
        address=Address("0x7266f1c07958d55ce36de0592604f1a915bdf1c2"),  # noqa: E501
    )
    # Source: lll
    # {  (RETURN 0 0xffffffff)  }
    addr_0x1000000000000000000000000000000000000008 = pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0xffffffff) + Op.STOP,
        nonce=0,
        address=Address("0x2ceb88d6c420e5c65593d9ebed9a25600ab9e113"),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0 0xffffffffffffffff) }
    addr_0x1000000000000000000000000000000000000009 = pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0xffffffffffffffff) + Op.STOP,
        nonce=0,
        address=Address("0x0b09ca4308585f026b8d02be147fea0739ec463a"),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0 0xfffffffffffffffffffffffffff) }
    addr_0x1000000000000000000000000000000000000010 = pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0xfffffffffffffffffffffffffff) + Op.STOP,
        nonce=0,
        address=Address("0xf519de4dcb9aaa53f8f0db9b18c715c928caade8"),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)  }
    addr_0x1000000000000000000000000000000000000011 = pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
        + Op.STOP,
        nonce=0,
        address=Address("0x28463490948d21efc49949b4d394989bf52c57f1"),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0xfffffff 0xfffffff) }
    addr_0x1000000000000000000000000000000000000012 = pre.deploy_contract(
        code=Op.RETURN(offset=0xfffffff, size=0xfffffff) + Op.STOP,
        nonce=0,
        address=Address("0x07084994c5891b1467d74bedb0477da4909e4c0e"),  # noqa: E501
    )
    # Source: lll
    # {  (RETURN 0xffffffff 0xffffffff)  }
    addr_0x1000000000000000000000000000000000000013 = pre.deploy_contract(
        code=Op.RETURN(offset=0xffffffff, size=0xffffffff) + Op.STOP,
        nonce=0,
        address=Address("0xad7754a8a56cc5ad4e319fa94194e435628dee67"),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0xffffffffffffffff 0xffffffffffffffff) }
    addr_0x1000000000000000000000000000000000000014 = pre.deploy_contract(
        code=Op.RETURN(offset=0xffffffffffffffff, size=0xffffffffffffffff) + Op.STOP,
        nonce=0,
        address=Address("0x416408c1d7fda274ddeb45ffe4817068808121ca"),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0xfffffffffffffffffffffffffff 0xfffffffffffffffffffffffffff) }
    addr_0x1000000000000000000000000000000000000015 = pre.deploy_contract(
        code=Op.RETURN(offset=0xfffffffffffffffffffffffffff, size=0xfffffffffffffffffffffffffff)
        + Op.STOP,
        nonce=0,
        address=Address("0x2548bda95a3831abcd613f4d24e4634615a71cca"),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)  }
    addr_0x1000000000000000000000000000000000000016 = pre.deploy_contract(
        code=Op.RETURN(offset=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff, size=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)
        + Op.STOP,
        nonce=0,
        address=Address("0x76006c948f3a0529479c6d18a6f95908426e8092"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=15000000,
        value=1,
        nonce=0,
        gas_price=10,
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
