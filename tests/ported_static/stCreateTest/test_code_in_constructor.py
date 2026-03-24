"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stCreateTest/CodeInConstructorFiller.yml
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
    ["tests/static/state_tests/stCreateTest/CodeInConstructorFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "83c7d7580000000000000000000000000000000000000000000000000000000000000001",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000000da7a"): Account(
                    storage={
                        0: 8,
                        1: 10,
                        2: 0x8AF6A7AF30D840BA137E8F3F34D54CFB8BEBA6E2,
                        3: 262,
                        5: 0x610100610100610100395861026052600060006020610260600061DA7A62FFFF,  # noqa: E501
                        7: 184,
                    }
                )
            },
        ),
        (
            "83c7d7580000000000000000000000000000000000000000000000000000000000000002",  # noqa: E501
            {
                Address("0x000000000000000000000000000000000000da7a"): Account(
                    storage={
                        0: 8,
                        1: 10,
                        2: 0x33C409678A4289F0184C95C627BA09DA2DAEAA46,
                        3: 262,
                        5: 0x610100610100610100395861026052600060006020610260600061DA7A62FFFF,  # noqa: E501
                        7: 184,
                    }
                )
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_code_in_constructor(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0xba5e0000ba5e0000ba5e0000ba5e0000ba5e0000")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4294967296,
    )

    # Source: LLL
    # {
    #     (def 'counterLoc 0)
    #     (def 'counterVal @@counterLoc)
    #     [[counterVal]] $0
    #     [[counterLoc]] (+ counterVal 1)
    # }
    pre.deploy_contract(
        code=(
            Op.SSTORE(key=Op.SLOAD(key=0x0), value=Op.CALLDATALOAD(offset=0x0))
            + Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
            + Op.STOP
        ),
        storage={0x0: 0x1},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x000000000000000000000000000000000000da7a"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
    # {
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'constructorCode   0x000)
    #   (def 'contractCode      0x100)
    #   (def 'contractLength    0x200)
    #   (def 'constructorLength 0x220)
    #   (def 'addr              0x240)
    #   (def 'dataLoc           0x260)
    #   ; The type of CREATE to use
    #   (def 'createType        $ 4)
    #   ; Other constants
    #   (def 'NOP 0)   ; No OPeration
    #   ; Send data to 0x00da7a
    #   (def 'sendData (data) {
    #      [dataLoc] data
    #      (call 0xFFFFFF 0xda7a 0 dataLoc 0x20 0 0)
    #   })
    #   ; Buffer length (use for constructor and contract)
    #   (def 'bufLength     0x100)
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Create the contract and a constructor to pass to CREATE[2]
    #   ;
    #   ;
    #   [contractLength]
    #     (lll
    #       (sstore 0 0xFF)
    #       contractCode
    #     )
    #   [constructorLength]
    # ... (36 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0x6]
            + Op.CODECOPY(
                dest_offset=0x100, offset=Op.PUSH2[0x4C], size=Op.DUP1
            )
            + Op.PUSH2[0x200]
            + Op.MSTORE
            + Op.PUSH1[0xDB]
            + Op.CODECOPY(dest_offset=0x0, offset=Op.PUSH2[0x52], size=Op.DUP1)
            + Op.PUSH2[0x220]
            + Op.MSTORE
            + Op.JUMPI(
                pc=0x37, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x1)
            )
            + Op.CREATE2(
                value=0x0,
                offset=0x0,
                size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
                salt=0x5A17,
            )
            + Op.JUMP(pc=0x45)
            + Op.JUMPDEST
            + Op.CREATE(
                value=0x0,
                offset=0x0,
                size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
            )
            + Op.JUMPDEST
            + Op.PUSH2[0x240]
            + Op.MSTORE
            + Op.STOP
            + Op.INVALID
            + Op.SSTORE(key=0x0, value=0xFF)
            + Op.STOP
            + Op.CODECOPY(dest_offset=0x100, offset=0x100, size=0x100)
            + Op.MSTORE(offset=0x260, value=Op.PC)
            + Op.POP(
                Op.CALL(
                    gas=0xFFFFFF,
                    address=0xDA7A,
                    value=0x0,
                    args_offset=0x260,
                    args_size=0x20,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x260, value=Op.ADDRESS)
            + Op.POP(
                Op.CALL(
                    gas=0xFFFFFF,
                    address=0xDA7A,
                    value=0x0,
                    args_offset=0x260,
                    args_size=0x20,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x260, value=Op.CODESIZE)
            + Op.POP(
                Op.CALL(
                    gas=0xFFFFFF,
                    address=0xDA7A,
                    value=0x0,
                    args_offset=0x260,
                    args_size=0x20,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x260, value=Op.EXTCODESIZE(address=Op.ADDRESS))
            + Op.POP(
                Op.CALL(
                    gas=0xFFFFFF,
                    address=0xDA7A,
                    value=0x0,
                    args_offset=0x260,
                    args_size=0x20,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.CODECOPY(dest_offset=0x100, offset=0x0, size=0x20)
            + Op.MSTORE(offset=0x260, value=Op.MLOAD(offset=0x100))
            + Op.POP(
                Op.CALL(
                    gas=0xFFFFFF,
                    address=0xDA7A,
                    value=0x0,
                    args_offset=0x260,
                    args_size=0x20,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.EXTCODECOPY(
                address=Op.ADDRESS,
                dest_offset=0x100,
                offset=0x0,
                size=0x20,
            )
            + Op.MSTORE(offset=0x260, value=Op.MLOAD(offset=0x100))
            + Op.POP(
                Op.CALL(
                    gas=0xFFFFFF,
                    address=0xDA7A,
                    value=0x0,
                    args_offset=0x260,
                    args_size=0x20,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x260, value=Op.PC)
            + Op.POP(
                Op.CALL(
                    gas=0xFFFFFF,
                    address=0xDA7A,
                    value=0x0,
                    args_offset=0x260,
                    args_size=0x20,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.RETURN(offset=0x100, size=Op.SUB(Op.CODESIZE, 0x100))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=9437184,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
