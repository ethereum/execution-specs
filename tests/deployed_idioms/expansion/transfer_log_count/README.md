# transfer_log_count — "my event is log 0", under EIP-7708

**Invariant.** A transaction's receipt contains exactly the logs the contracts
in it emitted, in the order they emitted them. Two deployed idioms rest on that:
`assert logs.length == N` / fixed log-index arithmetic, and `eth_getLogs`
subscriptions keyed on `topics[0]`.

EIP-7708 breaks both, and it is the corpus's cleanest example of a **semantic**
break with **no gas rule moved** — so none of the 24 gas-shaped archetypes in
`docs/INVARIANT-CLASSES.md` can reach it. The nearest existing class is the
semantic-identity family (#21–#25); this is a new member of it.

## Why it is rule-dependent

```
TRANSFER_TOPIC = keccak256(b"Transfer(address,address,uint256)")
SYSTEM_ADDRESS = 0xff...fe                      amsterdam/vm/__init__.py:35-38

execute_code:
    if evm.should_transfer_value and evm.value != 0:
        move_ether(...)
        if evm.caller != evm.current_target:
            emit_transfer_log(evm, caller, target, value)
                                                amsterdam/vm/interpreter.py:418-430
emit_transfer_log:
    if transfer_amount == 0: return             amsterdam/vm/__init__.py:270
                                                (a redundant backstop -- see below)
```

Two consequences the reference implementation makes exact:

1. **Position.** The transfer log is emitted *before the frame's first opcode*,
   so the callee's own event moves from index 0 to index 1. Anything reading
   `receipt.logs[0]` now reads the protocol's log.
2. **Topic collision.** `TRANSFER_TOPIC` is byte-identical to the ERC-20
   `Transfer` event signature. The protocol's log and a token's log are
   indistinguishable on topics — same `topics[0]`, same `(from, to)` indexing,
   same `uint256` data word. The **only** discriminator is `log.address` being
   `SYSTEM_ADDRESS`.

And the exceptions decide which transactions change shape:

```
value == 0          no log   (interpreter.py:418, `evm.value != 0`)
caller == target    no log   (self-call, interpreter.py:425)
DELEGATECALL        no log   (no value is moved)
```

**"Zero value, no log" is doubly guarded — found by mutation, not by reading
(CHECKED).** The rule is enforced at two independent sites: the call site
tests `evm.value != 0` before calling (interpreter.py:418), and
`emit_transfer_log` tests `transfer_amount == 0` again (vm/__init__.py:270).
Each guard alone is sufficient, so **no single-site mutation can falsify
arm 3**. Both were written and both survived every archetype in the matrix —
first the inner guard, then, after it was flagged undetected, the call-site
guard, which survived identically. Two registered mutations now record the
pair (`exp-tx-transfer-log-on-zero-value-inner-guard` and
`-call-site`). Arm 3 is therefore a **control against a single-site
regression**, not a mutation-falsifiable assertion, and falsifying it would
need a two-site mutation that `mutate.py` cannot express. That is a stated
tooling limit, not a hidden gap — and the alternative, deleting the arm, would
have left the archetype claiming that *every* call gained a log, which is
false.

So a zero-value ERC-20 `transfer()` is untouched; the same call with 1 wei
attached is not. A test matrix that only exercises zero-value calls sees
nothing.

## Measured (CHECKED)

Instrument: `expansion/tests/tools/test_exp_transferlog_probe.py`. A contract
emitting exactly one `LOG1`, called with and without value.

```text
                      logs in the receipt      the callee's event is at
fork            value=0        value=1         index (value=1)
Berlin..Osaka   1              1               0
Amsterdam       1              2               1
```

At Amsterdam the extra log's `address`, `topics` and `data` were asserted
against a hand-built expectation (`SYSTEM_ADDRESS`,
`keccak256("Transfer(address,address,uint256)")`, padded sender/recipient,
32-byte amount) and matched byte for byte, which is what confirms the ERC-20
topic collision rather than assuming it.

## Deployed witness

**Protocol constant, no address witness — stated rather than invented.** A log
consumer is off chain: no opcode lets a contract read a log, so there is no
on-chain idiom to point an address at, and `registry/` holds no log-counting
pattern because no lens could detect one. Over-claiming here would violate
SCHEMA §7.9.

What *is* a measured population is the other side of the collision: the
32 bytes `keccak256("Transfer(address,address,uint256)")` are emitted by every
ERC-20 contract on mainnet by construction, since that is the signature the
standard mandates. The collision is therefore total rather than probabilistic —
a topic0-only filter now matches ETH movements, and the amounts are in different
units from the token amounts it was built to read. That is an argument from the
standard, not a count, and is labelled INFERRED where it concerns how many
consumers filter on topic0 alone.

## Non-duplicative with the official suite (CHECKED)

`tests/amsterdam/eip7708_eth_transfer_logs/test_transfer_logs.py` is **1,594
lines over 36 tests** and covers the emission side exhaustively — including
`test_contract_log_and_transfer_ordering` and `test_nested_calls_log_order`,
which already pin ordering better than anything written here would. **Do not
rebuild that.**

The gap is one line: `pytestmark = pytest.mark.valid_from("EIP7708")`
(test_transfer_logs.py:41). The whole suite is fork-restricted to the fork that
*breaks* the invariant, so it asserts nothing about the six forks the deployed
consumers were written against. Arms 1 and 4 here are `valid_until("Osaka")` by
construction — they pin "exactly one log, the callee's, at index 0" and "only a
token emits the ERC-20 topic" on the forks where they hold, and they *would*
fail if run on Amsterdam. That is the product.

The topic collision is also stated from both sides. `spec.py:30` computes
`TRANSFER_TOPIC` from the same keccak, so the official suite encodes the
equality — but as a shared helper on both sides of its own assertions. Writing
the literal signature string out independently in this archetype means a fork
that *disambiguates* the topic (a plausible repair) fails a test instead of
silently changing every indexer's results a second time.

## Reproduce

```bash
cd tests/deployed_idioms
python3 tools/locked_fill.py \
    expansion/tests/transfer_log_count --until Amsterdam \
    --output /tmp/tlog --clean -q -p no:cacheprovider        # 47 passed

python3 tools/locked_fill.py \
    expansion/tests/tools/test_exp_transferlog_probe.py \
    --from Prague --until Amsterdam --output /tmp/tlogp --clean -q --tb=no \
    -p no:cacheprovider      # failures ARE the measurement

python3 tools/mutate.py --wave expansion -k exp-tx --archetype transfer_log
```

## Mutation result (CHECKED)

`python3 tools/mutate.py --wave expansion -k exp-tx`, run over all **9**
expansion archetypes. Baseline `pass(9)` at Amsterdam (the full Berlin→Amsterdam
fill is 47).

| mutation | this archetype | elsewhere in the expansion wave |
| --- | --- | --- |
| `exp-tx-transfer-log-suppressed` | DETECTED(6) | all 8 survive |
| `exp-tx-transfer-topic-disambiguated` | DETECTED(6) | all 8 survive |
| `exp-tx-transfer-log-from-the-sender` | DETECTED(6) | all 8 survive |
| `exp-tx-osaka-log-address-is-the-caller` | DETECTED(6) | all 8 survive |
| `exp-tx-reservoir-gets-all-evm-gas` | DETECTED(9) | detected by all 8 as well |
| `exp-tx-transfer-log-on-zero-value-call-site` | **survives, explained** | all 8 survive |
| `exp-tx-transfer-log-on-zero-value-inner-guard` | **survives, explained** | all 8 survive |

**Five detections, four with perfect specificity.** Nothing else in the wave can
see whether the log is emitted, what signature it carries, or which address it is
attributed to. `exp-tx-osaka-log-address-is-the-caller` is the one that reaches
the **pre-fork** arms: `mutate.py` fills only the mutated fork, so without an
Osaka-fork mutation the two `valid_until("Osaka")` arms would never be exercised.

**The topic mutation is the interesting one.** `exp-tx-transfer-topic-
disambiguated` gives the system log its own signature,
`keccak256("EthTransfer(address,address,uint256)")` — the obvious *repair* for
the ERC-20 collision. It is DETECTED, which is the point: this archetype pins the
collision as a fact, so a later fork that fixes it has to confront a failing test
rather than silently changing every topic0 subscription a second time.

**The explained survival, both halves measured.** "Zero value, no log" is
enforced twice — at the call site (`evm.value != 0`, interpreter.py:418) and
inside `emit_transfer_log` (`transfer_amount == 0`, vm/__init__.py:270). Either
guard alone suffices, so **no single-site mutation can falsify arm 3**. The inner
guard was mutated first and survived; the matrix flagged it undetected; the
call-site guard was then mutated and survived identically. Both are registered so
the pair is reproducible. Arm 3 is therefore a control against a single-site
regression, and falsifying it would need a two-site mutation `mutate.py` cannot
express — a stated tooling limit. Deleting the arm instead would have left the
archetype implying that *every* call gained a log, which is false.

**Direction.** This archetype detects **no gas mutation at all**, correctly: the
EIP-7708 break moves no price. The 11 gas-shaped `exp-tx-*` mutations all survive
here, and the four semantic ones fire only here. Direction is not a meaningful
axis for a semantic equality, so two-sidedness is provided differently — one
mutation removes the log, one renames its signature, one re-attributes its
address, and two loosen the zero-value guard.

## What a failure means

The set of events a transaction emits, or their order, or the signature the
protocol uses for them, changed. Every log-counting assertion, every fixed log
index, and every `topics[0]`-only subscription in the ecosystem is now reading
different data for an unchanged transaction — and because no gas number moved,
nothing else in this corpus would have noticed.
