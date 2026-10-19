"""
Verify where a three-deep call chain leaves its storage writes, and which
account a trailing SELFDESTRUCT removes, across the call opcodes that
differ in whether they switch the executing context.

Ported from:
state_tests/stCallCodes/callcallcallcode_001_SuicideEndFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_SuicideEndFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_SuicideEndFiller.json

@manually-enhanced: Do not overwrite. The three fillers are one chain
under a per-directory opcode substitution -- `stCallCodes` runs it
literally, `stCallDelegateCodesHomestead` swaps CALLCODE for
DELEGATECALL, and the `*CallCode*` variant additionally swaps CALL for
CALLCODE -- so they collapse to one test parametrized on the chain.

The post state is then derived from the opcodes rather than transcribed:
CALL moves the context to the callee while CALLCODE and DELEGATECALL keep
the caller's, and that alone decides which account each slot lands in and
which account the SELFDESTRUCT empties. `stCallCodes`' own post asserted
only two balances, so its storage outcome had never actually been
checked.

The beneficiary travels down as calldata because the fillers' hardcoded
addresses formed a reference cycle -- the third contract names the second
-- which is what forced `pre_alloc_mutable` on all three.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Fork,
    Op,
    Opcodes,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Cancun

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


# The ported argument/return window. Its first word carries the
# SELFDESTRUCT beneficiary down the chain.
WINDOW = 0x40

CONTRACT_BALANCE = 1

# The per-directory substitutions of the filler family's `001` chain.
CHAINS = {
    "call_call_callcode": (Op.CALL, Op.CALL, Op.CALLCODE),
    "call_call_delegatecall": (Op.CALL, Op.CALL, Op.DELEGATECALL),
    "callcode_callcode_delegatecall": (
        Op.CALLCODE,
        Op.CALLCODE,
        Op.DELEGATECALL,
    ),
}


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcallcallcode_001_SuicideEndFiller.json",
        "state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_SuicideEndFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("SpuriousDragon")
@pytest.mark.parametrize("chain", CHAINS.values(), ids=CHAINS.keys())
def test_callcallcallcode_001_suicide_end(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    chain: tuple[Opcodes, Opcodes, Opcodes],
) -> None:
    """Chained calls write where their context points; the last one dies."""
    sender = pre.fund_eoa()

    # Every link leaves `value` at its default, so the value-passing forms
    # assemble against the same argument list as DELEGATECALL, and leaves
    # `gas` alone so each frame forwards everything it holds.
    #
    # Deployed leaf-first: threading the beneficiary through calldata is
    # what breaks the fillers' address cycle and leaves a plain DAG.
    leaf = pre.deploy_contract(
        code=Op.SSTORE(key=3, value=0x1) + Op.STOP,
        balance=CONTRACT_BALANCE,
    )
    suicider = pre.deploy_contract(
        code=Op.SSTORE(
            key=2,
            value=chain[2](
                address=leaf,
                args_offset=0x0,
                args_size=WINDOW,
                ret_offset=0x0,
                ret_size=WINDOW,
            ),
        )
        + Op.SELFDESTRUCT(address=Op.CALLDATALOAD(0x0))
        + Op.STOP,
        balance=CONTRACT_BALANCE,
    )
    # Each frame gets fresh memory, so the beneficiary has to be restaged
    # from calldata before being forwarded another level down.
    middle = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(0x0))
        + Op.SSTORE(
            key=1,
            value=chain[1](
                address=suicider,
                args_offset=0x0,
                args_size=WINDOW,
                ret_offset=0x0,
                ret_size=WINDOW,
            ),
        )
        + Op.STOP,
        balance=CONTRACT_BALANCE,
    )
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=middle)
        + Op.SSTORE(
            key=0,
            value=chain[0](
                address=middle,
                args_offset=0x0,
                args_size=WINDOW,
                ret_offset=0x0,
                ret_size=WINDOW,
            ),
        )
        + Op.STOP,
        balance=CONTRACT_BALANCE,
    )

    # CALL switches the executing context to the callee; CALLCODE and
    # DELEGATECALL run the callee's code as the caller. Frame `i` writes
    # slot `i` into whichever account it is executing as.
    context = [target]
    for call_opcode, callee in zip(
        chain, (middle, suicider, leaf), strict=True
    ):
        context.append(callee if call_opcode == Op.CALL else context[-1])

    # The SELFDESTRUCT sits in the third frame, so it takes whichever
    # account that frame is running as -- not necessarily its own code's.
    destroyed = context[2]
    assert destroyed is not middle, "beneficiary must outlive the transfer"

    written: dict[Address, dict[int, int]] = {}
    for slot, account in zip(range(4), context, strict=True):
        written.setdefault(account, {})[slot] = 0x1

    balance = dict.fromkeys((target, middle, suicider, leaf), CONTRACT_BALANCE)
    balance[middle] += balance[destroyed]
    balance[destroyed] = 0

    tx = Transaction(sender=sender, to=target)

    # Before EIP-6780 the destroyed account is gone outright; from Cancun
    # on it keeps its code and storage and only surrenders its balance.
    post: dict[Address, Account | None] = {}
    for account in (target, middle, suicider, leaf):
        post[account] = (
            Account(storage=written.get(account, {}), balance=balance[account])
            if account is not destroyed or fork >= Cancun
            else Account.NONEXISTENT
        )

    state_test(pre=pre, post=post, tx=tx)
