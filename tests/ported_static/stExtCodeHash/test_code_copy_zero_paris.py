"""
https://github.com/ethereum/tests/issues/493,  CODECOPY and EXTCODECOPY...

Ported from:
tests/static/state_tests/stExtCodeHash/codeCopyZero_ParisFiller.yml
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
    ["tests/static/state_tests/stExtCodeHash/codeCopyZero_ParisFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_code_copy_zero_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Https://github.com/ethereum/tests/issues/493,  CODECOPY and..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )
    callee_1 = Address("0xa200000000000000000000000000000000000000")
    callee_2 = Address("0xa300000000000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: LLL
    # {
    #
    #   ;; EXTCODECOPY of nonexistent account
    #   (EXTCODECOPY 0xa222000000000000000000000000000000000000 0 0 32)
    #   (SSTORE 0x10 (MLOAD 0))
    #   (SSTORE 0x11 (EXTCODESIZE 0xa222000000000000000000000000000000000000))
    #   (SSTORE 0x12 (EXTCODEHASH 0xa222000000000000000000000000000000000000))
    #   (SSTORE 0x13 (CALLCODE 50000 0xa222000000000000000000000000000000000000 0 0 0 0 0))  # noqa: E501
    #
    #
    #   ;; EXTCODECOPY of account with empty code
    #   (EXTCODECOPY 0xa200000000000000000000000000000000000000 0 0 32)
    #   (SSTORE 0x20 (MLOAD 0))
    #   (SSTORE 0x21 (EXTCODESIZE 0xa200000000000000000000000000000000000000))
    #   (SSTORE 0x22 (EXTCODEHASH 0xa200000000000000000000000000000000000000))
    #   (SSTORE 0x23 (CALLCODE 50000 0xa200000000000000000000000000000000000000 0 0 0 0 0))  # noqa: E501
    #
    #
    #   ;; EXTCODECOPY of empty account with empty code
    #   (EXTCODECOPY 0xa300000000000000000000000000000000000000 0 0 32)
    #   (SSTORE 0x30 (MLOAD 0))
    #   (SSTORE 0x31 (EXTCODESIZE 0xa300000000000000000000000000000000000000))
    #   (SSTORE 0x32 (EXTCODEHASH 0xa300000000000000000000000000000000000000))
    #   (SSTORE 0x33 (CALLCODE 50000 0xa300000000000000000000000000000000000000 0 0 0 0 0))  # noqa: E501
    #
    #   ;; CODECOPY of dynamic account which has empty code
    #   (CALL 550000 0xa100000000000000000000000000000000000000 0 0 0 0 32)
    #   (SSTORE 0x40 (MLOAD 0))
    # }
    contract = pre.deploy_contract(
        code=(
            Op.EXTCODECOPY(
                address=0xA222000000000000000000000000000000000000,
                dest_offset=0x0,
                offset=0x0,
                size=0x20,
            )
            + Op.SSTORE(key=0x10, value=Op.MLOAD(offset=0x0))
            + Op.SSTORE(
                key=0x11,
                value=Op.EXTCODESIZE(
                    address=0xA222000000000000000000000000000000000000,
                ),
            )
            + Op.SSTORE(
                key=0x12,
                value=Op.EXTCODEHASH(
                    address=0xA222000000000000000000000000000000000000,
                ),
            )
            + Op.SSTORE(
                key=0x13,
                value=Op.CALLCODE(
                    gas=0xC350,
                    address=0xA222000000000000000000000000000000000000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.EXTCODECOPY(
                address=0xA200000000000000000000000000000000000000,
                dest_offset=0x0,
                offset=0x0,
                size=0x20,
            )
            + Op.SSTORE(key=0x20, value=Op.MLOAD(offset=0x0))
            + Op.SSTORE(
                key=0x21,
                value=Op.EXTCODESIZE(
                    address=0xA200000000000000000000000000000000000000,
                ),
            )
            + Op.SSTORE(
                key=0x22,
                value=Op.EXTCODEHASH(
                    address=0xA200000000000000000000000000000000000000,
                ),
            )
            + Op.SSTORE(
                key=0x23,
                value=Op.CALLCODE(
                    gas=0xC350,
                    address=0xA200000000000000000000000000000000000000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.EXTCODECOPY(
                address=0xA300000000000000000000000000000000000000,
                dest_offset=0x0,
                offset=0x0,
                size=0x20,
            )
            + Op.SSTORE(key=0x30, value=Op.MLOAD(offset=0x0))
            + Op.SSTORE(
                key=0x31,
                value=Op.EXTCODESIZE(
                    address=0xA300000000000000000000000000000000000000,
                ),
            )
            + Op.SSTORE(
                key=0x32,
                value=Op.EXTCODEHASH(
                    address=0xA300000000000000000000000000000000000000,
                ),
            )
            + Op.SSTORE(
                key=0x33,
                value=Op.CALLCODE(
                    gas=0xC350,
                    address=0xA300000000000000000000000000000000000000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.POP(
                Op.CALL(
                    gas=0x86470,
                    address=0xA100000000000000000000000000000000000000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x40, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xa000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   (MSTORE 0
    #     (CREATE2 0 0
    #       (lll
    #       {
    #         ;; codecopy of empty code
    #         (CODECOPY 0 0 32)
    #         [[0x50]] (MLOAD 0)
    #         [[0x51]] (EXTCODESIZE (ADDRESS))
    #         [[0x52]] (EXTCODEHASH (ADDRESS))
    #         [[0x53]] (EXTCODESIZE (CALLCODE 50000 (ADDRESS) 0 0 0 0 0))
    #         (EXTCODECOPY (ADDRESS) 0 0 32)
    #         (SSTORE 0x54 (MLOAD 0))
    #       }
    #       0)
    #     0))
    #    (RETURN 0 32)
    #    (STOP)
    # }
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0x39]
            + Op.CODECOPY(dest_offset=0x0, offset=0x1A, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.MSTORE(offset=0x0, value=Op.CREATE2)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.STOP
            + Op.STOP
            + Op.INVALID
            + Op.CODECOPY(dest_offset=0x0, offset=0x0, size=0x20)
            + Op.SSTORE(key=0x50, value=Op.MLOAD(offset=0x0))
            + Op.SSTORE(key=0x51, value=Op.EXTCODESIZE(address=Op.ADDRESS))
            + Op.SSTORE(key=0x52, value=Op.EXTCODEHASH(address=Op.ADDRESS))
            + Op.SSTORE(
                key=0x53,
                value=Op.EXTCODESIZE(
                    address=Op.CALLCODE(
                        gas=0xC350,
                        address=Op.ADDRESS,
                        value=0x0,
                        args_offset=0x0,
                        args_size=0x0,
                        ret_offset=0x0,
                        ret_size=0x0,
                    ),
                ),
            )
            + Op.EXTCODECOPY(
                address=Op.ADDRESS,
                dest_offset=0x0,
                offset=0x0,
                size=0x20,
            )
            + Op.SSTORE(key=0x54, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xa100000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[callee_1] = Account(balance=0xDE0B6B3A7640000, nonce=0)
    pre[callee_2] = Account(balance=10, nonce=0)
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1400000,
        value=1,
    )

    post = {
        Address("0x64bc50092fd622c9cc47d658b99c1af75aaa3d68"): Account(
            storage={
                80: 0x60206000600039600051605055303B605155303F605255600060006000600060,  # noqa: E501
                82: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
            },
        ),
        contract: Account(
            storage={
                19: 1,
                34: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                35: 1,
                50: 0xC5D2460186F7233C927E7DB2DCC703C0E500B653CA82273B7BFAD8045D85A470,  # noqa: E501
                51: 1,
                64: 0x64BC50092FD622C9CC47D658B99C1AF75AAA3D68,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
