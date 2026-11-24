"""Test suite for transaction signing and serialization."""

from typing import Any, Callable, Dict, List, Tuple

import pytest
from pydantic import ValidationError
from spec256k1 import PublicKey

from execution_testing.base_types import (
    AccessList,
    Address,
    Bytes,
    FrameSignatureScheme,
    Hash,
    Signer,
)
from execution_testing.forks import Bogota
from execution_testing.vm import Op

from .. import transaction_types
from ..account_types import EOA, P256Signer
from ..transaction_types import (
    Frame,
    FrameOutcome,
    FrameSettlement,
    FrameSignature,
    Transaction,
)
from ..utils import keccak256

SIGNING_KEY = Hash(bytes(range(1, 33)))
OTHER_KEY = Hash(bytes(range(33, 65)))


def signable_transaction(**kwargs: Any) -> Transaction:
    """Return a minimal legacy transaction ready to be signed."""
    return Transaction(ty=0, gas_limit=21_000, nonce=0, **kwargs)


def recover_sender(tx: Transaction) -> Address:
    """Recover the sender of a signed transaction from its signature."""
    public_key = PublicKey.from_signature_and_message(
        tx.signature_bytes,
        tx.rlp_signing_bytes().keccak256(),
    )
    return Address(
        keccak256(public_key.format(compressed=False)[1:])[32 - 20 :]
    )


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
                gas_limit=21000,
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
                gas_limit=21000,
                nonce=0,
                gas_price=1000000000,
                protected=False,
                to=None,
            ),
            (
                27,
                69580953802627422387708984158392304322597795331978871908970340300185024633230,
                9987437858655471264845875982426404737641514329900923987672173898100072610198,
            ),
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            "0xf84f80843b9aca008252088080801ba099d56c9a276e7b5c29f433bdc5ee0d551a242542445d2f"
            "f793be942cd4cc998ea01614b083596de05d65f22e0319d969a8465732ce5ad199c41c17fd72a651"
            "7996",
        ),
        (
            Transaction(
                ty=0,
                gas_limit=21000,
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
                gas_limit=21000,
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
                gas_limit=21000,
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
                gas_limit=21000,
                nonce=0,
                gas_price=1000000000,
                access_list=[
                    AccessList(
                        address="0x0000000000000000000000000000000000000123",
                        storage_keys=[0x456, 0x789],
                    )
                ],
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
                ty=1,
                gas_limit=21000,
                nonce=0,
                gas_price=1000000000,
                to=None,
                access_list=[
                    AccessList(address=0x123, storage_keys=[0x456, 0x789])
                ],
            ),
            (
                0,
                16814800520830332761874524721118962980778925570205706327283408113434790879234,
                38982159227826105391951884315531363239837729091757253660549724931098838198780,
            ),
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            "0x01f8ad0180843b9aca00825208808080f85bf85994000000000000000000000000000000000000"
            "0123f842a00000000000000000000000000000000000000000000000000000000000000456a00000"
            "00000000000000000000000000000000000000000000000000000000078980a0252cd6ff24fb485a"
            "50aa3cc4e11947e257c325213a6d5c6ae2ea70cb68b26002a0562f1ec7bfd17a0cc72ae25192b8a7"
            "450b315a4a8bcea8f60281d3e72bd669fc",
        ),
        (
            Transaction(
                ty=2,
                gas_limit=21000,
                nonce=0,
                access_list=[
                    AccessList(address=0x123, storage_keys=[0x456, 0x789])
                ],
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
                ty=2,
                gas_limit=21000,
                nonce=0,
                to=None,
                access_list=[
                    AccessList(address=0x123, storage_keys=[0x456, 0x789])
                ],
                max_fee_per_gas=10,
                max_priority_fee_per_gas=5,
            ),
            (
                0,
                90322080068302816931882206183311797596224841408506356995778410737685074239457,
                11150681916082931632476906514672946504836769153730288987778622018872414351162,
            ),
            "0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b",
            "0x02f8aa0180050a825208808080f85bf859940000000000000000000000000000000000000123f8"
            "42a00000000000000000000000000000000000000000000000000000000000000456a00000000000"
            "00000000000000000000000000000000000000000000000000078980a0c7b07c5552829e585f68e2"
            "eed4495ed6dfbe8cb1453edb2dc1e959d1087f5fe1a018a70ff379958b47e85172bc93fe5e47dc23"
            "d13e3b0e4a800f1f3a0766a0af3a",
        ),
        (
            Transaction(
                ty=3,
                gas_limit=21000,
                nonce=0,
                access_list=[
                    AccessList(address=0x123, storage_keys=[0x456, 0x789])
                ],
                max_fee_per_gas=10,
                max_priority_fee_per_gas=5,
                max_fee_per_blob_gas=100,
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
                gas_limit=21000,
                nonce=0,
                access_list=[
                    AccessList(address=0x123, storage_keys=[0x456, 0x789])
                ],
                max_fee_per_gas=10,
                max_priority_fee_per_gas=5,
                max_fee_per_blob_gas=100,
                blob_versioned_hashes=[Hash(0), Hash(0x01)],
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
        "type-0-protected-contract-creation",
        "type-0-protected",
        "type-1",
        "type-1-access-list-empty",
        "type-1-access-list-filled",
        "type-1-access-list-filled-contract-creation",
        "type-2",
        "type-2-contract-creation",
        "type-3-minimal-empty-blobs",
        "type-3-minimal-two-blobs",
    ],
)
def test_transaction_signing(
    tx: Transaction,
    expected_signature: Tuple[int, int, int],
    expected_sender: str,
    expected_serialized: str,
) -> None:
    """Test that transaction signing / serialization works as expected."""
    tx = tx.with_signature_and_sender()
    signature = (tx.v, tx.r, tx.s)
    assert signature is not None

    assert signature == expected_signature
    assert tx.sender is not None
    assert tx.sender.hex() == expected_sender
    assert (tx.rlp().hex()) == expected_serialized


