"""
Class #23: counterfactual address validity.

A contract derives an address it has **not yet deployed to**, commits to it
— pre-funds it, records it as an owner, writes it into a registry — and
only later puts code there. Counterfactual wallets, escrow pre-funding,
deterministic factories and cross-chain address parity all rest on one
invariant:

> the address the contract derived is the address the contract lands at.

Two derivations are in deployed use, and both are reimplemented *in EVM
bytecode* rather than looked up:

```text
CREATE2   keccak256(0xff || deployer || salt || keccak256(initcode))[12:]
          amsterdam/utils/address.py:88-93
CREATE    keccak256(rlp([deployer, nonce]))[12:]
          amsterdam/utils/address.py:60-63
```

**This class is semantic, not gas-shaped.** Nothing here moves if a price
moves; it moves if a derivation input, the hash preimage layout, the
truncation side, or the nonce-increment rule changes. `code_presence_identity`
is the precedent: EIP-7702 broke the most deployed identity idiom on
Ethereum while repricing nothing.

**Witnesses, read out of `registry/L2-bytecode.jsonl`** rather than from
the brief, whose figures conflated two columns — `instances` counts
*witnessing program points*, not addresses:

```text
shape                runtimes  addresses  program points  FP     confidence
adr.create2_derive      2,723      2,945           3,217  0.0    CHECKED
adr.create_derive         187        205             366  0.25   INFERRED
```

L2's `adr.create2_derive` detector is literally the shape these tests
build: *"a SHA3 site whose preimage length is exactly 85 (0x55)"*. Its
registry `invariant` field is this class's invariant verbatim, and its
calibration positive is **a major NFT exchange's conduit derivation**. Exemplar
`<address withheld>` pc 1870. An independent
source-side lens corroborates at a much larger scale: L1's *"CREATE2
address derived in source"* is **8,172 distinct runtimes over 22,270
confirmed source files**, exact count mode, hand-measured precision 1.0.

The CREATE-from-nonce population is **small and its FP rate is 0.25** — 2
of 8 hand-disassembled hits were storage-slot computations over 23 bytes,
not address derivations — so it is stated with that caveat rather than
leaned on. It is nonetheless **CHECKED on one named contract**: a gas-token contract
`<address withheld>` derives its children's
addresses from its own nonce in order to free them.

**Prior art, and what is left uncovered by it (CHECKED).** The official
suite derives counterfactual addresses **in Python** and then asserts the
contract landed there:
`tests/amsterdam/eip7997_deterministic_factory_contract/test_factory.py`
(1,437 lines), `tests/cancun/eip6780_selfdestruct/test_collision_selfdestruct.py`,
`tests/amsterdam/eip8037_state_creation_gas_cost_increase/test_state_gas_create.py`,
`tests/berlin/eip2929_gas_cost_increases/test_warm_status_revert.py` — every
one of them via `compute_create2_address(...)` from
`execution_testing.test_types.helpers`. That checks the client against
EEST's own Python reimplementation. It does **not** check the deployed
idiom, which is a `keccak256` built in EVM memory out of literals a
contract committed to years ago. Nothing in `tests/` hashes a CREATE2
preimage with `SHA3`; the only EVM-side `SHA3` in the 7997 directory hashes
the factory's *code* (`test_factory.py:86`). So a change on the contract's
side of the equality — the opcode, the memory layout the contract assumed —
is invisible to the official suite and visible here. The tests below assert
*both* sides: the in-EVM derivation against the landing site, and the
landing site against the Python helper, so a divergence is attributed
rather than merely detected.

**What a failure means.** Funds already sent to a counterfactual address
are stranded at an address no deployment will ever reach, and every
registry entry, allowlist and cross-chain mapping that pinned the old
derivation now points at the wrong account.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Initcode,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
    compute_create2_address,
    compute_create_address,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# Low 20 bytes of a keccak output: the `[-20:]` in `compute_*_address`,
# expressed the way deployed assembly expresses it.
MASK_160 = (1 << 160) - 1

# The CREATE2 preimage is 85 bytes: 1 + 20 + 32 + 32. Laid out so the
# 20-byte deployer sits right-aligned in the word at 0x00, which puts the
# preimage at 0x0b..0x5f -- the canonical layout every deployed
# `computeAddress` uses.
PREIMAGE_START = 0x0B
PREIMAGE_LEN = 0x55
CREATE2_PREFIX = 0xFF
INITCODE_AT = 0x80

# The CREATE preimage is 23 bytes: 0xd6 0x94 || deployer(20) || nonce(1).
# `0xd6 = 0xc0 + 22` is the RLP list header for a 22-byte payload and
# `0x94 = 0x80 + 20` the string header for the address; a single-byte nonce
# in [0x01, 0x7f] is its own RLP encoding.
RLP_LIST_HEADER = 0xD6
RLP_ADDRESS_HEADER = 0x94
RLP_START = 0x0A
RLP_LEN = 0x17

# EIP-7997 places the Arachnid deterministic deployment proxy here. The
# address is a *literal in deployed code* -- that is the point of the
# class: a counterfactual wallet factory hardcoded it and derives against
# it forever.
DETERMINISTIC_FACTORY = Address(0x4E59B44847B379578588920CA78FBF26C0B4956C)

SLOT_DERIVED = 0x01
SLOT_ACTUAL = 0x02
SLOT_AGREE = 0x03
SLOT_PREFUND_OK = 0x04
SLOT_BALANCE_BEFORE = 0x05
SLOT_BALANCE_AFTER = 0x06

PREFUND = 7


def _derive_create2(
    deployer: Bytecode | Address, salt_src: Bytecode
) -> Bytecode:
    """
    Build `keccak256(0xff || deployer || salt || keccak256(initcode))[12:]`
    in memory and leave the derived address on the stack.

    The init code is already at `INITCODE_AT`, length `CALLDATASIZE - 32`.
    Writes run high-to-low so the `0xff` byte is written *after* the word
    holding the deployer, which is the only ordering constraint.
    """
    initcode_len = Op.SUB(Op.CALLDATASIZE, 32)
    return (
        Op.MSTORE(0x40, Op.SHA3(INITCODE_AT, initcode_len))
        + Op.MSTORE(0x20, salt_src)
        + Op.MSTORE(0x00, deployer)
        + Op.MSTORE8(PREIMAGE_START, CREATE2_PREFIX)
        + Op.AND(Op.SHA3(PREIMAGE_START, PREIMAGE_LEN), MASK_160)
    )


def _create2_factory(prefund: bool) -> Bytecode:
    """
    Derive, optionally pre-fund, then deploy -- in that order.

    The order is the whole idiom: the commitment happens while the address
    is still empty. `prefund` sends value to an account that does not
    exist yet, exactly as an escrow or a counterfactual wallet funder does,
    and the balance has to survive the later deployment.
    """
    initcode_len = Op.SUB(Op.CALLDATASIZE, 32)
    body = (
        Op.CALLDATACOPY(INITCODE_AT, 0x20, initcode_len)
        + Op.SSTORE(
            SLOT_DERIVED,
            _derive_create2(Op.ADDRESS, Op.CALLDATALOAD(0)),
        )
    )
    if prefund:
        body += (
            # gas=0: a value-bearing call carries the 2,300 stipend, and
            # the recipient has no code to run. Forwarding `GAS` here would
            # make this test depend on the 63/64 rule, which is class #4.
            Op.SSTORE(
                SLOT_PREFUND_OK,
                Op.CALL(0, Op.SLOAD(SLOT_DERIVED), PREFUND, 0, 0, 0, 0),
            )
            + Op.SSTORE(
                SLOT_BALANCE_BEFORE, Op.BALANCE(Op.SLOAD(SLOT_DERIVED))
            )
        )
    body += (
        Op.SSTORE(
            SLOT_ACTUAL,
            Op.CREATE2(
                value=0,
                offset=INITCODE_AT,
                size=initcode_len,
                salt=Op.CALLDATALOAD(0),
            ),
        )
        + Op.SSTORE(
            SLOT_AGREE,
            Op.EQ(Op.SLOAD(SLOT_DERIVED), Op.SLOAD(SLOT_ACTUAL)),
        )
    )
    if prefund:
        body += (
            Op.SSTORE(SLOT_BALANCE_AFTER, Op.BALANCE(Op.SLOAD(SLOT_DERIVED)))
            # call the freshly deployed contract at the *derived* address,
            # so the test shows the counterfactual account is live rather
            # than merely present
            + Op.POP(
                Op.CALL(Op.GAS, Op.SLOAD(SLOT_DERIVED), 0, 0, 0, 0, 0)
            )
        )
    return body + Op.STOP


# Four shapes a deployed factory actually sees: a zero salt, a salt with the
# top bit set (so a sign-extension bug in the preimage would show), the
# maximum salt, and empty init code -- whose `keccak256(b"")` is the one
# preimage component a contract cannot get from its own calldata.
CREATE2_CASES = [
    pytest.param(0, Initcode(deploy_code=Op.STOP), id="zero_salt"),
    pytest.param(
        (1 << 255) | 0xDEADBEEF,
        Initcode(deploy_code=Op.SSTORE(0, 1) + Op.STOP),
        id="high_salt_stateful_runtime",
    ),
    pytest.param(
        2**256 - 1, Initcode(deploy_code=Op.STOP), id="max_salt"
    ),
    pytest.param(0x42, Bytecode(), id="empty_initcode"),
]


@pytest.mark.parametrize("salt,initcode", CREATE2_CASES)
@pytest.mark.valid_from("Berlin")
def test_create2_counterfactual_address_is_where_the_contract_lands(
    state_test: StateTestFiller,
    pre: Alloc,
    salt: int,
    initcode: Bytecode,
) -> None:
    """
    Test an in-EVM CREATE2 derivation equals the address CREATE2 uses.

    The factory builds the 85-byte preimage itself — `0xff`, its own
    `ADDRESS`, the salt from calldata, and `SHA3` over the init code it was
    handed — masks the hash to 20 bytes, and commits that address to
    storage *before* the `CREATE2` runs. Three markers are asserted: the
    derived address, the address `CREATE2` actually returned, and their
    equality. All three are stated as the Python helper computes them, so
    the test triangulates the client, EEST's reimplementation and the
    contract's own arithmetic against each other.

    A failure means every deployed `computeAddress` is wrong.
    """
    factory = pre.deploy_contract(_create2_factory(prefund=False))
    expected = compute_create2_address(factory, salt, initcode)

    storage = Storage().set_next_slot(SLOT_DERIVED)
    storage.store_next(int.from_bytes(expected, "big"), "derived_in_evm")
    storage.store_next(int.from_bytes(expected, "big"), "create2_returned")
    storage.store_next(1, "derivation_agrees_with_create2")

    tx = Transaction(
        to=factory,
        gas_limit=15_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        data=salt.to_bytes(32, "big") + bytes(initcode),
    )
    state_test(
        pre=pre,
        post={
            factory: Account(storage=storage),
            expected: Account(code=initcode.deploy_code)
            if isinstance(initcode, Initcode)
            else Account(code=b""),
        },
        tx=tx,
    )


@pytest.mark.parametrize(
    "salt,initcode", [CREATE2_CASES[1]], ids=["high_salt_stateful_runtime"]
)
@pytest.mark.valid_from("Berlin")
def test_counterfactual_prefunding_survives_the_deployment(
    state_test: StateTestFiller,
    pre: Alloc,
    salt: int,
    initcode: Bytecode,
) -> None:
    """
    Test value sent to a derived address before deployment is still there.

    This is the commitment that makes the class matter rather than being a
    hashing curiosity. The factory derives the address, **sends ether to an
    account that does not exist**, and only then deploys. Six markers pin
    four facts: the derivation agrees with `CREATE2` (three markers, as
    above), the value-bearing call to a codeless derived address succeeds,
    the balance is there before the deployment, and it is unchanged after
    it. So: the balance arrives at the derived address while it is still
    codeless, the deployment succeeds at that same address even though it
    already holds a balance (`account_deployable` tests nonce and code
    only, `state_tracker.py:362-370`), and the balance is unchanged
    afterwards. The factory then calls the derived address, and the
    runtime's own `SSTORE` is asserted — so the account is shown to be
    *live* at the counterfactual address, not merely present.

    If the derivation and the landing site ever diverge, the pre-funding is
    stranded at an address nothing will ever deploy to. Nothing reverts —
    the factory's own `CREATE2` succeeds — so the loss is silent.
    """
    factory = pre.deploy_contract(
        _create2_factory(prefund=True), balance=PREFUND
    )
    expected = compute_create2_address(factory, salt, initcode)
    addr = int.from_bytes(expected, "big")

    storage = Storage().set_next_slot(SLOT_DERIVED)
    storage.store_next(addr, "derived_in_evm")
    storage.store_next(addr, "create2_returned")
    storage.store_next(1, "derivation_agrees_with_create2")
    storage.store_next(1, "prefunding_call_succeeded")
    storage.store_next(PREFUND, "balance_before_deployment")
    storage.store_next(PREFUND, "balance_after_deployment")

    tx = Transaction(
        to=factory,
        gas_limit=15_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        data=salt.to_bytes(32, "big") + bytes(initcode),
    )
    state_test(
        pre=pre,
        post={
            factory: Account(storage=storage),
            expected: Account(
                balance=PREFUND,
                code=initcode.deploy_code,
                storage={0: 1},
            ),
        },
        tx=tx,
    )


# --------------------------------------------------------------------------
# The CREATE-from-nonce form
# --------------------------------------------------------------------------

# A single `STOP`: valid init code that deposits no code, so a throwaway
# CREATE costs nothing beyond the account.
THROWAWAY_INITCODE_LEN = 1


def _create_factory(nonce: int) -> Bytecode:
    """
    Burn nonces up to `nonce`, derive the RLP address, then CREATE.

    A contract's nonce is 1 at deployment (EIP-161) and each `CREATE`
    increments it, so after `nonce - 1` throwaway creates the next one
    lands at `keccak256(rlp([self, nonce]))[12:]`.
    """
    body = Bytecode()
    for _ in range(nonce - 1):
        # init code = memory[0..1] = 0x00 = STOP, deposits nothing
        body += Op.MSTORE(0, 0) + Op.POP(
            Op.CREATE(value=0, offset=0, size=THROWAWAY_INITCODE_LEN)
        )
    return (
        body
        + Op.MSTORE(0x00, Op.ADDRESS)
        + Op.MSTORE8(RLP_START, RLP_LIST_HEADER)
        + Op.MSTORE8(RLP_START + 1, RLP_ADDRESS_HEADER)
        + Op.MSTORE8(0x20, nonce)
        + Op.SSTORE(
            SLOT_DERIVED,
            Op.AND(Op.SHA3(RLP_START, RLP_LEN), MASK_160),
        )
        # init code = memory[0x20..0x21]; memory[0x20] is the nonce byte,
        # which for every nonce tested here is a one-byte opcode that
        # halts or is invalid, depositing no code. Use a dedicated word
        # instead so the deployed code is never accidentally meaningful.
        + Op.MSTORE(0x60, 0)
        + Op.SSTORE(
            SLOT_ACTUAL,
            Op.CREATE(value=0, offset=0x60, size=THROWAWAY_INITCODE_LEN),
        )
        + Op.SSTORE(
            SLOT_AGREE,
            Op.EQ(Op.SLOAD(SLOT_DERIVED), Op.SLOAD(SLOT_ACTUAL)),
        )
        + Op.STOP
    )


@pytest.mark.parametrize("nonce", [1, 2, 3], ids=lambda n: f"nonce_{n}")
@pytest.mark.valid_from("Berlin")
def test_create_from_nonce_counterfactual_address(
    state_test: StateTestFiller, pre: Alloc, nonce: int
) -> None:
    """
    Test an in-EVM RLP derivation equals where `CREATE` lands.

    The deployed idiom is a `computeAddress(deployer, nonce)` library that
    builds `0xd6 0x94 || deployer || nonce` in 23 bytes of memory and
    hashes it. It is far rarer than the CREATE2 form — 187 runtimes / 205
    addresses against 2,723 / 2,945 — and its detector's FP rate is 0.25,
    so the population carries that caveat. The named witness does not:
    a gas-token contract walks its own nonce range to address the children it frees.

    Parametrising the nonce is what makes this more than a hash check: it
    pins the **nonce-increment rule** as well as the preimage. Each
    throwaway `CREATE` must advance the creator's nonce by exactly one, or
    the derivation for nonce 2 and 3 points at the wrong account. Both
    halves of that rule have moved before: Spurious Dragon moved the
    increment to *before* the init code runs, and EIP-2681 capped the nonce
    at 2**64-1 (the cap is visible in `generic_create`'s preflight,
    `system.py:96`). A fork that stopped incrementing, or incremented
    twice, would leave the nonce-1 case correct and the others wrong — a
    graded failure that locates the change rather than just reporting one.
    """
    factory = pre.deploy_contract(_create_factory(nonce))
    expected = compute_create_address(address=factory, nonce=nonce)
    addr = int.from_bytes(expected, "big")

    storage = Storage().set_next_slot(SLOT_DERIVED)
    storage.store_next(addr, "derived_in_evm")
    storage.store_next(addr, "create_returned")
    storage.store_next(1, "derivation_agrees_with_create")

    tx = Transaction(
        to=factory,
        gas_limit=15_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
    )
    state_test(pre=pre, post={factory: Account(storage=storage)}, tx=tx)


# --------------------------------------------------------------------------
# EIP-7997: the same derivation against a factory nobody controls
# --------------------------------------------------------------------------


def _factory_client() -> Bytecode:
    """
    Derive against the hardcoded deterministic factory, then call it.

    The factory interprets calldata as `salt (32) || initcode` and returns
    the created address, so the client forwards its own calldata verbatim.
    """
    initcode_len = Op.SUB(Op.CALLDATASIZE, 32)
    return (
        Op.CALLDATACOPY(INITCODE_AT, 0x20, initcode_len)
        + Op.SSTORE(
            SLOT_DERIVED,
            _derive_create2(
                DETERMINISTIC_FACTORY, Op.CALLDATALOAD(0)
            ),
        )
        # forward the whole calldata to the factory; it returns 20 bytes
        + Op.CALLDATACOPY(0x100, 0, Op.CALLDATASIZE)
        + Op.POP(
            Op.CALL(
                gas=Op.GAS,
                address=DETERMINISTIC_FACTORY,
                value=0,
                args_offset=0x100,
                args_size=Op.CALLDATASIZE,
                ret_offset=0x200,
                ret_size=0x20,
            )
        )
        # the factory returns the address left-aligned in 20 bytes
        + Op.SSTORE(SLOT_ACTUAL, Op.SHR(96, Op.MLOAD(0x200)))
        + Op.SSTORE(
            SLOT_AGREE,
            Op.EQ(Op.SLOAD(SLOT_DERIVED), Op.SLOAD(SLOT_ACTUAL)),
        )
        + Op.STOP
    )


@pytest.mark.parametrize(
    "salt,initcode", [CREATE2_CASES[0]], ids=["zero_salt"]
)
@pytest.mark.valid_from("EIP7997")
def test_deterministic_factory_counterfactual_address(
    state_test: StateTestFiller,
    pre: Alloc,
    salt: int,
    initcode: Bytecode,
) -> None:
    """
    Test a derivation against the hardcoded factory address still holds.

    EIP-7997 makes the Arachnid proxy at
    `0x4e59b44847b379578588920ca78fbf26c0b4956c` part of the protocol. Its
    whole value is that counterfactual addresses derived against it are the
    same on every chain, which means deployed code carries that 20-byte
    literal and derives against it without ever calling it first. This test
    asserts the client's in-EVM derivation against what the real factory
    returns, which the official suite does not: `test_factory.py` derives
    in Python and never builds a preimage with `SHA3`.

    A failure means every cross-chain address commitment made against the
    canonical factory is void.
    """
    client = pre.deploy_contract(_factory_client())
    expected = compute_create2_address(DETERMINISTIC_FACTORY, salt, initcode)
    addr = int.from_bytes(expected, "big")

    storage = Storage().set_next_slot(SLOT_DERIVED)
    storage.store_next(addr, "derived_in_evm")
    storage.store_next(addr, "factory_returned")
    storage.store_next(1, "derivation_agrees_with_factory")

    tx = Transaction(
        to=client,
        gas_limit=15_000_000,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        data=salt.to_bytes(32, "big") + bytes(initcode),
    )
    state_test(
        pre=pre,
        post={
            client: Account(storage=storage),
            expected: Account(code=initcode.deploy_code),
        },
        tx=tx,
    )
