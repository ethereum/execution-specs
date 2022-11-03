"""
Test Yul Source Code Examples
"""

from ethereum_test import (
    Account,
    Environment,
    StateTest,
    TestAddress,
    Transaction,
    Yul,
    test_from,
)


@test_from("berlin")
def test_yul(fork):
    """
    Test YUL compiled bytecode.
    """
    env = Environment()

    pre = {
        "0x1000000000000000000000000000000000000000": Account(
            balance=0x0BA1A9CE0BA1A9CE,
            code=Yul(
                """
            {
                function f(a, b) -> c {
                    c := add(a, b)
                }

                sstore(0, f(1, 2))
                return(0, 32)
            }
            """
            ),
        ),
        TestAddress: Account(balance=0x0BA1A9CE0BA1A9CE),
    }

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        nonce=0,
        to="0x1000000000000000000000000000000000000000",
        gas_limit=500000,
        gas_price=10,
        protected=False,
    )

    post = {
        "0x1000000000000000000000000000000000000000": Account(
            code="""0x6010565b6000828201905092915050565b
                      601a600260016003565b60005560206000f3""",
            storage={
                0x00: 0x03,
            },
        ),
    }

    yield StateTest(env=env, pre=pre, post=post, txs=[tx])