def test_gas_limit_none_is_unset() -> None:
    """Test that `gas_limit=None` behaves exactly like omitting the field."""
    tx = Transaction(gas_limit=None)
    assert "gas_limit" not in tx.model_fields_set
    assert tx.gas_limit == 21_000


@pytest.mark.parametrize("alias", ["gas_limit", "gasLimit", "gas"])
def test_gas_limit_none_alias_is_unset(alias: str) -> None:
    """Test that a `None` gas limit via any alias counts as unset."""
    tx = Transaction.model_validate({alias: None})
    assert "gas_limit" not in tx.model_fields_set
    assert tx.gas_limit == 21_000


@pytest.mark.parametrize(
    "blob_versioned_hashes",
    [
        pytest.param([Hash(b"\x01" + bytes(31))], id="with_blobs"),
        pytest.param([], id="without_blobs"),
    ],
)
def test_frame_tx_max_fee_default(blob_versioned_hashes: List[Hash]) -> None:
    """
    A frame transaction defaults its `max_fee` budget, which the
    execution environment's per-gas fees leave alone, and encodes its
    fees as `[max_fee, max_priority_fee_per_gas]`.
    """
    tx = Transaction(
        sender=EOA(key=SIGNING_KEY),
        frames=[Frame()],
        blob_versioned_hashes=blob_versioned_hashes,
    )
    assert tx.max_fee == transaction_types.TransactionDefaults.max_fee
    assert "max_fee" not in tx.model_fields_set
    assert tx.max_fee_per_gas is None
    assert tx.max_fee_per_blob_gas is None
    tx.set_gas_price(
        gas_price=10,
        max_fee_per_gas=10,
        max_priority_fee_per_gas=1,
        max_fee_per_blob_gas=5,
    )
    assert tx.max_fee == transaction_types.TransactionDefaults.max_fee
    assert tx.fees == [tx.max_fee, 1]


def test_frame_tx_rejects_per_gas_fee_caps() -> None:
    """A frame transaction caps its fee with `max_fee` alone."""
    with pytest.raises(ValidationError, match="set max_fee"):
        Transaction(
            sender=EOA(key=SIGNING_KEY),
            frames=[Frame()],
            max_fee_per_gas=10,
        )


