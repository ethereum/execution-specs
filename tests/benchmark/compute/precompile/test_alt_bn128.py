"""Benchmark ALT_BN128 precompile."""

import math
import random

import pytest
from execution_testing import (
    Address,
    Alloc,
    BenchmarkTestFiller,
    Block,
    Bytes,
    Fork,
    JumpLoopGenerator,
    Op,
    OpcodeTarget,
    Transaction,
    While,
    WhileGas,
)
from py_ecc.bn128 import G1, G2, multiply
from py_ecc.fields import bn128_FQ2

from tests.benchmark.helper.precompile import Precompile
from tests.byzantium.eip196_ec_add_mul.spec import (
    PointG1,
    Scalar,
)
from tests.byzantium.eip196_ec_add_mul.spec import (
    Spec as EIP196Spec,
)
from tests.byzantium.eip197_ec_pairing.spec import (
    PointG2,
)
from tests.byzantium.eip197_ec_pairing.spec import (
    Spec as EIP197Spec,
)


@pytest.mark.parametrize(
    "precompile_address,calldata,target",
    [
        pytest.param(
            EIP196Spec.ECADD,
            PointG1(
                x=0x18B18ACFB4C2C30276DB5411368E7185B311DD124691610C5D3B74034E093DC9,
                y=0x063C909C4720840CB5134CB9F59FA749755796819658D32EFC0D288198F37266,
            )
            + PointG1(
                x=0x07C2B7F58A84BD6145F00C9C2BC0BB1A187F20FF2C92963A88019E7C6A014EED,
                y=0x06614E20C147E940F2D70DA3F74C9A17DF361706A4485C742BD6788478FA17D7,
            ),
            Precompile.BN128_ADD,
            id="bn128_add",
            marks=pytest.mark.repricing,
        ),
        pytest.param(
            EIP196Spec.ECADD,
            PointG1(
                x=0x18B18ACFB4C2C30276DB5411368E7185B311DD124691610C5D3B74034E093DC9,
                y=0x063C909C4720840CB5134CB9F59FA749755796819658D32EFC0D288198F37266,
            )
            + PointG1(
                x=0x18B18ACFB4C2C30276DB5411368E7185B311DD124691610C5D3B74034E093DC9,
                y=0x063C909C4720840CB5134CB9F59FA749755796819658D32EFC0D288198F37266,
            ),
            Precompile.BN128_ADD,
            id="bn128_double",
            marks=pytest.mark.repricing,
        ),
        # Second point is the negative of the first one
        pytest.param(
            EIP196Spec.ECADD,
            PointG1(
                x=0x18B18ACFB4C2C30276DB5411368E7185B311DD124691610C5D3B74034E093DC9,
                y=0x063C909C4720840CB5134CB9F59FA749755796819658D32EFC0D288198F37266,
            )
            + PointG1(
                x=0x18B18ACFB4C2C30276DB5411368E7185B311DD124691610C5D3B74034E093DC9,
                y=0x2A27BDD69A111C1D033CF8FC8BE1B1142229D40FD218F75E401363953F898AE1,
            ),
            Precompile.BN128_ADD,
            id="bn128_add_negative",
            marks=pytest.mark.repricing,
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L326
        pytest.param(
            EIP196Spec.ECADD,
            EIP196Spec.INF_G1 + EIP196Spec.INF_G1,
            Precompile.BN128_ADD,
            id="bn128_add_infinities",
            marks=pytest.mark.repricing,
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L329
        pytest.param(
            EIP196Spec.ECADD,
            EIP196Spec.G1 + EIP196Spec.G1,
            Precompile.BN128_ADD,
            id="bn128_add_1_2",
        ),
        pytest.param(
            EIP196Spec.ECMUL,
            PointG1(
                x=0x1A87B0584CE92F4593D161480614F2989035225609F08058CCFA3D0F940FEBE3,
                y=0x1A2F3C951F6DADCC7EE9007DFF81504B0FCD6D7CF59996EFDC33D92BF7F9F8F6,
            )
            + Scalar(
                x=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
            ),
            Precompile.BN128_MUL,
            id="bn128_mul",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L335
        pytest.param(
            EIP196Spec.ECMUL,
            EIP196Spec.INF_G1 + Scalar(x=2),
            Precompile.BN128_MUL,
            id="bn128_mul_infinities_2_scalar",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L338
        pytest.param(
            EIP196Spec.ECMUL,
            EIP196Spec.INF_G1
            + Scalar(
                x=0x25F8C89EA3437F44F8FC8B6BFBB6312074DC6F983809A5E809FF4E1D076DD585
            ),
            Precompile.BN128_MUL,
            id="bn128_mul_infinities_32_byte_scalar",
            marks=pytest.mark.repricing,
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L341
        pytest.param(
            EIP196Spec.ECMUL,
            EIP196Spec.G1 + Scalar(x=2),
            Precompile.BN128_MUL,
            id="bn128_mul_1_2_2_scalar",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L344
        pytest.param(
            EIP196Spec.ECMUL,
            EIP196Spec.G1
            + Scalar(
                x=0x25F8C89EA3437F44F8FC8B6BFBB6312074DC6F983809A5E809FF4E1D076DD585
            ),
            Precompile.BN128_MUL,
            id="bn128_mul_1_2_32_byte_scalar",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L347
        pytest.param(
            EIP196Spec.ECMUL,
            PointG1(
                x=0x089142DEBB13C461F61523586A60732D8B69C5B38A3380A74DA7B2961D867DBF,
                y=0x2D5FC7BBC013C16D7945F190B232EACC25DA675C0EB093FE6B9F1B4B4E107B36,
            )
            + Scalar(x=2),
            Precompile.BN128_MUL,
            id="bn128_mul_32_byte_coord_and_2_scalar",
            marks=pytest.mark.repricing,
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L350
        pytest.param(
            EIP196Spec.ECMUL,
            PointG1(
                x=0x089142DEBB13C461F61523586A60732D8B69C5B38A3380A74DA7B2961D867DBF,
                y=0x2D5FC7BBC013C16D7945F190B232EACC25DA675C0EB093FE6B9F1B4B4E107B36,
            )
            + Scalar(
                x=0x25F8C89EA3437F44F8FC8B6BFBB6312074DC6F983809A5E809FF4E1D076DD585
            ),
            Precompile.BN128_MUL,
            id="bn128_mul_32_byte_coord_and_scalar",
            marks=pytest.mark.repricing,
        ),
        # Pairing inputs below are py_ecc-generated (not external vectors),
        # so every point is on-curve and in the prime-order subgroup: each
        # G1 is k*G1, each G2 is k*G2 with FQ2 coeffs swapped to the
        # precompile's (imag, real) decode order. Scalars are small and
        # arbitrary - 1_pair (3, 5); 2_sets adds (7, 11); 3_pair (2,3),
        # (5,7), (11,13); 1_pair_empty is one 192-byte (inf, inf) pair.
        pytest.param(
            EIP197Spec.ECPAIRING,
            # First pairing
            PointG1(
                x=0x1C76476F4DEF4BB94541D57EBBA1193381FFA7AA76ADA664DD31C16024C43F59,
                y=0x3034DD2920F673E204FEE2811C678745FC819B55D3E9D294E45C9B03A76AEF41,
            )
            + PointG2(
                x=(
                    0x209DD15EBFF5D46C4BD888E51A93CF99A7329636C63514396B4A452003A35BF7,
                    0x04BF11CA01483BFA8B34B43561848D28905960114C8AC04049AF4B6315A41678,
                ),
                y=(
                    0x2BB8324AF6CFC93537A2AD1A445CFD0CA2A71ACD7AC41FADBF933C2A51BE344D,
                    0x120A2A4CF30C1BF9845F20C6FE39E07EA2CCE61F0C9BB048165FE5E4DE877550,
                ),
            )
            # Second pairing
            + PointG1(
                x=0x111E129F1CF1097710D41C4AC70FCDFA5BA2023C6FF1CBEAC322DE49D1B6DF7C,
                y=0x103188585E2364128FE25C70558F1560F4F9350BAF3959E603CC91486E110936,
            )
            + EIP197Spec.G2,
            Precompile.BN128_PAIRING,
            id="bn128_two_pairings",
        ),
        pytest.param(
            EIP197Spec.ECPAIRING,
            PointG1(
                x=0x1C76476F4DEF4BB94541D57EBBA1193381FFA7AA76ADA664DD31C16024C43F59,
                y=0x3034DD2920F673E204FEE2811C678745FC819B55D3E9D294E45C9B03A76AEF41,
            )
            + PointG2(
                x=(
                    0x209DD15EBFF5D46C4BD888E51A93CF99A7329636C63514396B4A452003A35BF7,
                    0x04BF11CA01483BFA8B34B43561848D28905960114C8AC04049AF4B6315A41678,
                ),
                y=(
                    0x2BB8324AF6CFC93537A2AD1A445CFD0CA2A71ACD7AC41FADBF933C2A51BE344D,
                    0x120A2A4CF30C1BF9845F20C6FE39E07EA2CCE61F0C9BB048165FE5E4DE877550,
                ),
            ),
            Precompile.BN128_PAIRING,
            id="bn128_one_pairing",
        ),
        # Ported from
        # https://github.com/NethermindEth/nethermind/blob/ceb8d57b8530ce8181d7427c115ca593386909d6/tools/EngineRequestsGenerator/TestCase.cs#L353
        pytest.param(
            EIP197Spec.ECPAIRING,
            [],
            Precompile.BN128_PAIRING,
            id="ec_pairing_zero_input",
        ),
        pytest.param(
            EIP197Spec.ECPAIRING,
            # First pairing
            PointG1(
                x=0x2CF44499D5D27BB186308B7AF7AF02AC5BC9EEB6A3D147C186B21FB1B76E18DA,
                y=0x2C0F001F52110CCFE69108924926E45F0B0C868DF0E7BDE1FE16D3242DC715F6,
            )
            + PointG2(
                x=(
                    0x1FB19BB476F6B9E44E2A32234DA8212F61CD63919354BC06AEF31E3CFAFF3EBC,
                    0x22606845FF186793914E03E21DF544C34FFE2F2F3504DE8A79D9159ECA2D98D9,
                ),
                y=(
                    0x2BD368E28381E8ECCB5FA81FC26CF3F048EEA9ABFDD85D7ED3AB3698D63E4F90,
                    0x2FE02E47887507ADF0FF1743CBAC6BA291E66F59BE6BD763950BB16041A0A85E,
                ),
            )
            # Second pairing
            + PointG1(
                x=0x17072B2ED3BB8D759A5325F477629386CB6FC6ECB801BD76983A6B86ABFFE078,
                y=0x168ADA6CD130DD52017BB54BFA19377AADFE3BF05D18F41B77809F7F60D4AF9E,
            )
            + PointG2(
                x=(
                    0x228B515A17F28B89920873207477F8C7FC05582DEBAF3184FEBF1CFDEDC5CE88,
                    0x12BB1156A9F6B360FCB2614E15D8A3FF07F2C699DC69CA830B20D2DF91FE9CD3,
                ),
                y=(
                    0x2B15DC62A5C9E36597914DDBBFDE48806A8EABE45C8D3CCCF9578AD08E058F92,
                    0x02A4FD764F52470E2FCFFF325FB9692F55D6B8B077EEFEAA04E07152B4D1FA94,
                ),
            ),
            Precompile.BN128_PAIRING,
            id="ec_pairing_2_sets",
        ),
        pytest.param(
            EIP197Spec.ECPAIRING,
            PointG1(
                x=0x0769BF9AC56BEA3FF40232BCB1B6BD159315D84715B8E679F2D355961915ABF0,
                y=0x2AB799BEE0489429554FDB7C8D086475319E63B40B9C5B57CDF1FF3DD9FE2261,
            )
            + PointG2(
                x=(
                    0x0A09CCF561B55FD99D1C1208DEE1162457B57AC5AF3759D50671E510E428B2A1,
                    0x2E539C423B302D13F4E5773C603948EAF5DB5DF8AE8A9A9113708390A06410D8,
                ),
                y=(
                    0x19B763513924A736E4EEBD0D78C91C1BC1D657FEE4214057D21414011CFCC763,
                    0x2F8D9F9AB83727C77A2FEC063CB7B6E5EB23044CCF535AD49D46D394FB6F6BF6,
                ),
            ),
            Precompile.BN128_PAIRING,
            id="ec_pairing_1_pair",
        ),
        pytest.param(
            EIP197Spec.ECPAIRING,
            # First pairing
            PointG1(
                x=0x2371E7D92E9FC444D0E11526F0752B520318C80BE68BF0131704B36B7976572E,
                y=0x2DCA8F05ED5D58E0F2E13C49AE40480C0F99DFCD9268521EEA6C81C6387B66C4,
            )
            + PointG2(
                x=(
                    0x051A93D697DB02AFD3DCF8414ECB906A114A2BFDB6B06C95D41798D1801B3CBD,
                    0x2E275FEF7A0BDB0A2AEA77D8EC5817E66E199B3D55BC0FA308DCDDA74E85060B,
                ),
                y=(
                    0x1C7E33C2A72D6E12A31EABABAD3DBC388525135628102BB64742D9E325F43410,
                    0x115DC41FA10B2DBF99036F252AD6F00E8876B22F02CB4738DC4413B22EA9B2DF,
                ),
            )
            # Second pairing: G2 generator
            + PointG1(
                x=0x09A760EA8F9BD87DC258A949395A03F7D2500C6E72C61F570986328A096B610A,
                y=0x148027063C072345298117EB2CB980AD79601DB31CC69BBA6BCBE4937ADA6720,
            )
            + EIP197Spec.G2,
            Precompile.BN128_PAIRING,
            id="ec_pairing_2_pair",
        ),
        pytest.param(
            EIP197Spec.ECPAIRING,
            # First pairing
            PointG1(
                x=0x030644E72E131A029B85045B68181585D97816A916871CA8D3C208C16D87CFD3,
                y=0x15ED738C0E0A7C92E7845F96B2AE9C0A68A6A449E3538FC7FF3EBF7A5A18A2C4,
            )
            + PointG2(
                x=(
                    0x1014772F57BB9742735191CD5DCFE4EBBC04156B6878A0A7C9824F32FFB66E85,
                    0x06064E784DB10E9051E52826E192715E8D7E478CB09A5E0012DEFA0694FBC7F5,
                ),
                y=(
                    0x021E2335F3354BB7922FFCC2F38D3323DD9453AC49B55441452AEACA147711B2,
                    0x058E1D5681B5B9E0074B0F9C8D2C68A069B920D74521E79765036D57666C5597,
                ),
            )
            # Second pairing
            + PointG1(
                x=0x17C139DF0EFEE0F766BC0204762B774362E4DED88953A39CE849A8A7FA163FA9,
                y=0x01E0559BACB160664764A357AF8A9FE70BAA9258E0B959273FFC5718C6D4CC7C,
            )
            + PointG2(
                x=(
                    0x2903BA015A9ABDE26A5D081E84551E63BE0FD4516E46EE6D593EDEBA46362455,
                    0x224BDC5D4327FCF8ED702E01DE1C2F1657A253BA75E32A89C390142AAA28B308,
                ),
                y=(
                    0x03C8B7CDA6B2DEDB7AEEAF5FDA464AD17036BEA1C4E6F7ADBAED1EBE0335E0D8,
                    0x1D92FFF52A265017EECCB372E37D7A7BD431800ECA28DFD82E21E8054114233F,
                ),
            )
            # Third pairing
            + PointG1(
                x=0x2A14705537B009189DA8808651EECDB82482477FE92AC12CA8B71F80FC3D49EF,
                y=0x2DF7EE7F243EA8B38E1DDF14029258877A618C779FD4717DB6177E19EA67EC38,
            )
            + PointG2(
                x=(
                    0x009EDAF0698A8C56F51139588ACC094CEE3C37D427BB6D2EAB830AAE529097D1,
                    0x23AD66F3A7CCA9DC75049635FAEBD124316244B91DE5FB2764CD151572A905F7,
                ),
                y=(
                    0x2700E8A29B7BB45F3022A18A07BDC66D0254559E17CCE64E3B4AD21578FCF410,
                    0x1AD4F87D3B4375A39988AC099B042B1E7C0C715678E4C2BEA8905F607CF950F8,
                ),
            ),
            Precompile.BN128_PAIRING,
            id="ec_pairing_3_pair",
        ),
        pytest.param(
            EIP197Spec.ECPAIRING,
            (
                PointG1(
                    x=0x24AB69F46F3E3333027D67D51AF71571141BD5652B9829157A3C5D1268461984,
                    y=0x0F0E1495665BCCF97D627B714E8A49E9C77C21E8D5B383AD7DDE7E50040D0F62,
                )
                + PointG2(
                    x=(
                        0x2CAB595B9D579F8B82E433249B83AE1D7B62D7073A4F67CB3AEB9B316988907F,
                        0x1326D1905FFDE0C77E8EBD98257AA239B05AE76C8EC7723EC19BBC8282B0DEBE,
                    ),
                    y=(
                        0x130502106676B537E01CC356765E91C005D6C4BD1A75F5F6D41D2556C73E56AC,
                        0x2DC4CB08068B4AA5F14B7F1096AB35D5C13D78319EC7E66E9F67A1FF20CBBF03,
                    ),
                )
            )
            + (
                PointG1(
                    x=0x1459F4140B271CBC8746DE9DFCB477D5B72D50EF95BEC5FEF4A68DD69DDFDB2E,
                    y=0x2C589584551D16A9723B5D356D1EE2066D10381555CDC739E39EFCA2612FC544,
                )
                + PointG2(
                    x=(
                        0x229AB0ABDB0A7D1A5F0D93FB36CE41E12A31BA52FD9E3C27BEBCE524AB6C4E9B,
                        0x00F8756832B244377D06E2D00EEB95EC8096DCFD81F4E4931B50FEA23C04A2FE,
                    ),
                    y=(
                        0x29605352CE973EC48D1AB2C8355643C999B70FF771946078B519C556058C3D56,
                        0x059A65AE6E0189D4E04A966140AA40F781A1345824A90A91BB035E12AD29AF1D,
                    ),
                )
            )
            + (
                PointG1(
                    x=0x1459F4140B271CBC8746DE9DFCB477D5B72D50EF95BEC5FEF4A68DD69DDFDB2E,
                    y=0x2C589584551D16A9723B5D356D1EE2066D10381555CDC739E39EFCA2612FC544,
                )
                + PointG2(
                    x=(
                        0x229AB0ABDB0A7D1A5F0D93FB36CE41E12A31BA52FD9E3C27BEBCE524AB6C4E9B,
                        0x00F8756832B244377D06E2D00EEB95EC8096DCFD81F4E4931B50FEA23C04A2FE,
                    ),
                    y=(
                        0x29605352CE973EC48D1AB2C8355643C999B70FF771946078B519C556058C3D56,
                        0x059A65AE6E0189D4E04A966140AA40F781A1345824A90A91BB035E12AD29AF1D,
                    ),
                )
            )
            + (
                PointG1(
                    x=0x24AB69F46F3E3333027D67D51AF71571141BD5652B9829157A3C5D1268461984,
                    y=0x0F0E1495665BCCF97D627B714E8A49E9C77C21E8D5B383AD7DDE7E50040D0F62,
                )
                + PointG2(
                    x=(
                        0x2CAB595B9D579F8B82E433249B83AE1D7B62D7073A4F67CB3AEB9B316988907F,
                        0x1326D1905FFDE0C77E8EBD98257AA239B05AE76C8EC7723EC19BBC8282B0DEBE,
                    ),
                    y=(
                        0x130502106676B537E01CC356765E91C005D6C4BD1A75F5F6D41D2556C73E56AC,
                        0x2DC4CB08068B4AA5F14B7F1096AB35D5C13D78319EC7E66E9F67A1FF20CBBF03,
                    ),
                )
            ),
            Precompile.BN128_PAIRING,
            id="ec_pairing_4_pair",
        ),
        pytest.param(
            EIP197Spec.ECPAIRING,
            # First pairing
            PointG1(
                x=0x1147057B17237DF94A3186435ACF66924E1D382B8C935FDD493CEB38C38DEF73,
                y=0x03CD046286139915160357CE5B29B9EA28BFB781B71734455D20EF1A64BE76CA,
            )
            + PointG2(
                x=(
                    0x0DAA7CC4983CF74C94607519DF747F61E317307C449BAFB6923F6D6A65299A7E,
                    0x1D48DB8F275830859FD61370ADDBC5D5EF3F0CE7491D16918E065F7E3727439D,
                ),
                y=(
                    0x1CA8AC2F4A0F540E5505EDBE1D15D13899A2A0DFCCB012D068134AC66EDEC625,
                    0x2162C315417D1D12C9D7028C5619015391003A9006D4D8979784C7AF2C4537A3,
                ),
            )
            # Second pairing
            + PointG1(
                x=0x0D221A19CA86DAFA8CB804DAFF78FD3D1BED30AA32E7D4029B1AA69AFDA2D750,
                y=0x018628C766A98DE1D0CCA887A6D90303E68A7729490F25F937B76B57624BA0BE,
            )
            + PointG2(
                x=(
                    0x14550CCF7139312DA6FA9EB1259C6365B0BD688A27473CCB42BC5CD6F14C8ABD,
                    0x165F8721EE9F614382C8C7EDB103C941D3A55C1849C9787F34317777D5D9365B,
                ),
                y=(
                    0x0D19DA7439EDB573A1B3E357FAADE63D5D68B6031771FD911459B7AB0BDA9D3F,
                    0x25A50A44D10C99C5F107E3B3874F717873CB2D4674699A468204DF27C0C50A9A,
                ),
            )
            # Third pairing
            + PointG1(
                x=0x0D7136C59B907615E1B45CF730FBFD6CF38B7E126E85E52BE804620A23ACE4FB,
                y=0x03E80C29D24ED5CC407329AE093BB1BE00F9E3C9332F532BC3658937110D7607,
            )
            + PointG2(
                x=(
                    0x2129813BD7247065AC58EAC42C81E874044E199F48C12AA749A9FE6BB6E4BDDC,
                    0x1B72B9AB4579283E62445555D5B2921424213D09A776152361C46988B82BE8A7,
                ),
                y=(
                    0x111BC8198F932E379B8F9825F01AF0F5E5CACBF8BFE274BF674F6EAA6E338E04,
                    0x259F58D438FD6391E158C991E155966218E6A432703A84068A32543965749857,
                ),
            )
            # Fourth pairing: G2 generator
            + PointG1(
                x=0x1BA47A91D487CCE77AA78390A295DF54D9351637D67810C400415FB374278E3F,
                y=0x24318BBC05A4E4D779B9498075841C360C6973C1C51DEA254281829BBC9AEF33,
            )
            + EIP197Spec.G2
            # Fifth pairing
            + PointG1(
                x=0x1E219772C16EEE72450BBF43E9CADAE7BF6B2E6AE6637CFEB1D1E8965287ACFB,
                y=0x0347E7BF4245DEBD3D00B6F51D2D50FD718E6769352F4FE1DB0EFE492FED2FC3,
            )
            + PointG2(
                x=(
                    0x24FDCC7D4ED0953E3DAD500C7EF9836FC61DED44BA454EC76F0A6D0687F4C1B4,
                    0x282B18F7E59C1DB4852E622919B2CE9AA5980CA883EAC312049C19A3DEB79F6D,
                ),
                y=(
                    0x0C9D6CE303B7811DD7EA506C8FA124837405BD209B8731BDA79A66EB7206277B,
                    0x1AC5DAC62D2332FAA8069FACA3B0D27FCDF95D8C8BAFC9074EE72B5C1F33AA70,
                ),
            ),
            Precompile.BN128_PAIRING,
            id="ec_pairing_5_pair",
        ),
        pytest.param(
            EIP197Spec.ECPAIRING,
            # One correctly sized (192-byte) pair of infinity points: the
            # minimal input the precompile still accepts and charges a full
            # pair for. bytes(32) would be rejected as a bad length.
            bytes(192),
            Precompile.BN128_PAIRING,
            id="ec_pairing_1_pair_empty",
        ),
    ],
)
def test_alt_bn128(
    benchmark_test: BenchmarkTestFiller,
    precompile_address: Address,
    calldata: bytes,
    target: OpcodeTarget,
) -> None:
    """Benchmark ALT_BN128 precompile."""
    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS, address=precompile_address, args_size=Op.CALLDATASIZE
        ),
    )

    benchmark_test(
        target_opcode=target,
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
        assert isinstance(point_y_affine[0], bn128_FQ2)
        assert isinstance(point_y_affine[1], bn128_FQ2)

        g1 = PointG1(
            x=point_x_affine[0].n,
            y=point_x_affine[1].n,
        )
        g2 = PointG2(
            x=(
                int(point_y_affine[0].coeffs[1]),
                int(point_y_affine[0].coeffs[0]),
            ),
            y=(
                int(point_y_affine[1].coeffs[1]),
                int(point_y_affine[1].coeffs[0]),
            ),
        )

        calldata = Bytes(calldata + g1 + g2)

    return calldata


def test_bn128_pairings_amortized(
    benchmark_test: BenchmarkTestFiller,
    fork: Fork,
    tx_gas_limit: int,
) -> None:
    """Test running a block with as many BN128 pairings as possible."""
    size_per_pairing = 192

    gsc = fork.gas_costs()
    base_cost = gsc.PRECOMPILE_ECPAIRING_BASE
    pairing_cost = gsc.PRECOMPILE_ECPAIRING_PER_POINT
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    mem_exp_gas_calculator = fork.memory_expansion_gas_calculator()
    warm_account_access_cost = Op.STATICCALL(
        gas=Op.GAS,
        address=Op.PUSH20(0),
        args_offset=Op.PUSH0,
        args_size=Op.PUSH0,
        ret_offset=Op.PUSH0,
        ret_size=Op.PUSH0,
        # gas accounting
        address_warm=True,
    ).gas_cost(fork)

    # This is a theoretical maximum number of pairings that can be done in a
    # block. It is only used for an upper bound for calculating the optimal
    # number of pairings below.
    maximum_number_of_pairings = (tx_gas_limit - base_cost) // pairing_cost

    # Discover the optimal number of pairings balancing two dimensions:
    # 1. Amortize the precompile base cost as much as possible.
    # 2. The cost of the memory expansion.
    max_pairings = 0
    optimal_per_call_num_pairings = 0
    for i in range(1, maximum_number_of_pairings + 1):
        # We'll pass all pairing arguments via calldata.
        available_gas_after_intrinsic = (
            tx_gas_limit
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

        approx_gas_cost_per_call = (
            warm_account_access_cost + base_cost + i * pairing_cost
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
        Op.STATICCALL(Op.GAS, EIP197Spec.ECPAIRING, 0, Op.CALLDATASIZE, 0, 0)
    )

    benchmark_test(
        target_opcode=Precompile.BN128_PAIRING,
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


@pytest.mark.repricing
@pytest.mark.parametrize("num_pairs", [1, 3, 6, 12, 24])
def test_alt_bn128_benchmark(
    benchmark_test: BenchmarkTestFiller,
    num_pairs: int,
) -> None:
    """Benchmark BN128 pairings precompile with varying number of pairs."""
    calldata = _generate_bn128_pairs(num_pairs, seed=42)

    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS,
            address=EIP197Spec.ECPAIRING,
            args_size=Op.CALLDATASIZE,
        ),
    )

    benchmark_test(
        target_opcode=Precompile.BN128_PAIRING,
        code_generator=JumpLoopGenerator(
            setup=Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE),
            attack_block=attack_block,
            tx_kwargs={"data": calldata},
        ),
    )


@pytest.mark.repricing
@pytest.mark.parametrize("num_pairs", [1, 3, 6, 12, 24])
def test_ec_pairing(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    num_pairs: int,
) -> None:
    """Benchmark ecpairing precompile with unique inputs per call."""
    pair_size = num_pairs * 192
    gsc = fork.gas_costs()
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    mem_exp = fork.memory_expansion_gas_calculator()
    precompile_cost = (
        gsc.PRECOMPILE_ECPAIRING_BASE
        + gsc.PRECOMPILE_ECPAIRING_PER_POINT * num_pairs
    )

    # Each iteration: STATICCALL ecpairing at advancing calldata offset,
    # then advance offset by pair_size at memory[CALLDATASIZE].
    # The loop condition checks remaining gas against one body execution.
    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS,
            address=EIP197Spec.ECPAIRING,
            args_offset=Op.MLOAD(Op.CALLDATASIZE),
            args_size=pair_size,
            # gas accounting
            address_warm=True,
            inner_call_cost=precompile_cost,
        ),
    ) + Op.MSTORE(
        Op.CALLDATASIZE,
        Op.ADD(Op.MLOAD(Op.CALLDATASIZE), pair_size),
    )

    setup = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
    loop = While(
        body=attack_block,
        condition=Op.GT(Op.CALLDATASIZE, Op.MLOAD(Op.CALLDATASIZE)),
    )
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    iteration_cost = loop.gas_cost(fork)
    setup_cost = setup.gas_cost(fork)

    # Conservative per-variant estimate for sizing the calldata:
    # one loop iteration + worst-case calldata intrinsic (all non-zero)
    # + CALLDATACOPY copy and linear memory expansion.
    words_per_variant = math.ceil(pair_size / 32)
    per_variant_gas = (
        iteration_cost
        + pair_size * 16
        + words_per_variant * (gsc.OPCODE_COPY_PER_WORD + gsc.MEMORY_PER_WORD)
    )
    empty_intrinsic = intrinsic_gas_calculator(
        calldata=[], return_cost_deducted_prior_execution=True
    )
    fixed_overhead = empty_intrinsic + setup_cost + mem_exp(new_bytes=32)

    seed_offset = 0
    txs: list[Transaction] = []
    remaining_gas = gas_benchmark_value

    expected_opcode_count = 0
    while remaining_gas > 0:
        per_tx_gas = min(tx_gas_limit, remaining_gas)
        per_tx_variants = max(
            1, (per_tx_gas - fixed_overhead) // per_variant_gas
        )
        calldata = Bytes(
            b"".join(
                _generate_bn128_pairs(num_pairs, seed=42 + seed_offset + i)
                for i in range(per_tx_variants)
            )
        )

        execution_intrinsic = intrinsic_gas_calculator(
            calldata=calldata,
            return_cost_deducted_prior_execution=True,
        )
        gas_for_loop = (
            per_tx_gas
            - execution_intrinsic
            - setup_cost
            - math.ceil(len(calldata) / 32) * gsc.OPCODE_COPY_PER_WORD
            - mem_exp(new_bytes=len(calldata) + 32)
        )

        if gas_for_loop < per_tx_variants * iteration_cost:
            break
        expected_opcode_count += per_tx_variants

        txs.append(
            Transaction(
                to=attack_contract_address,
                sender=pre.fund_eoa(),
                gas_limit=per_tx_gas,
                data=calldata,
            )
        )
        remaining_gas -= per_tx_gas
        seed_offset += per_tx_variants

    assert len(txs) != 0, "No transactions were added to the test."

    benchmark_test(
        target_opcode=Precompile.BN128_PAIRING,
        skip_gas_used_validation=True,
        expected_receipt_status=1,
        expected_opcode_count=expected_opcode_count,
        blocks=[Block(txs=txs)],
    )


def _generate_g1_point(seed: int) -> Bytes:
    """Generate a valid random G1 point from a deterministic seed."""
    rng = random.Random(seed)
    priv_key = rng.randint(1, 2**32 - 1)
    point = multiply(G1, priv_key)
    assert point is not None
    return Bytes(PointG1(x=point[0].n, y=point[1].n))


@pytest.mark.repricing
@pytest.mark.parametrize(
    "precompile_address,scalar,target",
    [
        pytest.param(
            EIP196Spec.ECADD, None, Precompile.BN128_ADD, id="ec_add"
        ),
        pytest.param(
            EIP196Spec.ECMUL,
            2,
            Precompile.BN128_MUL,
            id="ec_mul_small_scalar",
        ),
        pytest.param(
            EIP196Spec.ECMUL,
            2**256 - 1,
            Precompile.BN128_MUL,
            id="ec_mul_max_scalar",
        ),
    ],
)
def test_alt_bn128_uncachable(
    benchmark_test: BenchmarkTestFiller,
    pre: Alloc,
    fork: Fork,
    gas_benchmark_value: int,
    tx_gas_limit: int,
    precompile_address: Address,
    scalar: int | None,
    target: OpcodeTarget,
) -> None:
    """
    Benchmark ecAdd/ecMul with unique input per call.

    Write the precompile's G1 output (64 bytes) back over the
    input point so each loop iteration receives a distinct
    input, avoiding precompile result caching in clients.
    """
    intrinsic_gas_calculator = fork.transaction_intrinsic_cost_calculator()
    gsc = fork.gas_costs()
    precompile_cost = (
        gsc.PRECOMPILE_ECMUL
        if precompile_address == EIP196Spec.ECMUL
        else gsc.PRECOMPILE_ECADD
    )
    attack_block = Op.POP(
        Op.STATICCALL(
            gas=Op.GAS,
            address=precompile_address,
            args_size=Op.CALLDATASIZE,
            # One G1 point (2 * 32 bytes), overwrites the input point
            # so each iteration has unique precompile input.
            ret_size=64,
            # gas accounting
            address_warm=True,
            inner_call_cost=precompile_cost,
        ),
    )

    setup = Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE)
    loop = WhileGas(body=attack_block, fork=fork)
    code = setup + loop
    attack_contract_address = pre.deploy_contract(code=code)

    txs: list[Transaction] = []
    remaining_gas = gas_benchmark_value

    seed = 0
    expected_opcode_count = 0
    while remaining_gas > 0:
        gas_available = min(tx_gas_limit, remaining_gas)

        calldata = Bytes(
            _generate_g1_point(seed) + _generate_g1_point(seed + 1000)
            if scalar is None
            else _generate_g1_point(seed) + scalar.to_bytes(32, "big")
        )

        intrinsic = intrinsic_gas_calculator(
            calldata=calldata,
            return_cost_deducted_prior_execution=True,
        )
        gas_for_loop = gas_available - intrinsic - setup.gas_cost(fork)
        if gas_for_loop < loop.gas_cost(fork):
            break
        expected_opcode_count += gas_for_loop // loop.gas_cost(fork)
        txs.append(
            Transaction(
                to=attack_contract_address,
                sender=pre.fund_eoa(),
                gas_limit=gas_available,
                data=calldata,
            )
        )
        remaining_gas -= gas_available
        seed += 1

    benchmark_test(
        target_opcode=target,
        skip_gas_used_validation=True,
        expected_receipt_status=1,
        blocks=[Block(txs=txs)],
        expected_opcode_count=expected_opcode_count,
    )
