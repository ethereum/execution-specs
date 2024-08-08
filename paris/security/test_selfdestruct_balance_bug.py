"""
bug: Tests the Consensus Flaw During Block Processing related to SELFDESTRUCT
    Tests the consensus-vulnerability reported in
    [go-ethereum/security/advisories/GHSA-xw37-57qp-9mm4](https://github.com/ethereum/go-ethereum/security/advisories/GHSA-xw37-57qp-9mm4).

To reproduce the issue with this test case:

1. Fill the test with the most recent geth evm version.
2. Run the fixture output within a vulnerable geth version: v1.9.20 > geth >=
    v1.9.4.
"""

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    CalldataCase,
    Initcode,
    Switch,
    Transaction,
    compute_create_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op


@pytest.mark.valid_from("Constantinople")
def test_tx_selfdestruct_balance_bug(blockchain_test: BlockchainTestFiller, pre: Alloc):
    """
    Test that the vulnerability is not present by checking the balance of the
    `0xaa` contract after executing specific transactions:

    1. Start with contract `0xaa` which has initial balance of 3 wei.
        `0xaa` contract code simply performs a self-destruct to itself.

    2. Send a transaction (tx 1) to invoke caller contract `0xcc` (which
        has a balance of 1 wei), which in turn invokes `0xaa` with a 1 wei call.

    3. Store the balance of `0xaa` after the first transaction
        is processed. `0xaa` self-destructed. Expected outcome: 0 wei.

    4. Send another transaction (tx 2) to call 0xaa with 5 wei.

    5. Store the balance of `0xaa` after the second transaction
        is processed. No self-destruct. Expected outcome: 5 wei.

    6. Verify that:
        - Call within tx 1 is successful, i.e `0xaa` self-destructed.
        - The balances of `0xaa` after each tx are correct.
        - During tx 2, code in `0xaa` does not execute,
            hence self-destruct mechanism does not trigger.

    TODO: EOF - This test could be parametrized for EOFCREATE
    """
    deploy_code = Switch(
        default_action=Op.REVERT(0, 0),
        cases=[
            CalldataCase(
                value=0,
                action=Op.SELFDESTRUCT(Op.ADDRESS),
            ),
            CalldataCase(
                value=1,
                action=Op.SSTORE(0, Op.SELFBALANCE),
            ),
        ],
    )
    aa_code = Initcode(
        deploy_code=deploy_code,
    )
    cc_code = (
        Op.CALLDATACOPY(size=Op.CALLDATASIZE)
        + Op.MSTORE(
            0,
            Op.CREATE(
                value=3,  # Initial balance of 3 wei
                offset=0,
                size=Op.CALLDATASIZE,
            ),
        )
        + Op.SSTORE(0xCA1101, Op.CALL(gas=100000, address=Op.MLOAD(0), value=0))
        + Op.CALL(gas=100000, address=Op.MLOAD(0), value=1)
    )

    cc_address = pre.deploy_contract(cc_code, balance=1000000000)
    aa_location = compute_create_address(address=cc_address, nonce=1)
    balance_code = Op.SSTORE(0xBA1AA, Op.BALANCE(aa_location))
    balance_address_1 = pre.deploy_contract(balance_code)
    balance_address_2 = pre.deploy_contract(balance_code)

    sender = pre.fund_eoa()

    blocks = [
        Block(
            txs=[
                # Sender invokes caller, caller invokes 0xaa:
                # calling with 1 wei call
                Transaction(
                    sender=sender,
                    to=cc_address,
                    data=aa_code,
                    gas_limit=1000000,
                ),
                # Dummy tx to store balance of 0xaa after first TX.
                Transaction(
                    sender=sender,
                    to=balance_address_1,
                    gas_limit=100000,
                ),
                # Sender calls 0xaa with 5 wei.
                Transaction(
                    sender=sender,
                    to=aa_location,
                    gas_limit=100000,
                    value=5,
                ),
                # Dummy tx to store balance of 0xaa after second TX.
                Transaction(
                    sender=sender,
                    to=balance_address_2,
                    gas_limit=100000,
                ),
            ],
        ),
    ]

    post = {
        # Check call from caller has succeeded.
        cc_address: Account(nonce=2, storage={0xCA1101: 1}),
        # Check balance of 0xaa after tx 1 is 0 wei, i.e self-destructed.
        # Vulnerable versions should return 1 wei.
        balance_address_1: Account(storage={0xBA1AA: 0}),
        # Check that 0xaa exists and balance after tx 2 is 5 wei.
        # Vulnerable versions should return 6 wei.
        balance_address_2: Account(storage={0xBA1AA: 5}),
        aa_location: Account(storage={0: 0}),
    }

    blockchain_test(pre=pre, post=post, blocks=blocks)
