set positional-arguments := true

# List available recipes
default:
    @just --list

root := justfile_directory()
output_dir := root / ".just"
xdist_workers := env("PYTEST_XDIST_AUTO_NUM_WORKERS", "6")
evm_bin := env("EVM_BIN", "evm")
latest_fork := "Amsterdam"

# --- Static Analysis ---

# Auto-fix formatting and lint issues
[group('static analysis')]
fix:
    uv run ruff format
    uv run ruff check --fix

# Run all static checks (spellcheck, lint, format, mypy, ...)
[group('static analysis')]
static: spellcheck lint format-check typecheck ethereum-spec-lint lock-check actionlint

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
    fi

# Add a word to the spellcheck whitelist
[group('static analysis')]
whitelist *words:
    uv run whitelist "$@"

# Lint with ruff
[group('static analysis')]
lint *args:
    uv run ruff check "$@"

# Check formatting with ruff
[group('static analysis')]
format-check *args:
    uv run ruff format --check "$@"

# Run type checking with mypy
[group('static analysis')]
typecheck *args:
    uv run mypy "$@"

# Check EELS import isolation
[group('static analysis')]
ethereum-spec-lint:
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
actionlint:
    uv run actionlint -pyflakes pyflakes -shellcheck "shellcheck -S warning"

# --- Fill Tests ---

# Fill the tests using EELS (with Python)
[group('fill')]
py3 *args:
    @mkdir -p "{{ output_dir }}/py3/tmp" "{{ output_dir }}/py3/logs"
    uv run fill \
        -m "not slow" \
        -n {{ xdist_workers }} --dist=loadgroup \
        --skip-index \
        --output="{{ output_dir }}/py3/fixtures" \
        --cov-config=pyproject.toml \
        --cov=ethereum \
        --cov-report=term \
        --cov-report "xml:{{ output_dir }}/py3/coverage.xml" \
        --no-cov-on-fail \
        --cov-branch \
        --basetemp="{{ output_dir }}/py3/tmp" \
        --log-to "{{ output_dir }}/py3/logs" \
        --clean \
        --until {{ latest_fork }} \
        --durations=50 \
        "$@" \
        tests

# Fill the tests using EELS (with PyPy)
[group('fill')]
pypy3 *args:
    @mkdir -p "{{ output_dir }}/pypy3/tmp" "{{ output_dir }}/pypy3/logs"
    uv run --python pypy3.11 fill \
        --skip-index \
        --output="{{ output_dir }}/pypy3/fixtures" \
        --no-html \
        --tb=long \
        -ra \
        --show-capture=no \
        --disable-warnings \
        -m "eels_base_coverage and not derived_test" \
        -n auto --maxprocesses 7 \
        --dist=loadgroup \
        --basetemp="{{ output_dir }}/pypy3/tmp" \
        --log-to "{{ output_dir }}/pypy3/logs" \
        --clean \
        --until {{ latest_fork }} \
        --ignore=tests/ported_static \
        "$@" \
        tests

# --- Integration Tests ---

# Fill and run EELS against the resulting test fixtures
[group('integration tests')]
json_loader *args:
    @mkdir -p "{{ output_dir }}/json_loader/tmp"
    uv run fill \
        -m "eels_base_coverage and not derived_test" \
        --until {{ latest_fork }} \
        -n {{ xdist_workers }} --dist=loadgroup \
        --skip-index \
        --clean \
        --ignore=tests/ported_static \
        --output="{{ output_dir }}/json_loader/fixtures" \
        --cov-config=pyproject.toml \
        --cov=ethereum \
        --cov-fail-under=85
    uv run pytest \
        -m "not slow" \
        -n auto --maxprocesses 6 --dist=loadfile \
        --basetemp="{{ output_dir }}/json_loader/tmp" \
        "$@" \
        tests/json_loader \
        "{{ output_dir }}/json_loader/fixtures"

# --- Unit Tests ---

# Run the testing package unit tests (with Python)
[group('unit tests')]
tests_pytest_py3 *args:
    @mkdir -p "{{ output_dir }}/tests_pytest_py3/tmp"
    cd packages/testing && uv run pytest \
        -n {{ xdist_workers }} \
        --basetemp="{{ output_dir }}/tests_pytest_py3/tmp" \
        --ignore=src/execution_testing/cli/pytest_commands/plugins/filler/tests/test_benchmarking.py \
        "$@" \
        src

