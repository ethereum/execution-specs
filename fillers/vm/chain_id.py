"""
Test EIP-1344 CHAINID opcode
"""

from ethereum_test_tools import (
    Account,
    Environment,
    StateTest,
    Transaction,
    test_from,
)


@test_from("istanbul")
def test_chain_id(fork):
    """
    Test CHAINID opcode.
    """
    env = Environment(
        coinbase="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
        difficulty=0x20000,
        gas_limit=10000000000,
        number=1,
        timestamp=1000,
    )

    pre = {
        "0x1000000000000000000000000000000000000000": Account(
            code="0x4660015500"
        ),
        "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b": Account(
            balance=1000000000000000000000
        ),
    }

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        nonce=0,
        to="0x1000000000000000000000000000000000000000",
        gas_limit=100000000,
        gas_price=10,
        protected=False,
    )

    post = {
        "0x1000000000000000000000000000000000000000": Account(
            code="0x4660015500", storage={"0x01": "0x01"}
        ),
    }

    yield StateTest(env=env, pre=pre, post=post, txs=[tx], name="vm_chain_id")
