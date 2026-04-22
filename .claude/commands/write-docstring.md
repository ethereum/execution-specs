# Write Docstring

Conventions for writing docstrings in `src/ethereum/`. Docstrings are the primary prose of the specification — they read as a narrative explaining how Ethereum works, not as traditional Python API documentation. They are rendered into HTML by docc, which parses them as **Markdown** (via mistletoe). Run this skill before writing or modifying docstrings.

## General Rules

- **Markdown only** — no reStructuredText (`.. directives::`, `:param:`, RST section underlines)
- 79-character line limit (same as code)
- Imperative mood for summaries ("Obtain" not "Obtains", "Return" not "Returns")
- Summary on the line after opening `"""`
- Blank line after the summary for multi-line docstrings
- For multi-line docstrings, the closing `"""` should be on its own line
- No `__init__` docstrings (D107 is disabled), only the class itself is documented
- Reference link definitions go at the end of the docstring, after a blank line
- Do not include constants/numeric values in the docstring (values in docstrings can easily desync with the code, and no tool will detect it)
- Avoid restating what the code is doing (the code should speak for itself)
- Avoid mentioning the current fork unnecessarily (creates noisy diffs between forks)

## Module Docstrings

Module docstrings introduce the concepts in the module. They should read as narrative prose — imagine a textbook chapter opening.

Start with a one-line summary, then expand with paragraphs that explain what the module contains and why. Use cross-references to link to the key types and functions defined in the module.

```python
"""
Ethash is a proof-of-work algorithm designed to be [ASIC] resistant through
[memory hardness][mem-hard].

To achieve memory hardness, computing Ethash requires access to subsets of a
large structure. The particular subsets chosen are based on the nonce and block
header, while the set itself is changed every [`epoch`].

At a high level, the Ethash algorithm is as follows:

1. Create a **seed** value, generated with [`generate_seed`] and based on the
   preceding block numbers.
1. From the seed, compute a pseudorandom **cache** with [`generate_cache`].
1. From the cache, generate a **dataset** with [`generate_dataset`]. The
   dataset grows over time based on [`DATASET_EPOCH_GROWTH_SIZE`].
1. Miners hash slices of the dataset together, which is where the memory
   hardness is introduced. Verification of the proof-of-work only requires the
   cache to be able to recompute a much smaller subset of the full dataset.

[`DATASET_EPOCH_GROWTH_SIZE`]: ref:ethereum.ethash.DATASET_EPOCH_GROWTH_SIZE
[`generate_dataset`]: ref:ethereum.ethash.generate_dataset
[`generate_cache`]: ref:ethereum.ethash.generate_cache
[`generate_seed`]: ref:ethereum.ethash.generate_seed
[`epoch`]: ref:ethereum.ethash.epoch
[ASIC]: https://en.wikipedia.org/wiki/Application-specific_integrated_circuit
[mem-hard]: https://en.wikipedia.org/wiki/Memory-hard_function
"""
```

Short modules that need no narrative can use a single-line summary:

```python
"""
Utility functions used in this specification.
"""
```

## Function Docstrings

Function docstrings describe what the function does and why, as part of the specification narrative. Reference parameters inline with backticks — do **not** use formal `Parameters`, `Returns`, or `Raises` sections.

### Short (summary only)

```python
def convert(balance: str) -> U256:
    """
    Convert a string in either hexadecimal or base-10 to a `U256`.
    """
```

### Multi-paragraph (with context)

```python
def add_genesis_block(
    hardfork: GenesisFork, chain: Any, genesis: GenesisConfiguration
) -> None:
    """
    Add the genesis block to an empty blockchain.

    The genesis block is an entirely sui generis block (unique) that is not
    governed by the general rules applying to all other Ethereum blocks.
    Instead, the only consensus requirement is that it must be identical to
    the block added by this function.

    The initial state is populated with balances based on the Ethereum presale
    that happened on the Bitcoin blockchain. Additional ether worth 1.98% of
    the presale was given to the foundation.

    The `nonce` field is `0x42` referencing Douglas Adams' "HitchHiker's Guide
    to the Galaxy".

    On testnets the genesis configuration usually allocates 1 wei to addresses
    `0x00` to `0xFF` to avoid edge cases around precompiles being created or
    cleared (by [EIP-161]).

    [EIP-161]: https://eips.ethereum.org/EIPS/eip-161
    """
```

### With cross-references

```python
def cache_size(block_number: Uint) -> Uint:
    """
    Obtain the cache size (in bytes) of the epoch to which `block_number`
    belongs.

    See [`INITIAL_CACHE_SIZE`] and [`CACHE_EPOCH_GROWTH_SIZE`] for the initial
    size and linear growth rate, respectively. The cache is generated in
    [`generate_cache`].

    The actual cache size is smaller than simply multiplying
    `CACHE_EPOCH_GROWTH_SIZE` by the epoch number to minimize the risk of
    unintended cyclic behavior. It is defined as the highest prime number below
    what linear growth would calculate.

    [`INITIAL_CACHE_SIZE`]: ref:ethereum.ethash.INITIAL_CACHE_SIZE
    [`CACHE_EPOCH_GROWTH_SIZE`]: ref:ethereum.ethash.CACHE_EPOCH_GROWTH_SIZE
    [`generate_cache`]: ref:ethereum.ethash.generate_cache
    """
```

