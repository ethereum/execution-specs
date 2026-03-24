"""
EXTCODEHASH/EXTCODESIZE of an account created then deleted in a CALL,...

Ported from:
tests/static/state_tests/stExtCodeHash
extCodeHashCreatedAndDeletedAccountRecheckInOuterCallFiller.json
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
        "tests/static/state_tests/stExtCodeHash/extCodeHashCreatedAndDeletedAccountRecheckInOuterCallFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_hash_created_and_deleted_account_recheck_in_outer_call(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """EXTCODEHASH/EXTCODESIZE of an account created then deleted in a..."""
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
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: LLL
    # { (MSTORE 0 (CREATE2 0 128 (lll { (RETURN 0 (lll { (SELFDESTRUCT 0x0) } 0)) } 128) 0x10)) [[0]] (EXTCODEHASH (MLOAD 0)) [[1]] (EXTCODESIZE (MLOAD 0)) (CALL 0x10000 (MLOAD 0) 0 0 0 0 0) [[2]] (EXTCODEHASH (MLOAD 0)) [[3]] (EXTCODESIZE (MLOAD 0)) (STOP) }  # noqa: E501
    callee = pre.deploy_contract(
        code=(
            Op.PUSH1[0x10]
            + Op.PUSH1[0x11]
            + Op.CODECOPY(dest_offset=0x80, offset=0x44, size=Op.DUP1)
            + Op.PUSH1[0x80]
            + Op.PUSH1[0x0]
            + Op.MSTORE(offset=0x0, value=Op.CREATE2)
            + Op.SSTORE(
                key=0x0,
                value=Op.EXTCODEHASH(address=Op.MLOAD(offset=0x0)),
            )
            + Op.SSTORE(
                key=0x1,
                value=Op.EXTCODESIZE(address=Op.MLOAD(offset=0x0)),
            )
            + Op.POP(
                Op.CALL(
                    gas=0x10000,
                    address=Op.MLOAD(offset=0x0),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x2,
                value=Op.EXTCODEHASH(address=Op.MLOAD(offset=0x0)),
            )
            + Op.SSTORE(
                key=0x3,
                value=Op.EXTCODESIZE(address=Op.MLOAD(offset=0x0)),
            )
            + Op.STOP
            + Op.STOP
            + Op.INVALID
            + Op.PUSH1[0x4]
            + Op.CODECOPY(dest_offset=0x0, offset=0xD, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.RETURN
            + Op.STOP
            + Op.INVALID
            + Op.SELFDESTRUCT(address=0x0)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xdeadbeef00000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (CALL 0x20000 0xdeadbeef00000000000000000000000000000000 0 0 0 0 0) [[0]] (EXTCODEHASH 0x123f4c415171383dcf6f3ac6c3b70fe321e11b5e) [[1]] (EXTCODESIZE 0x123f4c415171383dcf6f3ac6c3b70fe321e11b5e) (STOP) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=0x20000,
                    address=0xDEADBEEF00000000000000000000000000000000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.EXTCODEHASH(
                    address=0x123F4C415171383DCF6F3AC6C3B70FE321E11B5E,
                ),
            )
            + Op.SSTORE(
                key=0x1,
                value=Op.EXTCODESIZE(
                    address=0x123F4C415171383DCF6F3AC6C3B70FE321E11B5E,
                ),
            )
            + Op.STOP
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xdeadbeef00000000000000000000000000000001"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=400000,
        value=1,
    )

    post = {
        callee: Account(
            storage={
                0: 0x73C5F15B1290FD9E66722596C2FA1E1C9341F7ACB185530DCE0BF0E0FEC7DFC6,  # noqa: E501
                1: 4,
                2: 0x73C5F15B1290FD9E66722596C2FA1E1C9341F7ACB185530DCE0BF0E0FEC7DFC6,  # noqa: E501
                3: 4,
            },
        ),
        contract: Account(
            storage={
                0: 0x73C5F15B1290FD9E66722596C2FA1E1C9341F7ACB185530DCE0BF0E0FEC7DFC6,  # noqa: E501
                1: 4,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
