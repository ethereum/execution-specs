set positional-arguments := true

alias help := list

# List available recipes (default)
[default, private]
list:
    @just --list

root := justfile_directory()
output_dir := root / ".just"
xdist_workers := env("PYTEST_XDIST_AUTO_NUM_WORKERS", "6")

# The env var's job ends with the `-n` value above; export it empty so
# pytest-xdist, which reads it as a numeric worker-count override in
# `-n auto` mode, does not warn on non-numeric values such as "auto".
export PYTEST_XDIST_AUTO_NUM_WORKERS := ""
evm_bin := env("EVM_BIN", "evm")
latest_fork := "Amsterdam"

# Use the faster sys.monitoring coverage core (default on 3.14, opt-in below).
export COVERAGE_CORE := "sysmon"

# --- Helpers ---

# Create a recipe's --basetemp scratch directory
[private]
_tmp name:
    @mkdir -p "{{ output_dir }}/{{ name }}/tmp"

# Create a recipe's --basetemp and --log-to directories
[private]
_tmp-logs name: (_tmp name)
    @mkdir -p "{{ output_dir }}/{{ name }}/logs"

# --- Static Analysis ---

# Auto-fix formatting and lint issues
[group('static analysis')]
fix:
    uv run ruff format
    uv run ruff check --fix

# Run all static checks (spellcheck, lint, format, mypy, ...)
[group('static analysis'), parallel]
static: typecheck lint-spec spellcheck deadcode lint-actions lock-check format-check lint

# Check spelling
[group('static analysis')]
spellcheck:
    #!/usr/bin/env bash
    if ! uv run codespell; then
        echo ""
        echo "If false positive, add to whitelist:"
        echo "  just whitelist <word>"
        echo ""
        echo "To auto-fix interactively:"
        echo "  uv run codespell -i 3"
        exit 1
    else
        echo "uv run codespell  # passed!"
    fi

# Add a word to the spellcheck whitelist
[group('static analysis')]
whitelist *words:
    uv run whitelist "$@"

# Lint with ruff
[group('static analysis')]
lint *args:
    uv run ruff check "$@"

# Check for dead code with vulture
[group('static analysis')]
deadcode:
    uv run vulture src/ vulture_whitelist.py

# Check formatting with ruff
[group('static analysis')]
format-check *args:
    uv run ruff format --check "$@"

# Run type checking with mypy (installs the optimized dependency group)
[group('static analysis')]
typecheck *args:
    uv run --group optimized mypy "$@"

# Check EELS import isolation
[group('static analysis')]
lint-spec:
    uv run ethereum-spec-lint

# Verify uv.lock is up to date
[group('static analysis')]
lock-check:
    #!/usr/bin/env bash
    if ! uv lock --check; then
        echo ""
        echo "To sync the lock file:"
        echo "  uv lock"
        echo ""
        echo "Then commit the updated uv.lock."
        exit 1
    fi

# Lint GitHub Actions workflows
[group('static analysis')]
lint-actions:
    uv run actionlint -pyflakes pyflakes -shellcheck "shellcheck -S warning"

# --- Consensus Tests ---

# Generate HTML coverage report from last just fill run
[group('consensus tests')]
coverage:
    uv run coverage html -d "{{ output_dir }}/fill/coverage-html"

# Generate EIP test checklists from eip_checklist markers                                                                         
[group('consensus tests')] 
checklist *args:
    uv run checklist --output tmp/checklist "$@"

# Fill the consensus tests using EELS (with Python)
[group('consensus tests')]
fill *args: (_tmp-logs "fill")
    uv run fill \
        -m "not slow" \
        -n {{ xdist_workers }} --dist=loadgroup \
        --skip-index \
        --output="{{ output_dir }}/fill/fixtures" \
        --cov-config=pyproject.toml \
        --cov=ethereum \
        --cov-report=term \
        --cov-report "xml:{{ output_dir }}/fill/coverage.xml" \
        --no-cov-on-fail \
        --cov-branch \
        --basetemp="{{ output_dir }}/fill/tmp" \
        --log-to "{{ output_dir }}/fill/logs" \
        --clean \
        --until "{{ latest_fork }}" \
        --durations=50 \
        "$@" \
        tests

