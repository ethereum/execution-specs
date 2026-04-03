"""
Test_random_statetest154.

Ported from:
state_tests/stRandom/randomStatetest154Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom/randomStatetest154Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest154(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest154."""
    coinbase = Address(0x4F3F701464972E74606D6EA82D4D3080599A0E79)
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x7db1267c8bba268d1408f7b3e269afee3fea86c5bc8aec8108fd6aaa954f5173b7d0e2328333e94698e0d570db9b316cba0adbae609d611ba1a2326004600d6005600f632de40a2773<contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>635c2491eef1  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.LOG2(
            offset=0x1BA1,
            size=0x9D,
            topic_1=0xB7D0E2328333E94698E0D570DB9B316CBA0ADBAE,
            topic_2=0xB1267C8BBA268D1408F7B3E269AFEE3FEA86C5BC8AEC8108FD6AAA954F51,  # noqa: E501
        )
        + Op.ORIGIN
        + Op.CALL(
            gas=0x5C2491EE,
            address=0xF8E70C18DB2BF1444417C2820AF74D3AB1D6A06F,
            value=0x2DE40A27,
            args_offset=0xF,
            args_size=0x5,
            ret_offset=0xD,
            ret_size=0x4,
        ),
        nonce=0,
        address=Address(0xF8E70C18DB2BF1444417C2820AF74D3AB1D6A06F),  # noqa: E501
    )
    # Source: raw
    # 0x6000355415600957005b60203560003555
    coinbase = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPI(
            pc=0x9,
            condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
        )
        + Op.STOP
        + Op.JUMPDEST
        + Op.SSTORE(
            key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)
        ),
        balance=46,
        nonce=0,
        address=Address(0x4F3F701464972E74606D6EA82D4D3080599A0E79),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "7767cc78eeac8d9db5297bde12b635c487b138a0dd4601a9236656945997db45a668500a3ba6eac5489fca6a1a60998fdd14d1f8b6df2f71d56852c0f085c7c3ba826a746e9dce4335b97488b092df3db7c8097366963ffc1f51e7f4740935567fc404dab22917cbb1e5cf6252d6e99952a889ec687e6bcdb9b3358f2b287d5d38793a6e6105063e96947760c35c317e5798e9a5f3cfef9030ea32917ec50268953856b1eae69744b4815f4808e2bcceaa482030b32689f51807af6e6840942dae7592985e688975e0ee12dbdc39eedbf43aabc2563df850d6781ed002fe78bd48083bb42742ee243eea1ecd201eef18f00f330fee8836df1234700f5824b76290232dd1863a69ca84d2786e74eed98d42b740cc037b156dd261441220cfaf15857c6e8b6f5e1eb9aee8d63ad473477df11660ac765fa5eebfccfed05bacf2809818d01db511686cde018f146e78fee9bff3ffe90a1b54cdc57ec52b6fda22f7f81fc1d9724b375ce206d29176797f9e42c2ec1ef6b468f7f8fbdb5011c4ddcddd72a6adde7d3d077cf96f9d13893a46aaaf5acc241eabd8712b6a2deea63f6f91cf162e2d6d65579257a17d7c66e07570d11280dc99"  # noqa: E501
        ),
        gas_limit=1617280826,
        value=0x651C295B,
    )

    post = {
        target: Account(storage={}, nonce=0),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
