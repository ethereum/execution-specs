"""
Test suite for transaction signing and serialization.
"""

from typing import Tuple

import pytest

from ..common import AccessList, Transaction


@pytest.mark.parametrize(
    [
        "tx",
        "expected_signature",
        "expected_sender",
        "expected_serialized",
    ],
    [
        (
            Transaction(
                ty=0,
                nonce=0,
                gas_price=1000000000,
                protected=False,
            ),
            (
                27,
                53278292994103027856810056625464356790495244130915206464977063215688423053889,
                51913880459033617104276213638042305667358907564476883662899087493955291953870,
            ),
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            "0xf86380843b9aca008252089400000000000000000000000000000000000000aa80801ba075ca71"
            "f8b7f1e95841db86704f4fe3da864694d135e0ed12ddf936f009541a41a072c6370f0c078df435b4"
            "041fe9e1fd596f7bcbd810993122b39a7f212617bace",
        ),
        (
            Transaction(
                ty=0,
                nonce=0,
                gas_price=1000000000,
                protected=True,
            ),
            (
                37,
                43493668498277122407922969255529421324465897185389682326746699251814478581534,
                22805784714726510606244238945786421174106485654201651664508077741484361436093,
            ),
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            "0xf86380843b9aca008252089400000000000000000000000000000000000000aa808025a060288b"
            "4319025f4955e36c53831871a91b2b59131b0355dbbc01a34f05b30f1ea0326b9de159e61d79e55c"
            "1844a8b0de520eef2fcb8b2992750c2f694d841ccbbd",
        ),
        (
            Transaction(
                ty=1,
                nonce=0,
                gas_price=1000000000,
            ),
            (
                1,
                64717097837956073364449107040675652683171442339602810813343912669101132492723,
                16766093433587703483635506527630997640109434240457156669715758246025787266781,
            ),
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            "0x01f8650180843b9aca008252089400000000000000000000000000000000000000aa8080c001a0"
            "8f14944d8d46e2b6280d61afee759646d42aa23189e0764ed409e68f45962fb3a0251145c8de5edc"
            "9a19b3244f37caca6858aec3a1056330e251491881cbd2d6dd",
        ),
        (
            Transaction(
                ty=1,
                nonce=0,
                gas_price=1000000000,
                access_list=[],
            ),
            (
                1,
                64717097837956073364449107040675652683171442339602810813343912669101132492723,
                16766093433587703483635506527630997640109434240457156669715758246025787266781,
            ),
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            "0x01f8650180843b9aca008252089400000000000000000000000000000000000000aa8080c001a0"
            "8f14944d8d46e2b6280d61afee759646d42aa23189e0764ed409e68f45962fb3a0251145c8de5edc"
            "9a19b3244f37caca6858aec3a1056330e251491881cbd2d6dd",
        ),
        (
            Transaction(
                ty=1,
                nonce=0,
                gas_price=1000000000,
                access_list=[AccessList(address="0x123", storage_keys=["0x456", "0x789"])],
            ),
            (
                0,
                66978004263684299215005885298552000328779940885769675563360335351527355325681,
                56105983548446712608196400571580400910290560012106232439738315212890613615554,
            ),
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            "0x01f8c10180843b9aca008252089400000000000000000000000000000000000000aa8080f85bf8"
            "59940000000000000000000000000000000000000123f842a0000000000000000000000000000000"
            "0000000000000000000000000000000456a000000000000000000000000000000000000000000000"
            "0000000000000000078980a0941434fdc19a5853453cad120ebdea00bc0fce323301794b908ca9f7"
            "a0661cf1a07c0adc80aec2b076a8dbfde04e0a51de29e9e904510f804cd57e153a804e0bc2",
        ),
        (
            Transaction(
                ty=2,
                nonce=0,
                access_list=[AccessList(address="0x123", storage_keys=["0x456", "0x789"])],
                max_fee_per_gas=10,
                max_priority_fee_per_gas=5,
            ),
            (
                0,
                91749892362404225540206401600149574009569116775084797886968775355264509620768,
                44616954018220623825844796436003012227293665710878821792267483622343477105629,
            ),
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            "0x02f8be0180050a8252089400000000000000000000000000000000000000aa8080f85bf8599400"
            "00000000000000000000000000000000000123f842a0000000000000000000000000000000000000"
            "0000000000000000000000000456a000000000000000000000000000000000000000000000000000"
            "0000000000078980a0cad8994ac160fd7e167715bbe20212939abdd5cd5a1f6c4dd6e5612cd8b332"
            "20a062a44d12b176bbd669d09d20d26281b5a693d8a52ab02a9d130201ee5db113dd",
        ),
        (
            Transaction(
                ty=3,
                nonce=0,
                access_list=[AccessList(address="0x123", storage_keys=["0x456", "0x789"])],
                max_fee_per_gas=10,
                max_priority_fee_per_gas=5,
                max_fee_per_data_gas=100,
                blob_versioned_hashes=[],
            ),
            (
                0,
                48031212734270141632897997738964470162703155533103542626635301519303700733477,
                25274846027382763458393508666208718022841865508839207374090140639125166603463,
            ),
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            "0x03f8c00180050a8252089400000000000000000000000000000000000000aa8080f85bf8599400"
            "00000000000000000000000000000000000123f842a0000000000000000000000000000000000000"
            "0000000000000000000000000456a000000000000000000000000000000000000000000000000000"
            "0000000000078964c080a06a30b3f8fd434b55ee40d662263ffa98ff9c31ca0f9bce61ca5de5019c"
            "4d5e25a037e10e4f6ca934236d6bf064134f7c3203b7308a16d5c43b3c9ce8b8a6fbbcc7",
        ),
        (
            Transaction(
                ty=3,
                nonce=0,
                access_list=[AccessList(address="0x123", storage_keys=["0x456", "0x789"])],
                max_fee_per_gas=10,
                max_priority_fee_per_gas=5,
                max_fee_per_data_gas=100,
                blob_versioned_hashes=[bytes(), bytes([0x01])],
            ),
            (
                1,
                16459258601065735918558202846976552354069849089672096317954578689965269615539,
                13812345945591193204859005420918043741474532833353814142223502482030426489098,
            ),
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            "0x03f901030180050a8252089400000000000000000000000000000000000000aa8080f85bf85994"
            "0000000000000000000000000000000000000123f842a00000000000000000000000000000000000"
            "000000000000000000000000000456a0000000000000000000000000000000000000000000000000"
            "000000000000078964f842a000000000000000000000000000000000000000000000000000000000"
            "00000000a0000000000000000000000000000000000000000000000000000000000000000101a024"
            "639c3863663bb71a82b48482fd92428a4e1e6962c8ebe467a72adf2dc283b3a01e8982c15e3b5b53"
            "e90ae56d2a6e93ebd918d778ff0cf7f4f8f96eb2f472810a",
        ),
    ],
    ids=[
        "type-0-not-protected",
        "type-0-protected",
        "type-1",
        "type-1-access-list-empty",
        "type-1-access-list-filled",
        "type-2",
        "type-3-minimal-empty-blobs",
        "type-3-minimal-two-blobs",
    ],
)
def test_transaction_signing(
    request,
    tx: Transaction,
    expected_signature: Tuple[int, int, int],
    expected_sender: str,
    expected_serialized: str,
):
    """
    Test that transaction signing / serialization works as expected.
    """
    tx = tx.with_signature_and_sender()
    signature = tx.signature
    assert signature is not None

    assert signature == expected_signature
    assert type(tx.sender) == bytes
    assert ("0x" + tx.sender.hex()) == expected_sender
    assert ("0x" + tx.serialized_bytes().hex()) == expected_serialized
