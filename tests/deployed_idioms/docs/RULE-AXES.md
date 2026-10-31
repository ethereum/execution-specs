# Rule axes — the canonical taxonomy

Owner: lens **L4**. Every other lens reports coverage against the `axis_id`s in this
file, and every `rule_axes` entry in `registry/*.jsonl` must be one of them.

## What an axis is

An **axis** is a class of execution rule that a hard fork can change, such that some
deployed contract's *observable behaviour* could depend on it. Observable means: a
committed effect differs (storage, logs, balances, status, deployed code, reachability)
— not merely that gas used differs. A pure gas-number change is on-axis only when some
contract's control flow or success depends on that number, which is almost always the
case via a fixed budget, a guard, or a stipend.

Axes are not EIPs. One EIP touches several axes (EIP-8037 touches nine); one axis is
changed by many EIPs (`storage-read-pricing` has moved four times). Axes are the finite
object; the contract space is not. See `SCHEMA.md` §2.

## How it was built

Grounded in the pinned EELS checkout at
`/home/devops/toni/datanalysis/eip-8037/engine/eels`, by diffing every adjacent pair of
`src/ethereum/forks/<fork>/{vm/gas.py, vm/instructions/*, vm/interpreter.py, fork.py,
transactions.py}` across the 15 semantically distinct mainnet forks
(frontier → homestead → tangerine_whistle → spurious_dragon → byzantium →
constantinople → istanbul → berlin → london → paris → shanghai → cancun → prague →
osaka → amsterdam; the glacier forks and `bpo1..5` change only difficulty-bomb delay and
blob schedule parameters and add no axis). Cross-checked against the per-EIP directory
names in `engine/eels/tests/`. Every constant and every "changed by" claim below marked
**C** was read out of the EELS source; claims marked **I** are inferred from EIP history
and not verified against this checkout.

Counts: **60 axes** in 7 families (A 15, B 4, C 12, D 6, E 12, F 8, G 3).

## Reading the entries

```
axis_id
  def       one-line definition of the rule
  changed   fork (EIP): what moved  — C = checked in EELS, I = inferred
  idiom     the kind of deployed code whose behaviour depends on it
```

---

## A. Gas metering, introspection and settlement (15 axes)

**`gas-introspection`**
- def — The value the `GAS` opcode pushes: how much of the frame's remaining budget is
  visible to the running code.
- changed — Tangerine Whistle (EIP-150): every surrounding cost moved, so the same
  program point reads a different number **C**. Amsterdam (EIP-8037): `GAS` pushes
  `gas_meter.gas_left` only — the state-gas reservoir is **invisible** to `GAS`, so a
  frame can have budget that `gasleft()` does not report **C**
  (`amsterdam/vm/instructions/control_flow.py:146`).
- idiom — Any contract that branches on `gasleft()`, sizes a loop by it, or passes
  `gasleft() - k` to a callee. Under EIP-8037 a contract that checks
  `gasleft() >= 20000` before an `SSTORE` is no longer measuring the thing that pays for
  the `SSTORE`.

**`gas-monotonicity`**
- def — Whether `gasleft()` is non-increasing between two reads in the same frame.
- changed — Amsterdam (EIP-8037): **broken**. A state-gas refund credits back into
  `gas_left` whenever the frame had spilled state charges there, so the second read can
  exceed the first **C** (`credit_state_gas_refund` is called from `sstore` directly:
  `amsterdam/vm/instructions/storage.py`; also `restore_state_gas`,
  `repay_state_gas_spill`). The official suite names this
  `test_same_frame_refund_increases_gas_left`.
- idiom — `uint g = gasleft(); ...; uint used = g - gasleft();` — a gas-delta meter.
  Relayers bill the delta, ERC-4337-style contracts bound it, and the subtraction
  underflows (reverts on solc ≥0.8, wraps below) when the inequality inverts.

**`gas-forwarding-6364`**
- def — The all-but-one-64th retention: how much of the parent's gas a child frame can
  receive, and how much the parent is guaranteed to keep.
- changed — Tangerine Whistle (EIP-150): introduced; a requested gas amount is clamped
  to `g - g/64` **C** (`max_message_call_gas`). Amsterdam (EIP-8037): the state-gas
  reservoir is **exempt** — `drain_state_gas_reservoir` hands the child the *whole*
  reservoir with no 63/64 rule, and restores it on return **C**.
- idiom — A caller that requests a specific gas amount and relies on getting it (so the
  clamp is a behaviour change), and the complement: a caller that relies on retaining
  1/64 to finish its own bookkeeping after an untrusted call. EIP-150 is the canonical
  "fork broke deployed contracts" event for this axis.

**`call-stipend`**
- def — The 2300-gas stipend added to a value-bearing call, and the rules that key off
  that number.
- changed — Tangerine Whistle (EIP-150): `CALL_STIPEND = 2300` against a repriced
  opcode set, so the stipend buys far less work **C**. Istanbul (EIP-2200/EIP-1706): an
  `SSTORE` now raises `OutOfGasError` outright when `gas_left <= 2300` **C**
  (`istanbul/vm/instructions/storage.py`). Amsterdam (EIP-8037): `CALL_VALUE` is
  redefined as `ACCOUNT_WRITE + CALL_STIPEND` **C**.
- idiom — `payable(x).transfer(v)` / `x.send(v)`, which forward exactly the stipend, and
  the receiving `receive()`/`fallback()` on the other side. This is the EIP-1884
  a deployed multisig-Safe break: a hook that fit in 2300 gas at one SLOAD price stopped fitting.

**`fixed-gas-budget`**
- def — Whether an absolute gas constant written into a contract (or into off-chain
  config it reads) still buys the work it was sized for.
