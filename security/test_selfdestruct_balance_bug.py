"""
Tests the following consensus-vulnerability.

https://github.com/ethereum/go-ethereum/security/advisories/GHSA-xw37-57qp-9mm4

To reproduce the bug fill the test with the most recent geth evm version.

Then run the fixture output within a vulnerable geth version:
v1.9.20 > geth >= v1.9.4
"""
import pytest

from ethereum_test_tools import (
    Account,
    Block,
    BlockchainTestFiller,
    TestAddress,
    Transaction,
    Yul,
    to_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op


@pytest.mark.valid_from("Constantinople")
def test_tx_selfdestruct_balance_bug(blockchain_test: BlockchainTestFiller):
    """
    Checks balance of 0xaa after executing specific txs:

        1. Start contract 0xaa that has initial balance of 3 wei.
           0xaa contract code simply performs a self-destruct to itself.

        2. Send a transaction (tx 1) to invoke caller contract (with
           1 wei balance), which in turn invokes 0xaa with a 1 wei call.

        3. Store the balance of 0xaa after the first transaction
           is processed. 0xaa self-destructed. Expected outcome: 0 wei.

        4. Send another transaction (tx 2) to call 0xaa with 5 wei.

        5. Store the balance of 0xaa after the second transaction
           is processed. No self-destruct. Expected outcome: 5 wei.

        6. Verify that:
            - call within tx 1 is successful, i.e 0xaa self-destructed.
            - the balances of 0xaa after each tx are correct.
            - during tx 2, code in 0xaa does not execute,
              hence self-destruct mechanism does not trigger.
    """
    aa_code = Yul(
        """
        {
            /* 1st entrance is self-destruct */
            if eq(0, callvalue()) {
                selfdestruct(0x00000000000000000000000000000000000000AA)
            }

            /* 2nd entrance is other rnd code execution */
            if eq(1, callvalue()) {
                let x := selfbalance()
                sstore(0, x)
            }
        }
        """
    )

    cc_code = Op.SSTORE(0xCA1101, Op.CALL(100000, 0xAA, 0, 0, 0, 0, 0)) + Op.CALL(
        100000, 0xAA, 1, 0, 0, 0, 0
    )

    balance_code = Op.SSTORE(0xBA1AA, Op.BALANCE(0xAA))

    pre = {
        # sender
        TestAddress: Account(balance=1000000000),
        # caller
        to_address(0xCC): Account(balance=1000000000, code=cc_code),
        # initial balance of 3 wei
        to_address(0xAA): Account(balance=3, code=aa_code),
        # stores balance of 0xaa after each tx 1
        to_address(0xBA11): Account(code=balance_code),
        # stores balance of 0xaa after each tx 2
        to_address(0xBA12): Account(code=balance_code),
    }

    blocks = [
        Block(
            txs=[
                # Sender invokes caller, caller invokes 0xaa:
                # calling with 1 wei call
                Transaction(
                    nonce=0,
                    to=to_address(0xCC),
                    gas_limit=1000000,
                    gas_price=10,
                ),
                # Dummy tx to store balance of 0xaa after first TX.
                Transaction(
                    nonce=1,
                    to=to_address(0xBA11),
                    gas_limit=100000,
                    gas_price=10,
                ),
                # Sender calls 0xaa with 5 wei.
                Transaction(
                    nonce=2,
                    to=to_address(0xAA),
                    gas_limit=100000,
                    gas_price=10,
                    value=5,
                ),
                # Dummy tx to store balance of 0xaa after second TX.
                Transaction(
                    nonce=3,
                    to=to_address(0xBA12),
                    gas_limit=100000,
                    gas_price=10,
                ),
            ],
        ),
    ]

    post = {
        # Check call from caller has succeeded.
        to_address(0xCC): Account(storage={0xCA1101: 1}),
        # Check balance of 0xaa after tx 1 is 0 wei, i.e self-destructed.
        # Vulnerable versions should return 1 wei.
        to_address(0xBA11): Account(storage={0xBA1AA: 0}),
        # Check that 0xaa exists and balance after tx 2 is 5 wei.
        # Vulnerable versions should return 6 wei.
        to_address(0xBA12): Account(storage={0xBA1AA: 5}),
        to_address(0xAA): Account(storage={0: 0}),
    }

    blockchain_test(pre=pre, post=post, blocks=blocks)
