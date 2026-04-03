"""Jinja2 rendering for filler-to-python codegen."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import jinja2

from .ir import AccountAssertionIR, IntermediateTestModel

TEMPLATE_DIR = Path(__file__).parent / "templates"


# ---------------------------------------------------------------------------
# Custom Jinja2 filters
# ---------------------------------------------------------------------------


def format_int(v: int | None) -> str:
    """Format an integer as Python literal: hex for large values."""
    if v is None:
        return "0"
    if isinstance(v, bool):
        return str(v)
    v = int(v)
    if v > 0xFFFF:
        return hex(v)
    return str(v)


def format_hex(v: int | str) -> str:
    """Always format as hex."""
    if isinstance(v, str):
        return v
    return hex(int(v))


def format_storage(d: dict) -> str:
    """Format a {slot: value} storage dict as Python literal."""
    if not d:
        return "{}"
    items = []
    for k in sorted(d.keys()):
        items.append(f"{format_int(k)}: {format_int(d[k])}")
    single = "{" + ", ".join(items) + "}"
    if len(single) <= 50:
        return single
    formatted = ",\n            ".join(items)
    return "{\n            " + formatted + ",\n        }"


def format_account(a: AccountAssertionIR) -> str:
    """Format an AccountAssertionIR as Account(...) expression."""
    if a.should_not_exist:
        return "Account.NONEXISTENT"

    parts: list[str] = []
    if a.storage is not None:
        if a.storage_any_keys:
            # Need Storage object with set_expect_any calls
            storage_str = format_storage(a.storage)
            any_keys = a.storage_any_keys
            parts.append(
                f"storage=_storage_with_any({storage_str}, {any_keys})"
            )
        else:
            parts.append(f"storage={format_storage(a.storage)}")
    if a.code is not None:
        if a.code:
            parts.append(f'code=bytes.fromhex("{a.code.hex()}")')
        else:
            parts.append('code=b""')
    if a.balance is not None:
        parts.append(f"balance={format_int(a.balance)}")
    if a.nonce is not None:
        parts.append(f"nonce={a.nonce}")

    if not parts:
        return "Account()"
    single = "Account(" + ", ".join(parts) + ")"
    if len(single) <= 60:
        return single
    inner = ",\n                ".join(parts)
    return "Account(\n                " + inner + ",\n            )"


def format_post(result: list) -> str:
    """Format a list of AccountAssertionIR as a post dict literal."""
    if not result:
        return "{}"

    entries: list[str] = []
    for a in result:
        entries.append(f"{a.var_ref}: {format_account(a)}")

    if len(entries) == 1:
        single = "{" + entries[0] + "}"
        if len(single) <= 70:
            return single

    inner = ",\n        ".join(entries)
    return "{\n        " + inner + ",\n    }"


def format_expect_exception(d: dict) -> str:
    """Format expect_exception dict with unquoted exception values."""
    items = []
    for k, v in d.items():
        items.append(f'"{k}": {v}')
    return "{" + ", ".join(items) + "}"


def wrap_op_chain(s: str, indent: int = 8) -> str:
    """Split an Op chain at + boundaries to fit 79-char lines."""
    if not s:
        return '""'

    prefix = " " * indent
    # If it fits on one line, just return it
    if len(prefix + s) <= 79:
        return s

    # If it's a bytes.fromhex expression, just return it (will get noqa)
    if s.startswith("bytes.fromhex("):
        return s

    # Split at " + "
    parts = s.split(" + ")
    if len(parts) <= 1:
        return s

    lines: list[str] = []
    current_line = parts[0]
    for part in parts[1:]:
        candidate = current_line + " + " + part
        if len(prefix + candidate) <= 79:
            current_line = candidate
        else:
            lines.append(current_line)
            current_line = part

    lines.append(current_line)

    if len(lines) == 1:
        return lines[0]

    joiner = "\n" + prefix + "+ "
    return lines[0] + joiner + joiner.join(lines[1:])


# ---------------------------------------------------------------------------
# Template rendering
# ---------------------------------------------------------------------------


def _build_template_env() -> jinja2.Environment:
    """Create and configure the Jinja2 environment."""
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATE_DIR)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["format_int"] = format_int
    env.filters["format_hex"] = format_hex
    env.filters["format_storage"] = format_storage
    env.filters["format_account"] = format_account
    env.filters["format_post"] = format_post
    env.filters["format_expect_exception"] = format_expect_exception
    env.filters["wrap_op_chain"] = wrap_op_chain
    return env


_template_env = _build_template_env()


def render_test(ir: IntermediateTestModel) -> str:
    """Render a Python test file from an IR model."""
    template = _template_env.get_template("state_test.py.j2")

    # Build short docstring (first sentence of filler comment)
    short_docstring = ir.filler_comment or ir.test_name
    if "." in short_docstring:
        short_docstring = short_docstring[: short_docstring.index(".") + 1]
    if len(short_docstring) > 70:
        # Truncate at word boundary
        truncated = short_docstring[:67]
        last_space = truncated.rfind(" ")
        if last_space > 40:
            truncated = truncated[:last_space]
        short_docstring = truncated + "..."
    # Ensure ends with period (D400/D415)
    if not short_docstring.endswith("."):
        short_docstring += "."
    # Capitalize first letter (D403), avoid "This" (D404)
    if short_docstring and short_docstring[0].islower():
        short_docstring = short_docstring[0].upper() + short_docstring[1:]
    if short_docstring.startswith("This "):
        short_docstring = "Test: t" + short_docstring[2:]
    # Escape any quotes
    short_docstring = short_docstring.replace('"', '\\"')

    # Build docstring — ensure first line ends with period (D400/D415)
    docstring = ir.filler_comment or ir.test_name
    first_line = docstring.split("\n")[0]
    if not first_line.rstrip().endswith("."):
        docstring = (
            first_line.rstrip() + ".\n" + "\n".join(docstring.split("\n")[1:])
        )
        docstring = docstring.rstrip()
    # Capitalize first letter (D403) and avoid starting with "This" (D404)
    if docstring and docstring[0].islower():
        docstring = docstring[0].upper() + docstring[1:]
    if docstring.startswith("This "):
        docstring = "Test: " + docstring[0].lower() + docstring[1:]
    # Ensure all docstring lines fit 79 chars.
    # First line must end with period (D400), so truncate if needed.
    import textwrap

    doc_lines = docstring.split("\n")
    first = doc_lines[0]
    if len(first) > 75:
        # Truncate at word boundary, add period
        trunc = first[:72]
        sp = trunc.rfind(" ")
        if sp > 40:
            trunc = trunc[:sp]
        first = trunc + "..."
        if not first.endswith("."):
            first += "."
    doc_lines[0] = first
    # Ensure blank line after first line so D400 only checks line 1
    if len(doc_lines) > 1 and doc_lines[1].strip():
        doc_lines.insert(1, "")
    wrapped_lines: list[str] = [doc_lines[0]]
    for line in doc_lines[1:]:
        if len(line) > 79:
            wrapped_lines.extend(textwrap.wrap(line, width=79))
        else:
            wrapped_lines.append(line)
    docstring = "\n".join(wrapped_lines)

    # Has exceptions?
    has_exceptions = any(p.has_exception for p in ir.parameters)

    # Needs _storage_with_any helper?
    needs_storage_any = any(
        a.storage_any_keys for entry in ir.expect_entries for a in entry.result
    )

    # Single-case post and error
    single_post = None
    single_error = None
    if ir.expect_entries and len(ir.expect_entries) == 1:
        entry = ir.expect_entries[0]
        if entry.result:
            single_post = entry.result
        if entry.expect_exception:
            exc_values = list(entry.expect_exception.values())
            if exc_values:
                single_error = exc_values[0]

    context = {
        "docstring": docstring,
        "filler_path": ir.filler_path,
        "test_name": ir.test_name,
        "short_docstring": short_docstring,
        "valid_from": ir.valid_from,
        "valid_until": ir.valid_until,
        "is_slow": ir.is_slow,
        "is_multi_case": ir.is_multi_case,
        "is_fork_dependent": ir.is_fork_dependent,
        "has_exceptions": has_exceptions,
        "env": ir.environment,
        "accounts": ir.accounts,
        "tx": ir.transaction,
        "tx_data": ir.tx_data,
        "tx_gas": ir.tx_gas,
        "tx_value": ir.tx_value,
        "expect_entries": ir.expect_entries,
        "parameters": ir.parameters,
        "sender": ir.sender,
        "address_constants": ir.address_constants,
        "needs_storage_any": needs_storage_any,
        "single_post": single_post,
        "single_error": single_error,
    } | asdict(ir.imports)

    return template.render(**context)
