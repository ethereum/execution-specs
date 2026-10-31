"""
Candidate class, identity dimension: assigning an opcode byte changes what
code *does* without changing what code *is*.

Class #22 (`tests/code_presence_identity/`) pins the deployed
`isContract(a) == (a.code.length > 0)` idiom. The adjacent and equally
deployed idiom is the **code-hash pin**: `EXTCODEHASH(a) == <expected>`,
used to assert "this is the implementation I audited" -- clone
verification, singleton checks, factory-template checks, allowlists keyed
by runtime hash.

Two halves, and they point in opposite directions.

**(a) A code-hash pin cannot see an opcode assignment.** `EXTCODEHASH`
hashes the raw deployed bytes and `EXTCODESIZE` counts them; neither
consults the opcode table (`amsterdam/vm/instructions/environment.py`,
`codesize = U256(len(code))`). So a contract whose bytes include `0x4B`
or `0x1E` keeps *exactly* the same size and hash across the fork that
turns those bytes into `SLOTNUM` and `CLZ`, while its behaviour may
change completely. A pin that was green before the fork is green after
it. This is the structural reason every identity-based safety check is
blind to this entire class -- the same way every gas-shaped archetype is.

**(b) The reverse: identical behaviour, different identity.** `PUSH0`
exists only to spell `PUSH1 0x00` in one byte instead of two. The two
contracts below compute the same value and commit the same storage, and
their sizes differ by exactly 1 and their hashes differ completely. So
recompiling an unchanged source with a `PUSH0`-capable compiler breaks
every hash pin against it, with no behavioural change to point at. This
is the mechanism behind the 2023 "solc 0.8.20 defaults to Shanghai"
breakage, from the identity side rather than the execution side.

**Deployed witness.** Protocol constant plus idiom, no single address
witness claimed here: the `EXTCODEHASH`-pin population belongs to class
#22's lens measurement (`EXTCODESIZE`/code-identity gates at 618,693
distinct runtime code hashes over 2,417,615 addresses, FP 0/8) and this
file does not re-measure it. Half (b)'s witness is the compiler, not a
contract: every runtime compiled by solc >= 0.8.20 with default settings
differs from its pre-Shanghai build.

**Prior art (CHECKED).** `tests/shanghai/eip3855_push0/test_push0.py` is
162 lines and asserts `PUSH0`'s stack and gas behaviour; it does not
compare a `PUSH0` build with its `PUSH1 0x00` twin, and it touches
neither `EXTCODEHASH` nor `EXTCODESIZE` (0 grep hits). The 7939/7843/8024
suites assert nothing about code identity either.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    keccak256,
)

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3855.md"
REFERENCE_SPEC_VERSION = "N/A"  # no single spec owns the invariant

VALUE = 0x1234

# Every byte four EIPs later claimed, plus the two that were never
# claimed, planted where control flow jumps over them.
LATER_ASSIGNED = b"\x5f\x1e\x4b\xe6\x80\xe7\x80\xe8\x8e\xfe\x0c"


def raw(code: bytes) -> Bytecode:
    """Emit literal bytes, with no stack bookkeeping claimed for them."""
    return Bytecode(code, popped_stack_items=0, pushed_stack_items=0)


@pytest.mark.valid_from("Berlin")
def test_code_identity_does_not_move_when_a_byte_is_assigned(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the size and hash of code containing later-assigned bytes are
    the same on every fork.

    One fixed byte string is deployed and three things are asserted from
    inside the EVM: it still runs and commits, its `EXTCODESIZE` is the
    exact byte count, and its `EXTCODEHASH` is the exact `keccak256` of
    those bytes. The hash literal is computed here in Python and is the
    **same literal on all eight forks**, which is the whole point: a
    deployed `EXTCODEHASH == <audited hash>` pin reads identically before
    and after `0x4B` becomes `SLOTNUM`, so it cannot be the thing that
    notices.

    Fork-identity is therefore demonstrated rather than assumed -- one
    literal, every fork, no per-fork table.
    """
    dest = 3 + len(LATER_ASSIGNED)
    code = (
        Op.PUSH1(dest)
        + Op.JUMP
        + raw(LATER_ASSIGNED)
        + Op.JUMPDEST
        + Op.SSTORE(0, VALUE)
        + Op.STOP
    )
    code_bytes = bytes(code)
    assert code_bytes[dest] == 0x5B, "the JUMPDEST moved; fix `dest`"

    target = pre.deploy_contract(code)

    storage = Storage()
    prober = pre.deploy_contract(
        Op.SSTORE(
            storage.store_next(1, "target_ran"),
            Op.CALL(gas=Op.GAS, address=target),
        )
        + Op.SSTORE(
            storage.store_next(len(code_bytes), "extcodesize"),
            Op.EXTCODESIZE(target),
        )
        + Op.SSTORE(
            storage.store_next(keccak256(code_bytes), "extcodehash"),
            Op.EXTCODEHASH(target),
        )
        + Op.STOP
    )

    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={
            target: Account(storage={0: VALUE}),
            prober: Account(storage=storage),
        },
        tx=tx,
    )


