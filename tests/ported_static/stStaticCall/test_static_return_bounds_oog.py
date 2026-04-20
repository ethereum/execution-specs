"""
Test_static_return_bounds_oog.

Ported from:
state_tests/stStaticCall/static_RETURN_BoundsOOGFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
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
    ["state_tests/stStaticCall/static_RETURN_BoundsOOGFiller.json"],
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
def test_static_return_bounds_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_return_bounds_oog."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x50EADFB1030587AB3A993A6ECC073041FC3B45E119DAA31A13D78C7E209631A5
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
    )

    # Source: lll
    # { [[1]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) [[2]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) [[3]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000003> 0 0 0 0) [[4]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000004> 0 0 0 0) [[5]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000005> 0 0 0 0) [[6]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[7]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[8]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[9]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[10]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[11]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[12]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[13]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[14]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[15]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[16]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) (IF (EQ (CALLDATALOAD 0) 0) (KECCAK256 0x00 0x2fffff) (GAS) ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.STATICCALL(
                gas=0x7FFFFFFFFFFFFFF,
                address=0x5EFBF04D8E1CC5B6B3719B16B5744A09BACFC18B,
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
                address=0xC7AA750FE05C7E38475A49FE98A301024D0C1D54,
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
                address=0xFF6B6D23BE161344E86EB7B174ACEDD4B1DC6DC7,
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
                address=0x7BBCF24C83493C4E733CB54079B51873D3211AD2,
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
                address=0x7A4461AC9F9CD13F40F9514A7C60E23A71C1DFF3,
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
                address=0x4912BC7B66A3BF27ADFA54AB049E90E8C9C4DC63,
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
                address=0x4912BC7B66A3BF27ADFA54AB049E90E8C9C4DC63,
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
                address=0x4912BC7B66A3BF27ADFA54AB049E90E8C9C4DC63,
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
                address=0x4912BC7B66A3BF27ADFA54AB049E90E8C9C4DC63,
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
                address=0x4912BC7B66A3BF27ADFA54AB049E90E8C9C4DC63,
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
                address=0x4912BC7B66A3BF27ADFA54AB049E90E8C9C4DC63,
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
                address=0x4912BC7B66A3BF27ADFA54AB049E90E8C9C4DC63,
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
                address=0x4912BC7B66A3BF27ADFA54AB049E90E8C9C4DC63,
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
                address=0x4912BC7B66A3BF27ADFA54AB049E90E8C9C4DC63,
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
                address=0x4912BC7B66A3BF27ADFA54AB049E90E8C9C4DC63,
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
                address=0x4912BC7B66A3BF27ADFA54AB049E90E8C9C4DC63,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.JUMPI(pc=0x2AF, condition=Op.EQ(Op.CALLDATALOAD(offset=0x0), 0x0))
        + Op.GAS
        + Op.JUMP(pc=0x2B7)
        + Op.JUMPDEST
        + Op.SHA3(offset=0x0, size=0x2FFFFF)
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
        address=Address(0x57545D218764BC417FDCBBC2C1F43B2A62105CE1),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0 0) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0x0) + Op.STOP,
        nonce=0,
        address=Address(0x5EFBF04D8E1CC5B6B3719B16B5744A09BACFC18B),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0xfffffff 0) }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFF, size=0x0) + Op.STOP,
        nonce=0,
        address=Address(0xC7AA750FE05C7E38475A49FE98A301024D0C1D54),  # noqa: E501
    )
    # Source: lll
    # {  (RETURN 0xffffffff 0)  }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFFF, size=0x0) + Op.STOP,
        nonce=0,
        address=Address(0xFF6B6D23BE161344E86EB7B174ACEDD4B1DC6DC7),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0xffffffffffffffff 0) }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFFFFFFFFFFF, size=0x0) + Op.STOP,
        nonce=0,
        address=Address(0x7BBCF24C83493C4E733CB54079B51873D3211AD2),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0xfffffffffffffffffffffffffff 0) }
    addr_5 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFF, size=0x0)
        + Op.STOP,
        nonce=0,
        address=Address(0x7A4461AC9F9CD13F40F9514A7C60E23A71C1DFF3),  # noqa: E501
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
        address=Address(0x4912BC7B66A3BF27ADFA54AB049E90E8C9C4DC63),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0 0xfffffff) }
    addr_7 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0xFFFFFFF) + Op.STOP,
        nonce=0,
        address=Address(0x7266F1C07958D55CE36DE0592604F1A915BDF1C2),  # noqa: E501
    )
    # Source: lll
    # {  (RETURN 0 0xffffffff)  }
    addr_8 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0xFFFFFFFF) + Op.STOP,
        nonce=0,
        address=Address(0x2CEB88D6C420E5C65593D9EBED9A25600AB9E113),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0 0xffffffffffffffff) }
    addr_9 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0xFFFFFFFFFFFFFFFF) + Op.STOP,
        nonce=0,
        address=Address(0x0B09CA4308585F026B8D02BE147FEA0739EC463A),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0 0xfffffffffffffffffffffffffff) }
    addr_10 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.STOP,
        nonce=0,
        address=Address(0xF519DE4DCB9AAA53F8F0DB9B18C715C928CAADE8),  # noqa: E501
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
        address=Address(0x28463490948D21EFC49949B4D394989BF52C57F1),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0xfffffff 0xfffffff) }
    addr_12 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFF, size=0xFFFFFFF) + Op.STOP,
        nonce=0,
        address=Address(0x07084994C5891B1467D74BEDB0477DA4909E4C0E),  # noqa: E501
    )
    # Source: lll
    # {  (RETURN 0xffffffff 0xffffffff)  }
    addr_13 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFFF, size=0xFFFFFFFF) + Op.STOP,
        nonce=0,
        address=Address(0xAD7754A8A56CC5AD4E319FA94194E435628DEE67),  # noqa: E501
    )
    # Source: lll
    # { (RETURN 0xffffffffffffffff 0xffffffffffffffff) }
    addr_14 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFFFFFFFFFFFFFFFF, size=0xFFFFFFFFFFFFFFFF)
        + Op.STOP,
        nonce=0,
        address=Address(0x416408C1D7FDA274DDEB45FFE4817068808121CA),  # noqa: E501
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
        address=Address(0x2548BDA95A3831ABCD613F4D24E4634615A71CCA),  # noqa: E501
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
        address=Address(0x76006C948F3A0529479C6D18A6F95908426E8092),  # noqa: E501
    )
    pre[sender] = Account(
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 1, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {
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
            },
        },
        {
            "indexes": {"data": 0, "gas": -1, "value": -1},
            "network": [">=Cancun"],
            "result": {target: Account(storage={}, balance=0)},
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("00"),
        Address(0x1),
    ]
    tx_gas = [15000000]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
