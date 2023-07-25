"""
abstract: Test DUP

    Test the DUP opcodes.

"""
from ethereum_test_forks import Frontier, Homestead
from ethereum_test_tools import (
    Account,
    Environment,
    StateTestFiller,
    Storage,
    Transaction,
    to_address,
)


def test_dup(state_test: StateTestFiller, fork: str):
    """
    Test the DUP1-DUP16 opcodes.

    note: Test case ported from:

        - [ethereum/tests/GeneralStateTests/VMTests/vmTests/dup.json](https://github.com/ethereum/tests/blob/develop/GeneralStateTests/VMTests/vmTests/dup.json)
        by Ori Pomerantz.
    """  # noqa: E501
    env = Environment()
    pre = {"0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b": Account(balance=1000000000000000000000)}
    txs = []
    post = {}

    """
    We are setting up 16 accounts, ranging from 0x100 to 0x10f.
    They push values into the stack from 0-16, but each contract uses a
    different DUP opcode, and depending on the opcode used, the item copied
    into the storage changes.
    """
    for i in range(0, 16):
        """
        Account 0x100 uses DUP1,
        Account 0x10f uses DUP16.
        """
        account = to_address(0x100 + i)
        dup_opcode = 0x80 + i

        pre[account] = Account(
            code=(
                # Push 0 - 16 onto the stack
                """0x6000 6001 6002 6003 6004 6005 6006 6007 6008 6009
                        600A 600B 600C 600D 600E 600F 6010"""
                +
                # Use the DUP opcode for this account
                hex(dup_opcode)[2:]
                +
                # Save each stack value into different keys in storage
                """6000 55 6001 55 6002 55 6003 55 6004 55 6005 55
                        6006 55 6007 55 6008 55 6009 55 600A 55 600B 55
                        600C 55 600D 55 600E 55 600F 55 6010 55"""
            )
        )

        """
        Also we are sending one transaction to each account.
        The storage of each will only change by one item: storage[0]
        The value depends on the DUP opcode used.
        """

        tx = Transaction(
            ty=0x0,
            nonce=i,
            to=account,
            gas_limit=500000,
            gas_price=10,
            protected=False if fork in [Frontier, Homestead] else True,
            data="",
        )
        txs.append(tx)

        """
        Storage will be structured as follows:

        0x00: 0x10-0x01 (Depending on DUP opcode)
        0x01: 0x10
        0x02: 0x0F
        0x03: 0x0E
        0x04: 0x0D
        0x05: 0x0C
        0x06: 0x0B
        0x07: 0x0A
        0x08: 0x09
        0x09: 0x08
        0x0A: 0x07
        0x0B: 0x06
        0x0C: 0x05
        0x0D: 0x04
        0x0E: 0x03
        0x0F: 0x02
        0x10: 0x01

        DUP1 copies the first element of the stack (0x10).
        DUP16 copies the 16th element of the stack (0x01).
        """
        s: Storage.StorageDictType = dict(zip(range(1, 17), range(16, 0, -1)))
        s[0] = 16 - i

        post[account] = Account(storage=s)

    state_test(env=env, pre=pre, post=post, txs=txs)
