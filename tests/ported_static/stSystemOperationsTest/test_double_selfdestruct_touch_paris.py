"""
A single contract can execute SELFDESTRUCT multiple times using by being...

multiple times. The second and later SELFDESTRUCTs have little effect but can
touch some new beneficiary addresses.

Ported from:
tests/static/state_tests/stSystemOperationsTest
doubleSelfdestructTouch_ParisFiller.yml
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
        "tests/static/state_tests/stSystemOperationsTest/doubleSelfdestructTouch_ParisFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_value, expected_post",
    [
        (
            0,
            {
                Address("0x29e4504a3d2a0e0ae0ebbbefedd4570639b3ebee"): Account(
                    storage={
                        0: 2,
                        1: 0x68FA59E127B7526718EB0A4E113DF5793628CB91,
                        2: 0x76FAE819612A29489A1A43208613D8F8557B8898,
                    }
                )
            },
        ),
        (
            1,
            {
                Address("0x29e4504a3d2a0e0ae0ebbbefedd4570639b3ebee"): Account(
                    storage={
                        0: 2,
                        1: 0x68FA59E127B7526718EB0A4E113DF5793628CB91,
                        2: 0x76FAE819612A29489A1A43208613D8F8557B8898,
                    }
                )
            },
        ),
        (
            2,
            {
                Address("0x29e4504a3d2a0e0ae0ebbbefedd4570639b3ebee"): Account(
                    storage={
                        0: 2,
                        1: 0x68FA59E127B7526718EB0A4E113DF5793628CB91,
                        2: 0x76FAE819612A29489A1A43208613D8F8557B8898,
                    }
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2"],
)
@pytest.mark.pre_alloc_mutable
def test_double_selfdestruct_touch_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_value: int,
    expected_post: dict,
) -> None:
    """A single contract can execute SELFDESTRUCT multiple times using..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE92C121432830128CA66D3D8C4E6D8D96CC4BEFA7C612D28415082EB3C8339C5
    )
    callee_1 = Address("0x68fa59e127b7526718eb0a4e113df5793628cb91")
    callee_2 = Address("0x76fae819612a29489a1a43208613d8f8557b8898")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=999,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre.deploy_contract(
        code=(
            Op.ADD(Op.SLOAD(key=0x0), 0x1)
            + Op.SSTORE(key=0x0, value=Op.DUP1)
            + Op.SELFDESTRUCT(address=Op.SLOAD)
        ),
        storage={
            0x0: 0x0,
            0x1: 0x68FA59E127B7526718EB0A4E113DF5793628CB91,
            0x2: 0x76FAE819612A29489A1A43208613D8F8557B8898,
        },
        nonce=0,
        address=Address("0x29e4504a3d2a0e0ae0ebbbefedd4570639b3ebee"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5F5E102)
    pre[callee_1] = Account(balance=10, nonce=0)
    pre[callee_2] = Account(balance=10, nonce=0)
    # Source: Yul
    # {
    #   let v0 := callvalue()
    #   let v1 := shr(1, v0)
    #   let r1 := call(70000, <contract:0x000000000000000000000000000000000000dead>, v1, 0, 0, 0, 0)  # noqa: E501
    #   let v2 := sub(v0, v1)
    #   let r2 := call(70000, <contract:0x000000000000000000000000000000000000dead>, v2, 0, 0, 0, 0)  # noqa: E501
    # }
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.DUP1
            + Op.DUP1
            + Op.DUP1
            + Op.CALLVALUE
            + Op.SHR(0x1, Op.DUP1)
            + Op.SWAP1
            + Op.POP(
                Op.CALL(
                    gas=0x11170,
                    address=0x29E4504A3D2A0E0AE0EBBBEFEDD4570639B3EBEE,
                    value=Op.DUP6,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=Op.DUP3,
                ),
            )
            + Op.SUB
            + Op.PUSH20[0x29E4504A3D2A0E0AE0EBBBEFEDD4570639B3EBEE]
            + Op.PUSH3[0x11170]
            + Op.CALL
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x8ec7465877d3957084dc907c0f6d8f2911a17a52"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=10000000,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