@pytest.mark.valid_from("Shanghai")
def test_push0_changes_identity_without_changing_behaviour(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test the `PUSH0` and `PUSH1 0x00` builds of one routine behave
    identically and hash differently.

    Both contracts write `VALUE` to the slot `PUSH0`/`PUSH1 0x00` names,
    so their behaviour is asserted equal by observing the same committed
    effect in both. Then the prober commits three facts about identity:

    * `EXTCODESIZE(push1) - EXTCODESIZE(push0) == 1`, the byte `PUSH0`
      saves;
    * the two `EXTCODEHASH` values are different;
    * each hash equals the `keccak256` of its own exact bytes.

    So a hash pin fails across a recompilation that changes nothing
    observable. The `PUSH0` arm also requires `0x5F` to be a valid
    instruction, which is what makes this test detectable by un-assigning
    it.
    """
    push0_code = Op.PUSH2(VALUE) + Op.PUSH0 + Op.SSTORE + Op.STOP
    push1_code = Op.PUSH2(VALUE) + Op.PUSH1(0) + Op.SSTORE + Op.STOP
    p0, p1 = bytes(push0_code), bytes(push1_code)
    assert len(p1) - len(p0) == 1
    assert keccak256(p0) != keccak256(p1)

    a = pre.deploy_contract(push0_code)
    b = pre.deploy_contract(push1_code)

    storage = Storage()
    prober = pre.deploy_contract(
        Op.SSTORE(
            storage.store_next(1, "push0_build_ran"),
            Op.CALL(gas=Op.GAS, address=a),
        )
        + Op.SSTORE(
            storage.store_next(1, "push1_build_ran"),
            Op.CALL(gas=Op.GAS, address=b),
        )
        + Op.SSTORE(
            storage.store_next(1, "push1_build_is_one_byte_longer"),
            Op.SUB(Op.EXTCODESIZE(b), Op.EXTCODESIZE(a)),
        )
        + Op.SSTORE(
            storage.store_next(1, "hashes_differ"),
            Op.ISZERO(Op.EQ(Op.EXTCODEHASH(a), Op.EXTCODEHASH(b))),
        )
        + Op.SSTORE(
            storage.store_next(keccak256(p0), "push0_build_hash"),
            Op.EXTCODEHASH(a),
        )
        + Op.SSTORE(
            storage.store_next(keccak256(p1), "push1_build_hash"),
            Op.EXTCODEHASH(b),
        )
        + Op.STOP
    )

    tx = Transaction(to=prober, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={
            a: Account(storage={0: VALUE}),
            b: Account(storage={0: VALUE}),
            prober: Account(storage=storage),
        },
        tx=tx,
    )