# Callers append the feature params, fork range and output; last flag wins.
# Fill fixtures with the flags shared by all fixture releases
[group('consensus tests')]
fill-release *args:
    uv run fill \
        -n {{ xdist_workers }} \
        --output="{{ output_dir }}/fill-release/fixtures" \
        --no-html \
        --durations=100 \
        --log-level=DEBUG \
        "$@"

# --- Integration Tests ---

# Fill the base coverage consensus tests using EELS with PyPy
[group('integration tests')]
fill-pypy *args: (_tmp-logs "fill-pypy")
    uv run --python pypy3.11 --no-dev --group test fill \
        --skip-index \
        --output="{{ output_dir }}/fill-pypy/fixtures" \
        --no-html \
        --tb=long \
        -ra \
        --show-capture=no \
        --disable-warnings \
        -m "eels_base_coverage and not derived_test" \
        -n auto --maxprocesses 7 \
        --dist=loadgroup \
        --basetemp="{{ output_dir }}/fill-pypy/tmp" \
        --log-to "{{ output_dir }}/fill-pypy/logs" \
        --clean \
        --until "{{ latest_fork }}" \
        --ignore=tests/ported_static \
        "$@" \
        tests

# Fill the base coverage consensus tests and run EELS against the fixtures
[group('integration tests')]
json-loader *args: (_tmp "json-loader")
    uv run fill \
        -m "eels_base_coverage and not derived_test" \
        --until "{{ latest_fork }}" \
        -n {{ xdist_workers }} --dist=loadgroup \
        --skip-index \
        --clean \
        --ignore=tests/ported_static \
        --output="tests/json_loader/fixtures" \
        --cov-config=pyproject.toml \
        --cov=ethereum \
        --cov-branch \
        --cov-report=term \
        --durations=50 \
        --cov-fail-under=85
    uv run pytest \
        -m "not slow" \
        -n {{ xdist_workers }} --dist=loadfile \
        --cov-config=pyproject.toml \
        --cov=ethereum \
        --cov-branch \
        --cov-report=term \
        --cov-report "xml:{{ output_dir }}/json-loader/coverage.xml" \
        --durations=50 \
        --basetemp="{{ output_dir }}/json-loader/tmp" \
        "$@" \
        tests/json_loader

# Run the spec-tools tests (lint and new-fork tooling)
[group('integration tests')]
spec-tools *args: (_tmp "spec-tools")
    uv run pytest \
        -n {{ xdist_workers }} \
        --basetemp="{{ output_dir }}/spec-tools/tmp" \
        --ignore=tests/evm_tools/test_count_opcodes.py \
        "$@" \
        tests/evm_tools

# --- Unit Tests ---

# Run the testing package unit tests (with Python)
[group('unit tests')]
test-tests *args: (_tmp "test-tests")
    cd packages/testing && uv run pytest \
        -n {{ xdist_workers }} \
        --basetemp="{{ output_dir }}/test-tests/tmp" \
        "$@" \
        src

# Run the testing package unit tests (with PyPy)
[group('unit tests')]
test-tests-pypy *args: (_tmp "test-tests-pypy")
    cd packages/testing && uv run --python pypy3.11 --no-dev --group test pytest \
        -n auto --maxprocesses 6 \
        --basetemp="{{ output_dir }}/test-tests-pypy/tmp" \
        --ignore=src/execution_testing/cli/pytest_commands/plugins/filler/tests/test_benchmarking.py \
        "$@" \
        src

# Run CI release script integration tests
[group('unit tests')]
test-ci-scripts *args:
    uv run pytest "$@" .github/scripts/tests/

# --- Benchmarks ---

# test_return_revert is excluded: its max-size INVALID-padded callees make
# EELS re-scan jumpdests on every call (100-270s per test, ~60% of the
# suite's runtime); the geth-backed benchmarks/** CI still fills it.
# Fill benchmark tests at 1M gas with the in-repo EELS t8n
[group('benchmark tests')]
fill-benchmark *args: (_tmp-logs "fill-benchmark")
    uv run fill \
        --gas-benchmark-values 1 \
        --fork "{{ latest_fork }}" \
        -m "not slow and not derived_test" \
        -k "not test_return_revert" \
        -n {{ xdist_workers }} --dist=loadgroup \
        --skip-index \
        --output="{{ output_dir }}/fill-benchmark/fixtures" \
        --basetemp="{{ output_dir }}/fill-benchmark/tmp" \
        --log-to "{{ output_dir }}/fill-benchmark/logs" \
        --clean \
        --durations=20 \
        "$@" \
        tests/benchmark/compute

