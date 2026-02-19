#!/bin/bash
set -e

file_path=$(jq -r '.tool_input.file_path' 2>/dev/null || echo "")
[ -z "$file_path" ] && exit 0

cd "$CLAUDE_PROJECT_DIR"

case "$file_path" in
  *.py)
    echo "=== Python: $file_path ==="
    # - uvx: faster if uv sync hasn't been called yet.
    # - human readable output: there is no advantage to giving claude json apparently.
    # - autofix (e.g., ruff format): don't do it, causes state confusion.
    uvx ruff check "$file_path" || true
    uvx mypy "$file_path" || true
    echo "--- Hint: Use 'uvx ruff check --fix' for auto-fixable issues, 'uvx ruff format' for formatting ---"
    ;;
  .github/workflows/*.yaml|.github/workflows/*.yml)
    echo "=== GitHub Workflow: $file_path ==="
    uvx --from actionlint-py actionlint -pyflakes pyflakes -shellcheck "shellcheck -S warning" "$file_path" || true
    ;;
  # Future extensions:
  # *.md)
  #   echo "=== Markdown: $file_path ==="
  #   npx markdownlint-cli2 "$file_path" || true
  #   ;;
  # *.yaml|*.yml)
  #   yamllint "$file_path" || true
  #   ;;
  # *.json)
  #   jq . "$file_path" > /dev/null || true
  #   ;;
  # *.toml)
  #   taplo check "$file_path" || true
  #   ;;
esac

exit 0
