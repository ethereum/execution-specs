"""
CREATE2 into an address that already holds an account.

Every case deploys the same full set of colliders, one per collider kind
and init code, so all cases share one pre-allocation. Each kind uses its
own CREATE2 salt to keep the collider addresses apart.

Ported from:
state_tests/stCreate2/create2collisionBalanceFiller.json
state_tests/stCreate2/create2collisionCodeFiller.json
state_tests/stCreate2/create2collisionCode2Filler.json
state_tests/stCreate2/create2collisionNonceFiller.json
state_tests/stCreate2/create2collisionSelfdestructedFiller.json
state_tests/stCreate2/create2collisionSelfdestructed2Filler.json
state_tests/stCreate2/create2collisionSelfdestructedRevertFiller.json
@manually-enhanced: Do not overwrite. Rewritten by hand; tx `gas_limit`
removed.
"""

from dataclasses import dataclass

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

COLLIDER_BALANCE = 1
TX_VALUE = 1

STORE_CODE = Op.SSTORE(key=1, value=1)


def deploy(code: bytes) -> bytes:
    """Return init code that deploys `code`."""
    return bytes(
        Op.MSTORE(offset=0, value=int.from_bytes(code, "big"))
        + Op.RETURN(offset=32 - len(code), size=len(code))
    )


INITCODES = {
    "empty": b"",
    "store": bytes(STORE_CODE),
    "deploy": deploy(bytes(STORE_CODE)),
    "deploy_010203": deploy(bytes.fromhex("010203")),
    "deploy_6010ff": deploy(bytes.fromhex("6010ff")),
}


@dataclass(frozen=True)
class ColliderKind:
    """Pre-existing account placed at a CREATE2 target."""

    salt: int
    nonce: int
    balance: int
    code: str
    initcodes: tuple[str, ...]

    @property
    def collides(self) -> bool:
        """Return whether CREATE2 into this account fails."""
        return self.nonce > 0 or self.code != ""

    @property
    def selfdestructs(self) -> bool:
        """Return whether this account selfdestructs when called."""
        return self.code.startswith("selfdestruct")


COLLIDER_KINDS = {
    "balance": ColliderKind(
        salt=0,
        nonce=0,
        balance=COLLIDER_BALANCE,
        code="",
        initcodes=("empty", "store", "deploy"),
    ),
    "code": ColliderKind(
        salt=1,
        nonce=0,
        balance=0,
        code="010203",
        initcodes=("empty", "store", "deploy", "deploy_010203"),
    ),
    "nonce": ColliderKind(
        salt=2,
        nonce=1,
        balance=0,
        code="",
        initcodes=("empty", "store", "deploy"),
    ),
    "selfdestructed": ColliderKind(
        salt=3,
        nonce=0,
        balance=COLLIDER_BALANCE,
        code="selfdestruct_stop",
        initcodes=("empty", "store", "deploy", "deploy_010203"),
    ),
    "selfdestructed_nonce": ColliderKind(
        salt=4,
        nonce=1,
        balance=COLLIDER_BALANCE,
        code="selfdestruct",
        initcodes=("deploy_6010ff",),
    ),
}


def collider_code(kind: ColliderKind, beneficiary: Address) -> bytes:
    """Return the runtime code of a collider."""
    if kind.code == "selfdestruct_stop":
        return bytes(Op.SELFDESTRUCT(address=beneficiary) + Op.STOP)
    if kind.code == "selfdestruct":
        return bytes(Op.SELFDESTRUCT(address=beneficiary))
    return bytes.fromhex(kind.code)


