# What a failing test means

**Binding acceptance gate: every fixture a client runs on the newest supported fork must
pass today.** A corpus that is red on the current fork cannot signal anything — the signal
is a test going from green to red.

```bash
python3 tools/verify_corpus.py --only-fork Amsterdam                  # 464 passed
python3 tools/verify_corpus.py --wave expansion --only-fork Amsterdam # 147 passed
```

611 fixtures, 0 failures, verified. Any new test that is red on the newest fork is
rejected: it must be re-scoped with `valid_until` so it only runs where its invariant
holds, or re-pinned to assert what the fork actually does.

## Two kinds of test, and only one is an application-layer alarm

88 test functions run on Glamsterdam. They are **not** interchangeable when one goes red.

**CANARY — asserts an invariant deployed code relies on (73 functions).**
Green today. If a future change turns one red, a real on-chain idiom just stopped working.
**This is the alarm the corpus exists to raise.** Examples: a frozen 140,000-gas budget
still completes its callee; the gas retained by 63/64 still funds the caller's epilogue; a
2,300-gas stipend still covers a cold `SLOAD`; a revert reason still bubbles verbatim.

**PIN — asserts the current behaviour, including where that behaviour is already a
break (15 functions, listed below).**
Also green today, because it asserts what the fork actually does. But if a future change
turns one red, that may be a **fix**, not a break — a later fork restoring gas monotonicity
would fail `test_gas_readings_invert_from_eip8037`, and nothing in the application layer
would have broken. A PIN going red means *"this semantic moved"*, not *"deployed code
broke"*.

Both are worth having: PINs catch unintended semantic drift and keep the CANARY/violation
pairs honest (if a fork restores the old rule, the PIN fails and its paired CANARY starts
applying again, which is the signal we want instead of silence). They just must not be read
the same way.

### The 15 PINs, hand-classified

```text
tests/block_vs_sender_accounting   test_receipt_gas_used_diverges_from_the_block_contribution
tests/code_presence_identity       test_code_presence_no_longer_identifies_a_contract
tests/gas_monotonicity             test_gas_readings_invert_from_eip8037
tests/gas_monotonicity             test_gas_readings_invert_across_an_inframe_clear
tests/gasleft_sufficiency          test_gasleft_understates_capacity_with_a_reservoir
tests/intrinsic_cost               test_intrinsic_cost_is_shape_dependent_from_eip2780
tests/subfloor_budget              test_subfloor_budget_cannot_create_state_from_eip8037
tests/transient_storage_lifetime   test_a_fresh_zero_one_lock_no_longer_fits_50000_at_eip8037
expansion/code_size_gate           test_the_eip170_gate_rejects_a_live_contract_from_eip7954
expansion/precompile_input_admis.  test_modexp_rejects_oversized_operands_from_eip7823
expansion/precompile_input_admis.  test_oversized_modexp_is_unaffordable_at_any_price
expansion/unassigned_precompile_id test_point_evaluation_assignment_inverts_the_probe
expansion/unassigned_precompile_id test_bls_g1add_assignment_inverts_the_probe
expansion/undefined_opcode_halt    test_assigned_byte_no_longer_guards
```

One was reclassified on review: `test_code_inspection_cannot_distinguish_a_precompile`
reads like a PIN by name but is a **CANARY** — a fork that gave precompiles observable code
would make every `extcodesize == 0` check start seeing them as contracts, which *is* an
application-layer break. Name heuristics are not sufficient here; the list above is
hand-classified, and that is why the rule below exists.

## Rule for new tests

Every new test declares its role on the last line of its docstring:

```python
    """
    Test <what it asserts>.

    Role: CANARY — a failure means deployed code relying on this stopped working.
    """
```

`Role: PIN` for a test asserting current behaviour. Unlabelled defaults to CANARY, which is
the stricter reading, so an unlabelled PIN will be mis-triaged — label it.

## Tests scoped before the newest fork

A test carrying `valid_until("Osaka")` does not run on Glamsterdam at all, so it can never
be red there. Those protect older-fork fixtures and record the invariant that *used* to
hold; the fork at which an invariant stopped holding is visible in `docs/TEST-INDEX.md`'s
fork column. A hardcoded forwarded-gas budget that works on Fusaka and dies on Glamsterdam
is written as a `valid_until("Osaka")` CANARY plus a `valid_from("EIP8037")` PIN — never as
one test expected to fail.
