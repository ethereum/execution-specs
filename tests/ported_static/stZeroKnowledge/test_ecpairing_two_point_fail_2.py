"""
Puts the given data into the ECPAIRING precompile.

Ported from:
tests/static/state_tests/stZeroKnowledge/ecpairing_two_point_fail_2Filler.json
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
        "tests/static/state_tests/stZeroKnowledge/ecpairing_two_point_fail_2Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, expected_post",
    [
        (
            333800,
            {
                Address("0xc305c901078781c232a2a521c2af7980f8385ee9"): Account(
                    storage={
                        0: 0x290DECD9548B62A8D60345A988386FC84BA6BC95484008F6362F93160EF3E563  # noqa: E501
                    }
                )
            },
        ),
        (
            90000,
            {
                Address("0xc305c901078781c232a2a521c2af7980f8385ee9"): Account(
                    storage={
                        0: 0xB10E2D527612073B26EECDFD717E6A320CF44B4AFAC2B0732D9FCBE2B7FA0CF6  # noqa: E501
                    }
                )
            },
        ),
        (
            110000,
            {
                Address("0xc305c901078781c232a2a521c2af7980f8385ee9"): Account(
                    storage={
                        0: 0xB10E2D527612073B26EECDFD717E6A320CF44B4AFAC2B0732D9FCBE2B7FA0CF6  # noqa: E501
                    }
                )
            },
        ),
        (
            140000,
            {
                Address("0xc305c901078781c232a2a521c2af7980f8385ee9"): Account(
                    storage={
                        0: 0xB10E2D527612073B26EECDFD717E6A320CF44B4AFAC2B0732D9FCBE2B7FA0CF6  # noqa: E501
                    }
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
def test_ecpairing_two_point_fail_2(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Puts the given data into the ECPAIRING precompile."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    sender = EOA(
        key=0x044852B2A670ADE5407E78FB2863C51DE9FCB96542A07186FE3AEDA6BB8A116D
    )
    callee = Address("0x0000000000000000000000000000000000000001")
    callee_1 = Address("0x0000000000000000000000000000000000000002")
    callee_2 = Address("0x0000000000000000000000000000000000000003")
    callee_3 = Address("0x0000000000000000000000000000000000000004")
    callee_4 = Address("0x0000000000000000000000000000000000000005")
    callee_5 = Address("0x0000000000000000000000000000000000000006")
    callee_6 = Address("0x0000000000000000000000000000000000000007")
    callee_7 = Address("0x0000000000000000000000000000000000000008")
    callee_8 = Address("0x10a1c1cb95c92ec31d3f22c66eef1d9f3f258c6b")
    callee_9 = Address("0x13cbb8d99c6c4e0f2728c7d72606e78a29c4e224")
    callee_10 = Address("0x24143873e0e0815fdcbcffdbe09c979cbf9ad013")
    callee_11 = Address("0x598443f1880ef585b21f1d7585bd0577402861e5")
    callee_12 = Address("0x77db2bebba79db42a978f896968f4afce746ea1f")
    callee_13 = Address("0x7d577a597b2742b498cb5cf0c26cdcd726d39e6e")
    callee_14 = Address("0x90f0b1ebbba1c1936aff7aaf20a7878ff9e04b6c")
    callee_15 = Address("0xdceceaf3fc5c0a63d195d69b1a90011b7b19650d")
    callee_16 = Address("0xe0fc04fa2d34a66b779fd5cee748268032a146c0")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[callee] = Account(balance=1, nonce=0)
    pre[callee_1] = Account(balance=1, nonce=0)
    pre[callee_2] = Account(balance=1, nonce=0)
    pre[callee_3] = Account(balance=1, nonce=0)
    pre[callee_4] = Account(balance=1, nonce=0)
    pre[callee_5] = Account(balance=1, nonce=0)
    pre[callee_6] = Account(balance=1, nonce=0)
    pre[callee_7] = Account(balance=1, nonce=0)
    pre[callee_8] = Account(balance=0xDE0B6B3A7640000, nonce=0)
    pre[callee_9] = Account(balance=0xDE0B6B3A7640000, nonce=0)
    pre[callee_10] = Account(balance=0xDE0B6B3A7640000, nonce=0)
    pre[coinbase] = Account(balance=0x39A4D9, nonce=0)
    pre[callee_11] = Account(balance=0xDE0B6B3A7640000, nonce=0)
    pre[callee_12] = Account(balance=0xDE0B6B3A7640000, nonce=0)
    pre[callee_13] = Account(balance=0xDE0B6B3A7640000, nonce=0)
    pre[sender] = Account(balance=0xDE0B6B3A72A5B27, nonce=16)
    pre[callee_14] = Account(balance=0xDE0B6B3A7640000, nonce=0)
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1C, value=Op.CALLDATALOAD(offset=0x0))
            + Op.MSTORE(
                offset=0x20,
                value=0x10000000000000000000000000000000000000000,
            )
            + Op.MSTORE(offset=0x40, value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
            + Op.MSTORE(
                offset=0x60,
                value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000001,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x80,
                value=0x2540BE3FFFFFFFFFFFFFFFFFFFFFFFFFDABF41C00,
            )
            + Op.MSTORE(
                offset=0xA0,
                value=0xFFFFFFFFFFFFFFFFFFFFFFFDABF41C00000000000000000000000002540BE400,  # noqa: E501
            )
            + Op.JUMPI(
                pc=0x12C,
                condition=Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x0), 0x30C8D1DA)),
            )
            + Op.JUMPI(
                pc=Op.PC,
                condition=Op.ISZERO(
                    Op.ISZERO(
                        Op.GT(
                            Op.CALLDATALOAD(
                                offset=Op.ADD(
                                    0x4, Op.CALLDATALOAD(offset=0x4)
                                ),
                            ),
                            0x780,
                        ),
                    ),
                ),
            )
            + Op.CALLDATACOPY(
                dest_offset=0x140,
                offset=Op.ADD(0x4, Op.CALLDATALOAD(offset=0x4)),
                size=Op.ADD(
                    0x20,
                    Op.CALLDATALOAD(
                        offset=Op.ADD(0x4, Op.CALLDATALOAD(offset=0x4)),
                    ),
                ),
            )
            + Op.JUMPI(
                pc=Op.PC,
                condition=Op.ISZERO(
                    Op.CALL(
                        gas=0x5F5E0FF,
                        address=0x8,
                        value=0x0,
                        args_offset=0x160,
                        args_size=Op.MLOAD(offset=0x140),
                        ret_offset=0x920,
                        ret_size=0x20,
                    ),
                ),
            )
            + Op.MSTORE(offset=0x900, value=0x20)
            + Op.PUSH2[0x900]
            + Op.PUSH1[0x40]
            + Op.POP(
                Op.CALL(
                    gas=0x18,
                    address=0x4,
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=Op.DUP3,
                    ret_offset=0x960,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.POP
            + Op.POP
            + Op.PUSH2[0x960]
            + Op.SHA3(
                offset=Op.ADD(Op.DUP3, 0x20), size=Op.MLOAD(offset=Op.DUP1)
            )
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.SSTORE
            + Op.PUSH2[0x960]
            + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x20), value=0x20)
            + Op.ADD(Op.MLOAD(offset=Op.DUP2), 0x40)
            + Op.SUB(Op.ADD(Op.DUP3, 0x1F), Op.MOD(Op.SUB(Op.DUP3, 0x1), 0x20))
            + Op.SWAP1
            + Op.POP
            + Op.SUB(Op.DUP3, 0x20)
            + Op.RETURN
            + Op.POP
            + Op.STOP
            + Op.JUMPDEST
        ),
        storage={
            0x0: 0xB10E2D527612073B26EECDFD717E6A320CF44B4AFAC2B0732D9FCBE2B7FA0CF6,  # noqa: E501
        },
        address=Address("0xc305c901078781c232a2a521c2af7980f8385ee9"),  # noqa: E501
    )
    pre[callee_15] = Account(balance=0xDE0B6B3A7640000, nonce=0)
    pre[callee_16] = Account(balance=0xDE0B6B3A7640000, nonce=0)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "30c8d1da0000000000000000000000000000000000000000000000000000000000000020"  # noqa: E501
            "0000000000000000000000000000000000000000000000000000000000000180105456a3"  # noqa: E501
            "33e6d636854f987ea7bb713dfd0ae8371a72aea313ae0c32c0bf10160cf031d41b41557f"  # noqa: E501
            "3e7e3ba0c51bebe5da8e6ecd855ec50fc87efcdeac168bcc0476be093a6d2b4bbf907172"  # noqa: E501
            "049874af11e1b6267606e00804d3ff0037ec57fd3010c68cb50161b7d1d96bb71edfec98"  # noqa: E501
            "80171954e56871abf3d93cc94d745fa114c059d74e5b6c4ec14ae5864ebe23a71781d86c"  # noqa: E501
            "29fb8fb6cce94f70d3de7a2101b33461f39d9e887dbb100f170a2345dde3c07e256d1dfa"  # noqa: E501
            "2b657ba5cd03042700000000000000000000000000000000000000000000000000000000"  # noqa: E501
            "000000010000000000000000000000000000000000000000000000000000000000000002"  # noqa: E501
            "105384b6dd6c48634b9fe89cb3e19667c1fe6736c69df070d674c95a42b3b8242c0d8e67"  # noqa: E501
            "f0f2c14c43734b430d8be4265af8c4f7a67deb0b029fd2dff99cc6b9015eaec465d92258"  # noqa: E501
            "0c7de5d4a5c26de75eaf2af6841b7412ef2eebd1e051076f1b4c21849e48de12d1bae2ba"  # noqa: E501
            "d3299717aa8664ade430e19dec72a6e10a39b0ab"
        ),
        gas_limit=tx_gas_limit,
        nonce=16,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
