# Unscheduled Features

Each directory here is a *feature*: a single EIP, or a set of EIPs, that is not
scheduled for any fork. A feature holds only the changes it makes to a fork,
and is built on top of its base fork whenever it runs. The process (a
`projects/<FEATURE>` branch first, then acknowledgement on ACDT) is described
in [Unscheduled features][process]. This guide covers the mechanics.

Every command below runs from the repository root.

## Layout

A feature named `evmified_identity` touches these places:

```text
src/ethereum/unscheduled/evmified_identity/
├── feature.toml                          # EIPs, owners, removals, base
├── base.lock                             # hashes of replaced definitions
├── __init__.py                           # overlay: module docstring
├── fork.py                               # overlay: replaces apply_fork
├── evmified_precompiles.py               # new module
└── vm/precompiled_contracts/mapping.py   # overlay: replaces the mapping

packages/testing/src/execution_testing/forks/forks/
├── eips/unscheduled/eip_7666.py          # EIP mixin for the framework
└── unscheduled.py                        # feature fork + transition fork

tests/unscheduled/evmified_identity/
└── eip7666_evmify_identity/              # one directory per EIP
```

The names must line up: the directory `evmified_identity` is the fork
`EvmifiedIdentity` in the framework and on the command line.

## 1. Describe the feature

`feature.toml`:

```toml
eips = [7666]
owners = ["spencer-tb"]

# Optional. Without it, the feature builds on the newest fork.
# base = "osaka"

# Files (relative to the fork package) and definitions (dotted, within the
# fork package) that the feature deletes from the fork.
remove = [
    "vm/precompiled_contracts/identity.py",
    "vm.precompiled_contracts.IDENTITY_ADDRESS",
    "vm.precompiled_contracts.mapping.identity",
    "vm.gas.GasCosts.PRECOMPILE_IDENTITY_BASE",
]
```

A removal can name a file, a top-level definition, a class attribute
(`module.Class.NAME`) or an imported name. Removing a name also drops it from
the module's `__all__`. Removing something the fork no longer has is an error.

By default a feature builds on the newest fork, so it picks up every EIP that
lands in the development fork. Set `base` to pin it to a fork that is no longer
under development instead.

## 2. Write the spec

Every Python file in the feature mirrors a path in the fork package.

- **New file:** a path that the fork lacks is copied in as is. Write it like
  any module in a fork: relative imports within the fork, absolute imports
  from the previous fork or from shared modules only.
- **Overlay:** a path that the fork has is merged into the fork's module.
  - Each top-level definition (function, class, constant) replaces the fork's
    definition of the same name, together with the docstring that follows it.
    A definition the fork lacks goes right before the next definition that
    the overlay replaces, or at the end of the module, so the built module
    keeps the overlay's order.
  - Imports are added where the fork does not already have them. Importing a
    name that the fork binds to something else is an error.
  - A module docstring replaces the fork's module docstring. Comments at the
    top of the overlay are for readers of the feature, and are not copied.
  - Anything else (an `if` block, a bare call) is an error.

An overlay replaces a definition whole: to change one line of a function, or
one constant of a class such as `GasCosts`, copy the whole definition into the
overlay and change it there. Keep features to the definitions they really
need to replace, since each one has to be re-reviewed whenever the fork
changes it (see [Keeping a feature alive](#keeping-a-feature-alive)).

Overlays are fragments that refer to names from the fork, so they are not
linted or type checked on their own. Check the built fork instead.

## 3. Build, read and check

```console
# Record the fork definitions that the overlays replace as reviewed.
uv run ethereum-spec-unscheduled evmified_identity --update-lock

# Write the full feature fork, then compare it with its base fork.
uv run ethereum-spec-unscheduled evmified_identity --output /tmp/feature
diff -ru src/ethereum/forks/bogota /tmp/feature/evmified_identity

# Lint, type check and spec-lint the built fork.
uv run ethereum-spec-unscheduled evmified_identity --check
```

Nothing generated is committed. Fills and the transition tool build the
feature in a temporary directory, once per process.

## 4. Add the feature fork

In `packages/testing/src/execution_testing/forks/forks/`:

1. Add an EIP mixin in `eips/unscheduled/eip_<N>.py`, like the mixins of
   scheduled EIPs (precompiles, system contracts, pre-allocation, gas
   costs). Mixins here are not enabled by any scheduled fork.
2. In `unscheduled.py`, add the feature fork on `LatestFork`, or on the fork
   that `base` pins, and a transition fork from that fork:

   ```python
   class EvmifiedIdentity(EIP7666, LatestFork, deployed=False):
       """EIP-7666: EVM-ify the identity precompile."""


   @transition_fork(
       to_fork=EvmifiedIdentity, from_fork=LatestFork, at_timestamp=15_000
   )
   class BogotaToEvmifiedIdentityAtTime15k(TransitionBaseClass):
       """Bogota to Evmified Identity transition at Timestamp 15k."""
   ```

The transition tool never runs `apply_fork`, for any fork. State that a feature
installs when it activates (code at an address, for example) belongs in the
mixin's pre-allocation, which every fork, including transition forks, sets at
genesis.

## 5. Write and fill the tests

Tests live in `tests/unscheduled/<feature>/eip<N>_<name>/` and follow the
usual conventions, marked with the EIP rather than a fork:

```python
pytestmark = pytest.mark.valid_from("EIP7666")
```

Use `valid_at_transition_to("EIP<N>")` for tests across the activation.

```console
uv run fill tests/unscheduled/evmified_identity --fork EvmifiedIdentity
```

`--fork` selects the feature fork and its transition fork. Feature forks
cannot be used with `--from` or `--until`, and fills up to a scheduled fork,
such as `--until Bogota`, never include them.

Pin each EIP's `REFERENCE_SPEC_VERSION` to the blob hash of its file in the
EIPs repository (not a commit hash), and check the pins with:

```console
GITHUB_TOKEN=$(gh auth token) uv run check_eip_versions \
    tests/unscheduled/evmified_identity --fork EvmifiedIdentity \
    --output /tmp/eip-versions --clean
```

Check that the tests really need the feature: a test that also passes on the
base fork proves nothing about it. For example, temporarily point
`resolve_fork` in `src/ethereum_spec_tools/utils.py` at the base fork and
confirm that the feature's tests fail.

## Keeping a feature alive

- **The base fork changes a replaced definition.** The feature refuses to
  build and names its owners. Carry the fork's change into the overlay if it
  applies, then run `--update-lock`.
- **The base fork changes something else.** The feature picks it up on its
  next build. If the change uses something the feature removed, the build or
  the feature's tests fail.
- **A new fork is added.** Move `LatestFork` in `unscheduled.py` to it, and
  rename the transition forks that start from it.
- **No traction or updates for 365 days.** The feature is deleted. Its owners
  can recreate it on a `projects/<FEATURE>` branch.

Pull requests to the fork never build or fill features, so none of this falls
on their authors.

## Scheduling a feature

Once its EIPs are scheduled, implement them in the fork like any other EIP,
move the tests to `tests/<fork>/`, and delete the feature directory, its
framework fork and its mixins.

## Limitations

- Fixtures name the feature fork, which clients and Hive do not know yet, so
  they only run against the specification for now.
- Features are not shipped in the `ethereum-execution` wheel. They only build
  from a source checkout.
- A fork enables one feature. Features cannot be combined yet.

[process]: ../../../docs/specs/adding_a_new_eip.md#unscheduled-features