# Smoke-test benchmark tests: fill blockchain_test fixtures, then verify against EELS.
[group('benchmark tests')]
bench-gas *args: (_tmp-logs "bench-gas")
    @echo "==> Step 1/3: Generating pre-alloc groups (smoke-tests the BlockchainEngineX path)"
    uv run fill \
        --generate-pre-alloc-groups \
        --evm-bin="{{ evm_bin }}" \
        --gas-benchmark-values 1 \
        --fork Amsterdam \
        -m "not slow" \
        -n auto --maxprocesses 10 --dist=loadgroup \
        --output="{{ output_dir }}/bench-gas/pre-alloc" \
        --basetemp="{{ output_dir }}/bench-gas/tmp" \
        --log-to "{{ output_dir }}/bench-gas/logs" \
        --clean \
        "$@" \
        tests/benchmark/compute
    @echo "==> Step 2/3: Filling blockchain_test fixtures with configured EVM (EVM_BIN={{ evm_bin }})"
    uv run fill \
        --evm-bin="{{ evm_bin }}" \
        --gas-benchmark-values 1 \
        --fork Amsterdam \
        -m "blockchain_test and (not derived_test) and (not slow)" \
        -n auto --maxprocesses 10 --dist=loadgroup \
        --durations=20 \
        --output="{{ output_dir }}/bench-gas/fixtures" \
        --basetemp="{{ output_dir }}/bench-gas/tmp" \
        --log-to "{{ output_dir }}/bench-gas/logs" \
        --clean \
        "$@" \
        tests/benchmark/compute
    @echo "==> Step 3/3: Running filled fixtures against EELS via json_loader"
    @rm -rf tests/json_loader/bench_gas_fixtures
    ln -sfn "{{ output_dir }}/bench-gas/fixtures" tests/json_loader/bench_gas_fixtures
    cd tests/json_loader && uv run --python pypy3.11 --no-dev --group test pytest \
        --fork Amsterdam \
        --allow-post-state-hash \
        -n auto --maxprocesses 10 --dist=loadfile \
        --durations=20 \
        --basetemp="{{ output_dir }}/bench-gas/json-loader-tmp" \
        bench_gas_fixtures

# Fill benchmark tests with --fixed-opcode-count 1
[group('benchmark tests')]
bench-opcode *args: (_tmp-logs "bench-opcode")
    uv run fill \
        --evm-bin="{{ evm_bin }}" \
        --fixed-opcode-count 1 \
        --fork Amsterdam \
        -m "repricing and not slow" \
        -n auto --maxprocesses 10 --dist=loadgroup \
        -k "not test_alt_bn128 and not test_bls12_381 and not test_modexp and not uncachable" \
        --output="{{ output_dir }}/bench-opcode/fixtures" \
        --basetemp="{{ output_dir }}/bench-opcode/tmp" \
        --log-to "{{ output_dir }}/bench-opcode/logs" \
        --clean \
        "$@" \
        tests/benchmark/compute

# Run benchmark_parser, then fill benchmark tests using its config
[group('benchmark tests')]
bench-opcode-config *args: (_tmp-logs "bench-opcode-config")
    uv run benchmark_parser
    uv run fill \
        --evm-bin="{{ evm_bin }}" \
        --fixed-opcode-count \
        --fork Amsterdam \
        -m "repricing and not slow" \
        -n auto --maxprocesses 10 --dist=loadgroup \
        -k "not test_alt_bn128 and not test_bls12_381 and not test_modexp and not uncachable" \
        --output="{{ output_dir }}/bench-opcode-config/fixtures" \
        --basetemp="{{ output_dir }}/bench-opcode-config/tmp" \
        --log-to "{{ output_dir }}/bench-opcode-config/logs" \
        --clean \
        "$@" \
        tests/benchmark/compute

# --- Docs ---

export GEN_TEST_DOC_VERSION := "local"
export DYLD_FALLBACK_LIBRARY_PATH := if os() == "macos" { "/opt/homebrew/lib" } else { "" }

# Generate documentation for EELS using docc
[group('docs')]
docs-spec $DOCC_SKIP_DIFFS=env_var_or_default("DOCC_SKIP_DIFFS", ""):
    uv run docc --output "{{ output_dir }}/docs-spec"
    uv run python -c 'import pathlib; print("documentation available under file://{0}".format(pathlib.Path(r"{{ output_dir }}") / "docs-spec" / "index.html"))'

