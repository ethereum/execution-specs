from ethereum_test.types import Account, Environment, Transaction
from ethereum_test.filler import StateTest, test_only


@test_only("istanbul")
def test_chain_id():
    """
    Test CHAINID opcode.
    """
    env = Environment(
        coinbase="0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba",
        difficulty=0x20000,
        gas_limit=10000000000,
        number=1,
        timestamp=1000,
        previous="0x92230ce5476ae868e98c7979cfc165a93f8b6ad1922acf2df62e340916efd49d",  # noqa: E501
        extra_data="0x00",
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
            code="0x46600155", storage={"0x01": "0x01"}
        ),
    }

    return StateTest(env, pre, post, [tx])
