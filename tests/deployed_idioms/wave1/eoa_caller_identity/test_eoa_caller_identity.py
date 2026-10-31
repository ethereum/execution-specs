r"""
Class #25: caller identity as an EOA test.

`require(tx.origin == msg.sender)` is the deployed way to assert "I was
called directly by a wallet, with no contract in between" -- flash-loan
guards, anti-bot and anti-sandwich checks, "humans only" mint gates. L2
measured the shape at **8,097 distinct runtime code hashes across 6,126
addresses**, FP 0.0; L1 independently measured a closely related shape at
**24,044 addresses / 19,017 runtimes**.

The invariant the deployed code believes: the equality holds exactly when
no contract frame intervenes. EELS states the same belief in a docstring
-- `origin()`: *"The origin address can only be an EOA."*
(`amsterdam/vm/instructions/environment.py:89-92`, CHECKED).

**This is the caller-side half of the break that class #22 covers on the
callee side.** A delegated EOA has 23 bytes of code --
`EOA_DELEGATION_MARKER = b"\xef\x01\x00"` plus a 20-byte address
(`vm/eoa_delegation.py:36`) -- and `EXTCODESIZE` reports it raw with no
delegation resolution (`vm/instructions/environment.py:357`). So from
Prague the two deployed "is this an EOA" tests answer **differently for
the same account**: `code.length > 0` says contract, `tx.origin ==
msg.sender` says wallet. Neither is right, and nothing reconciles them.

Measured here (all CHECKED, `tests/tools/test_cls25_origin_probe.py`):

```text
shape                         ORIGIN==CALLER   EXTCODESIZE(CALLER)
direct EOA -> gate                   1                 0
EOA -> relay -(CALL)-> gate          0                35   (the relay)
EOA -> entrypoint -> acct -> gate    0                35   (the account)
EOA -> proxy -(DELEGATECALL)->       1                 0   control, by design
7702 self-sponsored EOA(code)        1                23   THE BREAK
7702 sponsored by a relayer          0                23   gate still rejects
```

Two failure directions, and the corpus needs both:

* **false positive** (EIP-7702, self-sponsored): the gate passes code.
  A delegated EOA can batch, loop and re-enter atomically while every
  "humans only" gate reads it as a bare wallet.
* **false negative** (account abstraction): the gate rejects a real
  user. Under ERC-4337 the bundler is the origin and the account is the
  sender, so `tx.origin == msg.sender` is false for a legitimate human.
  The 6,126 addresses carrying this gate exclude smart-account users
  outright.

No repricing breaks any of this, which is why class #25 is in the
semantic-identity family and not in the gas-shaped part of the
catalogue.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    AuthorizationTuple,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-7702.md"
REFERENCE_SPEC_VERSION = "N/A"

# b"\xef\x01\x00" (3) + a 20-byte address, vm/eoa_delegation.py:36-38.
# A semantic constant, not a cost -- SCHEMA §4.1's prohibition on pinning
# gas numbers does not reach it.
DELEGATION_DESIGNATOR_LENGTH = 23


def _gate(
    pre: Alloc,
    storage: Storage,
    *,
    compare_to: Address,
    compare_label: str,
    origin_equals_caller: int,
    caller_code: int,
    caller_matches: int,
    entries: int,
    raw_codesize: bool = False,
) -> Address:
    """
    The deployed gate, instrumented.

    Commits four readings: the equality the gate actually tests, whether
    the caller carries code at all (class #22's test, for contrast), who
    the caller is, and how many times the gate was entered in this
    transaction. The entry counter is not decoration -- without it a
    gate that never ran would leave zeros, and zeros are the expected
    answer for two of the three arms below.
    """
    entries_slot = storage.store_next(entries, "times_the_gate_was_entered")
    return pre.deploy_contract(
        Op.SSTORE(
            storage.store_next(
                origin_equals_caller, "origin_equals_caller"
            ),
            Op.EQ(Op.ORIGIN, Op.CALLER),
        )
        + Op.SSTORE(
            storage.store_next(
                caller_code,
                "caller_code_size" if raw_codesize else "caller_has_code",
            ),
            Op.EXTCODESIZE(Op.CALLER)
            if raw_codesize
            else Op.GT(Op.EXTCODESIZE(Op.CALLER), 0),
        )
        + Op.SSTORE(
            storage.store_next(caller_matches, compare_label),
            Op.EQ(Op.CALLER, compare_to),
        )
        + Op.SSTORE(entries_slot, Op.ADD(Op.SLOAD(entries_slot), 1))
        + Op.STOP
    )


# ----------------------------------------------------------------------
# 1. the sound form, on every fork
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "shape,origin_equals_caller,caller_has_code",
    [
        pytest.param("direct", 1, 0, id="direct_wallet_call"),
        pytest.param("via_call", 0, 1, id="one_contract_frame"),
        pytest.param("entrypoint", 0, 1, id="erc4337_entry_point"),
    ],
)
@pytest.mark.valid_from("Berlin")
def test_origin_equals_caller_only_when_no_contract_frame_intervenes(
    state_test: StateTestFiller,
    pre: Alloc,
    shape: str,
    origin_equals_caller: int,
    caller_has_code: int,
) -> None:
    """
    Test the sound form of the gate, pinned from both sides.

    `direct_wallet_call` is the positive: an EOA calls the gate itself,
    so ORIGIN and CALLER are the same account and that account has no
    code. `one_contract_frame` is the negative: a single relay contract
    between them is enough to break the equality. Both arms are in one
    test so the discriminator is pinned rather than assumed -- a gate
    that always answered 1, or always 0, would be caught.

    `erc4337_entry_point` is the deployed negative that matters. Under
    account abstraction the bundler signs the transaction and the
    EntryPoint calls the smart account, which calls the application:
    two contract frames, so the gate rejects a real human user. This is
    the *false negative* direction, and it is the reason the equality is
    not a usable wallet test even before EIP-7702 is considered.

    A failure means `ORIGIN` or `CALLER` changed meaning, and 6,126
    deployed addresses' access gates changed behaviour with it.
    """
    sender = pre.fund_eoa()
    storage = Storage()
    gate = _gate(
        pre,
        storage,
        compare_to=sender,
        compare_label="caller_is_the_tx_sender",
        origin_equals_caller=origin_equals_caller,
        caller_code=caller_has_code,
        caller_matches=1 if shape == "direct" else 0,
        entries=1,
    )

    if shape == "direct":
        target = gate
    elif shape == "via_call":
        target = pre.deploy_contract(
            Op.POP(Op.CALL(gas=Op.GAS, address=gate)) + Op.STOP
        )
    else:
        account = pre.deploy_contract(
            Op.POP(Op.CALL(gas=Op.GAS, address=gate)) + Op.STOP
        )
        target = pre.deploy_contract(
            Op.POP(Op.CALL(gas=Op.GAS, address=account)) + Op.STOP
        )

    tx = Transaction(to=target, state_gas_reservoir=0, sender=sender)
    state_test(pre=pre, post={gate: Account(storage=storage)}, tx=tx)


@pytest.mark.valid_from("Berlin")
def test_a_delegatecall_proxy_keeps_the_caller_so_the_gate_still_passes(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the negative control: a contract frame that is meant to be
    transparent.

    `DELEGATECALL` passes its own caller through -- `caller=evm.caller`
    rather than `caller=evm.current_target`
    (`amsterdam/vm/instructions/system.py:866`, CHECKED, and the only
    call-like instruction that does). So an EOA reaching the gate's code
    through an upgradeable proxy still satisfies `tx.origin ==
    msg.sender`, even though a contract frame unquestionably intervened.

    **This is correct behaviour, not a break**, and that is exactly why
    it belongs here: it shows the invariant cannot be stated as "no
    contract frame intervenes" but only as "no frame that *rewrites the
    caller* intervenes". Pinning it keeps the next person from
    "repairing" the gate by making proxies opaque, which would break
    every deployed proxy at once.

    Measured: ORIGIN == CALLER == the EOA, and `EXTCODESIZE(CALLER)` is
    0, so here the two deployed EOA tests agree. They disagree only for
    a delegated EOA, below.
    """
    sender = pre.fund_eoa()
    storage = Storage()
    gate = _gate(
        pre,
        storage,
        compare_to=sender,
        compare_label="caller_is_the_tx_sender",
        origin_equals_caller=1,
        caller_code=0,
        caller_matches=1,
        entries=1,
    )
    proxy = pre.deploy_contract(
        Op.POP(Op.DELEGATECALL(gas=Op.GAS, address=gate)) + Op.STOP
    )
    tx = Transaction(to=proxy, state_gas_reservoir=0, sender=sender)
    # the gate's code runs in the proxy's storage, so the readings land
    # on the proxy
    state_test(pre=pre, post={proxy: Account(storage=storage)}, tx=tx)


# ----------------------------------------------------------------------
# 2. the EIP-7702 break
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "self_sponsored,origin_equals_caller,entries",
    [
        pytest.param(True, 1, 2, id="self_sponsored"),
        pytest.param(False, 0, 2, id="sponsored_by_a_relayer"),
    ],
)
@pytest.mark.valid_from("Prague")
def test_a_delegated_eoa_passes_the_eoa_gate_while_carrying_code(
    state_test: StateTestFiller,
    pre: Alloc,
    self_sponsored: bool,
    origin_equals_caller: int,
    entries: int,
) -> None:
    """
    Test a delegated EOA satisfies the gate while executing code.

    The signer is an externally owned account throughout: it signed one
    authorization, nothing more. In the `self_sponsored` arm it also
    sends the transaction, so when its delegated code calls the gate,
    ORIGIN and CALLER are both the signer and the gate reads "a wallet
    called me directly" -- while the caller is in fact arbitrary
    contract code that has already made one call and is about to make
    another. The entry counter is **2** in one transaction, which is the
    concrete harm: a "one action per wallet per transaction" gate is now
    a no-op, and so is every flash-loan guard built on the same test.

    Three things are asserted together, and the combination is the
    finding:

    ```text
    origin_equals_caller   1     the gate lets it through
    caller_code_size      23     the caller carries a delegation designator
    caller_is_the_signer   1     it is the EOA itself, not a proxy
    ```

    So `tx.origin == msg.sender` answers "wallet" for an account that
    `code.length > 0` answers "contract" for -- the same account, the
    same block, two deployed idioms, opposite verdicts. The 23 is the
    semantic constant, not a cost: `EOA_DELEGATION_MARKER` (3 bytes) plus
    a 20-byte address.

    `sponsored_by_a_relayer` is the boundary that keeps the finding
    honest. When someone else pays, ORIGIN is the relayer and the gate
    *does* reject, so the hazard is specific to a self-sponsored type-4
    transaction rather than to delegation as such. Both arms still show
    `caller_code_size == 23`, so class #22's break is present in both
    while this class's break is present in only one.

    A failure means either the designator format moved, or `ORIGIN`
    stopped being the transaction sender when that sender runs code -- in
    which case 6,126 deployed gates change behaviour again.
    """
    signer = pre.fund_eoa()
    storage = Storage()
    gate = _gate(
        pre,
        storage,
        compare_to=signer,
        compare_label="caller_is_the_signer",
        origin_equals_caller=origin_equals_caller,
        caller_code=DELEGATION_DESIGNATOR_LENGTH,
        caller_matches=1,
        entries=entries,
        raw_codesize=True,
    )
    # two calls in one transaction: atomic batching behind a gate that
    # believes it is talking to a bare wallet
    impl = pre.deploy_contract(
        Op.POP(Op.CALL(gas=Op.GAS, address=gate))
        + Op.POP(Op.CALL(gas=Op.GAS, address=gate))
        + Op.STOP
    )
    if self_sponsored:
        # a self-sponsored type-4 transaction bumps the sender's nonce
        # from 0 to 1 first, so the authorization nonce is 1
        # (tests/prague/eip7702_set_code_tx/test_set_code_txs.py:85).
        tx = Transaction(
            to=signer,
            state_gas_reservoir=0,
            sender=signer,
            authorization_list=[
                AuthorizationTuple(address=impl, nonce=1, signer=signer)
            ],
        )
    else:
        tx = Transaction(
            to=signer,
            state_gas_reservoir=0,
            sender=pre.fund_eoa(),
            authorization_list=[
                AuthorizationTuple(address=impl, nonce=0, signer=signer)
            ],
        )
    state_test(pre=pre, post={gate: Account(storage=storage)}, tx=tx)
