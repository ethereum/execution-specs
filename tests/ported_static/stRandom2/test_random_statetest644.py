"""
Geth Failed this test on Frontier and Homestead.

Ported from:
tests/static/state_tests/stRandom2/randomStatetest644Filler.json
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
    ["tests/static/state_tests/stRandom2/randomStatetest644Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest644(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Geth Failed this test on Frontier and Homestead."""
    coinbase = Address("0x02ebba385bd7f6dde6c57e2d3929a11a1ea0da7e")
    sender = EOA(
        key=0x0A10C9449493A34FD272F4BF6FC827C5B46ECE7D0253518E71286F47EC3AE23A
    )
    contract = Address("0x0000000000000000000000000000000000000001")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=27244094167015944,
    )

    pre.deploy_contract(
        code=(
            Op.PUSH24[0x351C4C5A02C8F13FA7C7F5800FA5C9BA2F3B971C13764F9B]
            + Op.PUSH2[0xC2DB]
            + Op.PUSH7[0xC3F909C17E434A]
            + Op.PUSH9[0xD685402956CC341DBF]
            + Op.PUSH8[0x79516900ED0A1E26]
            + Op.PUSH7[0xDFA40E70F3BCEE]
            + Op.PUSH24[0x3C2BFFD5B5422A2CF32B19E541F15AE2B6FBE16FD19BBD56]
            + Op.PUSH24[0x28190F83569F036DCCD3886AA69C1E685736DA06152E3B24]
            + Op.PUSH19[0x8B13546EA1ABD48EE47B1B2E1EC70B37FA14CC]
            + Op.PUSH17[0x9D35FCE7380230F426455385DA80771FFC]
            + Op.PUSH15[0x261F3BFE7BFE7F1827D17B0CF49A7D]
            + Op.PUSH32[
                0xF8CEB60B6A86EBBB762EB3E4DD1A8A09EAA9A500BC65CBEFD4251865B70CA7E2  # noqa: E501
            ]
            + Op.PUSH7[0x82F1A2BAD52A4A]
            + Op.PUSH10[0x7AA0BAF4EBE05130EC6A]
            + Op.PUSH3[0xE66E71]
            + Op.SWAP14
            + Op.LT(0x682DCA6786082A55EDA4D65F21E9, 0xB753654F0FF08533F6D088E1)
            + Op.LOG0(
                offset=0xF77E3D07CC9DAA30A1B2941C17F9039FFA3BADDF70DCE808,
                size=0x345D12B775CE0F47447731E5EEEFF44CA0A946E1DF,
            )
            + Op.SLOAD(key=0xACB22D3FE0B1ECEA101F659FD3FCFE7D9F16)
            + Op.EXTCODECOPY(
                address=0x2EBBA385BD7F6DDE6C57E2D3929A11A1EA0DA7E,
                dest_offset=0x118942,
                offset=0x32B792,
                size=0x73B023,
            )
            + Op.CALL(
                gas=0xB2DF5D6,
                address=0x2EBBA385BD7F6DDE6C57E2D3929A11A1EA0DA7E,
                value=0x6BD26962,
                args_offset=0x5B60D5,
                args_size=0x1ACB67,
                ret_offset=0x6AB8DE,
                ret_size=0x47F037,
            )
            + Op.CREATE(value=0x17EF5652, offset=0x958980, size=0x3402AF)
            + Op.ORIGIN
        ),
        balance=0x532F42C819FA5BED,
        nonce=28,
        address=coinbase,  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.EXTCODESIZE(address=0xA66737FDCC16CD591384A0B12FB650CE85011E55)
            + Op.PUSH30[
                0x85CC6995D8948AC88F5726F16627D809C92DBA32D01471809AD1C5046B53
            ]
            + Op.PUSH9[0x7D1FF18BCA5A755A0C]
            + Op.PUSH13[0xD7CE36E1DC18C7C2A909F6BC00]
            + Op.PUSH20[0xD53F4C10A2121E6B4F0AEADC71B441C331B19EC5]
            + Op.PUSH25[0x22835269748AE558697A082470ABAA3595D4B8256F8954C7ED]
            + Op.PUSH6[0x5896EB04017A]
            + Op.PUSH32[
                0x522BE50FD88E38EE27DE7EBD20794466F490BCB43162328A337A6E42FD88CACF  # noqa: E501
            ]
            + Op.PUSH11[0x8ECB264FE21836CF31D0AE]
            + Op.PUSH28[
                0xE53DA5FE2CAC802905640C0A18B2CCFD806FED6D7CBAF1FC19C6931D
            ]
            + Op.PUSH13[0x37B9320599CA5061121076A654]
            + Op.PUSH16[0xC888F04E94C09ADCC8A3CC9D00244883]
            + Op.DUP10
            + Op.PUSH24[0xC1010C1CDEF7438B3D1E99CF6D78B9D4F55962B04476323F]
            + Op.CALLVALUE
            + Op.COINBASE
        ),
        balance=0x23C22AEB4961B17E,
        nonce=148,
        address=Address("0x0346ad0b28ea31b7c3d398881dc11ebc97869461"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x236D08FE524712CB)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.PUSH21[0x357A5ADE2DA3B4A5F5459FAFF84E5EA9B714B60ED2]
            + Op.PUSH3[0x57EF59]
            + Op.PUSH30[
                0x9AA2E6D9316426366FE24FB9ED56C4A9E5DCF06AF08C42368FDAA12B7147
            ]
            + Op.PUSH3[0x83C5BD]
            + Op.PUSH2[0x47ED]
            + Op.SWAP4
            + Op.DELEGATECALL(
                gas=0xC30A604,
                address=Op.PUSH20[0x5],
                args_offset=0x28EC1A,
                args_size=0x4971D8,
                ret_offset=0x52D373,
                ret_size=0x5663AE,
            )
            + Op.SLOAD(
                key=0xFE44ADD6669B247CAD0F00251697572FA913A16C98038931DF
            )
        ),
        balance=0x9183FD5B40D86E03,
        nonce=28,
        address=Address("0xe4882ba8527df19159e6536f4aee12c298d28f33"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "7300000000000000000000000000000000000000013b7ea30da9ff11bd5f11e4529c93ce"  # noqa: E501
            "4b37d5a256d61e1f1a0ecccb5fbb21fec97f6b3d456b8caaaa84ef30a44fd8779fae5a48"  # noqa: E501
            "354b937835d82d57999d194d4edfbaf0a8dd026d727e3315a53e907b0e1873b4dcb7f806"  # noqa: E501
            "014bc23164e8cc0560256f0c6a8c09c0df2f0f8208ff622bb459d46ffab16ce9d64bcf9c"  # noqa: E501
            "ec668338ebbc7f9e64656ae99c617d0dd709c1f78f96bea46e2df76db8418e2b657fc77f"  # noqa: E501
            "f2f979952911a73b767a6ce270c7392d2ff340648610fe0219aaf24df2b26e97e2761497"  # noqa: E501
            "bc6b97dea1269de3aca3b69ec7098a7257114a4a2e22c401ec6319bc2deb70980ebef372"  # noqa: E501
            "a327809b3c2473ab86578d2fccd458e6b99a277c4a1d3e96351fbebe62fe63d300444afd"  # noqa: E501
            "3a9077c20905d2a92b5b2945de6bf9b28d1d42795ca74b029dce6934312994a31fed72e4"  # noqa: E501
            "5da26c73c636b40b1f6d529f35488625624a9dfd0b62309f286277b5ab6259b2fd621447"  # noqa: E501
            "22631c4722737300000000000000000000000000000000000000056317345497f13368b2"  # noqa: E501
            "a96595a00933d8dd6dc111a13b90768f330898544a443407620316d3625614816282f1e9"  # noqa: E501
            "622e741d730346ad0b28ea31b7c3d398881dc11ebc97869461631d791a38fa"
        ),
        gas_limit=48887,
        value=4077944035,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRandom2/randomStatetest644Filler.json"],
)
@pytest.mark.valid_from("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest644_from_prague(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Geth Failed this test on Frontier and Homestead."""
    coinbase = Address("0x02ebba385bd7f6dde6c57e2d3929a11a1ea0da7e")
    sender = EOA(
        key=0x0A10C9449493A34FD272F4BF6FC827C5B46ECE7D0253518E71286F47EC3AE23A
    )
    contract = Address("0x0000000000000000000000000000000000000001")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=27244094167015944,
    )

    pre.deploy_contract(
        code=(
            Op.PUSH24[0x351C4C5A02C8F13FA7C7F5800FA5C9BA2F3B971C13764F9B]
            + Op.PUSH2[0xC2DB]
            + Op.PUSH7[0xC3F909C17E434A]
            + Op.PUSH9[0xD685402956CC341DBF]
            + Op.PUSH8[0x79516900ED0A1E26]
            + Op.PUSH7[0xDFA40E70F3BCEE]
            + Op.PUSH24[0x3C2BFFD5B5422A2CF32B19E541F15AE2B6FBE16FD19BBD56]
            + Op.PUSH24[0x28190F83569F036DCCD3886AA69C1E685736DA06152E3B24]
            + Op.PUSH19[0x8B13546EA1ABD48EE47B1B2E1EC70B37FA14CC]
            + Op.PUSH17[0x9D35FCE7380230F426455385DA80771FFC]
            + Op.PUSH15[0x261F3BFE7BFE7F1827D17B0CF49A7D]
            + Op.PUSH32[
                0xF8CEB60B6A86EBBB762EB3E4DD1A8A09EAA9A500BC65CBEFD4251865B70CA7E2  # noqa: E501
            ]
            + Op.PUSH7[0x82F1A2BAD52A4A]
            + Op.PUSH10[0x7AA0BAF4EBE05130EC6A]
            + Op.PUSH3[0xE66E71]
            + Op.SWAP14
            + Op.LT(0x682DCA6786082A55EDA4D65F21E9, 0xB753654F0FF08533F6D088E1)
            + Op.LOG0(
                offset=0xF77E3D07CC9DAA30A1B2941C17F9039FFA3BADDF70DCE808,
                size=0x345D12B775CE0F47447731E5EEEFF44CA0A946E1DF,
            )
            + Op.SLOAD(key=0xACB22D3FE0B1ECEA101F659FD3FCFE7D9F16)
            + Op.EXTCODECOPY(
                address=0x2EBBA385BD7F6DDE6C57E2D3929A11A1EA0DA7E,
                dest_offset=0x118942,
                offset=0x32B792,
                size=0x73B023,
            )
            + Op.CALL(
                gas=0xB2DF5D6,
                address=0x2EBBA385BD7F6DDE6C57E2D3929A11A1EA0DA7E,
                value=0x6BD26962,
                args_offset=0x5B60D5,
                args_size=0x1ACB67,
                ret_offset=0x6AB8DE,
                ret_size=0x47F037,
            )
            + Op.CREATE(value=0x17EF5652, offset=0x958980, size=0x3402AF)
            + Op.ORIGIN
        ),
        balance=0x532F42C819FA5BED,
        nonce=28,
        address=coinbase,  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.EXTCODESIZE(address=0xA66737FDCC16CD591384A0B12FB650CE85011E55)
            + Op.PUSH30[
                0x85CC6995D8948AC88F5726F16627D809C92DBA32D01471809AD1C5046B53
            ]
            + Op.PUSH9[0x7D1FF18BCA5A755A0C]
            + Op.PUSH13[0xD7CE36E1DC18C7C2A909F6BC00]
            + Op.PUSH20[0xD53F4C10A2121E6B4F0AEADC71B441C331B19EC5]
            + Op.PUSH25[0x22835269748AE558697A082470ABAA3595D4B8256F8954C7ED]
            + Op.PUSH6[0x5896EB04017A]
            + Op.PUSH32[
                0x522BE50FD88E38EE27DE7EBD20794466F490BCB43162328A337A6E42FD88CACF  # noqa: E501
            ]
            + Op.PUSH11[0x8ECB264FE21836CF31D0AE]
            + Op.PUSH28[
                0xE53DA5FE2CAC802905640C0A18B2CCFD806FED6D7CBAF1FC19C6931D
            ]
            + Op.PUSH13[0x37B9320599CA5061121076A654]
            + Op.PUSH16[0xC888F04E94C09ADCC8A3CC9D00244883]
            + Op.DUP10
            + Op.PUSH24[0xC1010C1CDEF7438B3D1E99CF6D78B9D4F55962B04476323F]
            + Op.CALLVALUE
            + Op.COINBASE
        ),
        balance=0x23C22AEB4961B17E,
        nonce=148,
        address=Address("0x0346ad0b28ea31b7c3d398881dc11ebc97869461"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x236D08FE524712CB)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.PUSH21[0x357A5ADE2DA3B4A5F5459FAFF84E5EA9B714B60ED2]
            + Op.PUSH3[0x57EF59]
            + Op.PUSH30[
                0x9AA2E6D9316426366FE24FB9ED56C4A9E5DCF06AF08C42368FDAA12B7147
            ]
            + Op.PUSH3[0x83C5BD]
            + Op.PUSH2[0x47ED]
            + Op.SWAP4
            + Op.DELEGATECALL(
                gas=0xC30A604,
                address=Op.PUSH20[0x5],
                args_offset=0x28EC1A,
                args_size=0x4971D8,
                ret_offset=0x52D373,
                ret_size=0x5663AE,
            )
            + Op.SLOAD(
                key=0xFE44ADD6669B247CAD0F00251697572FA913A16C98038931DF
            )
        ),
        balance=0x9183FD5B40D86E03,
        nonce=28,
        address=Address("0xe4882ba8527df19159e6536f4aee12c298d28f33"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "7300000000000000000000000000000000000000013b7ea30da9ff11bd5f11e4529c93ce"  # noqa: E501
            "4b37d5a256d61e1f1a0ecccb5fbb21fec97f6b3d456b8caaaa84ef30a44fd8779fae5a48"  # noqa: E501
            "354b937835d82d57999d194d4edfbaf0a8dd026d727e3315a53e907b0e1873b4dcb7f806"  # noqa: E501
            "014bc23164e8cc0560256f0c6a8c09c0df2f0f8208ff622bb459d46ffab16ce9d64bcf9c"  # noqa: E501
            "ec668338ebbc7f9e64656ae99c617d0dd709c1f78f96bea46e2df76db8418e2b657fc77f"  # noqa: E501
            "f2f979952911a73b767a6ce270c7392d2ff340648610fe0219aaf24df2b26e97e2761497"  # noqa: E501
            "bc6b97dea1269de3aca3b69ec7098a7257114a4a2e22c401ec6319bc2deb70980ebef372"  # noqa: E501
            "a327809b3c2473ab86578d2fccd458e6b99a277c4a1d3e96351fbebe62fe63d300444afd"  # noqa: E501
            "3a9077c20905d2a92b5b2945de6bf9b28d1d42795ca74b029dce6934312994a31fed72e4"  # noqa: E501
            "5da26c73c636b40b1f6d529f35488625624a9dfd0b62309f286277b5ab6259b2fd621447"  # noqa: E501
            "22631c4722737300000000000000000000000000000000000000056317345497f13368b2"  # noqa: E501
            "a96595a00933d8dd6dc111a13b90768f330898544a443407620316d3625614816282f1e9"  # noqa: E501
            "622e741d730346ad0b28ea31b7c3d398881dc11ebc97869461631d791a38fa"
        ),
        gas_limit=48887,
        value=4077944035,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
