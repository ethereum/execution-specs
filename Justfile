set positional-arguments := true

# List available recipes
default:
    @just --list

root := justfile_directory()
output_dir := root / ".just"
xdist_workers := env("PYTEST_XDIST_AUTO_NUM_WORKERS", "6")
evm_bin := env("EVM_BIN", "evm")

# --- Static Analysis ---

# Auto-fix formatting and lint issues
[group('static analysis')]
fix:
    uv run ruff format
    uv run ruff check --fix

# Run spelling, lint, typechecking and dependency checks
[group('static analysis')]
static:
    uv run codespell
    uv run ruff check
    uv run ruff format --check
    uv run mypy
    uv run ethereum-spec-lint
    uv lock --check
    uv run actionlint -pyflakes pyflakes -shellcheck "shellcheck -S warning"

# --- Fill Tests ---

# Fill the tests using EELS (with Python)
[group('fill')]
py3 *args:
    uv run fill \
        -m "not slow" \
        -n {{ xdist_workers }} --dist=loadgroup \
        --skip-index \
        --cov-config=pyproject.toml \
        --cov=ethereum \
        --cov-report=term \
        --cov-report "xml:{{ output_dir }}/coverage.xml" \
        --no-cov-on-fail \
        --cov-branch \
        --basetemp="{{ output_dir }}/tmp/pytest" \
        --log-to "{{ output_dir }}/logs" \
        --clean \
        --until Amsterdam \
        --durations=50 \
        "$@" \
        tests

# Fill the tests using EELS (with PyPy)
[group('fill')]
pypy3 *args:
    uv run --python pypy3.11 fill \
        --skip-index \
        --no-html \
        --tb=long \
        -ra \
        --show-capture=no \
        --disable-warnings \
        -m "eels_base_coverage and not derived_test" \
        -n auto --maxprocesses 7 \
        --dist=loadgroup \
        --basetemp="{{ output_dir }}/tmp/pytest" \
        --log-to "{{ output_dir }}/logs" \
        --clean \
        --until Amsterdam \
        --ignore=tests/ported_static \
        "$@" \
        tests

# --- Integration Tests ---

# Fill and run EELS against the resulting test fixtures
[group('integration tests')]
json_loader *args:
    uv run fill \
        -m "eels_base_coverage and not derived_test" \
        --until Amsterdam \
        -n {{ xdist_workers }} --dist=loadgroup \
        --skip-index \
        --clean \
        --ignore=tests/ported_static \
        --output="tests/json_loader/fixtures" \
        --cov-config=pyproject.toml \
        --cov=ethereum \
        --cov-fail-under=85
    uv run pytest \
        -m "not slow" \
        -n auto --maxprocesses 6 --dist=loadfile \
        --basetemp="{{ output_dir }}/tmp/pytest" \
        "$@" \
        tests/json_loader

# --- Unit Tests ---

# Run the testing package unit tests (with Python)
[group('unit tests')]
tests_pytest_py3 *args:
    cd packages/testing && uv run pytest \
        -n {{ xdist_workers }} \
        --basetemp="{{ root }}/.just/tmp/pytest" \
        --ignore=src/execution_testing/cli/pytest_commands/plugins/filler/tests/test_benchmarking.py \
        "$@" \
        src

# Run the testing package unit tests (with PyPy)
[group('unit tests')]
tests_pytest_pypy3 *args:
    cd packages/testing && uv run --python pypy3.11 pytest \
        -n auto --maxprocesses 6 \
        --basetemp="{{ root }}/.just/tmp/pytest" \
        --ignore=src/execution_testing/cli/pytest_commands/plugins/filler/tests/test_benchmarking.py \
        "$@" \
        src

# Run benchmark framework unit tests (with Python)
[group('unit tests')]
tests_benchmark_pytest_py3 *args:
    uv run pytest \
        --basetemp="{{ output_dir }}/tmp/pytest" \
        "$@" \
        packages/testing/src/execution_testing/cli/pytest_commands/plugins/filler/tests/test_benchmarking.py

# --- Benchmarks ---

# Fill benchmark tests with --gas-benchmark-values
[group('benchmarks')]
benchmark-gas-values *args:
    uv run fill \
        --evm-bin="{{ evm_bin }}" \
        --gas-benchmark-values 1 \
        --generate-pre-alloc-groups \
        --fork Osaka \
        -m "not slow" \
        -n auto --maxprocesses 10 --dist=loadgroup \
        --basetemp="{{ output_dir }}/tmp/pytest" \
        --log-to "{{ output_dir }}/logs" \
        --clean \
        "$@" \
        tests/benchmark/compute

# Fill benchmark tests with --fixed-opcode-count 1
[group('benchmarks')]
benchmark-fixed-opcode-cli *args:
    uv run fill \
        --evm-bin="{{ evm_bin }}" \
        --fixed-opcode-count 1 \
        --fork Osaka \
        -m repricing \
        -n auto --maxprocesses 10 --dist=loadgroup \
        -k "not test_alt_bn128 and not test_bls12_381 and not test_modexp" \
        --basetemp="{{ output_dir }}/tmp/pytest" \
        --log-to "{{ output_dir }}/logs" \
        --clean \
        "$@" \
        tests/benchmark/compute

# Run benchmark_parser, then fill benchmark tests using its config
[group('benchmarks')]
benchmark-fixed-opcode-config *args:
    uv run benchmark_parser
    uv run fill \
        --evm-bin="{{ evm_bin }}" \
        --fixed-opcode-count \
        --fork Osaka \
        -m repricing \
        -n auto --maxprocesses 10 --dist=loadgroup \
        -k "not test_alt_bn128 and not test_bls12_381 and not test_modexp" \
        --basetemp="{{ output_dir }}/tmp/pytest" \
        --log-to "{{ output_dir }}/logs" \
        --clean \
        "$@" \
        tests/benchmark/compute

# --- Docs ---

# Generate documentation for EELS using docc
[group('docs')]
spec-docs:
    uv run docc --output "{{ output_dir }}/docs"
    uv run python -c 'import pathlib; print("documentation available under file://{0}".format(pathlib.Path(r"{{ output_dir }}") / "docs" / "index.html"))'

# Build HTML site documentation with mkdocs
[group('docs')]
docs:
    GEN_TEST_DOC_VERSION="just" DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib" uv run mkdocs build --strict

# Validate docs/CHANGELOG.md entries
[group('docs')]
changelog:
    uv run validate_changelog

# Lint markdown files (markdownlint)
[group('docs')]
markdownlint:
    uv run markdownlintcli2_soft_fail