- changed — Every repricing. Historically: Tangerine Whistle (EIP-150), Spurious Dragon
  (EIP-160), Istanbul (EIP-1884, EIP-2028), Berlin (EIP-2929), Amsterdam (EIP-8037,
  EIP-7981/8038, EIP-2780) **C**.
- idiom — `target.call{gas: 20000}(data)`, `uint constant CALLBACK_GAS_LIMIT = 200000`,
  `excessivelySafeCall(.., 50000, ..)`, oracle/relayer `gasLimit` stored in a slot. The
  dominant family in the EIP-8037 prior art
  (`8037-coordination/findings/`, 56 findings): a deployed randomness coordinator/CCIP callback limits,
  a deployed messaging protocol enforced options, OP/a deployed sidechain messengers, a deployed staking-pod module. **I** that this is
  the largest family by deployed count; **C** that the prior art is overwhelmingly this
  axis.

**`state-gas-reservoir`**
- def — Existence and behaviour of a second, separately-granted gas dimension that pays
  for state growth, with its own baseline/spill/refill rules.
- changed — Amsterdam (EIP-8037): introduced. `GasMeter{gas_left, state_gas_left,
  state_gas_baseline, state_gas_spilled, state_gas_committed_spill}`; charges draw from
  the reservoir first and spill into `gas_left`; refunds credit back LIFO **C**.
- idiom — Anything that reasons about "how much gas does a state write cost": a
  fixed budget sized for `20000` per `SSTORE`, a deploy-time budget sized for 200/byte
  of code, a meter that assumed one pool.

**`exceptional-halt-gas-burn`**
- def — Whether a failed frame consumes all its remaining gas (exceptional halt) or
  returns it to the caller (`REVERT`), and which failures are which.
- changed — Homestead (EIP-2): an exceptional halt now rolls back state **and** zeroes
  `gas_left`; before, a `CREATE` that ran out of gas left an account with empty code
  **C** (`homestead/vm/interpreter.py`). Byzantium (EIP-140): `REVERT` added — a
  distinct failure that *refunds* the remainder **C**. Amsterdam (EIP-8037):
  `forfeit_remaining_gas` asserts outstanding spill has been restored first, so the
  amount burned differs from the pre-8037 model **C**.
- idiom — `(bool ok,) = x.call(...)` followed by branch-on-`ok`: whether the caller has
  gas left to handle the failure depends on which kind of failure it was. Also the
  "burn the callee's budget deliberately" idiom (`assert`-style `INVALID`).

**`refund-cap`**
- def — The ceiling on the end-of-transaction refund, as a fraction of gas used.
- changed — Frontier..Istanbul: `gas_used // 2` **C**. London (EIP-3529):
  `gas_used // 5` **C** (`london/fork.py:810` vs `istanbul/fork.py:675`).
- idiom — Gas-token mints/frees (a gas-token contract, a gas-token contract) and any contract whose economics
  assumed it could reclaim half of a transaction. London is the fork that broke this.

