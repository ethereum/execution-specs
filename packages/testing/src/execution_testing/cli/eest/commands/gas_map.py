"""Display the mapping between EVM opcodes and GasCosts field names."""

import inspect
import json
import re
from collections import defaultdict
from dataclasses import fields

import click

from execution_testing.forks.base_fork import BaseFork
from execution_testing.forks.gas_costs import GasCosts
from execution_testing.forks.helpers import get_forks

OPCODE_TIER_FIELDS = (
    "OPCODE_JUMPDEST",
    "BASE",
    "VERY_LOW",
    "LOW",
    "MID",
    "HIGH",
    "OPCODE_BLOCKHASH",
    "WARM_SLOAD",
)


def _get_latest_fork() -> type[BaseFork]:
    """Return the latest fork class."""
    return get_forks()[-1]


def _get_fork(fork_name: str) -> type[BaseFork]:
    """Return the fork class matching fork_name, or exit with error."""
    for fork in get_forks():
        if fork.name().lower() == fork_name.lower():
            return fork
    available = ", ".join(f.name() for f in get_forks())
    raise click.ClickException(
        f"Unknown fork: {fork_name}. Available forks: {available}"
    )


def _build_tier_reverse_map(gas_costs: GasCosts) -> dict[int, list[str]]:
    """Build a reverse map from gas value to opcode tier field names only."""
    reverse = defaultdict(list)
    for name in OPCODE_TIER_FIELDS:
        value = getattr(gas_costs, name)
        reverse[value].append(name)
    return dict(reverse)


def _get_opcode_gas_map_sources(fork_class: type[BaseFork]) -> str:
    """Get source code of opcode_gas_map from the fork's MRO chain."""
    sources = []
    for cls in fork_class.__mro__:
        if cls is BaseFork or cls is object:
            continue
        if "opcode_gas_map" in cls.__dict__:
            try:
                # `cls` is typed as `type` (from `__mro__`)
                # The full chain up to python's default `object` is walked, and
                # the guard above ensures that opcode_gas_map exists before
                # adding the source.
                method = cls.opcode_gas_map  # type: ignore[attr-defined]
                sources.append(inspect.getsource(method))
            except (OSError, TypeError):
                pass
    return "\n".join(sources)


def _get_helper_method_fields(
    fork_class: type[BaseFork],
) -> dict[str, set[str]]:
    """Extract GasCosts fields from helper methods on the fork class."""
    valid_fields = {f.name for f in fields(GasCosts)}
    helper_fields = {}
    for cls in fork_class.__mro__:
        if cls is object:
            continue
        for name, method in cls.__dict__.items():
            if name.startswith("_with_") or name.startswith("_calculate_"):
                try:
                    src = inspect.getsource(method)
                except (OSError, TypeError):
                    continue
                found = set()
                for field_name in valid_fields:
                    if field_name in src:
                        found.add(field_name)
                if name == "_with_memory_expansion":
                    found.add("MEMORY_PER_WORD")
                if found:
                    helper_fields[name] = found
    return helper_fields


def _build_full_opcode_field_map(
    fork_class: type[BaseFork],
) -> dict[str, list[str]]:
    """Build complete opcode→GasCosts fields map using source analysis."""
    source = _get_opcode_gas_map_sources(fork_class)
    valid_fields = {f.name for f in fields(GasCosts)}
    helper_fields = _get_helper_method_fields(fork_class)
    opcode_fields = defaultdict(set)

    lines_iter = iter(source.split("\n"))
    opcode_re = re.compile(r"Opcodes\.(\w+)")
    field_re = re.compile(r"gas_costs\.(\w+)")
    helper_re = re.compile(r"cls\.(_with_\w+|_calculate_\w+)")

    current_opcode = None
    brace_depth = 0

    for line in lines_iter:
        opcode_match = opcode_re.search(line)
        if opcode_match:
            current_opcode = opcode_match.group(1)

        if current_opcode:
            for fm in field_re.finditer(line):
                fn = fm.group(1)
                if fn in valid_fields:
                    opcode_fields[current_opcode].add(fn)

            for hm in helper_re.finditer(line):
                hname = hm.group(1)
                if hname in helper_fields:
                    opcode_fields[current_opcode].update(helper_fields[hname])

        brace_depth += line.count("(") - line.count(")")
        if current_opcode and brace_depth <= 0 and "," in line:
            current_opcode = None
            brace_depth = 0

    return {k: sorted(v) for k, v in opcode_fields.items()}


