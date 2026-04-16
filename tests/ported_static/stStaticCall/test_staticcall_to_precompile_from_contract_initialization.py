"""
STATICCALL to precompiled contracts from contract initialization code.

It should execute successfully for each precompiled contract.


Ported from:
state_tests/stStaticCall/StaticcallToPrecompileFromContractInitializationFiller.yml
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
    [
        "state_tests/stStaticCall/StaticcallToPrecompileFromContractInitializationFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.pre_alloc_mutable
def test_staticcall_to_precompile_from_contract_initialization(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """STATICCALL to precompiled contracts from contract initialization code."""  # noqa: E501
    coinbase = Address(0xCAFE000000000000000000000000000000000001)
    contract_0 = Address(0xA000000000000000000000000000000000000000)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: lll
    # {
    #   (CALLDATACOPY 0 0 (CALLDATASIZE))
    #   [[ 0 ]] (CREATE2 0 0 (CALLDATASIZE) 0x5a175a175a17)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=Op.CALLDATASIZE)
        + Op.SSTORE(
            key=0x0,
            value=Op.CREATE2(
                value=0x0,
                offset=0x0,
                size=Op.CALLDATASIZE,
                salt=0x5A175A175A17,
            ),
        )
        + Op.STOP,
        nonce=0,
        address=Address(0xA000000000000000000000000000000000000000),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(
            "7f18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c600052601c6020527f73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f6040527feeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c454960605260206103e860806000600162061a80fa60005560a060020a6103e851066001556001543214600255600060005260006020526000604052600060605260006103e8527c0ccccccccccccccccccccccccccccccccccccccccccccccccccc00000060005260206103e86020600060025afa6003556000516004556103e851600555600060005260006103e8527c0ccccccccccccccccccccccccccccccccccccccccccccccccccc00000060005260206103e86020600060035afa6006556000516007556103e851600855600060005260006103e8527c0ccccccccccccccccccccccccccccccccccccccccccccccccccc00000060005260206103e86020600060045afa6009556103e851601055600060005260006103e8526001600052602060205260206040527f03fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc6060527f2efffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc6080527f2f0000000000000000000000000000000000000000000000000000000000000060a05260206103e860a1600060055afa6011556103e85160125560006000526000602052600060405260006060526000608052600060a05260006103e8527f0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd26000527f16da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba6020527f1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2866040527f0217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d460605260406103e86080600060065afa6013556103e85160145561040851601555600060005260006020526000604052600060605260006103e8526000610408527f0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd26000527f16da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba602052600360405260406103e86060600060075afa6016556103e8516017556104085160185560006000526000602052600060405260006103e8526000610408527f1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f596000527f3034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef416020527f209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf76040527f04bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416786060527f2bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d6080527f120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de87755060a0527f111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c60c0527f2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf41160e0527f198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2610100527f1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed610120527f090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b610140527f12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa6101605260206103e8610180600060085afa6019556103e85160205500"  # noqa: E501
        ),
        gas_limit=1000000,
        value=100,
    )

    post = {
        contract_0: Account(
            storage={0: 0xFAD204ED1275B429B66C9CE0614D62832D6B2580},
        ),
        Address(0xFAD204ED1275B429B66C9CE0614D62832D6B2580): Account(
            storage={
                0: 1,
                1: sender,
                2: 1,
                3: 1,
                4: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,
                5: 0x73F5062FB68ED2A1EC82FF8C73F9251BB9CF53A623BC93527E16BC5AE29DAD74,  # noqa: E501
                6: 1,
                7: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,
                8: 0x14EF238CFA4075E9EDE92F18B1566C1DD0B99AAA,
                9: 1,
                16: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
                17: 1,
                18: 1,
                19: 1,
                20: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
                21: 0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,  # noqa: E501
                22: 1,
                23: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
                24: 0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,  # noqa: E501
                25: 1,
                32: 1,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