# Generate documentation for EELS using docc, skipping the slow per-fork diff render
[group('docs')]
docs-spec-fast: (docs-spec "1")

# Build spec docs in parallel shards for fast PR validation
[group('docs')]
docs-spec-parallel shards="4":
    uv run python -m ethereum_spec_tools.docc_shards \
        -n {{ shards }} -o "{{ output_dir }}/docs-spec-parallel"

# Build HTML site documentation with mkdocs
[group('docs')]
docs *args:
    uv run mkdocs build --strict -d "{{ output_dir }}/docs/site" "$@"

# Build HTML site documentation with mkdocs (skip test case reference)
[group('docs')]
docs-fast *args:
    FAST_DOCS=True uv run mkdocs build --strict -d "{{ output_dir }}/docs/site" "$@"

# Serve site documentation locally with mkdocs (live reload)
[group('docs')]
docs-serve *args:
    uv run mkdocs serve "$@"

# Serve site documentation locally with mkdocs (skip test case reference)
[group('docs')]
docs-serve-fast *args:
    FAST_DOCS=True uv run mkdocs serve "$@"

# Lint markdown files (markdownlint)
[group('docs')]
lint-md:
    uv run markdownlintcli2_soft_fail

[private]
crops:
    @uvx pycowsay==0.0.0.2 "ethereum is good"

# --- Housekeeping ---

# Regenerate the vendored OpenRPC schema from execution-apis (requires Go)
[group('housekeeping')]
refresh-openrpc tag="v1.0.0-beta.7":
    #!/usr/bin/env bash
    set -euo pipefail
    # Flags mirror hive's rpc-compat Dockerfile, so the schema we validate
    # against matches the one clients are tested against upstream.
    dest="$(pwd)/packages/testing/src/execution_testing/rpc/schemas/openrpc.json"
    work="$(mktemp -d)"
    trap 'rm -rf "$work"' EXIT
    git clone --depth 1 -b "{{ tag }}" -q \
        https://github.com/ethereum/execution-apis.git "$work"
    cd "$work/tools" && go build -o specgen ./cmd/specgen
    cd "$work" && ./tools/specgen -o "$dest" -deref \
        -schemas 'src/schemas' -schemas 'src/engine/openrpc/schemas' \
        -methods 'src/eth' -methods 'src/debug' -methods 'src/txpool' \
        -methods 'src/engine/openrpc/methods' -methods 'src/testing' \
        -error-groups 'src/error-groups'
    echo "Regenerated from {{ tag }} ($(git -C "$work" rev-parse HEAD))."
    echo "Update the pin table in the schemas README if the tag changed."

# Remove caches and build artifacts (.pytest_cache, .mypy_cache, __pycache__, ...)
[group('housekeeping')]
clean *args:
    uv run eest clean "$@"

# Remove caches, build artifacts, .just, and .venv
[group('housekeeping')]
clean-all *args:
    uv run eest clean --all "$@"

# Print the command to install shell completions for just recipes
[group('housekeeping')]
shell-completions:
    #!/usr/bin/env bash
    case "$(basename "$SHELL")" in
        bash)
            echo "Run the following commands to install just completions for bash:"
            echo ""
            echo "  mkdir -p ~/.local/share/bash-completion/completions"
            echo "  just --completions bash > ~/.local/share/bash-completion/completions/just"
            ;;
        zsh)
            echo "Run the following commands to install just completions for zsh:"
            echo ""
            echo "  mkdir -p ~/.zsh/completions"
            echo "  just --completions zsh > ~/.zsh/completions/_just"
            echo ""
            echo "Then add to your .zshrc:"
            echo ""
            echo "  fpath=(~/.zsh/completions \$fpath)"
            echo "  autoload -U compinit"
            echo "  compinit"
            ;;
        fish)
            echo "Run the following commands to install just completions for fish:"
            echo ""
            echo "  mkdir -p ~/.config/fish/completions"
            echo "  just --completions fish > ~/.config/fish/completions/just.fish"
            ;;
        *)
            echo "See the link below for instructions for your shell."
            ;;
    esac
    echo ""
    echo "For more details, see https://just.systems/man/en/shell-completion-scripts.html"