**`storage-refunds`**
- def — When an `SSTORE` grants or revokes a refund, and how much.
- changed — Frontier: `+15000` on non-zero → zero **C**. Constantinople: EIP-1283 was
  *removed* before mainnet (EELS's `constantinople` SSTORE is byte-identical to
  Byzantium's **C**) and shipped at Istanbul as EIP-2200 with net metering and the
  original-value-restore refunds **C**. Berlin (EIP-2929): refund formulas rewritten in
  terms of warm/cold constants **C**. London (EIP-3529): `REFUND_STORAGE_CLEAR`
  15000 → 4800 **C**. Amsterdam (EIP-8037): clear refund derived from
  `(STORAGE_WRITE + COLD_STORAGE_ACCESS) * 4800 / 5000`; restore refund is the full
  `STORAGE_WRITE`; state-gas `STORAGE_SET` refills the reservoir separately **C**.
- idiom — Refund harvesters; batch operations that clear many slots and were sized
  assuming the refund would pay for part of the transaction; any contract whose
  "net cost" accounting includes the refund.

**`selfdestruct-refund`**
- def — Whether `SELFDESTRUCT` grants a gas refund.
- changed — Tangerine Whistle: `REFUND_SELF_DESTRUCT = 24000` **C**. London
  (EIP-3529): removed entirely **C** (constant gone from `london/vm/gas.py`).
- idiom — Gas tokens that minted child contracts and destroyed them to harvest 24000
  each. London deleted the mechanism.

**`intrinsic-gas`**
- def — The fixed cost of a transaction before any code runs: base, per-calldata-byte,
  create surcharge, access-list items, authorization items.
- changed — Homestead (EIP-2): `TX_CREATE = 32000` added **C**. Istanbul (EIP-2028):
  non-zero calldata byte 68 → 16 **C**. Berlin (EIP-2930): access-list items 2400/1900
  **C**. Prague (EIP-7623): recast as token counting, `TX_DATA_TOKEN_STANDARD = 4` **C**.
  Amsterdam (EIP-2780): `TX_BASE` 21000 → 12000, plus a new `TX_VALUE_COST = 6000`
  **C**; access-list items become `COLD_* - WARM_ACCESS` **C**.
- idiom — Off-chain senders and on-chain gas estimators that hardcode 21000, and
  contracts that reimburse `21000 + 16*len(data)`. Meta-transaction relayers compute
  exactly this.

**`calldata-floor`**
- def — A lower bound on a transaction's gas used, derived from its calldata size,
  independent of the work performed.
- changed — Prague (EIP-7623): floor = `tokens * 10 + TX_BASE`, and validity requires
  `max(regular, floor) <= tx.gas` **C**. Amsterdam (EIP-7976): token floor 10 → 16, and
  the check becomes `intrinsic.calldata_floor > tx.gas` plus a cap check against
  `TX_MAX_GAS_LIMIT` **C**.
- idiom — Data-heavy, compute-light calls: rollup batch submitters, calldata-as-storage
  (`SSTORE2`/blob-era archival), DA posting. A sender whose gas limit was sized by
  simulated execution now fails validation.

**`tx-gas-limit-cap`**
- def — A per-transaction ceiling on `gas_limit`, independent of the block limit.
- changed — Osaka (EIP-7825): `TX_MAX_GAS_LIMIT = 16_777_216` (2^24) **C**. Amsterdam
  adds `TX_MAX_TOTAL_GAS_LIMIT = 4_294_967_295` **C**.
- idiom — Single transactions that need more than 16.7M gas: large governance payload
  executions, mass airdrops, big contract deployments, a deployed lending protocol/Compound multi-market
  proposals (see `8037-coordination/findings/mainnet-aave-large-governance-payloads.md`).

**`block-gas-accounting`**
- def — What counts toward the block gas limit: whether refunds reduce the block's
  accounted gas, and whether the two gas dimensions share one limit.
- changed — Amsterdam (EIP-7778): block gas accounting without refunds **C** (test dir
  `tests/amsterdam/eip7778_block_gas_accounting_without_refunds`). EIP-8037 adds
  `check_block_gas_capacity` over two dimensions **C**.
- idiom — Block-filling batchers that pack transactions to the limit using refund-aware
  estimates; builders. Mostly off-chain, but on-chain batchers that loop
  `while (gasleft() > X)` against a block-limit assumption are in scope.

**`block-gas-limit-field`**
- def — The block gas limit a contract can read via `GASLIMIT`, and its adjustment rule.
- changed — Frontier: `LIMIT_ADJUSTMENT_FACTOR = 1024`, `LIMIT_MINIMUM = 5000` **C**
  (unchanged since, but a live rule). London (EIP-1559): elasticity 2 — the *target* is
  half the limit, so `GASLIMIT` doubled in meaning **C**.
- idiom — `require(gasleft() > block.gaslimit / 64)`, loop bounds expressed as a
  fraction of `block.gaslimit`, and anti-gas-griefing checks.

---

## B. Access accounting (4 axes)

**`warm-cold-storage-access`**
- def — Whether a storage slot's first touch in a transaction costs more than later
  touches, and the two prices.
- changed — Berlin (EIP-2929): `COLD_STORAGE_ACCESS = 2100`, `WARM_ACCESS = 100`,
  replacing a flat `SLOAD` **C**. Amsterdam (EIP-8038): state-access cost increase;
  `COLD_STORAGE_ACCESS` stays 2100 in this checkout but `COLD_ACCOUNT_ACCESS` moves
  **C**.
- idiom — Any contract whose gas budget for a callee was sized by measuring a *warm*
  path and is then exercised cold (first call of a block), or vice versa. Order-dependent
  gas: the same function costs differently depending on what ran before it in the
  transaction.

**`warm-cold-account-access`**
- def — Same, for accounts: `BALANCE`, `EXTCODE*`, and the call family's address access.
- changed — Berlin (EIP-2929): `COLD_ACCOUNT_ACCESS = 2600` **C**. Shanghai (EIP-3651):
  the coinbase is pre-warmed **C** (`shanghai/fork.py:566`). Prague (EIP-7702): resolving
  a delegation charges an additional access for the delegate **C** (`access_delegation`).
  Amsterdam (EIP-7981): `COLD_ACCOUNT_ACCESS` 2600 → 3000 **C**.
- idiom — Fixed-gas calls into a cold target (the extra 2600/3000 is taken off the
  callee's budget before it starts); multicall/aggregator loops over many addresses;
  MEV contracts that pay the coinbase.

**`access-list-prewarm`**
- def — A transaction can declare addresses and slots to pre-warm, at a price.
- changed — Berlin (EIP-2930): introduced, 2400/address + 1900/slot **C**. Amsterdam:
  repriced to exactly `COLD_* - WARM_ACCESS` **C**.
- idiom — Not a contract idiom but a *sender* idiom that changes what the contract sees:
  the same call is cheap or expensive depending on the access list, so a fixed-gas
  forwarding decision made off-chain can be right or wrong. Relevant to relayers.

**`block-level-access-lists`**
- def — A block-level record of accessed accounts/slots, with its own validity and gas
  constraints.
- changed — Amsterdam (EIP-7928): introduced; `BLOCK_ACCESS_LIST_ITEM = 2000` and a
  cap of `block_gas_limit // 2000` items **C** (`amsterdam/block_access_lists.py:887`).
- idiom — **No deployed contract idiom identified.** This axis constrains block
  *builders*, and its observable effect on a contract is indirect (a block may not fit
  a transaction that touches very many distinct slots). Reported as a likely
  zero-dependent axis — see `lenses/L4/REPORT.md`.

---

## C. Opcode and precompile pricing (12 axes)

**`storage-write-pricing`**
- def — What an `SSTORE` costs, by slot transition.
- changed — Frontier: `STORAGE_SET = 20000`, reset 5000 **C**. Istanbul (EIP-2200): net
  metering — a repeat write in the same transaction costs `SLOAD` **C**. Berlin
  (EIP-2929): set 20000 + cold 2100, reset `5000 - 2100` **C**. Amsterdam (EIP-8037):
  one `STORAGE_WRITE = 10000` execution charge plus `64 * 1530 = 97,920` **state** gas
  for a first-time set of a zero slot **C**.
- idiom — Fixed budgets sized for "one SSTORE = 20000"; `require(gasleft() > 20000)`
  before a write; relayers that quote per-write costs; any hook called with a tight
  budget that writes.

**`storage-read-pricing`**
- def — What an `SLOAD` costs.
- changed — Frontier 50 → Tangerine Whistle (EIP-150) 200 → Istanbul (EIP-1884) 800 →
  Berlin (EIP-2929) 2100 cold / 100 warm **C** (all four read out of the respective
  `vm/gas.py`).
- idiom — **The canonical proven break.** A `receive()`/`fallback()` that does one or two
  `SLOAD`s and is invoked with the 2300 stipend: fine at 200, fatal at 800. EIP-1884
  broke deployed a widely deployed smart-account wallet wallets and a long tail of `transfer()`-receiving
  contracts; it is the reason EIP-1884 shipped with a known-breakage analysis. **I** on
  the specific a widely deployed smart-account wallet attribution (historical, not re-derived here); **C** on the
  repricing sequence.

**`account-query-pricing`**
- def — What `BALANCE`, `EXTCODESIZE`, `EXTCODECOPY`, `EXTCODEHASH` and `SELFBALANCE`
  cost.
- changed — Tangerine Whistle (EIP-150): `BALANCE` 20 → 400, `EXTERNAL_BASE` 20 → 700
  **C**. Constantinople (EIP-1052): `EXTCODEHASH` added at 400 **C**. Istanbul
  (EIP-1884): `BALANCE` 400 → 700, `EXTCODEHASH` 400 → 700, `SELFBALANCE` added at 5
  **C**. Berlin (EIP-2929): all folded into warm/cold **C**.
- idiom — `isContract()` via `extcodesize` inside a tight-budget hook; ERC-777/ERC-1820
  registry lookups; `address(this).balance` → `selfbalance()` rewrites. EIP-1884's
  `BALANCE` increase is part of the same deployed-code break as `SLOAD`.

**`call-base-pricing`**
- def — The base cost of entering a call frame, and the surcharges for value transfer
  and for creating the recipient.
- changed — Tangerine Whistle (EIP-150): `CALL_BASE` 40 → 700 **C**. Berlin (EIP-2929):
  base folded into warm/cold account access **C**. Amsterdam (EIP-8037): `CALL_VALUE`
  becomes `ACCOUNT_WRITE + CALL_STIPEND = 9000 + 2300`, `NEW_ACCOUNT` leaves execution
  gas for the state-gas reservoir **C**.
- idiom — Multicall/batch routers that forward a fixed amount per sub-call; fan-out
  loops whose iteration count was sized against the per-call overhead.

**`memory-expansion-pricing`**
- def — The linear + quadratic cost of growing a frame's memory.
- changed — Never, in this checkout: `MEMORY_PER_WORD = 3` and `words^2 // 512` are
  identical frontier → amsterdam **C**. A live rule nonetheless.
- idiom — Contracts that copy large return data or build large calldata under a fixed
  budget; `abi.encode` of big arrays inside a hook. A repricing here is the cheapest
  way to break "I allocated 50000 gas for this ABI encode".

**`copy-word-pricing`**
- def — Per-word cost of `CALLDATACOPY`, `CODECOPY`, `RETURNDATACOPY`, `MCOPY`.
- changed — Byzantium (EIP-211): `RETURNDATACOPY` added at 3/word **C**. Cancun
  (EIP-5656): `MCOPY` added at 3/word **C**. The 3/word rate itself: unchanged **C**.
- idiom — Proxy `delegatecall` trampolines that copy all calldata and all return data;
  `CODECOPY`-based `SSTORE2` readers. Fixed-gas proxies depend on the rate.

**`log-pricing`**
- def — `LOG*` base, per-topic, per-byte cost.
- changed — Never, in this checkout: 375 / 375 / 8 frontier → amsterdam **C**.
- idiom — Event-heavy hooks under a fixed budget; indexers' assumption that emitting is
  cheap. Also interacts with `protocol-logs`.

**`keccak-pricing`**
- def — `KECCAK256` base + per-word cost.
- changed — Never, in this checkout: 30 + 6/word **C**. But Amsterdam adds a *new*
  keccak charge at code deposit: `6 * ceil32(len(code))/32` execution gas **C**
  (`amsterdam/vm/interpreter.py:370`).
- idiom — Merkle-proof verifiers given a fixed gas budget (proof length × hash cost);
  commit-reveal schemes; `CREATE2` address computation on-chain.

**`exp-pricing`**
- def — `EXP` base + per-exponent-byte cost.
- changed — Spurious Dragon (EIP-160): per-byte 10 → 50 **C**.
- idiom — Fixed-point math libraries that exponentiate (interest accrual `(1+r)^n`,
  bonding curves) inside a bounded budget. A 5× rise is the kind that turns a
  comfortable budget into an OOG.

**`create-pricing`**
- def — The cost of a `CREATE`/`CREATE2` operation apart from the child's execution.
- changed — Shanghai (EIP-3860): `CODE_INIT_PER_WORD = 2` charged on init code, and
  init code capped **C**. Amsterdam (EIP-8037): `OPCODE_CREATE_BASE = 32000` replaced by
  `CREATE_ACCESS = ACCOUNT_WRITE + COLD_ACCOUNT_ACCESS = 12000`, with the account
  creation moved to `120 * 1530 = 183,600` state gas **C**; the `MAX_INIT_CODE_SIZE`
  check also moves to *after* the gas charge, changing which error surfaces **C**.
- idiom — Factories that deploy with a fixed gas budget (`create2` clone factories,
  Safe proxy factories, a major DEX-style pool deployment, `8037-coordination/findings/
  mainnet-govblk-*-factories`). A factory whose per-deploy allowance was sized
  pre-Shanghai pays the init-code word cost it never budgeted.

**`code-deposit-pricing`**
- def — The cost of writing the deployed bytecode at the end of a successful create.
- changed — Frontier..Osaka: `CODE_DEPOSIT_PER_BYTE = 200` execution gas **C**.
  Amsterdam (EIP-8037): the constant is **gone**; deposit costs
  `len(code) * COST_PER_STATE_BYTE = len(code) * 1530` **state** gas **C**
  (`amsterdam/vm/interpreter.py:376`). A 7.65× rise, paid from a different pool.
- idiom — Deployment under a fixed gas budget: governance proposals that deploy an
  implementation, factories with a per-deploy allowance, `CREATE3` deployers. A
  24 KB contract's deposit goes from ~4.9M to ~37.6M state gas.

**`precompile-pricing`**
- def — What each precompile charges.
- changed — Byzantium (EIP-196/197/198): ecAdd 500, ecMul 40000, pairing 100000+80000,
  modexp added **C**. Istanbul (EIP-1108): ecAdd 500 → 150, ecMul 40000 → 6000, pairing
  100000/80000 → 45000/34000 **C**; (EIP-152) blake2f 1/round **C**. Berlin (EIP-2565):
  modexp repriced **I**. Cancun (EIP-4844): point evaluation 50000 **C**. Prague
  (EIP-2537): BLS12-381 set **C**. Osaka (EIP-7883): modexp increase **C**; (EIP-7951)
  p256verify 6900 **C**; (EIP-7823) modexp input bounds **C**.
- idiom — ZK verifiers with a fixed gas allowance (the pairing cost dominates); any
  contract that calls `modexp` under a budget — EIP-7883 *raises* modexp, the direction
  that breaks things. a deployed zk protocol/Tornado-style verifiers, BLS signature aggregators.

---

## D. Control-flow and failure semantics (6 axes)

**`return-data-semantics`**
- def — Whether a frame can see the callee's return data, how much, and what happens on
  an out-of-range read.
- changed — Byzantium (EIP-211): `RETURNDATASIZE`/`RETURNDATACOPY` added; an
  out-of-bounds `RETURNDATACOPY` is an **exceptional halt** (`OutOfBoundsRead`), not a
  zero-fill **C**. Prague (EIP-7702): the top-level frame gains `return_data` **C**.
- idiom — Proxies and try/catch wrappers that `returndatacopy` the whole buffer;
  contracts that distinguish "callee returned nothing" from "callee reverted with a
  reason"; `abi.decode` of a short return (the out-of-bounds halt is what makes a
  malformed ERC-20 `transfer` revert rather than read garbage).

**`revert-propagation`**
- def — How a sub-call's failure is reported to the caller: the success flag, whether
  the caller keeps executing, and whether revert data bubbles.
- changed — Homestead (EIP-2): a failed `CREATE` pushes 0 and the caller continues **C**.
  Byzantium (EIP-140): `REVERT` gives a failure that preserves revert data and returns
  gas **C**; (EIP-211) that data became readable.
- idiom — `try/catch`; `(bool ok, bytes memory ret) = x.call(...)` with
  `if (!ok) revert(ret)`; the "swallow the failure and continue" pattern in batch
  executors (see `8037-coordination/findings/mainnet-dexrouter-lbp-migrate-catch.md`).

**`call-depth-limit`**
- def — The maximum call-frame nesting depth.
- changed — Frontier: `STACK_DEPTH_LIMIT = 1024` **C**; unchanged since, but EIP-150's
  63/64 rule made the limit practically unreachable by gas starvation first — a
  behaviour change without a constant change.
- idiom — Deliberately recursive contracts (recursive `CREATE`, flash-loan chains);
  depth-limit griefing guards; `require(ok)` after a call that could fail *only* from
  depth.

**`static-context-enforcement`**
- def — Which operations raise in a static frame.
- changed — Byzantium (EIP-214): `STATICCALL` added; `SSTORE`, `LOG*`, `CREATE*`,
  `SELFDESTRUCT`, value-bearing `CALL` raise `WriteInStaticContext` — note `LOG*` was
  added to the set at Byzantium **C** (`byzantium/vm/instructions/log.py`). Cancun
  (EIP-1153): `TSTORE` joins the set **C**. Amsterdam (EIP-7708): if `SELFDESTRUCT` or a
  transfer emits a protocol log, the static-frame rule must cover it **I**.
- idiom — `view`-declared functions that actually mutate via `delegatecall`; ERC-20
  `balanceOf` implementations that lazily write; `staticcall`-based oracle reads of
  contracts that want to cache.

**`stack-depth-limit`**
- def — The 1024-item EVM stack bound and the instructions that can reach past 16 items.
- changed — Frontier: 1024 **C**. Amsterdam (EIP-8024): `DUPN`/`SWAPN`/`EXCHANGE` added,
  giving access beyond the 16-deep window **C**.
- idiom — Hand-written Yul/assembly with deep stacks; `stack too deep` workarounds
  compiled to memory. Low expected deployed dependence.

**`jumpdest-validity`**
- def — Which byte offsets are legal jump targets, and how `JUMPDEST` analysis treats
  push data.
- changed — Frontier: `get_valid_jump_destinations` over push-aware scan **C**.
  Unchanged, but EIP-3540/EOF proposals would change it **I**.
- idiom — Runtime-constructed jump tables; `SSTORE2`/metamorphic code whose data bytes
  coincidentally contain `0x5B`; Solidity's internal function pointers.

---

## E. State and account model (12 axes)

**`account-existence-empty`**
- def — Whether an account with zero nonce, zero balance and no code exists, and when it
  is removed.
- changed — Spurious Dragon (EIP-158/161): touched empty accounts are deleted at the end
  of a transaction; `touched_accounts` tracking added **C**. Paris: the tracking is
  **removed** — the clearing campaign is complete and no empty accounts remain **C**
  (`london → paris` interpreter diff deletes `touched_accounts`). Prague (EIP-7702):
  authorizing an empty account costs `AUTH_PER_EMPTY_ACCOUNT = 25000` with a 12500
  refund for an existing one **C**.
- idiom — "Has this address been initialised?" tests via `balance != 0 || nonce != 0`;
  contracts that send 1 wei to mark an address; `EXTCODEHASH` returning zero for an
  empty account vs the empty-code hash for an existing one.

**`new-account-charge`**
- def — The surcharge for a value transfer that brings a previously non-existent
  account into existence, and the predicate for "non-existent".
- changed — Tangerine Whistle (EIP-150): `NEW_ACCOUNT = 25000`,
  `OPCODE_SELFDESTRUCT_NEW_ACCOUNT = 25000` **C**. Amsterdam (EIP-8037): execution-gas
  `NEW_ACCOUNT` removed; replaced by `120 * 1530 = 183,600` state gas, and the predicate
  becomes `is_account_alive` rather than `account_exists` **C**; a failed create
  *refills* the charge **C**.
- idiom — "First transfer to a fresh recipient" — exactly the prior-art family
  `mainnet-ccip-token-release-fresh-receiver`, `mainnet-fixed-limit-token-senders`:
  a payout with a fixed gas allowance that succeeds for an existing recipient and OOGs
  for a fresh one. The 25000 → 183,600 move is the biggest single multiplier in
  EIP-8037.

**`selfdestruct-semantics`**
- def — What `SELFDESTRUCT` does: whether the account and its code/storage are deleted,
  and where the balance goes.
- changed — Cancun (EIP-6780): the account is deleted **only if it was created in the
  same transaction**; otherwise only the balance moves **C**
  (`cancun/vm/instructions/system.py`: `if originator in ...created_accounts`). Also at
  Cancun, a self-beneficiary `SELFDESTRUCT` **burns** the ETH **C**. Amsterdam
  (EIP-8246): the burn is removed **C** (test dir
  `tests/amsterdam/eip8246_selfdestruct_no_burn`). London (EIP-3529) removed its refund
  (see `selfdestruct-refund`).
- idiom — Three distinct deployed idioms, all affected differently: (a) force-send ETH
  to a beneficiary that refuses calls — still works; (b) **metamorphic / redeploy at the
  same address** via `CREATE2` after destroying the occupant — broken by EIP-6780 unless
  the destroy happens in the creating transaction; (c) `selfdestruct(address(this))` as a
  deliberate burn — the burn disappears at EIP-8246.

**`transient-storage-lifetime`**
- def — Existence and lifetime of per-transaction storage: when it is cleared and
  whether it is reverted with a frame.
- changed — Cancun (EIP-1153): `TSTORE`/`TLOAD` introduced at 100 gas, cleared at
  transaction end, reverted with the frame **C**. Amsterdam: priced as a literal 100
  rather than aliasing `WARM_ACCESS` **C** — so a `WARM_ACCESS` repricing no longer
  moves `TSTORE`.
- idiom — Reentrancy guards migrated from `SSTORE` to `TSTORE`; a major DEX v4 hook
  accounting; flash-accounting locks. The invariant they need is "cleared between
  transactions, survives across frames within one".

**`original-value-tracking`**
- def — Whether gas and refund decisions can see a slot's value at the *start of the
  transaction*, distinct from its current value.
- changed — Istanbul (EIP-2200): `get_storage_original` introduced **C**. Amsterdam
  (EIP-8037): also governs whether the state-gas `STORAGE_SET` is charged and refilled
  **C**.
- idiom — Not usually a deliberate idiom, but it makes cost **order-dependent**: a
  contract that writes a slot twice in one transaction pays differently depending on
  what it was at entry. Batch executors that touch the same slot per item hit this, and
  their fixed per-item budgets depend on it.

**`created-account-storage`**
- def — Whether a freshly created account can observe pre-existing storage at its
  address, and how that interacts with refunds.
- changed — Spurious Dragon: `increment_nonce` on the create target; `MAX_CODE_SIZE`
  check **C**. Istanbul: `mark_account_created` added so a recreated account's
  pre-existing storage is ignored for refund purposes **C**
  (`istanbul/vm/interpreter.py`). Cancun: the same tracking is reused by EIP-6780 **C**.
- idiom — `CREATE2` redeploy at an address that previously held storage; the
  metamorphic-contract family; counterfactual-instantiation wallets that receive funds
  before deployment.

**`code-size-limit`**
- def — The maximum size of deployed code, and of init code.
- changed — Spurious Dragon (EIP-170): `MAX_CODE_SIZE = 0x6000` (24,576) **C**.
  Shanghai (EIP-3860): `MAX_INIT_CODE_SIZE = 2 * MAX_CODE_SIZE` plus a word charge **C**.
  Amsterdam (EIP-7954): `MAX_CODE_SIZE = 0x10000` (65,536) **C**.
- idiom — Contracts squeezed to just under 24,576 bytes (the diamond/facet pattern,
  library splitting, `viaIR` tuning exist because of this limit); contracts that
  *assert* a size bound; `SSTORE2`-style data contracts that store payloads as code and
  chunk at 24 KB.

**`code-prefix-reserved`**
- def — Which leading bytes deployed code may not have, and what a reserved prefix means.
- changed — London (EIP-3541): code starting `0xEF` is rejected at deposit
  (`InvalidContractPrefix`) **C**. Prague (EIP-7702): `0xef0100 || address` is the
  delegation designator — a 23-byte "code" value with special meaning **C**.
- idiom — `SSTORE2`/`SSTORE3` data contracts that store arbitrary bytes as code (they
  prepend a `0x00` STOP byte precisely to dodge this); code-as-data readers that must
  now distinguish real code from a delegation designator.

**`address-derivation`**
- def — How a created contract's address is computed.
- changed — Frontier: `keccak(rlp([sender, nonce]))[12:]` **C**. Constantinople
  (EIP-1014): `CREATE2` = `keccak(0xff ++ sender ++ salt ++ keccak(init))[12:]` **C**.
  Amsterdam (EIP-7997): a deterministic factory predeploy **C** (test dir
  `tests/amsterdam/eip7997_deterministic_factory_contract`).
- idiom — Counterfactual addresses: a contract that computes a future deployment's
  address and trusts funds sent there (`CREATE2` clone factories, Safe proxy
  prediction, `CREATE3` deployers, state-channel/4337 wallets). Any change to the
  derivation strands funds at an address nobody can deploy to.

**`nonce-semantics`**
- def — When and how account nonces change, and their bounds.
- changed — Spurious Dragon: `increment_nonce` on the create target before running init
  code **C**. EIP-2681: nonce capped at 2^64-1 **C** (test dir
  `tests/frontier/eip2681_limit_account_nonce`). Prague (EIP-7702): authorizations carry
  and bump nonces **C**.
- idiom — Factories that derive `CREATE` addresses from their own nonce and so depend on
  nonce ordering; contracts that read a counterparty's nonce as an activity proof;
  `nonce`-based replay protection in wallets (see
  `8037-coordination/findings/mainnet-nxv-exectransaction-consumed-nonce.md`).

**`eoa-delegation`**
- def — Whether an EOA can have code, what the code-introspection opcodes report for it,
  and what executes when it is called.
- changed — Prague (EIP-7702): `EXTCODESIZE`/`EXTCODEHASH`/`EXTCODECOPY` on a delegated
  EOA report the **23-byte designator**, not the delegate's code; calling it executes the
  delegate's code; precompiles are **disabled** through a delegation
  (`disable_precompiles`) **C**; the EIP-3607 sender-has-code rejection is relaxed for
  valid delegations **C**.
- idiom — `isContract()` / `extcodesize(a) == 0` used as an "is EOA" or
  anti-contract guard — the single most affected idiom, since a delegated EOA now has
  non-zero `extcodesize`. Also ERC-1271 signature checks, `tx.origin == msg.sender`
  guards, airdrop "humans only" filters.

**`protocol-logs`**
- def — Whether the protocol itself emits logs for value movements, independent of
  contract code.
- changed — Amsterdam (EIP-7708): ETH transfers emit logs **C** (test dir
  `tests/amsterdam/eip7708_eth_transfer_logs`; `emit_transfer_log` in
  `amsterdam/vm/__init__.py`).
- idiom — Contracts that count or index their own logs (`LOG` indices shift); anything
  asserting on a specific log position in a receipt; off-chain indexers keyed on log
  index. On-chain dependence is rare — flagged as a thin-dependence axis.

---

## F. Block and environment (8 axes)

**`block-fields`**
- def — The block header values a contract can read and what they mean.
- changed — London (EIP-1559): `BASEFEE` added **C**. Paris (EIP-4399): `DIFFICULTY`
  becomes `PREVRANDAO` — same opcode, completely different value and range **C**.
  Cancun (EIP-7516): `BLOBBASEFEE` added **C**. Amsterdam (EIP-7843): `SLOTNUM` added
  **C**. Shanghai (EIP-3651): the coinbase is pre-warmed, affecting reads of it **C**.
- idiom — `block.difficulty` as a randomness source — the canonical Paris break: lottery
  and NFT-mint contracts that used `block.difficulty % n` silently changed distribution
  (post-merge it is a 32-byte random beacon value, not a small integer). Also
  `block.basefee`-based fee reimbursement, and `block.number`-based schedules.

**`blockhash-window`**
- def — Which past block hashes are readable, and from where.
- changed — Frontier: the most recent 256 blocks, zero outside **C**
  (`OPCODE_BLOCKHASH = 20`). Prague (EIP-2935): served from a system-contract ring
  buffer at `<address withheld>` **C**, widening the window.
- idiom — Commit-reveal randomness with a reveal deadline ("reveal within 256 blocks or
  the hash is zero"); the `blockhash(n) == 0` test used as "too old / in the future";
  plasma/optimistic exit challenges that quote a block hash.

**`beacon-root`**
- def — Availability of the parent beacon block root in state.
- changed — Cancun (EIP-4788): predeploy at
  `<address withheld>`, ring buffer of roots **C**.
- idiom — Consensus-layer-proving contracts: liquid-staking oracles, restaking
  verifiers, cross-chain light clients reading the beacon root.

**`blob-semantics`**
- def — Blob transactions: `BLOBHASH`, the blob fee market, and blob count limits.
- changed — Cancun (EIP-4844): introduced; `PER_BLOB = 2^17`, target 393216, update
  fraction 3338477 **C**. Prague: target 786432, fraction 5007716 **C**. Osaka
  (EIP-7918): a reserve price and `BLOB_BASE_COST = 2^13`; `BLOB_SCHEDULE_TARGET = 6`,
  `MAX = 9`, `BLOB_COUNT_LIMIT = 6` **C**. Amsterdam: target 14, max 21, fraction
  11684671 **C**; (EIP-8070) sparse blobpool **C**.
- idiom — Rollup batch inboxes that read `BLOBHASH(i)` and verify a KZG proof via the
  point-evaluation precompile; blob-fee-based pricing in L2 fee oracles.

**`chain-id`**
- def — The chain identifier, in transaction validity and as an opcode.
- changed — Spurious Dragon (EIP-155): `WrongChainIdError` on a mismatched tx **C**.
  Istanbul (EIP-1344): `CHAINID` opcode **C**.
- idiom — EIP-712 domain separators cached in storage at deploy time (a chain-id change
  invalidates them — the reason a widely used contract library re-derives the separator when
  `block.chainid` differs); replay-protection checks.

**`system-contracts`**
- def — Protocol-mandated predeploys: their addresses, code and storage layout.
- changed — Cancun (EIP-4788): beacon roots **C**. Prague (EIP-2935) history storage,
  (EIP-7002) withdrawals at `<address withheld>`, (EIP-7251)
  consolidations at `<address withheld>` **C**. Amsterdam
  (EIP-7997) deterministic factory, (EIP-8282) builder execution requests **C**; plus
  `SYSTEM_MAX_SSTORES_PER_CALL = 16` **C**.
- idiom — Contracts that call a predeploy and depend on its exact interface and revert
  behaviour: staking routers calling the withdrawal predeploy, light clients reading
  the history contract.

**`block-size-limit`**
- def — A limit on the encoded size of a block, independent of gas.
- changed — Osaka (EIP-7934): `MAX_RLP_BLOCK_SIZE = 10,485,760 - 2,097,152` **C**.
- idiom — **No deployed contract idiom identified.** Constrains builders; a very large
  calldata transaction can become unincludable. Reported as a likely zero-dependent
  axis.

---

**`precompile-set`**
- def — Which addresses are precompiles, and whether a call to one dispatches to native
  code or to account code.
- changed — Byzantium (EIP-196/197/198): `0x06`–`0x08` **C**. Istanbul (EIP-152): `0x09`
  **C**. Cancun (EIP-4844): `0x0a` **C**. Prague (EIP-2537): `0x0b`–`0x11` **C**. Osaka
  (EIP-7951): p256verify **C**. Prague (EIP-7702): a delegation *disables* precompile
  dispatch for the delegated address (`disable_precompiles`) **C**.
- idiom — Contracts that `staticcall` a low address and treat a zero-length return as
  "precompile absent" (a fork that adds the precompile changes the answer); contracts
  that loop over low addresses; anything that assumed an address was a dead hole.
  Also the inverse risk: a contract deployed at a low address later shadowed.

## G. Transaction validity (3 axes)

**`tx-type-validity`**
- def — Which transaction types exist and what each may do (notably: may it be a
  create?).
- changed — Berlin (EIP-2718/2930): typed envelope **C**. London (EIP-1559):
  `FeeMarketTransaction`, `InsufficientMaxFeePerGasError` **C**. Cancun (EIP-4844):
  blob transactions must have a `to` **C**. Prague (EIP-7702): `SetCodeTransaction`,
  must have a `to`, non-empty authorization list **C**.
- idiom — Mostly a sender concern, but contracts that inspect `tx.gasprice` /
  `msg.sender` fee economics, and 4337 bundlers that must choose a type, depend on it.

**`sender-code-restriction`**
- def — Whether a transaction's sender may have code.
- changed — London (EIP-3607): rejected — a sender with code cannot originate a
  transaction **I** (EELS applies the check in every fork since it is unobservable
  earlier **C**). Prague (EIP-7702): relaxed for valid delegation designators **C**.
- idiom — Contracts that assume `msg.sender == tx.origin` implies an EOA with no code —
  false for a 7702-delegated account. Airdrop filters, `onlyEOA` modifiers, and
  flash-loan guards.

**`authorization-semantics`**
- def — How an EIP-7702 authorization list is validated and applied, and its gas.
- changed — Prague (EIP-7702): `set_delegation`, `AUTH_PER_EMPTY_ACCOUNT = 25000`,
  `REFUND_AUTH_PER_EXISTING_ACCOUNT = 12500` **C**. Amsterdam (EIP-8037):
  `EXECUTION_PER_AUTH_BASE_COST` derived from calldata tokens + ecrecover + accesses,
  plus `23 * 1530` state gas; `commit_state_gas` makes applied delegations survive a
  failure of the dispatched code **C**.
- idiom — Gasless-relayer flows that bundle an authorization with a call and budget for
  it (`8037-coordination/findings/mainnet-walletcore-7702-gasless-relayer.md`); wallet
  contracts that read their own delegation.

---

## Axis index (for `rule_axes` fields)

```
A  gas-introspection  gas-monotonicity  gas-forwarding-6364  call-stipend
   fixed-gas-budget  state-gas-reservoir  exceptional-halt-gas-burn  refund-cap
   storage-refunds  selfdestruct-refund  intrinsic-gas  calldata-floor
   tx-gas-limit-cap  block-gas-accounting  block-gas-limit-field
B  warm-cold-storage-access  warm-cold-account-access  access-list-prewarm
   block-level-access-lists
C  storage-write-pricing  storage-read-pricing  account-query-pricing
   call-base-pricing  memory-expansion-pricing  copy-word-pricing  log-pricing
   keccak-pricing  exp-pricing  create-pricing  code-deposit-pricing
   precompile-pricing
D  return-data-semantics  revert-propagation  call-depth-limit
   static-context-enforcement  stack-depth-limit  jumpdest-validity
E  account-existence-empty  new-account-charge  selfdestruct-semantics
   transient-storage-lifetime  original-value-tracking  created-account-storage
   code-size-limit  code-prefix-reserved  address-derivation  nonce-semantics
   eoa-delegation  protocol-logs
F  block-fields  blockhash-window  beacon-root  blob-semantics  chain-id
   system-contracts  precompile-set  block-size-limit
G  tx-type-validity  sender-code-restriction  authorization-semantics
```

## Axes deliberately excluded

Rules a fork can change that **no contract can observe**, so they are out of scope per
`SCHEMA.md` §1:

- Consensus/difficulty: `MINIMUM_DIFFICULTY`, `BOMB_DELAY_BLOCKS`, the ethash→PoS
  switch as such, ommer rules, `BLOCK_REWARD` (frontier 5 → byzantium 3 →
  constantinople 2 ETH **C**). Observable only via `block.difficulty`, which is
  `block-fields`.
- Block/header structure: withdrawals root, requests hash, receipt encoding, the
  transactions trie. Observable only to clients.
- P2P and mempool rules (`blob-semantics` covers only the parts a contract reads).
- `bpo1..bpo5`: blob schedule parameters only — folded into `blob-semantics`.
- Glacier forks (muir, arrow, gray): difficulty-bomb delay only; **no axis** **C**.
