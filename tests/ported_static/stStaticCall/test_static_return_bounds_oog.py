"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_RETURN_BoundsOOGFiller.json
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
        "tests/static/state_tests/stStaticCall/static_RETURN_BoundsOOGFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        ("00", {}),
        (
            "0000000000000000000000000000000000000001",
            {
                Address("0x57545d218764bc417fdcbbc2c1f43b2a62105ce1"): Account(
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
                    }
                )
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_return_bounds_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x50EADFB1030587AB3A993A6ECC073041FC3B45E119DAA31A13D78C7E209631A5
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre.deploy_contract(
        code=Op.RETURN(offset=0xFFFFFFF, size=0xFFFFFFF) + Op.STOP,
        nonce=0,
        address=Address("0x07084994c5891b1467d74bedb0477da4909e4c0e"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0xFFFFFFFFFFFFFFFF) + Op.STOP,
        nonce=0,
        address=Address("0x0b09ca4308585f026b8d02be147fea0739ec463a"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.RETURN(
                offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFF,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x2548bda95a3831abcd613f4d24e4634615a71cca"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.RETURN(
                offset=0x0,
                size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x28463490948d21efc49949b4d394989bf52c57f1"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0xFFFFFFFF) + Op.STOP,
        nonce=0,
        address=Address("0x2ceb88d6c420e5c65593d9ebed9a25600ab9e113"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.RETURN(offset=0xFFFFFFFFFFFFFFFF, size=0xFFFFFFFFFFFFFFFF)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x416408c1d7fda274ddeb45ffe4817068808121ca"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.RETURN(
                offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x4912bc7b66a3bf27adfa54ab049e90e8c9c4dc63"),  # noqa: E501
    )
    # Source: LLL
    # { [[1]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) [[2]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) [[3]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000003> 0 0 0 0) [[4]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000004> 0 0 0 0) [[5]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000005> 0 0 0 0) [[6]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[7]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[8]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[9]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[10]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[11]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[12]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[13]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[14]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[15]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) [[16]] (STATICCALL 0x7ffffffffffffff <contract:0x1000000000000000000000000000000000000006> 0 0 0 0) (IF (EQ (CALLDATALOAD 0) 0) (KECCAK256 0x00 0x2fffff) (GAS) ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
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
            + Op.JUMPI(
                pc=0x2AF, condition=Op.EQ(Op.CALLDATALOAD(offset=0x0), 0x0)
            )
            + Op.GAS
            + Op.JUMP(pc=0x2B7)
            + Op.JUMPDEST
            + Op.SHA3(offset=0x0, size=0x2FFFFF)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x57545d218764bc417fdcbbc2c1f43b2a62105ce1"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0x0) + Op.STOP,
        nonce=0,
        address=Address("0x5efbf04d8e1cc5b6b3719b16b5744a09bacfc18b"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0xFFFFFFF) + Op.STOP,
        nonce=0,
        address=Address("0x7266f1c07958d55ce36de0592604f1a915bdf1c2"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.RETURN(
                offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
                size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x76006c948f3a0529479c6d18a6f95908426e8092"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.RETURN(offset=0xFFFFFFFFFFFFFFFFFFFFFFFFFFF, size=0x0) + Op.STOP
        ),
        nonce=0,
        address=Address("0x7a4461ac9f9cd13f40f9514a7c60e23a71c1dff3"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.RETURN(offset=0xFFFFFFFFFFFFFFFF, size=0x0) + Op.STOP,
        nonce=0,
        address=Address("0x7bbcf24c83493c4e733cb54079b51873d3211ad2"),  # noqa: E501
    )
    pre[sender] = Account(
        balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.RETURN(offset=0xFFFFFFFF, size=0xFFFFFFFF) + Op.STOP,
        nonce=0,
        address=Address("0xad7754a8a56cc5ad4e319fa94194e435628dee67"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.RETURN(offset=0xFFFFFFF, size=0x0) + Op.STOP,
        nonce=0,
        address=Address("0xc7aa750fe05c7e38475a49fe98a301024d0c1d54"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.RETURN(offset=0x0, size=0xFFFFFFFFFFFFFFFFFFFFFFFFFFF) + Op.STOP
        ),
        nonce=0,
        address=Address("0xf519de4dcb9aaa53f8f0db9b18c715c928caade8"),  # noqa: E501
    )
    pre.deploy_contract(
        code=Op.RETURN(offset=0xFFFFFFFF, size=0x0) + Op.STOP,
        nonce=0,
        address=Address("0xff6b6d23be161344e86eb7b174acedd4b1dc6dc7"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=15000000,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
