"""
Puts the base 0, exponent 0 and modulus 0 into the MODEXP precompile, saves...

Ported from:
tests/static/state_tests/stPreCompiledContracts2/modexp_0_0_0_22000Filler.json
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
        "tests/static/state_tests/stPreCompiledContracts2/modexp_0_0_0_22000Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        48136,
        90000,
        110000,
        200000,
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_0_0_0_22000(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the base 0, exponent 0 and modulus 0 into the MODEXP..."""
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
    pre[coinbase] = Account(balance=0x201EE, nonce=0)
    pre[sender] = Account(balance=0xDE0B6B3A761FE12, nonce=1)
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
                pc=0x12B,
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
                            0x84,
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
                        address=0x5,
                        value=0x0,
                        args_offset=0x160,
                        args_size=Op.MLOAD(offset=0x140),
                        ret_offset=0x240,
                        ret_size=0x1,
                    ),
                ),
            )
            + Op.MSTORE(offset=0x220, value=0x1)
            + Op.PUSH2[0x220]
            + Op.PUSH1[0x21]
            + Op.POP(
                Op.CALL(
                    gas=0x15,
                    address=0x4,
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=Op.DUP3,
                    ret_offset=0x280,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.POP
            + Op.POP
            + Op.PUSH2[0x280]
            + Op.SHA3(
                offset=Op.ADD(Op.DUP3, 0x20), size=Op.MLOAD(offset=Op.DUP1)
            )
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.SSTORE
            + Op.PUSH2[0x280]
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
        address=Address("0xc305c901078781c232a2a521c2af7980f8385ee9"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "30c8d1da0000000000000000000000000000000000000000000000000000000000000020"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000000000006000000000"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
            "0000000000000000000000000000000000000000"
        ),
        gas_limit=tx_gas_limit,
        nonce=1,
    )

    post = {
        contract: Account(
            storage={
                0: 0xBC36789E7A1E281436464229828F817D6612F7B477D66591FF96A9E064BCC98A,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stPreCompiledContracts2/modexp_0_0_0_22000Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Osaka")
@pytest.mark.parametrize(
    "tx_gas_limit",
    [
        48136,
        90000,
        110000,
        200000,
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_0_0_0_22000_from_osaka(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
) -> None:
    """Puts the base 0, exponent 0 and modulus 0 into the MODEXP..."""
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
    pre[coinbase] = Account(balance=0x201EE, nonce=0)
    pre[sender] = Account(balance=0xDE0B6B3A761FE12, nonce=1)
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
                pc=0x12B,
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
                            0x84,
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
                        address=0x5,
                        value=0x0,
                        args_offset=0x160,
                        args_size=Op.MLOAD(offset=0x140),
                        ret_offset=0x240,
                        ret_size=0x1,
                    ),
                ),
            )
            + Op.MSTORE(offset=0x220, value=0x1)
            + Op.PUSH2[0x220]
            + Op.PUSH1[0x21]
            + Op.POP(
                Op.CALL(
                    gas=0x15,
                    address=0x4,
                    value=0x0,
                    args_offset=Op.DUP5,
                    args_size=Op.DUP3,
                    ret_offset=0x280,
                    ret_size=Op.DUP1,
                ),
            )
            + Op.POP
            + Op.POP
            + Op.PUSH2[0x280]
            + Op.SHA3(
                offset=Op.ADD(Op.DUP3, 0x20), size=Op.MLOAD(offset=Op.DUP1)
            )
            + Op.SWAP1
            + Op.POP
            + Op.PUSH1[0x0]
            + Op.SSTORE
            + Op.PUSH2[0x280]
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
        address=Address("0xc305c901078781c232a2a521c2af7980f8385ee9"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "30c8d1da0000000000000000000000000000000000000000000000000000000000000020"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000000000006000000000"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
            "000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
            "0000000000000000000000000000000000000000"
        ),
        gas_limit=tx_gas_limit,
        nonce=1,
    )

    post = {
        contract: Account(
            storage={
                0: 0xBC36789E7A1E281436464229828F817D6612F7B477D66591FF96A9E064BCC98A,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
