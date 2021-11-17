from ethereum_test.common import TestPrivateKey
from ethereum_test.filler import fill_fixture, StateTest
from ethereum_test.helpers import AddrAA
from ethereum_test.types import Account, Environment, Transaction


def test_fill_state_test():
    pre = {
        "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b": Account(
            nonce=1, balance=10000
        ),
        "0x00000000000000000000000000000000000000aa": Account(
            code="0x6001600101600055"
        ),
    }

    tx = Transaction(
        ty=0x2,
        nonce=1,
        to=AddrAA,
        gas_limit=30000,
        max_fee_per_gas=100,
        max_priority_fee_per_gas=101,
    )

    test = StateTest(Environment(base_fee=0x7), pre, pre, [tx])
    fixture = fill_fixture(test, "london", "ethash")

    print(fixture)
