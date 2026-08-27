# Advanced: Bytecode Placeholders

## Overview

A bytecode placeholder reserves a fixed-width slot inside a data portion so that the value can be supplied *after* the bytecode has been assembled. This breaks the circular dependency that arises whenever a value embedded in the code depends on a property of the code that contains it:

- **Gas reserves in loops** — the loop condition compares `GAS` against the cost of one more iteration, but that cost cannot be measured until the loop (including the condition itself) has been built.
- **Self-referential offsets** — `CODECOPY` and `CREATE2` initcode offsets depend on the length of the execution code that precedes the embedded data.
- **Jump targets** — a `JUMP` destination is only known once the code up to that destination exists.

Placeholders solve this in two passes: build the code with a named slot, measure it, then substitute the measured value back in.

## The Problem Placeholders Replace

Without placeholders, tests reserve space with a stand-in literal chosen to have the same encoded width as the final value, then rebuild the bytecode from scratch:

```python
# Relies on "PUSH costs 3 gas regardless of the pushed value"
placeholder = Op.GT(Op.GAS, Op.PUSH1(0))
per_iter_gas = While(body=body, condition=placeholder).gas_cost(fork)
```

```python
# Relies on "0xFF happens to be the same byte size as the final value"
placeholder_offset = 0xFF
factory_execution_template = Op.CODECOPY(0, placeholder_offset, init_code_size) + ...
```

Both patterns work, but the width match is an unchecked invariant maintained by a comment. If the final value needs a wider `PUSH` than the stand-in, the measurement silently describes bytecode that is no longer the bytecode being deployed. Placeholders make the width explicit and enforce it.

## Creating a Placeholder

Pass `data_placeholder` with a name to any opcode that takes a data portion. The data portion is zeroed and the slot is registered under that name:

```python
code = Op.POP(Op.PUSH2(data_placeholder="loop_cost"))
# bytes: 61 0000 50
```

The opcode you choose fixes the slot width — `PUSH2` reserves two bytes. Pick an opcode wide enough for the largest value you intend to substitute; substituting a value that does not fit is an error rather than a silent truncation.

Any opcode with a data portion is accepted: `PUSH1`–`PUSH32`, which is the common case, as well as `DUPN`, `SWAPN`, and `EXCHANGE`. Until it is substituted, the slot holds zero, which for `DUPN` and `SWAPN` is not a valid index — see [Restrictions](#restrictions).

The result is an ordinary `Bytecode` object. It concatenates, hashes, and reports gas like any other bytecode, and it can be nested inside further opcode calls.

## Substituting Values

`Bytecode.substitute()` takes placeholder names as keyword arguments and returns a **new** `Bytecode` with those slots filled:

```python
final = code.substitute(loop_cost=1000)
# bytes: 61 03e8 50
assert bytes(final) == bytes(Op.POP(Op.PUSH2(1000)))
```

The original is left untouched, so a template can be reused for several substitutions. Names that have been substituted are no longer tracked on the result.

## Why the Measurement Is Exact

Because the placeholder's width is fixed when the code is built, the bytecode's length and gas cost are identical before and after substitution:

- Every `PUSH1`–`PUSH32` costs the same 3 gas (`G_VERY_LOW`) regardless of width or pushed value, and none of them incur state gas.
- The encoded length does not change, so every offset, jump target, and code-size calculation measured on the template remains valid.

This is what makes the two-pass approach sound: measure on the template, then substitute.

```python
body = Op.MSTORE(0, Op.SHA3(0, 32))
loop = (
    Op.JUMPDEST
    + body
    + Op.JUMPI(Op.GT(Op.GAS, Op.PUSH2(data_placeholder="reserve")), 0)
)

# Measure the loop, including its own condition
per_iteration = loop.gas_cost(fork)

# Feed the measurement back into the code that produced it
final_loop = loop.substitute(reserve=per_iteration)

assert final_loop.gas_cost(fork) == per_iteration
assert len(final_loop) == len(loop)
```

## Multiple Placeholders

A single bytecode may carry any number of placeholders, as long as their names are distinct. They can be substituted together or one at a time:

```python
code = Op.ADD(
    Op.PUSH2(data_placeholder="first"),
    Op.PUSH1(data_placeholder="second"),
)

# Together
code.substitute(first=0x1234, second=0xAB)

# Or progressively, leaving the rest for later
partial = code.substitute(first=0x1234)
final = partial.substitute(second=0xAB)
```

Substituting a subset is useful when the values become known at different points, for example a gas reserve known after measuring the loop and a jump target known after the surrounding program is assembled.

## Concatenation

Placeholder offsets are tracked through concatenation, so a template can be built up from fragments and substituted at the end:

```python
prefix = Op.PUSH1(0xFF) + Op.POP          # 3 bytes
suffix = Op.POP(Op.PUSH2(data_placeholder="value"))

combined = prefix + suffix                # offset shifts from 1 to 4
combined.substitute(value=0xBEEF)
```

Because names identify slots globally within a bytecode, concatenating two fragments that use the **same** name raises an exception rather than silently dropping one:

```python
code = Op.POP(Op.PUSH2(data_placeholder="value"))
code + code   # Exception: Conflicting data placeholders between bytecode objects
```

Give each slot a distinct name, or substitute one fragment before combining it.

## Restrictions

- **The opcode must have a data portion.** `Op.ADD(1, 2, data_placeholder="x")` raises `ValueError`; there is nowhere to put the slot.
- **The name must be a string.** `Op.PUSH2(data_placeholder=1)` raises `ValueError`.
- **Substitution checks the slot width, not the opcode's own constraints.** A placeholder writes raw bytes into the data portion, so encoder validation that normally runs when the data portion is given directly is skipped. `Op.DUPN(5)` raises, because a `DUPN` index must be in `[17, 235]`, but `Op.DUPN(data_placeholder="depth").substitute(depth=5)` produces `e605` without complaint. For `PUSH1`–`PUSH32` this is irrelevant, since every byte value is a valid operand; for `DUPN`, `SWAPN`, and `EXCHANGE` the caller is responsible for the range.
- **Bytecode containing placeholders cannot be repeated with `*`.** Duplicating the bytes would duplicate the slot, leaving one name pointing at several offsets, so `code * 3` raises `ValueError`. Multiplying by `0` or `1` is still allowed. Substitute first, then repeat.

## Error Reference

| Condition | Exception | Message |
|-----------|-----------|---------|
| Opcode has no data portion | `ValueError` | ``` `data_placeholder` requires an opcode with data portion ``` |
| Name is not a string | `ValueError` | ``` `data_placeholder` must be a str ``` |
| Unknown name passed to `substitute()` | `KeyError` | `Placeholder <name> not found in bytecode` |
| Value too large for the slot | `ValueError` | `Value <n> doesn't fit in <k> bytes (max <max>)` |
| Negative value | `ValueError` | `Value -1 doesn't fit in <k> bytes (max <max>)` |
| Same name on both sides of `+` | `Exception` | `Conflicting data placeholders between bytecode objects` |
| `*` on bytecode with placeholders | `ValueError` | `Cannot multiply bytecode containing placeholders` |

## Related

- [Opcode Metadata and Gas Calculations](./opcode_metadata.md) — how `gas_cost(fork)`, `state_cost(fork)`, and `refund(fork)` derive the measurements that get substituted back in.
- [Gas Optimization](./gas_optimization.md) — choosing gas limits for tests.
