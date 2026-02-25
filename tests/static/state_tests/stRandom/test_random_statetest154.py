"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest154Filler.json

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
    push30 0xb1267c8bba268d1408f7b3e269afee3fea86c5bc8aec8108fd6aaa954f51
    push20 0xb7d0e2328333e94698e0d570db9b316cba0adbae
    push1 0x9d
    push2 0x1ba1
    log2
    origin
    push1 0x04
    push1 0x0d
    push1 0x05
    push1 0x0f
    push4 0x2de40a27
    push20 0xf8e70c18db2bf1444417c2820af74d3ab1d6a06f
    push4 0x5c2491ee
    call
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
    ["tests/static/state_tests/stRandom/randomStatetest154Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest154(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0xf8e70c18db2bf1444417c2820af74d3ab1d6a06f")

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
        Op.PUSH30[0xb1267c8bba268d1408f7b3e269afee3fea86c5bc8aec8108fd6aaa954f51]
        + Op.PUSH20[0xb7d0e2328333e94698e0d570db9b316cba0adbae] + Op.PUSH1[0x9d]
        + Op.PUSH2[0x1ba1] + Op.LOG2 + Op.ORIGIN + Op.PUSH1[0x4] + Op.PUSH1[0xd]
        + Op.PUSH1[0x5] + Op.PUSH1[0xf] + Op.PUSH4[0x2de40a27]
        + Op.PUSH20[0xf8e70c18db2bf1444417c2820af74d3ab1d6a06f] + Op.PUSH4[0x5c2491ee]
        + Op.CALL
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "7767cc78eeac8d9db5297bde12b635c487b138a0dd4601a9236656945997db45a668500a"
            "3ba6eac5489fca6a1a60998fdd14d1f8b6df2f71d56852c0f085c7c3ba826a746e9dce43"
            "35b97488b092df3db7c8097366963ffc1f51e7f4740935567fc404dab22917cbb1e5cf62"
            "52d6e99952a889ec687e6bcdb9b3358f2b287d5d38793a6e6105063e96947760c35c317e"
            "5798e9a5f3cfef9030ea32917ec50268953856b1eae69744b4815f4808e2bcceaa482030"
            "b32689f51807af6e6840942dae7592985e688975e0ee12dbdc39eedbf43aabc2563df850"
            "d6781ed002fe78bd48083bb42742ee243eea1ecd201eef18f00f330fee8836df1234700f"
            "5824b76290232dd1863a69ca84d2786e74eed98d42b740cc037b156dd261441220cfaf15"
            "857c6e8b6f5e1eb9aee8d63ad473477df11660ac765fa5eebfccfed05bacf2809818d01d"
            "b511686cde018f146e78fee9bff3ffe90a1b54cdc57ec52b6fda22f7f81fc1d9724b375c"
            "e206d29176797f9e42c2ec1ef6b468f7f8fbdb5011c4ddcddd72a6adde7d3d077cf96f9d"
            "13893a46aaaf5acc241eabd8712b6a2deea63f6f91cf162e2d6d65579257a17d7c66e075"
            "70d11280dc99"
        ),
        gas_limit=1617280826,
        gas_price=10,
        nonce=0,
        value=1696344411,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