def test_derived_sender_matches_recovery() -> None:
    """The derived sender equals the one recovered from the signature."""
    signed = signable_transaction(
        secret_key=SIGNING_KEY
    ).with_signature_and_sender()
    assert signed.sender == recover_sender(signed)


def test_known_sender_skips_recovery(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A sender holding the signing key is reused as-is."""

    def unexpected_recovery(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError(
            "recovered the public key even though the sender was known"
        )

    monkeypatch.setattr(
        transaction_types.PublicKey,
        "from_signature_and_message",
        unexpected_recovery,
    )
    sender = EOA(key=SIGNING_KEY)
    signed = signable_transaction(sender=sender).with_signature_and_sender()
    assert signed.sender == sender


@pytest.mark.parametrize(
    "sender",
    [
        pytest.param(EOA(key=OTHER_KEY), id="holds_another_key"),
        pytest.param(EOA(address=0x1234), id="keyless"),
    ],
)
def test_sender_without_the_signing_key_is_derived(sender: EOA) -> None:
    """A sender that does not hold the signing key is not trusted."""
    tx = signable_transaction(sender=sender, secret_key=SIGNING_KEY)
    assert tx.with_signature_and_sender().sender == EOA(key=SIGNING_KEY)


def test_reassigned_sender_does_not_override_the_signer() -> None:
    """
    A sender reassigned after construction is not trusted.

    `validate_assignment=True` lets `sender` be replaced while
    `secret_key` keeps the original key.
    """
    tx = signable_transaction(sender=EOA(key=SIGNING_KEY))
    assert tx.secret_key == SIGNING_KEY
    tx.sender = EOA(key=OTHER_KEY)
    assert tx.with_signature_and_sender().sender == EOA(key=SIGNING_KEY)


def test_mismatched_sender_address_is_trusted() -> None:
    """
    An `EOA` whose address does not derive from its key is taken as-is.
    """
    inconsistent = EOA(address=0x1234, key=SIGNING_KEY)
    signed = signable_transaction(
        sender=inconsistent
    ).with_signature_and_sender()
    assert signed.sender == inconsistent
    assert signed.sender != recover_sender(signed)


@pytest.mark.parametrize(
    "copy_transaction",
    [
        pytest.param(lambda tx: tx.copy(), id="copy"),
        pytest.param(lambda tx: tx.with_nonce(1), id="with_nonce"),
        pytest.param(lambda tx: tx.with_error([]), id="with_error"),
    ],
)
def test_frame_tx_copy_unsupported(
    copy_transaction: Callable[[Transaction], Transaction],
) -> None:
    """
    Copying a frame transaction raises instead of returning a copy whose
    signature entries have lost their signers.
    """
    tx = Transaction(sender=EOA(key=SIGNING_KEY), frames=[Frame()])
    with pytest.raises(NotImplementedError, match="frame transaction"):
        copy_transaction(tx)


@pytest.mark.parametrize(
    "budget",
    [
        pytest.param({}, id="default_budget"),
        pytest.param({"gas_limit_delta": 0}, id="budget_delta"),
    ],
)
def test_frame_tx_reused_frames_match_fresh_frames(
    budget: Dict[str, int],
) -> None:
    """
    Frames reused by a second frame transaction expect the receipts fresh
    frames would, whatever the first transaction deduced for them.
    """
    first_sender = EOA(key=SIGNING_KEY)
    second_sender = EOA(key=OTHER_KEY)

    def build_frames() -> List[Frame]:
        return [
            Frame.verify(),
            Frame.default(target=first_sender, **budget),
        ]

    shared_frames = build_frames()
    Transaction(
        sender=first_sender, frames=shared_frames
    ).expect_frame_receipts(Bogota)
    reused = Transaction(
        sender=second_sender, frames=shared_frames
    ).expect_frame_receipts(Bogota)
    fresh = Transaction(
        sender=second_sender, frames=build_frames()
    ).expect_frame_receipts(Bogota)
    assert reused.expected_receipt == fresh.expected_receipt


EXPECTATION_FIELDS = [
    pytest.param({"outcome": FrameOutcome.REVERT}, id="outcome"),
    pytest.param({"code": Op.STOP}, id="code"),
    pytest.param({"execution_gas": 0}, id="execution_gas"),
    pytest.param({"gas_limit_delta": 0}, id="gas_limit_delta"),
    pytest.param({"state_gas_limit_delta": 0}, id="state_gas_limit_delta"),
    pytest.param({"warm": True}, id="warm"),
    pytest.param({"delegated": False}, id="delegated_default_value"),
    pytest.param({"delegation_warm": True}, id="delegation_warm"),
    pytest.param({"pin_gas": False}, id="pin_gas"),
    pytest.param({"gas_used": 0}, id="gas_used"),
    pytest.param({"state_gas_used": 0}, id="state_gas_used"),
    pytest.param({"logs": []}, id="logs"),
]
"""
One value per expectation field. A value equal to the field's default
still counts, since the caller set it.
"""


@pytest.mark.parametrize("expectation", EXPECTATION_FIELDS)
def test_frame_expectation_requires_settlement(
    expectation: Dict[str, Any],
) -> None:
    """Setting any expectation field requires the frame to be settled."""
    assert Frame.default(**expectation).requires_settlement


@pytest.mark.parametrize(
    "frame",
    [
        pytest.param(Frame(), id="frame"),
        pytest.param(Frame.default(), id="default"),
        pytest.param(Frame.sender(), id="sender"),
        pytest.param(Frame.verify(), id="verify"),
        pytest.param(Frame.expiry(), id="expiry"),
    ],
)
def test_frame_without_expectations_requires_no_settlement(
    frame: Frame,
) -> None:
    """
    A frame setting no expectation field requires no settlement, and its
    transaction encodes without `expect_frame_receipts`.
    """
    assert not frame.requires_settlement
    assert not frame.settled
    Transaction(
        sender=EOA(key=SIGNING_KEY), frames=[Frame.verify(), frame]
    ).rlp()


@pytest.mark.parametrize("expectation", EXPECTATION_FIELDS)
def test_frame_tx_encoding_requires_settlement(
    expectation: Dict[str, Any],
) -> None:
    """
    A frame transaction whose frames set expectation fields encodes only
    once `expect_frame_receipts` settled them, so its signature never
    covers a budget that settlement changes afterwards.
    """
    tx = Transaction(
        sender=EOA(key=SIGNING_KEY),
        frames=[Frame.verify(), Frame.default(**expectation)],
    )
    with pytest.raises(AssertionError, match="expect_frame_receipts"):
        tx.rlp()
    tx.expect_frame_receipts(Bogota)
    assert tx.frames is not None
    assert all(frame.settled for frame in tx.frames)
    tx.rlp()


def test_frame_tx_settled_budget_is_signed() -> None:
    """
    A frame transaction encodes and signs its frames' settled budgets, not
    the placeholder a frame declaring a budget delta starts with.
    """
    sender = EOA(key=SIGNING_KEY)
    target = Address(0x1234)
    settled = Transaction(
        sender=sender,
        frames=[
            Frame.verify(),
            Frame.default(target=target, gas_limit_delta=0),
        ],
    ).expect_frame_receipts(Bogota)
    placeholder = Transaction(
        sender=sender,
        frames=[
            Frame.verify(),
            Frame.default(target=target, gas_limit=Frame().gas_limit),
        ],
    )
    assert settled.frames is not None
    assert settled.frames[1].gas_limit != Frame().gas_limit
    assert settled.rlp() != placeholder.rlp()
    assert settled.signatures is not None
    assert placeholder.signatures is not None
    assert (
        settled.signatures[0].signature != placeholder.signatures[0].signature
    )


def test_frame_receipt_requires_settlement() -> None:
    """
    The receipt of a frame setting expectation fields is only available
    from its settled copy in the transaction, not from the frame passed in.
    """
    frame = Frame.default(outcome=FrameOutcome.REVERT)
    with pytest.raises(AssertionError, match="expect_frame_receipts"):
        frame.receipt(Bogota)
    tx = Transaction(
        sender=EOA(key=SIGNING_KEY), frames=[Frame.verify(), frame]
    ).expect_frame_receipts(Bogota)
    assert tx.frames is not None
    assert tx.frames[1].settled
    assert not frame.settled
    receipt = tx.frames[1].receipt(Bogota)
    assert tx.expected_receipt is not None
    assert tx.expected_receipt.frame_receipts is not None
    assert receipt == tx.expected_receipt.frame_receipts[1]


SIGNERS = [
    pytest.param(EOA(key=SIGNING_KEY), id="eoa"),
    pytest.param(P256Signer(1), id="p256"),
]


@pytest.mark.parametrize("signer", SIGNERS)
def test_frame_signature_defaults_to_signer_scheme(signer: Any) -> None:
    """
    An entry built from a signer defaults to the scheme that verifies the
    signer natively, and identifies the signer by its bytes.
    """
    entry = FrameSignature(signer=signer)
    assert entry.scheme == signer.signature_scheme
    assert entry.signer == Bytes(bytes(signer))
    assert entry.signed_by is signer


@pytest.mark.parametrize("signer", SIGNERS)
def test_frame_signature_arbitrary_scheme_accepted(signer: Any) -> None:
    """
    Any signer can sign an `ARBITRARY` entry, which leaves the signer
    bytes empty for the account's code to verify.
    """
    entry = FrameSignature(
        signer=signer, scheme=FrameSignatureScheme.ARBITRARY
    )
    assert entry.scheme == FrameSignatureScheme.ARBITRARY
    assert entry.signer == Bytes(b"")
    assert entry.signed_by is signer


@pytest.mark.parametrize(
    "signer,scheme",
    [
        pytest.param(
            EOA(key=SIGNING_KEY), FrameSignatureScheme.P256, id="eoa_as_p256"
        ),
        pytest.param(
            P256Signer(1), FrameSignatureScheme.SECP256K1, id="p256_as_k1"
        ),
    ],
)
def test_frame_signature_foreign_scheme_rejected(
    signer: Any, scheme: FrameSignatureScheme
) -> None:
    """A signer cannot sign an entry of another native scheme."""
    with pytest.raises(ValidationError, match="cannot sign scheme"):
        FrameSignature(signer=signer, scheme=scheme)


def test_frame_signature_without_native_scheme_defaults_to_arbitrary() -> None:
    """
    A signer no scheme verifies natively signs `ARBITRARY` entries by
    default, and no other scheme.
    """

    class CodeVerifiedSigner(Address):
        """A signer whose signatures only account code can verify."""

        signature_scheme = None
        signature_length = 32

        def sign_message(self, message: Hash) -> Bytes:
            return Bytes(bytes(message))

    signer = CodeVerifiedSigner(0x1234)
    entry = FrameSignature(signer=signer)
    assert entry.scheme == FrameSignatureScheme.ARBITRARY
    assert entry.signer == Bytes(b"")
    with pytest.raises(ValidationError, match="cannot sign scheme"):
        FrameSignature(signer=signer, scheme=FrameSignatureScheme.SECP256K1)


def test_expiry_frame_target_fixed() -> None:
    """An expiry frame always targets the expiry verifier."""
    assert Frame.expiry().target is not None
    with pytest.raises(AssertionError, match="not an expiry frame"):
        Frame.expiry(target=Address(0x1234))


# Warmth deduction

STRANGER = Address(0x1234)
"""An address outside the warm set a transaction starts with."""


@pytest.mark.parametrize(
    "target,warm",
    [
        pytest.param(None, True, id="no_target_resolves_to_sender"),
        pytest.param("sender", True, id="sender"),
        pytest.param(Address(0x01), True, id="precompile"),
        pytest.param(STRANGER, False, id="stranger"),
    ],
)
def test_frame_tx_deduces_target_warmth(target: Any, warm: bool) -> None:
    """
    A frame whose resolved target is in the warm set a transaction starts
    with, the sender or a precompile, is warm unless it says otherwise.
    """
    sender = EOA(key=SIGNING_KEY)
    if isinstance(target, str):
        target = sender
    tx = Transaction(
        sender=sender, frames=[Frame.verify(), Frame.default(target=target)]
    ).expect_frame_receipts(Bogota)
    assert tx.frames is not None
    assert tx.frames[1].warm is warm


@pytest.mark.parametrize(
    "target,warm",
    [
        pytest.param(None, False, id="sender_declared_cold"),
        pytest.param(STRANGER, True, id="stranger_declared_warm"),
    ],
)
def test_frame_tx_keeps_declared_warmth(target: Any, warm: bool) -> None:
    """
    A frame that declares its warmth keeps it, such as a target an earlier
    frame touched, whatever the deduction would give.
    """
    tx = Transaction(
        sender=EOA(key=SIGNING_KEY),
        frames=[Frame.verify(), Frame.default(target=target, warm=warm)],
    ).expect_frame_receipts(Bogota)
    assert tx.frames is not None
    assert tx.frames[1].warm is warm


def test_frame_tx_warmth_prices_entry() -> None:
    """A warm target is charged less at entry than a cold one."""
    frames = [
        Transaction(
            sender=EOA(key=SIGNING_KEY),
            frames=[Frame.verify(), Frame.default(target=target)],
        ).expect_frame_receipts(Bogota)
        for target in (None, STRANGER)
    ]
    warm_frame, cold_frame = (tx.frames[1] for tx in frames if tx.frames)
    assert warm_frame.entry_gas(Bogota) < cold_frame.entry_gas(Bogota)


# Settlement


def test_frame_settlement_arithmetic() -> None:
    """
    The settled amounts follow from the execution gas, state gas, calldata
    floor and refund: the floor holds the refunded execution gas up, state
    gas is never refunded or floored, and the header takes the larger
    dimension.
    """
    settlement = FrameSettlement(
        execution_gas=100,
        state_gas=30,
        calldata_floor=80,
        effective_refund=40,
    )
    assert settlement.gas_before_refund == 130
    assert settlement.floor_binds()
    assert not settlement.floor_binds(after_refund=False)
    assert settlement.payer_gas_used() == 80 + 30
    assert settlement.block_gas_used() == 100 + 30
    assert settlement.block_header_gas_used() == 100

    state_heavy = FrameSettlement(
        execution_gas=100, state_gas=300, calldata_floor=0, effective_refund=0
    )
    assert not state_heavy.floor_binds()
    assert state_heavy.payer_gas_used() == 400
    assert state_heavy.block_header_gas_used() == 300


def settled_frame_tx(**frame_fields: Any) -> Transaction:
    """Return a settled frame transaction with one `DEFAULT` frame."""
    return Transaction(
        sender=EOA(key=SIGNING_KEY),
        frames=[Frame.verify(), Frame.default(**frame_fields)],
    ).expect_frame_receipts(Bogota)


def test_frame_settlement_sums_receipts() -> None:
    """
    The settled execution and state gas grow by exactly what a frame's
    receipt reports.
    """
    base = settled_frame_tx(gas_used=0, state_gas_used=0).frame_settlement(
        Bogota
    )
    more = settled_frame_tx(
        gas_used=1_000, state_gas_used=500
    ).frame_settlement(Bogota)
    assert more.execution_gas - base.execution_gas == 1_000
    assert more.state_gas - base.state_gas == 500
    assert more.calldata_floor == base.calldata_floor


@pytest.mark.parametrize(
    "refund,capped",
    [
        pytest.param(1, False, id="below_cap"),
        pytest.param(10**9, True, id="above_cap"),
    ],
)
def test_frame_settlement_caps_refund(refund: int, capped: bool) -> None:
    """The refund survives up to the fork's share of the spent gas."""
    tx = settled_frame_tx(gas_used=50_000)
    settlement = tx.frame_settlement(Bogota, refund=refund)
    cap = settlement.gas_before_refund // Bogota.max_refund_quotient()
    assert settlement.effective_refund == (cap if capped else refund)


def test_frame_settlement_matches_expected_receipt() -> None:
    """
    The expected receipt charges the payer what the settlement gives, for
    the refund it was settled with.
    """
    sender = EOA(key=SIGNING_KEY)
    tx = Transaction(
        sender=sender,
        frames=[Frame.verify(), Frame.default(gas_used=50_000)],
    ).expect_frame_receipts(Bogota, refund=1_000)
    assert tx.expected_receipt is not None
    assert tx.expected_receipt.payer == sender
    assert (
        tx.expected_receipt.cumulative_gas_used
        == tx.frame_settlement(Bogota, refund=1_000).payer_gas_used()
    )


def test_frame_settlement_unpinned_without_total() -> None:
    """
    A frame whose execution gas is unpinned leaves the receipt's total
    unpinned too, since the total follows from every frame's gas.
    """
    tx = settled_frame_tx(pin_gas=False)
    assert tx.expected_receipt is not None
    assert tx.expected_receipt.cumulative_gas_used is None


# Signers in the signature list


def test_frame_tx_default_signature_from_sender() -> None:
    """
    A frame transaction without signatures gets one canonical-hash entry
    signed by its sender, or none for a sender without a key.
    """
    sender = EOA(key=SIGNING_KEY)
    tx = Transaction(sender=sender, frames=[Frame.verify()])
    assert tx.signatures is not None
    assert len(tx.signatures) == 1
    assert tx.signatures[0].signed_by is sender
    assert tx.signatures[0].msg == Bytes(b"")

    keyless = Transaction(sender=EOA(Address(0x1234)), frames=[Frame.verify()])
    assert keyless.signatures == []


def test_frame_tx_signers_become_signed_entries() -> None:
    """
    Signers in the signature list become canonical-hash entries of their
    own scheme, signed with their own key when the transaction is.
    """
    sender = EOA(key=SIGNING_KEY)
    payer = EOA(key=OTHER_KEY)
    signers: List[Signer] = [sender, payer, P256Signer(1)]
    tx = Transaction(
        sender=sender, frames=[Frame.verify()], signatures=signers
    )
    assert tx.signatures is not None
    assert [entry.signed_by for entry in tx.signatures] == signers
    assert all(len(entry.signature) == 0 for entry in tx.signatures)
    tx.rlp()
    for entry, signer in zip(tx.signatures, signers, strict=True):
        assert entry.scheme == signer.signature_scheme
        assert entry.signer == Bytes(bytes(signer))
        assert entry.msg == Bytes(b"")
        assert len(entry.signature) == signer.signature_length


def test_frame_tx_signature_entries_copied() -> None:
    """
    Entries passed in are copied, so signing a transaction never modifies
    an entry shared with the caller or another transaction.
    """
    sender = EOA(key=SIGNING_KEY)
    entry = FrameSignature(signer=sender)
    first = Transaction(
        sender=sender, frames=[Frame.verify()], signatures=[entry]
    )
    second = Transaction(
        sender=sender,
        frames=[Frame.verify(), Frame.default()],
        signatures=[entry, EOA(key=OTHER_KEY)],
    )
    first.rlp()
    second.rlp()
    assert first.signatures is not None and second.signatures is not None
    assert first.signatures[0] is not entry
    assert len(entry.signature) == 0
    assert first.signatures[0].signature != second.signatures[0].signature


@pytest.mark.parametrize(
    "frame",
    [
        pytest.param(Frame.sender(), id="no_expectation_fields"),
        pytest.param(Frame.default(gas_used=0), id="expectation_fields"),
    ],
)
def test_frame_settlement_requires_expected_receipts(frame: Frame) -> None:
    """
    Settling a frame transaction's gas requires `expect_frame_receipts`
    first, which deduces the frames' warmth: settled any earlier, a frame
    targeting the sender would be priced as cold.
    """
    tx = Transaction(
        sender=EOA(key=SIGNING_KEY), frames=[Frame.verify(), frame]
    )
    with pytest.raises(AssertionError, match="expect_frame_receipts"):
        tx.frame_settlement(Bogota)
    tx.expect_frame_receipts(Bogota)
    tx.frame_settlement(Bogota)


def test_frame_settlement_requires_pinned_gas() -> None:
    """
    A frame whose execution gas is unpinned leaves nothing to settle the
    transaction's gas from, rather than counting as no gas.
    """
    tx = settled_frame_tx(pin_gas=False)
    with pytest.raises(AssertionError, match="unpinned"):
        tx.frame_settlement(Bogota)