# Run the testing package unit tests (with PyPy)
[group('unit tests')]
tests_pytest_pypy3 *args:
    @mkdir -p "{{ output_dir }}/tests_pytest_pypy3/tmp"
    cd packages/testing && uv run --python pypy3.11 pytest \
        -n auto --maxprocesses 6 \
        --basetemp="{{ output_dir }}/tests_pytest_pypy3/tmp" \
        --ignore=src/execution_testing/cli/pytest_commands/plugins/filler/tests/test_benchmarking.py \
        "$@" \
        src

# Run benchmark framework unit tests (with Python)
[group('unit tests')]
[group('benchmarks')]
tests_benchmark_pytest_py3 *args:
    @mkdir -p "{{ output_dir }}/tests_benchmark_pytest_py3/tmp"
    uv run pytest \
        --basetemp="{{ output_dir }}/tests_benchmark_pytest_py3/tmp" \
        "$@" \
        packages/testing/src/execution_testing/cli/pytest_commands/plugins/filler/tests/test_benchmarking.py

# --- Benchmarks ---

# Fill benchmark tests with --gas-benchmark-values
[group('benchmarks')]
benchmark-gas-values *args:
    @mkdir -p "{{ output_dir }}/benchmark-gas-values/tmp" "{{ output_dir }}/benchmark-gas-values/logs"
    uv run fill \
        --evm-bin="{{ evm_bin }}" \
        --gas-benchmark-values 1 \
        --generate-pre-alloc-groups \
        --fork Osaka \
        -m "not slow" \
        -n auto --maxprocesses 10 --dist=loadgroup \
        --output="{{ output_dir }}/benchmark-gas-values/fixtures" \
        --basetemp="{{ output_dir }}/benchmark-gas-values/tmp" \
        --log-to "{{ output_dir }}/benchmark-gas-values/logs" \
        --clean \
        "$@" \
        tests/benchmark/compute

# Fill benchmark tests with --fixed-opcode-count 1
[group('benchmarks')]
benchmark-fixed-opcode-cli *args:
    @mkdir -p "{{ output_dir }}/benchmark-fixed-opcode-cli/tmp" "{{ output_dir }}/benchmark-fixed-opcode-cli/logs"
    uv run fill \
        --evm-bin="{{ evm_bin }}" \
        --fixed-opcode-count 1 \
        --fork Osaka \
        -m repricing \
        -n auto --maxprocesses 10 --dist=loadgroup \
        -k "not test_alt_bn128 and not test_bls12_381 and not test_modexp" \
        --output="{{ output_dir }}/benchmark-fixed-opcode-cli/fixtures" \
        --basetemp="{{ output_dir }}/benchmark-fixed-opcode-cli/tmp" \
        --log-to "{{ output_dir }}/benchmark-fixed-opcode-cli/logs" \
        --clean \
        "$@" \
        tests/benchmark/compute

# Run benchmark_parser, then fill benchmark tests using its config
[group('benchmarks')]
benchmark-fixed-opcode-config *args:
    @mkdir -p "{{ output_dir }}/benchmark-fixed-opcode-config/tmp" "{{ output_dir }}/benchmark-fixed-opcode-config/logs"
    uv run benchmark_parser
    uv run fill \
        --evm-bin="{{ evm_bin }}" \
        --fixed-opcode-count \
        --fork Osaka \
        -m repricing \
        -n auto --maxprocesses 10 --dist=loadgroup \
        -k "not test_alt_bn128 and not test_bls12_381 and not test_modexp" \
        --output="{{ output_dir }}/benchmark-fixed-opcode-config/fixtures" \
        --basetemp="{{ output_dir }}/benchmark-fixed-opcode-config/tmp" \
        --log-to "{{ output_dir }}/benchmark-fixed-opcode-config/logs" \
        --clean \
        "$@" \
        tests/benchmark/compute

# --- Docs ---

# Generate documentation for EELS using docc
[group('docs')]
spec-docs:
    uv run docc --output "{{ output_dir }}/spec-docs"
    uv run python -c 'import pathlib; print("documentation available under file://{0}".format(pathlib.Path(r"{{ output_dir }}") / "spec-docs" / "index.html"))'

# Build HTML site documentation with mkdocs
[group('docs')]
docs:
    GEN_TEST_DOC_VERSION="just" DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib" uv run mkdocs build --strict -d "{{ output_dir }}/docs/site"

# Build HTML site documentation with mkdocs (fast mode, skips test case reference)
[group('docs')]
fast-docs:
    FAST_DOCS=True GEN_TEST_DOC_VERSION="just" DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib" uv run mkdocs build --strict -d "{{ output_dir }}/docs/site"

# Validate docs/CHANGELOG.md entries
[group('docs')]
changelog:
    uv run validate_changelog

# Lint markdown files (markdownlint)
[group('docs')]
markdownlint:
    uv run markdownlintcli2_soft_fail
