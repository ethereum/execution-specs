from ethereum.base_types import U256

from ethereum_test.code import Code
from ethereum_test.filler import StateTest, test_from, test_only
from ethereum_test.helpers import AddrAA, TestAddress, TestCode
from ethereum_test.types import Account, Environment, Transaction

#  @valid_from("Frontier")
#  @valid_until("London")
#  def test_add():
#      pre = {
#          "0xaa": 
#              code="6001600201600055"
#          )
#      }

#      post = {
#          "0xaa": Account(
#              storage={ "0": "0x03" }
#          )
#      }

#      tx = helper.NewTransaction(to=common.AddrAA)

#      return StateTest(pre, post, tx)


@test_only("London")
def test_add_simpler():
    code = Code("""
        push1 1
        push1 2
        add
        push1 0
        sstore
    """)

    expect = {
        U256(0): U256(3)
    }

    return TestCode(code, expect)


@test_from("London")
def test_tip_too_high():
    pre = {
        TestAddress: Account(balance=U256(100000), nonce=U256(1)),
        AddrAA: Account(code=Code("6001600101600055")),
    }

    tx = Transaction(
        to=AddrAA,
        gas_limit=U256(30000),
        max_fee_per_gas=U256(100),
        max_priority_fee_per_gas=U256(101),
        nonce=U256(1)
    )

    return StateTest(Environment(), pre, pre, [tx])
