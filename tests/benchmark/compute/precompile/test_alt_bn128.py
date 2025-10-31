"""Benchmark ALT_BN128 precompile."""

import random

import pytest
from execution_testing import (
    Address,
    BenchmarkTestFiller,
    Bytes,
    Fork,
    JumpLoopGenerator,
    Op,
)
from py_ecc.bn128 import G1, G2, multiply

from tests.benchmark.compute.helpers import concatenate_parameters


@pytest.mark.parametrize(
    "precompile_address,calldata",
    [
        pytest.param(
            0x06,
            concatenate_parameters(
                [
                    "18B18ACFB4C2C30276DB5411368E7185B311DD124691610C5D3B74034E093DC9",
                    "063C909C4720840CB5134CB9F59FA749755796819658D32EFC0D288198F37266",
                    "07C2B7F58A84BD6145F00C9C2BC0BB1A187F20FF2C92963A88019E7C6A014EED",
                    "06614E20C147E940F2D70DA3F74C9A17DF361706A4485C742BD6788478FA17D7",
                ]
            ),
            id="bn128_add",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L326
        pytest.param(
            0x06,
            concatenate_parameters(
                [
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                ]
            ),
            id="bn128_add_infinities",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L329
        pytest.param(
            0x06,
            concatenate_parameters(
                [
                    "0000000000000000000000000000000000000000000000000000000000000001",
                    "0000000000000000000000000000000000000000000000000000000000000002",
                    "0000000000000000000000000000000000000000000000000000000000000001",
                    "0000000000000000000000000000000000000000000000000000000000000002",
                ]
            ),
            id="bn128_add_1_2",
        ),
        pytest.param(
            0x07,
            concatenate_parameters(
                [
                    "1A87B0584CE92F4593D161480614F2989035225609F08058CCFA3D0F940FEBE3",
                    "1A2F3C951F6DADCC7EE9007DFF81504B0FCD6D7CF59996EFDC33D92BF7F9F8F6",
                    "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
                ]
            ),
            id="bn128_mul",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L335
        pytest.param(
            0x07,
            concatenate_parameters(
                [
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000002",
                ]
            ),
            id="bn128_mul_infinities_2_scalar",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L338
        pytest.param(
            0x07,
            concatenate_parameters(
                [
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "25f8c89ea3437f44f8fc8b6bfbb6312074dc6f983809a5e809ff4e1d076dd585",
                ]
            ),
            id="bn128_mul_infinities_32_byte_scalar",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L341
        pytest.param(
            0x07,
            concatenate_parameters(
                [
                    "0000000000000000000000000000000000000000000000000000000000000001",
                    "0000000000000000000000000000000000000000000000000000000000000002",
                    "0000000000000000000000000000000000000000000000000000000000000002",
                ]
            ),
            id="bn128_mul_1_2_2_scalar",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L344
        pytest.param(
            0x07,
            concatenate_parameters(
                [
                    "0000000000000000000000000000000000000000000000000000000000000001",
                    "0000000000000000000000000000000000000000000000000000000000000002",
                    "25f8c89ea3437f44f8fc8b6bfbb6312074dc6f983809a5e809ff4e1d076dd585",
                ]
            ),
            id="bn128_mul_1_2_32_byte_scalar",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L347
        pytest.param(
            0x07,
            concatenate_parameters(
                [
                    "089142debb13c461f61523586a60732d8b69c5b38a3380a74da7b2961d867dbf",
                    "2d5fc7bbc013c16d7945f190b232eacc25da675c0eb093fe6b9f1b4b4e107b36",
                    "0000000000000000000000000000000000000000000000000000000000000002",
                ]
            ),
            id="bn128_mul_32_byte_coord_and_2_scalar",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L350
        pytest.param(
            0x07,
            concatenate_parameters(
                [
                    "089142debb13c461f61523586a60732d8b69c5b38a3380a74da7b2961d867dbf",
                    "2d5fc7bbc013c16d7945f190b232eacc25da675c0eb093fe6b9f1b4b4e107b36",
                    "25f8c89ea3437f44f8fc8b6bfbb6312074dc6f983809a5e809ff4e1d076dd585",
                ]
            ),
            id="bn128_mul_32_byte_coord_and_scalar",
        ),
        pytest.param(
            0x08,
            concatenate_parameters(
                [
                    # First pairing
                    "1C76476F4DEF4BB94541D57EBBA1193381FFA7AA76ADA664DD31C16024C43F59",
                    "3034DD2920F673E204FEE2811C678745FC819B55D3E9D294E45C9B03A76AEF41",
                    "209DD15EBFF5D46C4BD888E51A93CF99A7329636C63514396B4A452003A35BF7",
                    "04BF11CA01483BFA8B34B43561848D28905960114C8AC04049AF4B6315A41678",
                    "2BB8324AF6CFC93537A2AD1A445CFD0CA2A71ACD7AC41FADBF933C2A51BE344D",
                    "120A2A4CF30C1BF9845F20C6FE39E07EA2CCE61F0C9BB048165FE5E4DE877550",
                    # Second pairing
                    "111E129F1CF1097710D41C4AC70FCDFA5BA2023C6FF1CBEAC322DE49D1B6DF7C",
                    "103188585E2364128FE25C70558F1560F4F9350BAF3959E603CC91486E110936",
                    "198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2",
                    "1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED",
                    "090689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B",
                    "12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA",
                ]
            ),
            id="bn128_two_pairings",
        ),
        pytest.param(
            0x08,
            concatenate_parameters(
                [
                    # First pairing
                    "1C76476F4DEF4BB94541D57EBBA1193381FFA7AA76ADA664DD31C16024C43F59",
                    "3034DD2920F673E204FEE2811C678745FC819B55D3E9D294E45C9B03A76AEF41",
                    "209DD15EBFF5D46C4BD888E51A93CF99A7329636C63514396B4A452003A35BF7",
                    "04BF11CA01483BFA8B34B43561848D28905960114C8AC04049AF4B6315A41678",
                    "2BB8324AF6CFC93537A2AD1A445CFD0CA2A71ACD7AC41FADBF933C2A51BE344D",
                    "120A2A4CF30C1BF9845F20C6FE39E07EA2CCE61F0C9BB048165FE5E4DE877550",
                ]
            ),
            id="bn128_one_pairing",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L353
        pytest.param(0x08, [], id="ec_pairing_zero_input"),
        pytest.param(
            0x08,
            concatenate_parameters(
                [
                    # First pairing
                    "2cf44499d5d27bb186308b7af7af02ac5bc9eeb6a3d147c186b21fb1b76e18da",
                    "2c0f001f52110ccfe69108924926e45f0b0c868df0e7bde1fe16d3242dc715f6",
                    "1fb19bb476f6b9e44e2a32234da8212f61cd63919354bc06aef31e3cfaff3ebc",
                    "22606845ff186793914e03e21df544c34ffe2f2f3504de8a79d9159eca2d98d9",
                    "2bd368e28381e8eccb5fa81fc26cf3f048eea9abfdd85d7ed3ab3698d63e4f90",
                    "2fe02e47887507adf0ff1743cbac6ba291e66f59be6bd763950bb16041a0a85e",
                    # Second pairing
                    "0000000000000000000000000000000000000000000000000000000000000013",
                    "0644e72e131a029b85045b68181585d97816a916871ca8d3c208c16d87cfd451",
                    "971ff0471b09fa93caaf13cbf443c1aede09cc4328f5a62aad45f40ec133eb40",
                    "91058a3141822985733cbdddfed0fd8d6c104e9e9eff40bf5abfef9ab163bc72",
                    "a23af9a5ce2ba2796c1f4e453a370eb0af8c212d9dc9acd8fc02c2e907baea22",
                    "3a8eb0b0996252cb548a4487da97b02422ebc0e834613f954de6c7e0afdc1fc0",
                ]
            ),
            id="ec_pairing_2_sets",
        ),
        pytest.param(
            0x08,
            concatenate_parameters([""]),
            id="ec_pairing_1_pair",
        ),
        pytest.param(
            0x08,
            concatenate_parameters(
                [
                    # First pairing
                    "2371e7d92e9fc444d0e11526f0752b520318c80be68bf0131704b36b7976572e",
                    "2dca8f05ed5d58e0f2e13c49ae40480c0f99dfcd9268521eea6c81c6387b66c4",
                    "051a93d697db02afd3dcf8414ecb906a114a2bfdb6b06c95d41798d1801b3cbd",
                    "2e275fef7a0bdb0a2aea77d8ec5817e66e199b3d55bc0fa308dcdda74e85060b",
                    "1c7e33c2a72d6e12a31eababad3dbc388525135628102bb64742d9e325f43410",
                    "115dc41fa10b2dbf99036f252ad6f00e8876b22f02cb4738dc4413b22ea9b2df",
                    # Second pairing
                    "09a760ea8f9bd87dc258a949395a03f7d2500c6e72c61f570986328a096b610a",
                    "148027063c072345298117eb2cb980ad79601db31cc69bba6bcbe4937ada6720",
                    "198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2",
                    "1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed",
                    "090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b",
                    "12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
                ]
            ),
            id="ec_pairing_2_pair",
        ),
        pytest.param(
            0x08,
            concatenate_parameters(
                [
                    # First pairing
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "0ef4aac9b7954d5fc6eafae7f4f4c2a732ab05b45f8d50d102cee4973f36eb2c",
                    "23db7d30c99e0a2a7f3bb5cd1f04635aaea58732b58887df93d9239c28230d28",
                    "2bd99d31a5054f2556d226f2e5ef0e075423d8604178b2e2c08006311caee54f",
                    "0f11afb0c6073d12d21b13f4f78210e8ca9a66729206d3fcc2c1b04824c425f2",
                    # Second pairing
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2",
                    "1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed",
                    "090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b",
                    "12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
                    # Third pairing
                    "0000000000000000000000000000000000000000000000000000000000000000",
                    "198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2",
                    "1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed",
                    "090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b",
                    "12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
                ]
            ),
            id="ec_pairing_3_pair",
        ),
        pytest.param(
            0x08,
            concatenate_parameters(
                [
                    # First pairing
                    "24ab69f46f3e3333027d67d51af71571141bd5652b9829157a3c5d1268461984",
                    "0f0e1495665bccf97d627b714e8a49e9c77c21e8d5b383ad7dde7e50040d0f62",
                    "2cab595b9d579f8b82e433249b83ae1d7b62d7073a4f67cb3aeb9b316988907f",
                    "1326d1905ffde0c77e8ebd98257aa239b05ae76c8ec7723ec19bbc8282b0debe",
                    "130502106676b537e01cc356765e91c005d6c4bd1a75f5f6d41d2556c73e56ac",
                    "2dc4cb08068b4aa5f14b7f1096ab35d5c13d78319ec7e66e9f67a1ff20cbbf03",
                    # Second pairing
                    "1459f4140b271cbc8746de9dfcb477d5b72d50ef95bec5fef4a68dd69ddfdb2e",
                    "2c589584551d16a9723b5d356d1ee2066d10381555cdc739e39efca2612fc544",
                    "229ab0abdb0a7d1a5f0d93fb36ce41e12a31ba52fd9e3c27bebce524ab6c4e9b",
                    "00f8756832b244377d06e2d00eeb95ec8096dcfd81f4e4931b50fea23c04a2fe",
                    "29605352ce973ec48d1ab2c8355643c999b70ff771946078b519c556058c3d56",
                    "059a65ae6e0189d4e04a966140aa40f781a1345824a90a91bb035e12ad29af1d",
                    # Third pairing
                    "1459f4140b271cbc8746de9dfcb477d5b72d50ef95bec5fef4a68dd69ddfdb2e",
                    "2c589584551d16a9723b5d356d1ee2066d10381555cdc739e39efca2612fc544",
                    "229ab0abdb0a7d1a5f0d93fb36ce41e12a31ba52fd9e3c27bebce524ab6c4e9b",
                    "00f8756832b244377d06e2d00eeb95ec8096dcfd81f4e4931b50fea23c04a2fe",
                    "29605352ce973ec48d1ab2c8355643c999b70ff771946078b519c556058c3d56",
                    "059a65ae6e0189d4e04a966140aa40f781a1345824a90a91bb035e12ad29af1d",
                    # Fourth pairing
                    "24ab69f46f3e3333027d67d51af71571141bd5652b9829157a3c5d1268461984",
                    "0f0e1495665bccf97d627b714e8a49e9c77c21e8d5b383ad7dde7e50040d0f62",
                    "2cab595b9d579f8b82e433249b83ae1d7b62d7073a4f67cb3aeb9b316988907f",
                    "1326d1905ffde0c77e8ebd98257aa239b05ae76c8ec7723ec19bbc8282b0debe",
                    "130502106676b537e01cc356765e91c005d6c4bd1a75f5f6d41d2556c73e56ac",
                    "2dc4cb08068b4aa5f14b7f1096ab35d5c13d78319ec7e66e9f67a1ff20cbbf03",
                ]
            ),
            id="ec_pairing_4_pair",
        ),
        pytest.param(
            0x08,
            concatenate_parameters(
                [
                    # First pairing
                    "1147057b17237df94a3186435acf66924e1d382b8c935fdd493ceb38c38def73",
                    "03cd046286139915160357ce5b29b9ea28bfb781b71734455d20ef1a64be76ca",
                    "0daa7cc4983cf74c94607519df747f61e317307c449bafb6923f6d6a65299a7e",
                    "1d48db8f275830859fd61370addbc5d5ef3f0ce7491d16918e065f7e3727439d",
                    "1ca8ac2f4a0f540e5505edbe1d15d13899a2a0dfccb012d068134ac66edec625",
                    "2162c315417d1d12c9d7028c5619015391003a9006d4d8979784c7af2c4537a3",
                    # Second pairing
                    "0d221a19ca86dafa8cb804daff78fd3d1bed30aa32e7d4029b1aa69afda2d750",
                    "018628c766a98de1d0cca887a6d90303e68a7729490f25f937b76b57624ba0be",
                    "14550ccf7139312da6fa9eb1259c6365b0bd688a27473ccb42bc5cd6f14c8abd",
                    "165f8721ee9f614382c8c7edb103c941d3a55c1849c9787f34317777d5d9365b",
                    "0d19da7439edb573a1b3e357faade63d5d68b6031771fd911459b7ab0bda9d3f",
                    "25a50a44d10c99c5f107e3b3874f717873cb2d4674699a468204df27c0c50a9a",
                    # Third pairing
                    "0d7136c59b907615e1b45cf730fbfd6cf38b7e126e85e52be804620a23ace4fb",
                    "03e80c29d24ed5cc407329ae093bb1be00f9e3c9332f532bc3658937110d7607",
                    "2129813bd7247065ac58eac42c81e874044e199f48c12aa749a9fe6bb6e4bddc",
                    "1b72b9ab4579283e62445555d5b2921424213d09a776152361c46988b82be8a7",
                    "111bc8198f932e379b8f9825f01af0f5e5cacbf8bfe274bf674f6eaa6e338e04",
                    "259f58d438fd6391e158c991e155966218e6a432703a84068a32543965749857",
                    # Fourth pairing
                    "1ba47a91d487cce77aa78390a295df54d9351637d67810c400415fb374278e3f",
                    "24318bbc05a4e4d779b9498075841c360c6973c1c51dea254281829bbc9aef33",
                    "198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2",
                    "1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed",
                    "090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b",
                    "12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa",
                    # Fifth pairing
                    "1e219772c16eee72450bbf43e9cadae7bf6b2e6ae6637cfeb1d1e8965287acfb",
                    "0347e7bf4245debd3d00b6f51d2d50fd718e6769352f4fe1db0efe492fed2fc3",
                    "24fdcc7d4ed0953e3dad500c7ef9836fc61ded44ba454ec76f0a6d0687f4c1b4",
                    "282b18f7e59c1db4852e622919b2ce9aa5980ca883eac312049c19a3deb79f6d",
                    "0c9d6ce303b7811dd7ea506c8fa124837405bd209b8731bda79a66eb7206277b",
                    "1ac5dac62d2332faa8069faca3b0d27fcdf95d8c8bafc9074ee72b5c1f33aa70",
                ]
            ),
            id="ec_pairing_5_pair",
        ),
        pytest.param(
            0x08,
            concatenate_parameters(
                [
                    "0000000000000000000000000000000000000000000000000000000000000000",
                ]
            ),
            id="ec_pairing_1_pair_empty",
        ),
    ],
)
def test_alt_bn128(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    precompile_address: Address,
    calldata: bytes,
) -> None:
    """Benchmark ALT_BN128 precompile."""
    if precompile_address not in fork.precompiles():
        pytest.skip("Precompile not enabled")

    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS, address=precompile_address, args_size=Op.CALLDATASIZE
        ),
    )

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),
            attack_block=attack_block,
            tx_kwargs={"data": calldata},
        ),
    )


def _generate_bn128_pairs(n: int, seed: int = 0) -> Bytes:
    rng = random.Random(seed)
    calldata = Bytes()

    for _ in range(n):
        priv_key_g1 = rng.randint(1, 2**32 - 1)
        priv_key_g2 = rng.randint(1, 2**32 - 1)

        point_x_affine = multiply(G1, priv_key_g1)
        point_y_affine = multiply(G2, priv_key_g2)

        assert point_x_affine is not None, (
            "G1 multiplication resulted in point at infinity"
        )
        assert point_y_affine is not None, (
            "G2 multiplication resulted in point at infinity"
        )

        g1_x_bytes = point_x_affine[0].n.to_bytes(32, "big")
        g1_y_bytes = point_x_affine[1].n.to_bytes(32, "big")
        g1_serialized = g1_x_bytes + g1_y_bytes

        g2_x_c1_bytes = point_y_affine[0].coeffs[1].n.to_bytes(32, "big")  # type: ignore
        g2_x_c0_bytes = point_y_affine[0].coeffs[0].n.to_bytes(32, "big")  # type: ignore
        g2_y_c1_bytes = point_y_affine[1].coeffs[1].n.to_bytes(32, "big")  # type: ignore
        g2_y_c0_bytes = point_y_affine[1].coeffs[0].n.to_bytes(32, "big")  # type: ignore
        g2_serialized = (
            g2_x_c1_bytes + g2_x_c0_bytes + g2_y_c1_bytes + g2_y_c0_bytes
        )

        pair_calldata = g1_serialized + g2_serialized
        calldata = Bytes(calldata + pair_calldata)

    return calldata


def test_bn128_pairings_amortized(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    gas_benchmark_value: int,
) -> None:
    """Test running a block with as many BN128 pairings as possible."""
    base_cost = 45_000
    pairing_cost = 34_000
    size_per_pairing = 192

    gsc = fork.gas_costs()
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    mem_exp_gas_calculator = fork.memory_expansion_gas_calculator()

    # This is a theoretical maximum number of pairings that can be done in a
    # block. It is only used for an upper bound for calculating the optimal
    # number of pairings below.
    maximum_number_of_pairings = (
        gas_benchmark_value - base_cost
    ) // pairing_cost

    # Discover the optimal number of pairings balancing two dimensions:
    # 1. Amortize the precompile base cost as much as possible.
    # 2. The cost of the memory expansion.
    max_pairings = 0
    optimal_per_call_num_pairings = 0
    for i in range(1, maximum_number_of_pairings + 1):
        # We'll pass all pairing arguments via calldata.
        available_gas_after_intrinsic = (
            gas_benchmark_value
            - intrinsic_gas_calculator(
                calldata=[0xFF]
                * size_per_pairing
                * i  # 0xFF is to indicate non-
                # zero bytes.
            )
        )
        available_gas_after_expansion = max(
            0,
            available_gas_after_intrinsic
            - mem_exp_gas_calculator(new_bytes=i * size_per_pairing),
        )

        # This is ignoring "glue" opcodes, but helps to have a rough idea of
        # the right cutting point.
        approx_gas_cost_per_call = (
            gsc.G_WARM_ACCOUNT_ACCESS + base_cost + i * pairing_cost
        )

        num_precompile_calls = (
            available_gas_after_expansion // approx_gas_cost_per_call
        )
        num_pairings_done = num_precompile_calls * i  # Each precompile call
        # does i pairings.

        if num_pairings_done > max_pairings:
            max_pairings = num_pairings_done
            optimal_per_call_num_pairings = i

    setup = Op.CALLDATACOPY(size=Op.CALLDATASIZE)
    attack_block = Op.POP(
        Op.STATICCALL(Op.GAS, 0x08, 0, Op.CALLDATASIZE, 0, 0)
    )

    benchmark_test(
        code_generator=JumpLoopGenerator(
            setup=setup,
            attack_block=attack_block,
            tx_kwargs={
                "data": _generate_bn128_pairs(
                    optimal_per_call_num_pairings, 42
                )
            },
        ),
    )