## Class Docstrings

Brief summary of what the class represents, with optional narrative and cross-references.

```python
class GenesisConfiguration:
    """
    Configuration for the first block of an Ethereum chain.

    Specifies the allocation of ether set out in the pre-sale, and some of
    the fields of the genesis block.
    """
```

```python
class EvmTracer(Protocol):
    """
    [`Protocol`] that describes tracer functions.

    See [`ethereum.trace`] for details about tracing in general, and
    [`__call__`] for more on how to implement a tracer.

    [`Protocol`]: https://docs.python.org/3/library/typing.html#typing.Protocol
    [`ethereum.trace`]: ref:ethereum.trace
    [`__call__`]: ref:ethereum.trace.EvmTracer.__call__
    """
```

## Attribute Docstrings

docc documents any assignment that is followed by a bare string literal. This is non-standard Python — normally only modules, classes, and functions can have docstrings. Place a triple-quoted string immediately after the assignment.

This works for **constants**, **class fields**, **module-level variables**, and **type aliases**.

### Constants

```python
EPOCH_SIZE = Uint(30000)
"""
Number of blocks before a dataset needs to be regenerated (known as an
"epoch".) See [`epoch`].

[`epoch`]: ref:ethereum.ethash.epoch
"""
```

### Class fields

```python
class Example:
    chain_id: U64
    """
    Discriminant between diverged blockchains; `1` for Ethereum's main network.
    """
```

### Module-level variables

```python
_evm_trace: EvmTracer = discard_evm_trace
"""
Active [`EvmTracer`] that is used for generating traces.

[`EvmTracer`]: ref:ethereum.trace.EvmTracer
"""
```

### Type aliases

```python
TraceEvent = (
    TransactionStart
    | TransactionEnd
    | PrecompileStart
    | PrecompileEnd
    | OpStart
    | OpEnd
    | OpException
    | EvmStop
    | GasAndRefund
)
"""
All possible types of events that an [`EvmTracer`] is expected to handle.

[`EvmTracer`]: ref:ethereum.trace.EvmTracer
"""
```

## Cross-References

docc resolves Markdown reference links with the `ref:` scheme into hyperlinks in the generated documentation.

### Internal (to other Python objects)

Use backtick-wrapped names as the link text, with `ref:` pointing to the fully-qualified path:

```
[`ForkCriteria`]: ref:ethereum.fork_criteria.ForkCriteria
[`generate_cache`]: ref:ethereum.ethash.generate_cache
```

Short aliases work when the full name is unwieldy:

```
[ds]: ref:ethereum.ethash.DATASET_EPOCH_GROWTH_SIZE
```

### External URLs

Standard Markdown reference links:

```
[ASIC]: https://en.wikipedia.org/wiki/Application-specific_integrated_circuit
[EIP-3155]: https://eips.ethereum.org/EIPS/eip-3155
```

Bare URLs in angle brackets for inline use:

```
Available at <https://github.com/ethereum/genesis_block_generator>.
```

### Usage in text

Reference links are used inline with brackets:

```
For these intentional forks to succeed, all participants need to agree on
exactly when to switch rules. The agreed upon criteria are represented by
subclasses of [`ForkCriteria`], like [`ByBlockNumber`] and [`ByTimestamp`].
```

## Markdown Formatting

- `_italic_` to introduce domain terms: `_Genesis_ is the term for...`
- `**bold**` to highlight key concepts: `Create a **seed** value`
- Backticks for code references: `` `block_number` ``, `` `0x42` ``
- Numbered lists (`1.`) for sequential steps
- Bullet lists (`-`) for unordered items
- Markdown headings are rarely needed inside docstrings; use paragraphs instead

## Anti-Patterns

- **No RST directives**: `.. contents::`, `.. note::`, `:param:`, `:returns:` — these are outdated
- **No NumPy/Google sections**: no `Parameters\n----------` or `Args:` blocks
- **No RST section underlines**: `Introduction\n------------` is RST, not Markdown
- **No type repetition in docstrings**: types come from annotations, not prose
- **No empty boilerplate**: don't write `"""Ethereum Specification."""` with a `.. contents::` block — write real narrative or a concise summary
- **Don't skip attribute docstrings**: constants and fields deserve explanations

## Reference Files

For examples of well-written docstrings, see:

- `src/ethereum/ethash.py` — narrative module + function docstrings
- `src/ethereum/genesis.py` — class, attribute, and multi-paragraph function docstrings
- `src/ethereum/trace.py` — class, attribute, and protocol docstrings
- `src/ethereum/fork_criteria.py` — narrative module docstring with Markdown formatting

If these files no longer exist or are no longer good examples, abort with an appropriate error message.
