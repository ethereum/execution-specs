"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stCreateTest/CreateCollisionResultsFiller.yml
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
    ["tests/static/state_tests/stCreateTest/CreateCollisionResultsFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "01",
            {
                Address("0x40f1299359ea754ac29eb2662a1900752bf8275f"): Account(
                    storage={0: 29}
                ),
                Address("0x8af6a7af30d840ba137e8f3f34d54cfb8beba6e2"): Account(
                    storage={0: 29}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        32: 89,
                        33: 143,
                        34: 200,
                        48: 6,
                        49: 0x601D600055000000000000000000000000000000000000000000000000000000,  # noqa: E501
                        50: 6,
                        51: 0x601D600055000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    }
                ),
            },
        ),
        (
            "02",
            {
                Address("0x40f1299359ea754ac29eb2662a1900752bf8275f"): Account(
                    storage={0: 29}
                ),
                Address("0x8af6a7af30d840ba137e8f3f34d54cfb8beba6e2"): Account(
                    storage={0: 29}
                ),
                Address("0xcccccccccccccccccccccccccccccccccccccccc"): Account(
                    storage={
                        32: 89,
                        33: 143,
                        34: 200,
                        48: 6,
                        49: 0x601D600055000000000000000000000000000000000000000000000000000000,  # noqa: E501
                        50: 6,
                        51: 0x601D600055000000000000000000000000000000000000000000000000000000,  # noqa: E501
                    }
                ),
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_create_collision_results(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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
    #   [[0]] 0x001D
    # }
    pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1D) + Op.STOP,
        storage={0x0: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x40f1299359ea754ac29eb2662a1900752bf8275f"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   [[0]] 0x001D
    # }
    pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x1D) + Op.STOP,
        storage={0x0: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x8af6a7af30d840ba137e8f3f34d54cfb8beba6e2"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: LLL
    # {
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'creation          0x100)
    #   (def 'contractCode      0x200)
    #   (def 'constructorCode   0x300)
    #   (def 'contractLength    0x520)
    #   (def 'constructorLength 0x540)
    #   (def 'addr1             0x600)
    #   (def 'callRet           0x640)
    #   (def 'buffer            0x660)
    #   ; Addresses of the contracts (to check what code is there)
    #   (def 'OrigAddr1 0x8af6a7af30d840ba137e8f3f34d54cfb8beba6e2)
    #   (def 'OrigAddr2 0x40f1299359ea754ac29eb2662a1900752bf8275f)
    #   ; Other constants
    #   (def 'NOP 0)   ; No OPeration
    #   ; Understand the input.
    #   [creation]       (shr $ 0 248)
    #   ; Code for created contract
    #   (def 'contractMacro
    #       (lll
    #          (sstore 0 0xFF)
    #          contractCode
    #       )
    #   )
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Create the contract and a constructor to pass to CREATE[2]
    #   ;
    #   [constructorLength]
    #     (lll
    # ... (43 more lines)
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x100,
                value=Op.DIV(Op.CALLDATALOAD(offset=0x0), Op.EXP(0x2, 0xF8)),
            )
            + Op.PUSH1[0x15]
            + Op.CODECOPY(dest_offset=0x300, offset=0x158, size=Op.DUP1)
            + Op.PUSH2[0x540]
            + Op.MSTORE
            + Op.PUSH1[0x6]
            + Op.CODECOPY(dest_offset=0x200, offset=0x16D, size=Op.DUP1)
            + Op.PUSH2[0x520]
            + Op.MSTORE
            + Op.JUMPI(
                pc=Op.PUSH2[0x49],
                condition=Op.EQ(Op.MLOAD(offset=0x100), 0x1),
            )
            + Op.MSTORE(
                offset=0x600,
                value=Op.CREATE2(
                    value=0x0,
                    offset=0x300,
                    size=Op.MLOAD(offset=0x540),
                    salt=0x5A17,
                ),
            )
            + Op.JUMP(pc=Op.PUSH2[0x58])
            + Op.JUMPDEST
            + Op.MSTORE(
                offset=0x600,
                value=Op.CREATE(
                    value=0x0,
                    offset=0x300,
                    size=Op.MLOAD(offset=0x540),
                ),
            )
            + Op.JUMPDEST
            + Op.SSTORE(key=0x20, value=Op.PC)
            + Op.SSTORE(key=0x10, value=Op.RETURNDATASIZE)
            + Op.SSTORE(key=0x11, value=Op.MLOAD(offset=0x600))
            + Op.MSTORE(
                offset=0x640,
                value=Op.CALL(
                    gas=0xFFFF,
                    address=0x8AF6A7AF30D840BA137E8F3F34D54CFB8BEBA6E2,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x21, value=Op.PC)
            + Op.SSTORE(key=0x12, value=Op.SUB(Op.MLOAD(offset=0x640), 0x1))
            + Op.SSTORE(key=0x13, value=Op.RETURNDATASIZE)
            + Op.MSTORE(
                offset=0x640,
                value=Op.CALL(
                    gas=0xFFFF,
                    address=0x40F1299359EA754AC29EB2662A1900752BF8275F,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x22, value=Op.PC)
            + Op.SSTORE(key=0x14, value=Op.SUB(Op.MLOAD(offset=0x640), 0x1))
            + Op.SSTORE(key=0x15, value=Op.RETURNDATASIZE)
            + Op.SSTORE(
                key=0x30,
                value=Op.EXTCODESIZE(
                    address=0x8AF6A7AF30D840BA137E8F3F34D54CFB8BEBA6E2,
                ),
            )
            + Op.EXTCODECOPY(
                address=0x8AF6A7AF30D840BA137E8F3F34D54CFB8BEBA6E2,
                dest_offset=0x660,
                offset=0x0,
                size=Op.SLOAD(key=0x30),
            )
            + Op.SSTORE(key=0x31, value=Op.MLOAD(offset=0x660))
            + Op.SSTORE(
                key=0x32,
                value=Op.EXTCODESIZE(
                    address=0x40F1299359EA754AC29EB2662A1900752BF8275F,
                ),
            )
            + Op.EXTCODECOPY(
                address=0x40F1299359EA754AC29EB2662A1900752BF8275F,
                dest_offset=0x660,
                offset=0x0,
                size=Op.SLOAD(key=0x32),
            )
            + Op.SSTORE(key=0x33, value=Op.MLOAD(offset=0x660))
            + Op.STOP
            + Op.INVALID
            + Op.PUSH1[0x6]
            + Op.CODECOPY(dest_offset=0x200, offset=0xF, size=Op.DUP1)
            + Op.PUSH2[0x200]
            + Op.RETURN
            + Op.STOP
            + Op.INVALID
            + Op.SSTORE(key=0x0, value=0xFF)
            + Op.STOP
            + Op.SSTORE(key=0x0, value=0xFF)
            + Op.STOP
        ),
        storage={
            0x10: 0x60A7,
            0x11: 0x60A7,
            0x12: 0x60A7,
            0x13: 0x60A7,
            0x14: 0x60A7,
            0x15: 0x60A7,
            0x20: 0x60A7,
            0x21: 0x60A7,
            0x22: 0x60A7,
        },
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
