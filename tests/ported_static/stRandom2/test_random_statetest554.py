"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom2/randomStatetest554Filler.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
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

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x9,
                condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLDATALOAD(offset=0x20),
            )
        ),
        balance=46,
        nonce=0,
        address=coinbase,  # noqa: E501
    )
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.LOG0(offset=0xDC, size=0x14)
            + Op.PUSH1[0x29]
            + Op.PUSH19[0x8B67BA4C2FC8C63C46F19BB45A4BE3F678B306]
            + Op.PUSH10[0xBA571E944074C21B140A]
            + Op.PUSH27[
                0x65D14A921EC804A45ECF4D952AA923FB23A0574ACD8EF9F82C7DB1
            ]
            + Op.PUSH31[
                0x157F651BBEB520203BD398160345137B0419A395630FCE1A7ED24C0CCCFD91  # noqa: E501
            ]
            + Op.PUSH23[0x6140E0682F6BD571DB701B4616B567F215FAF42FB37D2A]
            + Op.PUSH29[
                0x43C05A634612322EDA99F09CC2907A6CBA01BB6869B7D24B897EC43B9B
            ]
            + Op.PUSH4[0xA8747A89]
            + Op.PUSH27[
                0xF14C1F4C0B186C6311D36DE86B8C8172AA43C3DFE3EA1650338087
            ]
            + Op.PUSH32[
                0xA7F32DEB9F60254D124338105942B4B5B88C443351DE5EBF14C2380F4A91327D  # noqa: E501
            ]
            + Op.PUSH9[0xA0DA66ABD627DB7573]
            + Op.SWAP10
            + Op.TIMESTAMP
            + Op.LT(0xAFEC536E37D0DA8122CF8681BC, 0x5F5855728FD67764)
            + Op.CALL(
                gas=0x176FE819,
                address=0xD4932C914A13BD1791675290FDD56965C3FCBD03,
                value=0x7EFE33A,
                args_offset=0x8,
                args_size=0x3,
                ret_offset=0x1B,
                ret_size=0x13,
            )
            + Op.PUSH6[0x66B603CCCF38]
            + Op.PUSH29[
                0x5F10E5CDB2BA1B456D2A0386EE72DDF3FF65B33A551AFA423F8AF05E34
            ]
            + Op.PUSH28[
                0x5C50B6FE69C77F0682EF890D8ED8AB3833F128389F6407911FB20590
            ]
            + Op.PUSH5[0x2C9765E97C]
            + Op.PUSH32[
                0x31DFA251377A47CA45B72CE5C1896A697990D60A01CABAF5E4D8F55F11FD3742  # noqa: E501
            ]
            + Op.PUSH20[0x51D1F8E89810C7AEEC6482FD03D7E7CA58FBAAE3]
            + Op.PUSH2[0xE393]
            + Op.PUSH10[0x36543D6DACB1F97F19C3]
            + Op.PUSH19[0x1866491BAD73F32FAEA37B4A8C273668E04DFF]
            + Op.DUP9
            + Op.PUSH4[0xA542E117]
            + Op.PUSH22[0xA693C3B4BCD4FC1A87DDB6450F8F6C2F1BA807AAFFB6]
            + Op.PUSH31[
                0x62AF22CD93175B5FFB428EE9116DAD4A695AA514B8CA4D615FD728A61C124C  # noqa: E501
            ]
            + Op.PUSH26[0x6554A98241320AC2D6B9F16EE1C203DBBA537A211142DF4C2E62]
            + Op.PUSH15[0x4108F87AB6D5B8E9CE86F92ABA50A4]
            + Op.PUSH27[
                0xCC60D734E7A066131D99DAD149451B386120EED210723BD8304CAA
            ]
            + Op.PUSH2[0x48C]
            + Op.PUSH8[0x512CA417AE8857A4]
            + Op.PUSH11[0xD24CA1F2CB75F75EF86A92]
            + Op.PUSH18[0x52BD86981A216D8147F49EAD4BE46967DD10]
            + Op.PUSH22[0x1491F9F1AC2F50FD5DAD394B7838A9EB89B372698362]
            + Op.PUSH5[0x7BDDBB9058]
            + Op.PUSH15[0x4E921A8CC96EA0C50D07DA472B3E63]
            + Op.PUSH1[0xA3]
            + Op.SWAP13
        ),
        nonce=0,
        address=Address("0xd4932c914a13bd1791675290fdd56965c3fcbd03"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "336e88fae59ccc17cac0ec3a4a984fcdc77c2ba8961cb09c97e4f874f69667ea58bce674"  # noqa: E501
            "fe4d474c8898fff5b73e6a7e25d7d5e25ccea0601ea15066d5497deee377fccbfcf7d46f"  # noqa: E501
            "462eb9d2fe6a3782658a9ffd73aa457677100ca7d35d68df5ee8465c2ca2af480e6e3cb2"  # noqa: E501
            "04021b6ae2234a9f3462784bb45c4f087003c9352268b7e9890647fba7f034faad2663bf"  # noqa: E501
            "b15f1e0b7381d4fe5d7ba9c59455e62fe93c8cca7dd3f20d81644c2494b098686d466eb0"  # noqa: E501
            "fec9f497f163bdf627d76f49e3d1b74b142996652c0d53f709553560656e36e89deb34f3"  # noqa: E501
            "2a7b7b5dfb3b309d57704dfa8c0ec20f2c0f70e1761c949c14c6fd619d947e42f23136ff"  # noqa: E501
            "517ac0b92f6df9d2989eb6828d7213a0b9a20959957ade2b1c1f6222920664c7ddf31a03"  # noqa: E501
            "7c866146cabefec6c2f9f02d050c2ec8ef5da91eb65cc7d0b0d7eb3654407e7cb3eae4ea"  # noqa: E501
            "612eb678374b229c0e0fcc178293fd5d500210352eea769ccafa6c7a7e444322c60c241a"  # noqa: E501
            "937bbcf365ba988cb9f0628f7a33e43ba75bc44c38707ca76e02d3ff70e772c56dc9b9bc"  # noqa: E501
            "fd8116b972e66b6a28583e9f272065e9b7f112858c5f71c66dd37755c458bd56109d4dec"  # noqa: E501
            "2015b23774fa549dd52567557117d2fbda2a4f53cbd065fc9b907736d432b2730969562c"  # noqa: E501
            "e445fd6f9dcf91e092390173406e5b047944eafa8607c63c7e79aa872e5ce29de18e48ed"  # noqa: E501
            "9a62f440a0d4d4651d624ff767ac7fc52281bc7fec896a501952622f30e718b484e56e8c"  # noqa: E501
            "a7ab57c2ef2a6d37944e14759a52961dda795af1e984eea7d2689937b0a76ab8494b7acf"  # noqa: E501
            "579c90a0eb949199c0f87e566759722c0799c2c03a027b51a87372e64f7a1fb661d72eac"  # noqa: E501
            "23f2dc691d34981660bf7cfa421c5bf5e3225a4653ae7e0e43bfe4af206d4e69635b55c2"  # noqa: E501
            "4537fe20705e010f348d477b1aef6aeb2388b508a44e640353e169a37221ba3dcf805c6a"  # noqa: E501
            "9ebe283a53e9dcbaee4081a098"
        ),
        gas_limit=1845353713,
        value=1213415884,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
