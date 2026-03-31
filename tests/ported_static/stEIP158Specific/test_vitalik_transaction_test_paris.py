"""
Test_vitalik_transaction_test_paris.

Ported from:
state_tests/stEIP158Specific/vitalikTransactionTestParisFiller.json
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
    ["state_tests/stEIP158Specific/vitalikTransactionTestParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_vitalik_transaction_test_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_vitalik_transaction_test_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xEE098E6C2A43D9E2C04F08F0C3A87B0BA59079D4)
    sender = EOA(
        key=0xC85EF7D79691FE79573B1A7064C19C1A9819EBDBD1FAAAB1A8EC92344438AAF4
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFF, nonce=335)
    # Source: hex
    # 0x
    contract_0 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=10,
        nonce=0,
        address=Address(0xEE098E6C2A43D9E2C04F08F0C3A87B0BA59079D4),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=Op.MSTORE8(offset=0x7F, value=0x0)
        + Op.MSIZE
        + Op.PUSH2[0x43]
        + Op.CODECOPY(
            dest_offset=Op.MSIZE, offset=Op.PUSH2[0x13], size=Op.DUP1
        )
        + Op.JUMP(pc=Op.PUSH2[0x56])
        + Op.SELFDESTRUCT(
            address=Op.SDIV(
                0xEE098E6C2A43D9E2C04F08F0C3A87B0BA59079D4D53532071D6CD0CB86FACD56,  # noqa: E501
                0x1000000000000000000000000,
            )
        )
        + Op.PUSH2[0x0]
        + Op.CODECOPY(dest_offset=0x0, offset=Op.PUSH2[0x3F], size=Op.DUP1)
        + Op.JUMP(pc=Op.PUSH2[0x3F])
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.JUMPDEST
        + Op.DUP2
        + Op.PUSH1[0x0]
        + Op.CREATE
        + Op.SWAP1
        + Op.POP * 2
        + Op.MSIZE
        + Op.PUSH2[0x71]
        + Op.CODECOPY(
            dest_offset=Op.MSIZE, offset=Op.PUSH2[0x6C], size=Op.DUP1
        )
        + Op.JUMP(pc=Op.PUSH2[0xDD])
        + Op.PUSH2[0x5F]
        + Op.CODECOPY(dest_offset=0x0, offset=Op.PUSH2[0xE], size=Op.DUP1)
        + Op.JUMP(pc=Op.PUSH2[0x6D])
        + Op.MSTORE8(offset=0x3F, value=0x0)
        + Op.MSIZE
        + Op.PUSH2[0x43]
        + Op.CODECOPY(
            dest_offset=Op.MSIZE, offset=Op.PUSH2[0x13], size=Op.DUP1
        )
        + Op.JUMP(pc=Op.PUSH2[0x56])
        + Op.SELFDESTRUCT(
            address=Op.SDIV(
                0xEE098E6C2A43D9E2C04F08F0C3A87B0BA59079D4D53532071D6CD0CB86FACD56,  # noqa: E501
                0x1000000000000000000000000,
            )
        )
        + Op.PUSH2[0x0]
        + Op.CODECOPY(dest_offset=0x0, offset=Op.PUSH2[0x3F], size=Op.DUP1)
        + Op.JUMP(pc=Op.PUSH2[0x3F])
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.JUMPDEST
        + Op.DUP2
        + Op.PUSH1[0x0]
        + Op.CREATE
        + Op.SWAP1
        + Op.POP * 2
        + Op.INVALID
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.RETURN
        + Op.JUMPDEST
        + Op.DUP2
        + Op.PUSH1[0x0]
        + Op.CREATE
        + Op.SWAP1
        + Op.POP
        + Op.PUSH1[0x40]
        + Op.MSTORE
        + Op.POP(
            Op.CALL(
                gas=0x249F0,
                address=Op.MLOAD(offset=0x40),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.PUSH2[0x0]
        + Op.CODECOPY(dest_offset=0x0, offset=0x108, size=Op.DUP1)
        + Op.JUMP(pc=0x108)
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.RETURN,
        gas_limit=2097151,
        nonce=335,
    )

    post = {
        coinbase: Account(storage={}, code=b"", nonce=1),
        sender: Account(storage={}, code=b"", nonce=336),
        Address(0x1BC78AE0E5EC5CB439F1D5355D6F90D38343E109): Account(
            storage={}, code=b"", nonce=3
        ),
        Address(0x51F9D7F98E997BDD6BEBDE4C2DD27BE8C99303AA): Account(
            storage={},
            code=bytes.fromhex(
                "6000603f5359610043806100135939610056566c010000000000000000000000007fee098e6c2a43d9e2c04f08f0c3a87b0ba59079d4d53532071d6cd0cb86facd5605ff6100008061003f60003961003f565b6000f35b816000f0905050fe"  # noqa: E501
            ),
            balance=0,
            nonce=1,
        ),
        contract_0: Account(storage={}, code=b"", balance=10, nonce=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
