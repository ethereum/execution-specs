set positional-arguments := true

alias help := list

# List available recipes (default)
[default, private]
list:
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

# Run type checking with mypy
[group('static analysis')]
typecheck *args:
    uv run mypy "$@"

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
fill *args:
    @mkdir -p "{{ output_dir }}/fill/tmp" "{{ output_dir }}/fill/logs"
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

# --- Integration Tests ---

# Fill the base coverage consensus tests using EELS with PyPy
[group('integration tests')]
fill-pypy *args:
    @mkdir -p "{{ output_dir }}/fill-pypy/tmp" "{{ output_dir }}/fill-pypy/logs"
    uv run --python pypy3.11 fill \
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
json-loader *args:
    @mkdir -p "{{ output_dir }}/json-loader/tmp"
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
        --cov-fail-under=85
    uv run pytest \
        -m "not slow" \
        -n auto --maxprocesses 6 --dist=loadfile \
        --basetemp="{{ output_dir }}/json-loader/tmp" \
        "$@" \
        tests/json_loader

# --- Unit Tests ---

# Run the testing package unit tests (with Python)
[group('unit tests')]
test-tests *args:
    @mkdir -p "{{ output_dir }}/test-tests/tmp"
    cd packages/testing && uv run pytest \
        -n {{ xdist_workers }} \
        --basetemp="{{ output_dir }}/test-tests/tmp" \
        --ignore=src/execution_testing/cli/pytest_commands/plugins/filler/tests/test_benchmarking.py \
        "$@" \
        src

# Run the testing package unit tests (with PyPy)
[group('unit tests')]
test-tests-pypy *args:
    @mkdir -p "{{ output_dir }}/test-tests-pypy/tmp"
    cd packages/testing && uv run --python pypy3.11 pytest \
        -n auto --maxprocesses 6 \
        --basetemp="{{ output_dir }}/test-tests-pypy/tmp" \
        --ignore=src/execution_testing/cli/pytest_commands/plugins/filler/tests/test_benchmarking.py \
        "$@" \
        src

# Run benchmark framework unit tests (with Python)
[group('unit tests')]
[group('benchmark tests')]
test-tests-bench *args:
    @mkdir -p "{{ output_dir }}/test-tests-bench/tmp"
    uv run pytest \
        --basetemp="{{ output_dir }}/test-tests-bench/tmp" \
        "$@" \
        packages/testing/src/execution_testing/cli/pytest_commands/plugins/filler/tests/test_benchmarking.py

# Run CI release script integration tests
[group('unit tests')]
test-ci-scripts *args:
    uv run pytest "$@" .github/scripts/tests/

# --- Benchmarks ---

# Fill benchmark tests with --gas-benchmark-values
[group('benchmark tests')]
bench-gas *args:
    @mkdir -p "{{ output_dir }}/bench-gas/tmp" "{{ output_dir }}/bench-gas/logs"
    uv run fill \
        --evm-bin="{{ evm_bin }}" \
        --gas-benchmark-values 1 \
        --generate-all-formats \
        --fork Osaka \
        -m "not slow" \
        -n auto --maxprocesses 10 --dist=loadgroup \
        --output="{{ output_dir }}/bench-gas/fixtures" \
        --basetemp="{{ output_dir }}/bench-gas/tmp" \
        --log-to "{{ output_dir }}/bench-gas/logs" \
        --clean \
        "$@" \
        tests/benchmark/compute

# Fill benchmark tests with --fixed-opcode-count 1
[group('benchmark tests')]
bench-opcode *args:
    @mkdir -p "{{ output_dir }}/bench-opcode/tmp" "{{ output_dir }}/bench-opcode/logs"
    uv run fill \
        --evm-bin="{{ evm_bin }}" \
        --fixed-opcode-count 1 \
        --fork Osaka \
        -m repricing \
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
bench-opcode-config *args:
    @mkdir -p "{{ output_dir }}/bench-opcode-config/tmp" "{{ output_dir }}/bench-opcode-config/logs"
    uv run benchmark_parser
    uv run fill \
        --evm-bin="{{ evm_bin }}" \
        --fixed-opcode-count \
        --fork Osaka \
        -m repricing \
        -n auto --maxprocesses 10 --dist=loadgroup \
        -k "not test_alt_bn128 and not test_bls12_381 and not test_modexp and not test_point_evaluation_uncachable" \
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
docs-spec $DOCC_SKIP_DIFFS="":
    uv run docc --output "{{ output_dir }}/docs-spec"
    uv run python -c 'import pathlib; print("documentation available under file://{0}".format(pathlib.Path(r"{{ output_dir }}") / "docs-spec" / "index.html"))'

# Generate documentation for EELS using docc, skipping the slow per-fork diff render
[group('docs')]
docs-spec-fast: (docs-spec "1")

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

# Validate docs/CHANGELOG.md entries
[group('docs')]
changelog:
    uv run validate_changelog

# Lint markdown files (markdownlint)
[group('docs')]
lint-md:
    uv run markdownlintcli2_soft_fail

[private]
crops:
    @uvx pycowsay==0.0.0.2 "ethereum is good"

# --- Housekeeping ---

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
