"""
STATICCALL to precompiled contracts from contract initialization code.
It should execute successfully for each precompiled contract.


Ported from:
tests/static/state_tests/stStaticCall/StaticcallToPrecompileFromContractInitializationFiller.yml

contract code:
    calldatasize
    push1 0x00
    push1 0x00
    calldatacopy
    push6 0x5a175a175a17
    calldatasize
    push1 0x00
    push1 0x00
    create2
    push1 0x00
    sstore
    stop
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
    ["tests/static/state_tests/stStaticCall/StaticcallToPrecompileFromContractInitializationFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_staticcall_to_precompile_from_contract_initialization(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """STATICCALL to precompiled contracts from contract initialization code.
It should execute successfully for each precompiled contract.
."""
    coinbase = Address("0xcafe000000000000000000000000000000000001")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xa000000000000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.CALLDATASIZE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.CALLDATACOPY
        + Op.PUSH6[0x5a175a175a17] + Op.CALLDATASIZE + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CREATE2 + Op.PUSH1[0x0] + Op.SSTORE + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=bytes.fromhex(
            "7f18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c600052"
            "601c6020527f73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5"
            "a75f6040527feeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c"
            "454960605260206103e860806000600162061a80fa60005560a060020a6103e851066001"
            "556001543214600255600060005260006020526000604052600060605260006103e8527c"
            "0ccccccccccccccccccccccccccccccccccccccccccccccccccc00000060005260206103"
            "e86020600060025afa6003556000516004556103e851600555600060005260006103e852"
            "7c0ccccccccccccccccccccccccccccccccccccccccccccccccccc000000600052602061"
            "03e86020600060035afa6006556000516007556103e851600855600060005260006103e8"
            "527c0ccccccccccccccccccccccccccccccccccccccccccccccccccc0000006000526020"
            "6103e86020600060045afa6009556103e851601055600060005260006103e85260016000"
            "52602060205260206040527f03ffffffffffffffffffffffffffffffffffffffffffffff"
            "fffffffffefffffc6060527f2effffffffffffffffffffffffffffffffffffffffffffff"
            "fffffffffefffffc6080527f2f0000000000000000000000000000000000000000000000"
            "000000000000000060a05260206103e860a1600060055afa6011556103e8516012556000"
            "6000526000602052600060405260006060526000608052600060a05260006103e8527f0f"
            "25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd26000527f16"
            "da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba6020527f1d"
            "e49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2866040527f02"
            "17327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d46060526040"
            "6103e86080600060065afa6013556103e851601455610408516015556000600052600060"
            "20526000604052600060605260006103e8526000610408527f0f25929bcb43d5a5739156"
            "4615c9e70a992b10eafa4db109709649cf48c50dd26000527f16da2f5cb6be7a0aa72c44"
            "0c53c9bbdfec6c36c7d515536431b3a865468acbba602052600360405260406103e86060"
            "600060075afa6016556103e8516017556104085160185560006000526000602052600060"
            "405260006103e8526000610408527f1c76476f4def4bb94541d57ebba1193381ffa7aa76"
            "ada664dd31c16024c43f596000527f3034dd2920f673e204fee2811c678745fc819b55d3"
            "e9d294e45c9b03a76aef416020527f209dd15ebff5d46c4bd888e51a93cf99a7329636c6"
            "3514396b4a452003a35bf76040527f04bf11ca01483bfa8b34b43561848d28905960114c"
            "8ac04049af4b6315a416786060527f2bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7a"
            "c41fadbf933c2a51be344d6080527f120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c"
            "9bb048165fe5e4de87755060a0527f111e129f1cf1097710d41c4ac70fcdfa5ba2023c6f"
            "f1cbeac322de49d1b6df7c60c0527f2032c61a830e3c17286de9462bf242fca2883585b9"
            "3870a73853face6a6bf41160e0527f198e9393920d483a7260bfb731fb5d25f1aa493335"
            "a9e71297e485b7aef312c2610100527f1800deef121f1e76426a00665e5c4479674322d4"
            "f75edadd46debd5cd992f6ed610120527f090689d0585ff075ec9e99ad690c3395bc4b31"
            "3370b38ef355acdadcd122975b610140527f12c85ea5db8c6deb4aab71808dcb408fe3d1"
            "e7690c43d37b4ce6cc0166fa7daa6101605260206103e8610180600060085afa60195561"
            "03e85160205500"
        ),
        gas_limit=1000000,
        gas_price=10,
        nonce=0,
        value=100,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
