"""
abstract: Tests [EIP-1153: Transient Storage Opcodes](https://eips.ethereum.org/EIPS/eip-1153)

    Test [EIP-1153: Transient Storage Opcodes](https://eips.ethereum.org/EIPS/eip-1153). Ports
    the tests from the ./stEIP1153-transientStorage folder, originally from ethereum/tests.

"""  # noqa: E501

# from typing import Mapping

import pytest

from ethereum_test_tools import Account, Environment
from ethereum_test_tools import Opcodes as Op
from ethereum_test_tools import StateTestFiller, TestAddress, Transaction

from .spec import ref_spec_1153

REFERENCE_SPEC_GIT_PATH = ref_spec_1153.git_path
REFERENCE_SPEC_VERSION = ref_spec_1153.version

pytestmark = [pytest.mark.valid_from("Cancun")]

code_address = 0x100


def test_transient_storage_unset_values(state_test: StateTestFiller):
    """
      Test that tload returns zero for unset values.

      Ports the following ethereum/tests yaml style test to Python format:

       01_tloadBeginningTxn:
    _info:
      comment: load arbitrary value is 0 at beginning of transaction

    env:
      currentCoinbase: 2adc25665018aa1fe0e6bc666dac8fc2697ff9ba
      currentDifficulty: 0x20000
      currentNumber: 1
      currentTimestamp: 1000
      currentGasLimit: 0x10000000000000
      previousHash: 5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6
      currentBaseFee: 10
    pre:
      A00000000000000000000000000000000000000A:
        balance: 1000000000000000000
        nonce: 0
        code: |
          :yul {
            let val := verbatim_1i_1o(hex"5c", 0)
            sstore(1, val)
          }
        storage: { 0x01: 0xffff }

      a94f5374fce5edbc8e2a8697c15331677e6ebf0b:
        balance: 1000000000000000000000
        code: "0x"
        nonce: 0
        storage: {}

    transaction:
      data:
        - data: 0x
          accessList: []
      gasLimit:
        - 0x10000000000000
      nonce: 0
      to: A00000000000000000000000000000000000000A
      value:
        - 0
      secretKey: "45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
      maxPriorityFeePerGas: 0
      maxFeePerGas: 2000

    expect:
      - network:
          - ">=Cancun"
        result:
          A00000000000000000000000000000000000000A:
            storage:
              0x01: 0
    """
    env = Environment()

    slots_under_test = [0, 1, 2, 2**128, 2**256 - 1]
    code = b"".join([Op.SSTORE(slot, Op.TLOAD(slot)) for slot in slots_under_test])

    pre = {
        TestAddress: Account(balance=10_000_000),
        code_address: Account(code=code, storage={slot: 1 for slot in slots_under_test}),
    }

    txs = [
        Transaction(
            to=code_address,
            data=b"",
            gas_limit=1_000_000,
        )
    ]

    post = {code_address: Account(storage={slot: 0 for slot in slots_under_test})}

    state_test(
        env=env,
        pre=pre,
        post=post,
        txs=txs,
    )


def test_tload_after_tstore(state_test: StateTestFiller):
    """
        Ports the following ethereum/tests yaml style test to Python format:
        # 02
    # Loading after storing returns the stored value: TSTORE(x, y), TLOAD(x) returns y
    #
    # Expect storage slot 1 to have value 88

    02_tloadAfterTstore:
      _info:
        comment: tload from same slot after tstore returns correct value

      env:
        currentCoinbase: 2adc25665018aa1fe0e6bc666dac8fc2697ff9ba
        currentDifficulty: 0x20000
        currentNumber: 1
        currentTimestamp: 1000
        currentGasLimit: 0x10000000000000
        previousHash: 5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6
        currentBaseFee: 10

      pre:
        A00000000000000000000000000000000000000A:
          balance: 1000000000000000000
          nonce: 0
          code: |
            :yul {
              verbatim_2i_0o(hex"5D", 0, 88)
              let val := verbatim_1i_1o(hex"5C", 0)
              sstore(1, val)
            }
          storage: {}
        a94f5374fce5edbc8e2a8697c15331677e6ebf0b:
          balance: 1000000000000000000000
          code: "0x"
          nonce: 0
          storage: {}

      transaction:
        data:
          - data: 0x
            accessList: []
        gasLimit:
          - 0x10000000000000
        nonce: 0
        to: A00000000000000000000000000000000000000A
        value:
          - 0
        secretKey: "45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        maxPriorityFeePerGas: 0
        maxFeePerGas: 4000

      expect:
        - network:
            - ">=Cancun"
          result:
            A00000000000000000000000000000000000000A:
              storage:
                0x01: 88
    """
    env = Environment()

    slots_under_test = [0, 1, 2, 2**128, 2**256 - 1]
    code = b"".join(
        [Op.TSTORE(slot, slot) + Op.SSTORE(slot, Op.TLOAD(slot)) for slot in slots_under_test]
    )

    pre = {
        TestAddress: Account(balance=10_000_000),
        code_address: Account(code=code, storage={slot: 0 for slot in slots_under_test}),
    }

    txs = [
        Transaction(
            to=code_address,
            data=b"",
            gas_limit=1_000_000,
        )
    ]

    post = {code_address: Account(storage={slot: slot for slot in slots_under_test})}

    state_test(
        env=env,
        pre=pre,
        post=post,
        txs=txs,
    )


