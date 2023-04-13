"""
Test EIP-1344 CHAINID opcode
"""

from ethereum_test_forks import Istanbul
from ethereum_test_tools import (
    Account,
    Environment,
    StateTest,
    TestAddress,
    Transaction,
    test_from,
    to_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op


@test_from(Istanbul)
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
        to_address(0x100): Account(code=Op.SSTORE(1, Op.CHAINID) + Op.STOP),
        TestAddress: Account(balance=1000000000000000000000),
    }

    tx = Transaction(
        ty=0x0,
        chain_id=0x0,
        nonce=0,
        to=to_address(0x100),
        gas_limit=100000000,
        gas_price=10,
        protected=False,
    )

    post = {
        to_address(0x100): Account(
            code="0x4660015500", storage={"0x01": "0x01"}
        ),
    }

    yield StateTest(env=env, pre=pre, post=post, txs=[tx])