def _format_grouped_output(fork_class: type[BaseFork]) -> str:
    """Format the full grouped-by-GasCosts-field output."""
    fork_name = fork_class.name()
    gas_costs = fork_class.gas_costs()
    opcode_map = fork_class.opcode_gas_map()
    tier_reverse = _build_tier_reverse_map(gas_costs)
    source_fields = _build_full_opcode_field_map(fork_class)

    field_to_opcodes = defaultdict(list)
    dynamic_opcodes = []
    constant_opcodes = []

    for opcode, cost in opcode_map.items():
        name = opcode._name_
        if callable(cost):
            gas_fields = source_fields.get(name, [])
            dynamic_opcodes.append((name, gas_fields))
        elif cost in tier_reverse:
            for field_name in tier_reverse[cost]:
                field_to_opcodes[field_name].append(name)
        else:
            constant_opcodes.append((name, cost))

    lines = [
        f"Opcode-to-GasCosts mapping for {fork_name}",
        "\u2550" * 50,
        "",
    ]

    for field_name in OPCODE_TIER_FIELDS:
        if field_name not in field_to_opcodes:
            continue
        value = getattr(gas_costs, field_name)
        opcodes = field_to_opcodes[field_name]
        lines.append(f"{field_name} ({value})")
        line = "  "
        for i, op in enumerate(opcodes):
            suffix = ", " if i < len(opcodes) - 1 else ""
            if len(line) + len(op) + len(suffix) > 72:
                lines.append(line.rstrip(", "))
                line = "  "
            line += op + suffix
        if line.strip():
            lines.append(line.rstrip(", "))
        lines.append("")

    if dynamic_opcodes:
        lines.append("Dynamic (multiple GasCosts fields)")
        for name, gas_fields in sorted(dynamic_opcodes):
            if gas_fields:
                fields_str = ", ".join(gas_fields)
                lines.append(f"  {name:<18}{fields_str}")
            else:
                lines.append(f"  {name:<18}(unknown)")
        lines.append("")

    if constant_opcodes:
        lines.append("Constants (no GasCosts field)")
        for name, value in sorted(constant_opcodes):
            lines.append(f"  {name:<18}{value}")
        lines.append("")

    return "\n".join(lines)


def _format_single_opcode(fork_class: type[BaseFork], opcode_name: str) -> str:
    """Format detailed output for a single opcode."""
    fork_name = fork_class.name()
    gas_costs = fork_class.gas_costs()
    opcode_map = fork_class.opcode_gas_map()
    tier_reverse = _build_tier_reverse_map(gas_costs)
    source_fields = _build_full_opcode_field_map(fork_class)

    target = None
    for opcode in opcode_map:
        if opcode._name_.upper() == opcode_name.upper():
            target = opcode
            break

    if target is None:
        available = sorted(op._name_ for op in opcode_map)
        raise click.ClickException(
            f"Unknown opcode: {opcode_name}. Available: {', '.join(available)}"
        )

    cost = opcode_map[target]
    name = target._name_
    lines = [
        f"{name} \u2014 {fork_name}",
        "\u2550" * 30,
    ]

    gas_fields = source_fields.get(name, [])
    repricing_fields: list[str] = []
    if callable(cost):
        repricing_fields = gas_fields
        lines.append("Type:     dynamic")
        if gas_fields:
            parts = []
            for gf in gas_fields:
                val = getattr(gas_costs, gf)
                parts.append(f"{gf} ({val})")
            lines.append(f"GasCosts: {', '.join(parts)}")
    elif cost in tier_reverse:
        repricing_fields = tier_reverse[cost]
        lines.append("Type:     static")
        parts = [f"{fn} ({cost})" for fn in repricing_fields]
        lines.append(f"GasCosts: {', '.join(parts)}")
    else:
        lines.append("Type:     constant")
        lines.append(f"Value:    {cost}")
        lines.append("")
        lines.append(
            "This opcode has a fixed cost not tied to a GasCosts field."
        )

    if repricing_fields:
        snippet = {fork_name: dict.fromkeys(repricing_fields, 0)}
        lines.append("")
        lines.append("To reprice in gas_repricing.json:")
        lines.extend(json.dumps(snippet, indent=2).splitlines())

    return "\n".join(lines)


@click.command(
    name="gas-map",
    short_help="Display opcode-to-GasCosts field mapping.",
)
@click.option(
    "--fork",
    "-f",
    "fork_name",
    default=None,
    help="Fork name (default: latest fork).",
)
@click.option(
    "--opcode",
    "-o",
    "opcode_name",
    default=None,
    help="Show detail for a single opcode.",
)
def gas_map(fork_name: str | None, opcode_name: str | None) -> None:
    """Display the mapping between EVM opcodes and GasCosts field names."""
    if fork_name:
        fork_class = _get_fork(fork_name)
    else:
        fork_class = _get_latest_fork()

    if opcode_name:
        output = _format_single_opcode(fork_class, opcode_name)
    else:
        output = _format_grouped_output(fork_class)

    click.echo(output)
