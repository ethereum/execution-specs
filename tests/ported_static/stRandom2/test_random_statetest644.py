"""
Geth Failed this test on Frontier and Homestead

Ported from:
state_tests/stRandom2/randomStatetest644Filler.json
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
    ["state_tests/stRandom2/randomStatetest644Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest644(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Geth Failed this test on Frontier and Homestead"""
    coinbase = Address("0x02ebba385bd7f6dde6c57e2d3929a11a1ea0da7e")
    sender = EOA(
        key=0xa10c9449493a34fd272f4bf6fc827c5b46ece7d0253518e71286f47ec3ae23a
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=27244094167015944,
    )

    # Source: raw
    # 0x73a66737fdcc16cd591384a0b12fb650ce85011e553b7d85cc6995d8948ac88f5726f16627d809c92dba32d01471809ad1c5046b53687d1ff18bca5a755a0c6cd7ce36e1dc18c7c2a909f6bc0073d53f4c10a2121e6b4f0aeadc71b441c331b19ec57822835269748ae558697a082470abaa3595d4b8256f8954c7ed655896eb04017a7f522be50fd88e38ee27de7ebd20794466f490bcb43162328a337a6e42fd88cacf6a8ecb264fe21836cf31d0ae7be53da5fe2cac802905640c0a18b2ccfd806fed6d7cbaf1fc19c6931d6c37b9320599ca5061121076a6546fc888f04e94c09adcc8a3cc9d002448838977c1010c1cdef7438b3d1e99cf6d78b9d4f55962b04476323f3441
    addr_0x1000000000000000000000000000000000000000 = pre.deploy_contract(
        code=Op.EXTCODESIZE(address=0xa66737fdcc16cd591384a0b12fb650ce85011e55)
        + Op.PUSH30[0x85cc6995d8948ac88f5726f16627d809c92dba32d01471809ad1c5046b53]
        + Op.PUSH9[0x7d1ff18bca5a755a0c]
        + Op.PUSH13[0xd7ce36e1dc18c7c2a909f6bc00]
        + Op.PUSH20[0xd53f4c10a2121e6b4f0aeadc71b441c331b19ec5]
        + Op.PUSH25[0x22835269748ae558697a082470abaa3595d4b8256f8954c7ed]
        + Op.PUSH6[0x5896eb04017a]
        + Op.PUSH32[0x522be50fd88e38ee27de7ebd20794466f490bcb43162328a337a6e42fd88cacf]
        + Op.PUSH11[0x8ecb264fe21836cf31d0ae]
        + Op.PUSH28[0xe53da5fe2cac802905640c0a18b2ccfd806fed6d7cbaf1fc19c6931d]
        + Op.PUSH13[0x37b9320599ca5061121076a654]
        + Op.PUSH16[0xc888f04e94c09adcc8a3cc9d00244883] + Op.DUP10
        + Op.PUSH24[0xc1010c1cdef7438b3d1e99cf6d78b9d4f55962b04476323f]
        + Op.CALLVALUE + Op.COINBASE,
        balance=0x23c22aeb4961b17e,
        nonce=148,
        address=Address("0x0346ad0b28ea31b7c3d398881dc11ebc97869461"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x236d08fe524712cb)
    # Source: raw
    # 0x74357a5ade2da3b4a5f5459faff84e5ea9b714b60ed26257ef597d9aa2e6d9316426366fe24fb9ed56c4a9e5dcf06af08c42368fdaa12b71476283c5bd6147ed93625663ae6252d373624971d86228ec1a730000000000000000000000000000000000000005630c30a604f478fe44add6669b247cad0f00251697572fa913a16c98038931df54
    addr_0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=Op.PUSH21[0x357a5ade2da3b4a5f5459faff84e5ea9b714b60ed2]
        + Op.PUSH3[0x57ef59]
        + Op.PUSH30[0x9aa2e6d9316426366fe24fb9ed56c4a9e5dcf06af08c42368fdaa12b7147]
        + Op.PUSH3[0x83c5bd] + Op.PUSH2[0x47ed] + Op.SWAP4
        + Op.DELEGATECALL(gas=0xc30a604, address=Op.PUSH20[0x5], args_offset=0x28ec1a, args_size=0x4971d8, ret_offset=0x52d373, ret_size=0x5663ae)
        + Op.SLOAD(key=0xfe44add6669b247cad0f00251697572fa913a16c98038931df),
        balance=0x9183fd5b40d86e03,
        nonce=28,
        address=Address("0xe4882ba8527df19159e6536f4aee12c298d28f33"),  # noqa: E501
    )
    # Source: raw
    # 0x77351c4c5a02c8f13fa7c7f5800fa5c9ba2f3b971c13764f9b61c2db66c3f909c17e434a68d685402956cc341dbf6779516900ed0a1e2666dfa40e70f3bcee773c2bffd5b5422a2cf32b19e541f15ae2b6fbe16fd19bbd567728190f83569f036dccd3886aa69c1e685736da06152e3b24728b13546ea1abd48ee47b1b2e1ec70b37fa14cc709d35fce7380230f426455385da80771ffc6e261f3bfe7bfe7f1827d17b0cf49a7d7ff8ceb60b6a86ebbb762eb3e4dd1a8a09eaa9a500bc65cbefd4251865b70ca7e26682f1a2bad52a4a697aa0baf4ebe05130ec6a62e66e719d6bb753654f0ff08533f6d088e16d682dca6786082a55eda4d65f21e91074345d12b775ce0f47447731e5eeeff44ca0a946e1df77f77e3d07cc9daa30a1b2941c17f9039ffa3baddf70dce808a071acb22d3fe0b1ecea101f659fd3fcfe7d9f16546273b0236232b7926211894273<contract:0xffffffffffffffffffffffffffffffffffffffff>3c6247f037626ab8de621acb67625b60d5636bd2696273<contract:0xffffffffffffffffffffffffffffffffffffffff>630b2df5d6f1623402af629589806317ef5652f032
    coinbase = pre.deploy_contract(
        code=Op.PUSH24[0x351c4c5a02c8f13fa7c7f5800fa5c9ba2f3b971c13764f9b]
        + Op.PUSH2[0xc2db] + Op.PUSH7[0xc3f909c17e434a]
        + Op.PUSH9[0xd685402956cc341dbf] + Op.PUSH8[0x79516900ed0a1e26]
        + Op.PUSH7[0xdfa40e70f3bcee]
        + Op.PUSH24[0x3c2bffd5b5422a2cf32b19e541f15ae2b6fbe16fd19bbd56]
        + Op.PUSH24[0x28190f83569f036dccd3886aa69c1e685736da06152e3b24]
        + Op.PUSH19[0x8b13546ea1abd48ee47b1b2e1ec70b37fa14cc]
        + Op.PUSH17[0x9d35fce7380230f426455385da80771ffc]
        + Op.PUSH15[0x261f3bfe7bfe7f1827d17b0cf49a7d]
        + Op.PUSH32[0xf8ceb60b6a86ebbb762eb3e4dd1a8a09eaa9a500bc65cbefd4251865b70ca7e2]
        + Op.PUSH7[0x82f1a2bad52a4a] + Op.PUSH10[0x7aa0baf4ebe05130ec6a]
        + Op.PUSH3[0xe66e71] + Op.SWAP14
        + Op.LT(0x682dca6786082a55eda4d65f21e9, 0xb753654f0ff08533f6d088e1)
        + Op.LOG0(offset=0xf77e3d07cc9daa30a1b2941c17f9039ffa3baddf70dce808, size=0x345d12b775ce0f47447731e5eeeff44ca0a946e1df)
        + Op.SLOAD(key=0xacb22d3fe0b1ecea101f659fd3fcfe7d9f16)
        + Op.EXTCODECOPY(address=0x2ebba385bd7f6dde6c57e2d3929a11a1ea0da7e, dest_offset=0x118942, offset=0x32b792, size=0x73b023)
        + Op.CALL(gas=0xb2df5d6, address=0x2ebba385bd7f6dde6c57e2d3929a11a1ea0da7e, value=0x6bd26962, args_offset=0x5b60d5, args_size=0x1acb67, ret_offset=0x6ab8de, ret_size=0x47f037)
        + Op.CREATE(value=0x17ef5652, offset=0x958980, size=0x3402af) + Op.ORIGIN,
        balance=0x532f42c819fa5bed,
        nonce=28,
        address=Address("0x02ebba385bd7f6dde6c57e2d3929a11a1ea0da7e"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=Address("0x0000000000000000000000000000000000000001"),
        data=bytes.fromhex("7300000000000000000000000000000000000000013b7ea30da9ff11bd5f11e4529c93ce4b37d5a256d61e1f1a0ecccb5fbb21fec97f6b3d456b8caaaa84ef30a44fd8779fae5a48354b937835d82d57999d194d4edfbaf0a8dd026d727e3315a53e907b0e1873b4dcb7f806014bc23164e8cc0560256f0c6a8c09c0df2f0f8208ff622bb459d46ffab16ce9d64bcf9cec668338ebbc7f9e64656ae99c617d0dd709c1f78f96bea46e2df76db8418e2b657fc77ff2f979952911a73b767a6ce270c7392d2ff340648610fe0219aaf24df2b26e97e2761497bc6b97dea1269de3aca3b69ec7098a7257114a4a2e22c401ec6319bc2deb70980ebef372a327809b3c2473ab86578d2fccd458e6b99a277c4a1d3e96351fbebe62fe63d300444afd3a9077c20905d2a92b5b2945de6bf9b28d1d42795ca74b029dce6934312994a31fed72e45da26c73c636b40b1f6d529f35488625624a9dfd0b62309f286277b5ab6259b2fd62144722631c4722737300000000000000000000000000000000000000056317345497f13368b2a96595a00933d8dd6dc111a13b90768f330898544a443407620316d3625614816282f1e9622e741d730346ad0b28ea31b7c3d398881dc11ebc97869461631d791a38fa"),  # noqa: E501
        gas_limit=48887,
        value=0xf3107ce3,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0x1000000000000000000000000000000000000000: Account(storage={}, nonce=148),
        sender: Account(storage={}, code=b"", nonce=1),
        addr_0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}, nonce=28),
        coinbase: Account(storage={}, nonce=28),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
