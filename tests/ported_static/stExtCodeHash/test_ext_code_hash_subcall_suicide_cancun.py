"""
transaction to B | B call to A | A delegatecall/callcode to C (C has...

Ported from:
tests/static/state_tests/stExtCodeHash
extCodeHashSubcallSuicideCancunFiller.yml
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
        "tests/static/state_tests/stExtCodeHash/extCodeHashSubcallSuicideCancunFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_subcall_suicide_cancun(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Transaction to B | B call to A | A delegatecall/callcode to C (C..."""
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
        gas_limit=10000000,
    )

    # Source: LLL
    # {
    #   (CALLCODE 350000 0x3e180b1862f9d158abb5e519a6d8605540c23682 0 0 0 0 32)
    # }
    pre.deploy_contract(
        code=(
            Op.CALLCODE(
                gas=0x55730,
                address=0x3E180B1862F9D158ABB5E519A6D8605540C23682,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xa000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # {
    #   ;; create 0x3e180b1862f9d158abb5e519a6d8605540c23682 (Account A)
    #   (CREATE 1000000000000000000 0 (lll
    #         {
    #             (CALL 100000 0xd000000000000000000000000000000000000000 0 0 0 0 0)  # noqa: E501
    #             (RETURN 0 (lll
    #                 {
    #                   (SELFDESTRUCT 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b)  # noqa: E501
    #                 }
    #             0))
    #         }
    #   0))
    #
    #   (SSTORE 1 (EXTCODEHASH 0xa000000000000000000000000000000000000000))
    #   (SSTORE 2 (EXTCODESIZE 0xa000000000000000000000000000000000000000))
    #   (EXTCODECOPY 0xa000000000000000000000000000000000000000 0 0 32)
    #   (SSTORE 3 (MLOAD 0))
    #
    #   (CALL 350000 0xa000000000000000000000000000000000000000 0 0 0 0 32)
    #
    #   (SSTORE 4 (EXTCODEHASH 0xa000000000000000000000000000000000000000))
    #   (SSTORE 5 (EXTCODESIZE 0xa000000000000000000000000000000000000000))
    #   (EXTCODECOPY 0xa000000000000000000000000000000000000000 0 0 32)
    #   (SSTORE 6 (MLOAD 0))
    #
    #   [[7]] (CALL 350000 0xa000000000000000000000000000000000000000 0 0 0 0 32)  # noqa: E501
    # }
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0x49]
            + Op.CODECOPY(dest_offset=0x0, offset=0x10C, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH8[0xDE0B6B3A7640000]
            + Op.POP(Op.CREATE)
            + Op.SSTORE(
                key=0x1,
                value=Op.EXTCODEHASH(
                    address=0xA000000000000000000000000000000000000000,
                ),
            )
            + Op.SSTORE(
                key=0x2,
                value=Op.EXTCODESIZE(
                    address=0xA000000000000000000000000000000000000000,
                ),
            )
            + Op.EXTCODECOPY(
                address=0xA000000000000000000000000000000000000000,
                dest_offset=0x0,
                offset=0x0,
                size=0x20,
            )
            + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x0))
            + Op.POP(
                Op.CALL(
                    gas=0x55730,
                    address=0xA000000000000000000000000000000000000000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(
                key=0x4,
                value=Op.EXTCODEHASH(
                    address=0xA000000000000000000000000000000000000000,
                ),
            )
            + Op.SSTORE(
                key=0x5,
                value=Op.EXTCODESIZE(
                    address=0xA000000000000000000000000000000000000000,
                ),
            )
            + Op.EXTCODECOPY(
                address=0xA000000000000000000000000000000000000000,
                dest_offset=0x0,
                offset=0x0,
                size=0x20,
            )
            + Op.SSTORE(key=0x6, value=Op.MLOAD(offset=0x0))
            + Op.SSTORE(
                key=0x7,
                value=Op.CALL(
                    gas=0x55730,
                    address=0xA000000000000000000000000000000000000000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.STOP
            + Op.INVALID
            + Op.POP(
                Op.CALL(
                    gas=0x186A0,
                    address=0xD000000000000000000000000000000000000000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.PUSH1[0x17]
            + Op.CODECOPY(dest_offset=0x0, offset=0x32, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.RETURN
            + Op.STOP
            + Op.INVALID
            + Op.SELFDESTRUCT(
                address=0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xb000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   [[1]] 1
    # }
    callee_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xd000000000000000000000000000000000000000"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=500000,
        value=1,
    )

    post = {
        contract: Account(
            storage={
                1: 0x807D478BD0D0173122F5531D4C43781631444232A0816DD35578747C7D67AF0D,  # noqa: E501
                2: 37,
                3: 0x60206000600060006000733E180B1862F9D158ABB5E519A6D8605540C2368262,  # noqa: E501
                4: 0x807D478BD0D0173122F5531D4C43781631444232A0816DD35578747C7D67AF0D,  # noqa: E501
                5: 37,
                6: 0x60206000600060006000733E180B1862F9D158ABB5E519A6D8605540C2368262,  # noqa: E501
                7: 1,
            },
        ),
        callee_1: Account(storage={1: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