@pytest.mark.ported_from(
    [
        "state_tests/stCreate2/create2collisionBalanceFiller.json",
        "state_tests/stCreate2/create2collisionCodeFiller.json",
        "state_tests/stCreate2/create2collisionCode2Filler.json",
        "state_tests/stCreate2/create2collisionNonceFiller.json",
        "state_tests/stCreate2/create2collisionSelfdestructedFiller.json",
        "state_tests/stCreate2/create2collisionSelfdestructed2Filler.json",
        "state_tests/stCreate2/create2collisionSelfdestructedRevertFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "kind_name, initcode_name, create_value, revert_after",
    [
        pytest.param("balance", "empty", 0, False, id="balance-empty"),
        pytest.param("balance", "store", 0, False, id="balance-store"),
        pytest.param("balance", "deploy", 0, False, id="balance-deploy"),
        pytest.param("balance", "empty", 1, False, id="balance-empty-value"),
        pytest.param("code", "empty", 0, False, id="code-empty"),
        pytest.param("code", "store", 0, False, id="code-store"),
        pytest.param("code", "deploy", 0, False, id="code-deploy"),
        pytest.param(
            "code", "deploy_010203", 0, False, id="code-deploy_010203"
        ),
        pytest.param(
            "code", "deploy_010203", 1, False, id="code-deploy_010203-value"
        ),
        pytest.param("nonce", "empty", 0, False, id="nonce-empty"),
        pytest.param("nonce", "store", 0, False, id="nonce-store"),
        pytest.param("nonce", "deploy", 0, False, id="nonce-deploy"),
        pytest.param(
            "selfdestructed", "empty", 0, False, id="selfdestructed-empty"
        ),
        pytest.param(
            "selfdestructed", "store", 0, False, id="selfdestructed-store"
        ),
        pytest.param(
            "selfdestructed", "deploy", 0, False, id="selfdestructed-deploy"
        ),
        pytest.param(
            "selfdestructed",
            "deploy_010203",
            0,
            False,
            id="selfdestructed-deploy_010203",
        ),
        pytest.param(
            "selfdestructed_nonce",
            "deploy_6010ff",
            0,
            False,
            id="selfdestructed_nonce-deploy_6010ff",
        ),
        pytest.param(
            "selfdestructed",
            "empty",
            0,
            True,
            id="selfdestructed-empty-revert",
        ),
        pytest.param(
            "selfdestructed",
            "store",
            0,
            True,
            id="selfdestructed-store-revert",
        ),
        pytest.param(
            "selfdestructed",
            "deploy",
            0,
            True,
            id="selfdestructed-deploy-revert",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create2collision(
    state_test: StateTestFiller,
    pre: Alloc,
    kind_name: str,
    initcode_name: str,
    create_value: int,
    revert_after: bool,
) -> None:
    """CREATE2 into an address that already holds an account."""
    sender = pre.fund_eoa()
    beneficiary = pre.nonexistent_account()
    creator = compute_create_address(address=sender, nonce=0)

    colliders: dict[tuple[str, str], Address] = {}
    for name, collider_kind in COLLIDER_KINDS.items():
        for collider_initcode in collider_kind.initcodes:
            address = compute_create_address(
                address=creator,
                salt=collider_kind.salt,
                initcode=INITCODES[collider_initcode],
                opcode=Op.CREATE2,
            )
            pre.deploy_contract(
                code=collider_code(collider_kind, beneficiary),
                balance=collider_kind.balance,
                nonce=collider_kind.nonce,
                address=address,
            )
            colliders[(name, collider_initcode)] = address

    kind = COLLIDER_KINDS[kind_name]
    initcode = INITCODES[initcode_name]
    target = colliders[(kind_name, initcode_name)]

    outer = Bytecode()
    if kind.selfdestructs:
        outer += Op.POP(Op.CALL(address=target))
    if initcode:
        outer += Op.MSTORE(offset=0, value=int.from_bytes(initcode, "big"))
    create2 = Op.CREATE2(
        value=create_value,
        offset=32 - len(initcode) if initcode else 0,
        size=len(initcode),
        salt=kind.salt,
    )
    if revert_after:
        outer += Op.POP(create2) + Op.REVERT(offset=0, size=0)
    else:
        outer += Op.SSTORE(key=0, value=create2) + Op.STOP

    tx = Transaction(sender=sender, to=None, data=outer, value=TX_VALUE)

    target_code = collider_code(kind, beneficiary)
    post: dict = {sender: Account(nonce=1)}
    if revert_after:
        post[creator] = Account.NONEXISTENT
        post[target] = Account(
            code=target_code, balance=kind.balance, nonce=kind.nonce
        )
        post[beneficiary] = Account.NONEXISTENT
    elif kind.collides:
        post[creator] = Account(storage={0: 0}, balance=TX_VALUE, nonce=2)
        if kind.selfdestructs:
            post[target] = Account(
                code=target_code, balance=0, nonce=kind.nonce, storage={}
            )
            post[beneficiary] = Account(balance=kind.balance)
        else:
            post[target] = Account(
                code=target_code,
                balance=kind.balance,
                nonce=kind.nonce,
                storage={},
            )
    else:
        post[creator] = Account(
            storage={0: target}, balance=TX_VALUE - create_value, nonce=2
        )
        post[target] = Account(
            code=STORE_CODE if initcode_name == "deploy" else b"",
            storage={1: 1} if initcode_name == "store" else {},
            balance=kind.balance + create_value,
            nonce=1,
        )

    state_test(pre=pre, post=post, tx=tx)
