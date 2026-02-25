"""
Ported from:
tests/static/state_tests/stRandom2/randomStatetest554Filler.json

coinbase code:
    push1 0x00
    calldataload
    sload
    iszero
    push1 0x09
    jumpi
    stop
    jumpdest
    push1 0x20
    calldataload
    push1 0x00
    calldataload
    sstore

contract code:
    push1 0x14
    push1 0xdc
    log0
    push1 0x29
    push19 0x8b67ba4c2fc8c63c46f19bb45a4be3f678b306
    push10 0xba571e944074c21b140a
    push27 0x65d14a921ec804a45ecf4d952aa923fb23a0574acd8ef9f82c7db1
    push31 0x157f651bbeb520203bd398160345137b0419a395630fce1a7ed24c0cccfd91
    push23 0x6140e0682f6bd571db701b4616b567f215faf42fb37d2a
    push29 0x43c05a634612322eda99f09cc2907a6cba01bb6869b7d24b897ec43b9b
    push4 0xa8747a89
    push27 0xf14c1f4c0b186c6311d36de86b8c8172aa43c3dfe3ea1650338087
    push32 0xa7f32deb9f60254d124338105942b4b5b88c443351de5ebf14c2380f4a91327d
    push9 0xa0da66abd627db7573
    swap10
    timestamp
    push8 0x5f5855728fd67764
    push13 0xafec536e37d0da8122cf8681bc
    lt
    push1 0x13
    ... (32 more instructions)
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRandom2/randomStatetest554Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest554(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xd4932c914a13bd1791675290fdd56965c3fcbd03")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(
        balance=46,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SLOAD + Op.ISZERO + Op.PUSH1[0x9]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x20] + Op.CALLDATALOAD
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SSTORE
    ),
    )
    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH1[0x14] + Op.PUSH1[0xdc] + Op.LOG0 + Op.PUSH1[0x29]
        + Op.PUSH19[0x8b67ba4c2fc8c63c46f19bb45a4be3f678b306]
        + Op.PUSH10[0xba571e944074c21b140a]
        + Op.PUSH27[0x65d14a921ec804a45ecf4d952aa923fb23a0574acd8ef9f82c7db1]
        + Op.PUSH31[0x157f651bbeb520203bd398160345137b0419a395630fce1a7ed24c0cccfd91]
        + Op.PUSH23[0x6140e0682f6bd571db701b4616b567f215faf42fb37d2a]
        + Op.PUSH29[0x43c05a634612322eda99f09cc2907a6cba01bb6869b7d24b897ec43b9b]
        + Op.PUSH4[0xa8747a89]
        + Op.PUSH27[0xf14c1f4c0b186c6311d36de86b8c8172aa43c3dfe3ea1650338087]
        + Op.PUSH32[0xa7f32deb9f60254d124338105942b4b5b88c443351de5ebf14c2380f4a91327d]
        + Op.PUSH9[0xa0da66abd627db7573] + Op.SWAP10 + Op.TIMESTAMP
        + Op.PUSH8[0x5f5855728fd67764] + Op.PUSH13[0xafec536e37d0da8122cf8681bc]
        + Op.LT + Op.PUSH1[0x13] + Op.PUSH1[0x1b] + Op.PUSH1[0x3] + Op.PUSH1[0x8]
        + Op.PUSH4[0x7efe33a] + Op.PUSH20[0xd4932c914a13bd1791675290fdd56965c3fcbd03]
        + Op.PUSH4[0x176fe819] + Op.CALL + Op.PUSH6[0x66b603cccf38]
        + Op.PUSH29[0x5f10e5cdb2ba1b456d2a0386ee72ddf3ff65b33a551afa423f8af05e34]
        + Op.PUSH28[0x5c50b6fe69c77f0682ef890d8ed8ab3833f128389f6407911fb20590]
        + Op.PUSH5[0x2c9765e97c]
        + Op.PUSH32[0x31dfa251377a47ca45b72ce5c1896a697990d60a01cabaf5e4d8f55f11fd3742]
        + Op.PUSH20[0x51d1f8e89810c7aeec6482fd03d7e7ca58fbaae3] + Op.PUSH2[0xe393]
        + Op.PUSH10[0x36543d6dacb1f97f19c3]
        + Op.PUSH19[0x1866491bad73f32faea37b4a8c273668e04dff] + Op.DUP9
        + Op.PUSH4[0xa542e117]
        + Op.PUSH22[0xa693c3b4bcd4fc1a87ddb6450f8f6c2f1ba807aaffb6]
        + Op.PUSH31[0x62af22cd93175b5ffb428ee9116dad4a695aa514b8ca4d615fd728a61c124c]
        + Op.PUSH26[0x6554a98241320ac2d6b9f16ee1c203dbba537a211142df4c2e62]
        + Op.PUSH15[0x4108f87ab6d5b8e9ce86f92aba50a4]
        + Op.PUSH27[0xcc60d734e7a066131d99dad149451b386120eed210723bd8304caa]
        + Op.PUSH2[0x48c] + Op.PUSH8[0x512ca417ae8857a4]
        + Op.PUSH11[0xd24ca1f2cb75f75ef86a92]
        + Op.PUSH18[0x52bd86981a216d8147f49ead4be46967dd10]
        + Op.PUSH22[0x1491f9f1ac2f50fd5dad394b7838a9eb89b372698362]
        + Op.PUSH5[0x7bddbb9058] + Op.PUSH15[0x4e921a8cc96ea0c50d07da472b3e63]
        + Op.PUSH1[0xa3] + Op.SWAP13
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "336e88fae59ccc17cac0ec3a4a984fcdc77c2ba8961cb09c97e4f874f69667ea58bce674"
            "fe4d474c8898fff5b73e6a7e25d7d5e25ccea0601ea15066d5497deee377fccbfcf7d46f"
            "462eb9d2fe6a3782658a9ffd73aa457677100ca7d35d68df5ee8465c2ca2af480e6e3cb2"
            "04021b6ae2234a9f3462784bb45c4f087003c9352268b7e9890647fba7f034faad2663bf"
            "b15f1e0b7381d4fe5d7ba9c59455e62fe93c8cca7dd3f20d81644c2494b098686d466eb0"
            "fec9f497f163bdf627d76f49e3d1b74b142996652c0d53f709553560656e36e89deb34f3"
            "2a7b7b5dfb3b309d57704dfa8c0ec20f2c0f70e1761c949c14c6fd619d947e42f23136ff"
            "517ac0b92f6df9d2989eb6828d7213a0b9a20959957ade2b1c1f6222920664c7ddf31a03"
            "7c866146cabefec6c2f9f02d050c2ec8ef5da91eb65cc7d0b0d7eb3654407e7cb3eae4ea"
            "612eb678374b229c0e0fcc178293fd5d500210352eea769ccafa6c7a7e444322c60c241a"
            "937bbcf365ba988cb9f0628f7a33e43ba75bc44c38707ca76e02d3ff70e772c56dc9b9bc"
            "fd8116b972e66b6a28583e9f272065e9b7f112858c5f71c66dd37755c458bd56109d4dec"
            "2015b23774fa549dd52567557117d2fbda2a4f53cbd065fc9b907736d432b2730969562c"
            "e445fd6f9dcf91e092390173406e5b047944eafa8607c63c7e79aa872e5ce29de18e48ed"
            "9a62f440a0d4d4651d624ff767ac7fc52281bc7fec896a501952622f30e718b484e56e8c"
            "a7ab57c2ef2a6d37944e14759a52961dda795af1e984eea7d2689937b0a76ab8494b7acf"
            "579c90a0eb949199c0f87e566759722c0799c2c03a027b51a87372e64f7a1fb661d72eac"
            "23f2dc691d34981660bf7cfa421c5bf5e3225a4653ae7e0e43bfe4af206d4e69635b55c2"
            "4537fe20705e010f348d477b1aef6aeb2388b508a44e640353e169a37221ba3dcf805c6a"
            "9ebe283a53e9dcbaee4081a098"
        ),
        gas_limit=1845353713,
        gas_price=10,
        nonce=0,
        value=1213415884,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