def test_tload_after_tstore_is_zero(state_test: StateTestFiller):
    """
    Test that tload returns zero after tstore is called with zero.

    Ports the tests from the following ethereum/tests yaml style test to Python format:
      03_tloadAfterStoreIs0:
    _info:
      comment: Loading any other slot after storing to a slot returns 0.

    env:
      currentCoinbase: 2adc25665018aa1fe0e6bc666dac8fc2697ff9ba
      currentDifficulty: 0x20000
      currentNumber: 1
      currentTimestamp: 1000
      currentGasLimit: 0x10000000000000
      previousHash: 5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6
      currentBaseFee: 10

    pre:
      A00000000000000000000000000000000000000A:
        balance: 1000000000000000000
        nonce: 0
        code: |
          :yul {
            verbatim_2i_0o(hex"5D", 0, 30)
            let val := verbatim_1i_1o(hex"5C", 1)
            sstore(1, val)
          }
        storage: { 0x00: 0xffff, 0x01: 0xffff }
      a94f5374fce5edbc8e2a8697c15331677e6ebf0b:
        balance: 1000000000000000000000
        code: "0x"
        nonce: 0
        storage: {}

    transaction:
      data:
        - data: 0x
          accessList: []
      gasLimit:
        - "400000"
      nonce: 0
      to: A00000000000000000000000000000000000000A
      value:
        - 0
      secretKey: "45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
      maxPriorityFeePerGas: 0
      maxFeePerGas: 2000

    expect:
      - network:
          - ">=Cancun"
        result:
          A00000000000000000000000000000000000000A:
            storage:
              # The result we expect
              0x00: 0xffff # ensure tstore never wrote to storage
              0x01: 0 # ensure loading from an unused key is 0
    """
    env = Environment()

    slots_to_write = [1, 4, 2**128, 2**256 - 2]
    slots_to_read = [slot - 1 for slot in slots_to_write] + [slot + 1 for slot in slots_to_write]
    assert set.intersection(set(slots_to_write), set(slots_to_read)) == set()

    code = b"".join([Op.TSTORE(slot, 1234) for slot in slots_to_write]) + b"".join(
        [Op.SSTORE(slot, Op.TLOAD(slot)) for slot in slots_to_read]
    )

    pre = {
        TestAddress: Account(balance=10_000_000),
        code_address: Account(
            code=code, storage={slot: 0xFFFF for slot in slots_to_write + slots_to_read}
        ),
    }

    txs = [
        Transaction(
            to=code_address,
            data=b"",
            gas_limit=1_000_000,
        )
    ]

    post = {
        code_address: Account(
            storage={slot: 0 for slot in slots_to_read} | {slot: 0xFFFF for slot in slots_to_write}
        )
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        txs=txs,
    )


def test_tload_after_call(state_test: StateTestFiller):
    """
    Ports the tests from the following ethereum/tests yaml style test to Python format:

    # 04
    # Contracts have separate transient storage.
    # Loading a slot in a separate contract after storing returns 0: TSTORE(x, y), CALL(z, ...),
    #   TLOAD(x) returns 0
    # Storing to a slot in a separate contract does not affect calling contract: TSTORE(x, y),
    #   CALL(z, ...), TSTORE(x, f) and original calling contract TLOAD(x) returns y
    #
    # Expect storage slot 0 of address a to be 10. Ensures that tstore in a different contract
    #   doesn't modify calling contract transient storage.
    # Expect storage slot 1 of address a to be 1 (successful call).
    # Expect storage slot 0 of address b to be 0. Ensures that tload doesn't load the calling
    #   contracts transient storage.
    # Expect storage slot 1 of address b to be 20. Ensures that tstore did result in a change
    #   to the transient storage of a called contract.

    04_tloadAfterCall:
      _info:
        comment: Loading a slot after a call to another contract is 0.

      env:
        currentCoinbase: 2adc25665018aa1fe0e6bc666dac8fc2697ff9ba
        currentDifficulty: 0x20000
        currentNumber: 1
        currentTimestamp: 1000
        currentGasLimit: 0x10000000000000
        previousHash: 5e20a0453cecd065ea59c37ac63e079ee08998b6045136a8ce6635c7912ec0b6
        currentBaseFee: 10

      pre:
        A00000000000000000000000000000000000000A:
          balance: 1000000000000000000
          nonce: 0
          code: |
            :yul {
              verbatim_2i_0o(hex"5D", 0, 10)
              let success := call(gas(), 0xB00000000000000000000000000000000000000B, 0, 0, 32, 0,0)
              let val := verbatim_1i_1o(hex"5C", 0)
              sstore(0, val)
              sstore(1, success)
            }
          storage: {}
        B00000000000000000000000000000000000000B:
          balance: 1000000000000000000
          nonce: 0
          code: |
            :yul {
              let val := verbatim_1i_1o(hex"5C", 0)
              sstore(0, val)

              verbatim_2i_0o(hex"5D", 0, 20)
              let updated_val := verbatim_1i_1o(hex"5C", 0)
              sstore(1, updated_val)
            }
          storage: { 0x00: 0xffff }
        a94f5374fce5edbc8e2a8697c15331677e6ebf0b:
          balance: 1000000000000000000000
          code: "0x"
          nonce: 0
          storage: {}

      transaction:
        data:
          - data: 0x
            accessList: []
        gasLimit:
          - "400000"
        nonce: 0
        to: A00000000000000000000000000000000000000A
        value:
          - 0
        secretKey: "45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        maxPriorityFeePerGas: 0
        maxFeePerGas: 2000

      expect:
        - network:
            - ">=Cancun"
          result:
            A00000000000000000000000000000000000000A:
              storage:
                # expect 1 (successful call) at slot 1
                0x00: 10
                0x01: 1
            B00000000000000000000000000000000000000B:
              storage:
                0x00: 0
                0x01: 20
    """
