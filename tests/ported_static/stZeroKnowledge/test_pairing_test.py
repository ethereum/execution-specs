"""
Test the BN254 pairing check precompile with valid and failing inputs.

Ported from:
state_tests/stZeroKnowledge/pairingTestFiller.json

@manually-enhanced: Do not overwrite. Parametrized on the pairing input and
its expected result. The arbitrary transaction gas limits are replaced by
forwarding exactly the pairing cost or one gas less, the input is copied
with CALLDATACOPY instead of word by word, its length comes from
CALLDATASIZE, the forwarded gas is passed in calldata so one contract
serves every case, and the unused ECMUL/ECADD helper contracts are
dropped.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Fork,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

PAIRING_ADDRESS = 0x8
PAIR_SIZE = 192
RESULT_OFFSET = 0x400
SENTINEL = 0x60A7


@pytest.mark.ported_from(
    ["state_tests/stZeroKnowledge/pairingTestFiller.json"],
)
@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    "enough_gas", [True, False], ids=["enough_gas", "one_gas_short"]
)
@pytest.mark.parametrize(
    "pairing_input, pairing_result",
    [
        pytest.param(
            Bytes(
                "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f59"
                "3034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41"
                "209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf7"
                "04bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a41678"
                "2bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d"
                "120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550"
                "111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c"
                "2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf411"
                "198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2"
                "1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed"
                "090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b"
                "12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa"
            ),
            1,
            id="two_pairs_a",
        ),
        pytest.param(
            Bytes(
                "2eca0c7238bf16e83e7a1e6c5d49540685ff51380f309842a98561558019fc02"
                "03d3260361bb8451de5ff5ecd17f010ff22f5c31cdf184e9020b06fa5997db84"
                "1213d2149b006137fcfb23036606f848d638d576a120ca981b5b1a5f9300b3ee"
                "2276cf730cf493cd95d64677bbb75fc42db72513a4c1e387b476d056f80aa75f"
                "21ee6226d31426322afcda621464d0611d226783262e21bb3bc86b537e986237"
                "096df1f82dff337dd5972e32a8ad43e28a78a96a823ef1cd4debe12b6552ea5f"
                "06967a1237ebfeca9aaae0d6d0bab8e28c198c5a339ef8a2407e31cdac516db9"
                "22160fa257a5fd5b280642ff47b65eca77e626cb685c84fa6d3b6882a283ddd1"
                "198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2"
                "1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed"
                "090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b"
                "12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa"
            ),
            1,
            id="two_pairs_b",
        ),
        pytest.param(
            Bytes(
                "0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd2"
                "16da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba"
                "2e89718ad33c8bed92e210e81d1853435399a271913a6520736a4729cf0d51eb"
                "01a9e2ffa2e92599b68e44de5bcf354fa2642bd4f26b259daa6f7ce3ed57aeb3"
                "14a9a87b789a58af499b314e13c3d65bede56c07ea2d418d6874857b70763713"
                "178fb49a2d6cd347dc58973ff49613a20757d0fcc22079f9abd10c3baee24590"
                "1b9e027bd5cfc2cb5db82d4dc9677ac795ec500ecd47deee3b5da006d6d049b8"
                "11d7511c78158de484232fc68daf8a45cf217d1c2fae693ff5871e8752d73b21"
                "198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2"
                "1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed"
                "090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b"
                "12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa"
            ),
            1,
            id="two_pairs_c",
        ),
        pytest.param(
            Bytes(
                "2f2ea0b3da1e8ef11914acf8b2e1b32d99df51f5f4f206fc6b947eae860eddb6"
                "068134ddb33dc888ef446b648d72338684d678d2eb2371c61a50734d78da4b72"
                "25f83c8b6ab9de74e7da488ef02645c5a16a6652c3c71a15dc37fe3a5dcb7cb1"
                "22acdedd6308e3bb230d226d16a105295f523a8a02bfc5e8bd2da135ac4c245d"
                "065bbad92e7c4e31bf3757f1fe7362a63fbfee50e7dc68da116e67d600d9bf68"
                "06d302580dc0661002994e7cd3a7f224e7ddc27802777486bf80f40e4ca3cfdb"
                "186bac5188a98c45e6016873d107f5cd131f3a3e339d0375e58bd6219347b008"
                "122ae2b09e539e152ec5364e7e2204b03d11d3caa038bfc7cd499f8176aacbee"
                "1f39e4e4afc4bc74790a4a028aff2c3d2538731fb755edefd8cb48d6ea589b5e"
                "283f150794b6736f670d6a1033f9b46c6f5204f50813eb85c8dc4b59db1c5d39"
                "140d97ee4d2b36d99bc49974d18ecca3e7ad51011956051b464d9e27d46cc25e"
                "0764bb98575bd466d32db7b15f582b2d5c452b36aa394b789366e5e3ca5aabd4"
                "15794ab061441e51d01e94640b7e3084a07e02c78cf3103c542bc5b298669f21"
                "1b88da1679b0b64a63b7e0e7bfe52aae524f73a55be7fe70c7e9bfc94b4cf0da"
                "1213d2149b006137fcfb23036606f848d638d576a120ca981b5b1a5f9300b3ee"
                "2276cf730cf493cd95d64677bbb75fc42db72513a4c1e387b476d056f80aa75f"
                "21ee6226d31426322afcda621464d0611d226783262e21bb3bc86b537e986237"
                "096df1f82dff337dd5972e32a8ad43e28a78a96a823ef1cd4debe12b6552ea5f"
            ),
            1,
            id="three_pairs_a",
        ),
        pytest.param(
            Bytes(
                "20a754d2071d4d53903e3b31a7e98ad6882d58aec240ef981fdf0a9d22c5926a"
                "29c853fcea789887315916bbeb89ca37edb355b4f980c9a12a94f30deeed3021"
                "1213d2149b006137fcfb23036606f848d638d576a120ca981b5b1a5f9300b3ee"
                "2276cf730cf493cd95d64677bbb75fc42db72513a4c1e387b476d056f80aa75f"
                "21ee6226d31426322afcda621464d0611d226783262e21bb3bc86b537e986237"
                "096df1f82dff337dd5972e32a8ad43e28a78a96a823ef1cd4debe12b6552ea5f"
                "1abb4a25eb9379ae96c84fff9f0540abcfc0a0d11aeda02d4f37e4baf74cb0c1"
                "1073b3ff2cdbb38755f8691ea59e9606696b3ff278acfc098fa8226470d03869"
                "217cee0a9ad79a4493b5253e2e4e3a39fc2df38419f230d341f60cb064a0ac29"
                "0a3d76f140db8418ba512272381446eb73958670f00cf46f1d9e64cba057b53c"
                "26f64a8ec70387a13e41430ed3ee4a7db2059cc5fc13c067194bcc0cb49a9855"
                "2fd72bd9edb657346127da132e5b82ab908f5816c826acb499e22f2412d1a2d7"
                "0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd2"
                "198a1f162a73261f112401aa2db79c7dab1533c9935c77290a6ce3b191f2318d"
                "198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2"
                "1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed"
                "090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b"
                "12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa"
            ),
            1,
            id="three_pairs_b",
        ),
        pytest.param(
            Bytes(
                "1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f59"
                "3034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41"
                "209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf7"
                "04bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a41678"
                "2bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d"
                "120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550"
                "111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c"
                "103188585e2364128fe25c70558f1560f4f9350baf3959e603cc91486e110936"
                "198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2"
                "1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed"
                "090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b"
                "12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa"
            ),
            0,
            id="two_pairs_false",
        ),
    ],
)
def test_pairing_test(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    pairing_input: Bytes,
    pairing_result: int,
    enough_gas: bool,
) -> None:
    """
    Call the pairing check precompile with `pairing_input`.

    Forwarding exactly the pairing cost, the call succeeds and returns
    `pairing_result`. One gas less and the precompile runs out of gas: the
    call fails and both slots are overwritten with zero, which a reverted
    transaction would leave at their pre-set value.
    """
    gas_costs = fork.gas_costs()
    pairing_cost = (
        gas_costs.PRECOMPILE_ECPAIRING_BASE
        + gas_costs.PRECOMPILE_ECPAIRING_PER_POINT
        * (len(pairing_input) // PAIR_SIZE)
    )
    call_gas = pairing_cost if enough_gas else pairing_cost - 1

    # Calldata: the gas to forward, followed by the pairing input. The same
    # contract serves every case.
    input_size = Op.SUB(Op.CALLDATASIZE, 0x20)
    pairing_caller = pre.deploy_contract(
        code=Op.CALLDATACOPY(dest_offset=0, offset=0x20, size=input_size)
        + Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=Op.CALLDATALOAD(offset=0),
                address=PAIRING_ADDRESS,
                args_offset=0,
                args_size=input_size,
                ret_offset=RESULT_OFFSET,
                ret_size=0x20,
            ),
        )
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=RESULT_OFFSET))
        + Op.STOP,
        storage={0: SENTINEL, 1: SENTINEL},
    )

    if enough_gas:
        storage = {0: 1, 1: pairing_result}
    else:
        storage = {0: 0, 1: 0}
    post = {pairing_caller: Account(storage=storage)}

    tx = Transaction(
        sender=pre.fund_eoa(),
        to=pairing_caller,
        data=Hash(call_gas) + pairing_input,
    )

    state_test(pre=pre, post=post, tx=tx)
