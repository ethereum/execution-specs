"""
Pytest plugin for generating EIP test completion checklists.

This plugin collects checklist markers from tests and generates a filled checklist
for each EIP based on the template at
docs/writing_tests/checklist_templates/eip_testing_checklist_template.md
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest

from .gen_test_doc.page_props import EipChecklistPageProps

logger = logging.getLogger("mkdocs")


def pytest_addoption(parser: pytest.Parser):
    """Add command-line options for checklist generation."""
    group = parser.getgroup("checklist", "EIP checklist generation options")
    group.addoption(
        "--checklist-output",
        action="store",
        dest="checklist_output",
        type=Path,
        default=Path("./checklists"),
        help="Directory to output the generated checklists",
    )
    group.addoption(
        "--checklist-eip",
        action="append",
        dest="checklist_eips",
        type=int,
        default=[],
        help="Generate checklist only for specific EIP(s)",
    )
    group.addoption(
        "--checklist-doc-gen",
        action="store_true",
        dest="checklist_doc_gen",
        default=False,
        help="Generate checklists for documentation (uses mkdocs_gen_files)",
    )


TITLE_LINE = "# EIP Execution Layer Testing Checklist Template"
PERCENTAGE_LINE = "| TOTAL_CHECKLIST_ITEMS | COVERED_CHECKLIST_ITEMS | PERCENTAGE |"
TEMPLATE_PATH = (
    Path(__file__).parents[3]
    / "docs"
    / "writing_tests"
    / "checklist_templates"
    / "eip_testing_checklist_template.md"
)
TEMPLATE_CONTENT = TEMPLATE_PATH.read_text()
EXTERNAL_COVERAGE_FILE_NAME = "eip_checklist_external_coverage.txt"
NOT_APPLICABLE_FILE_NAME = "eip_checklist_not_applicable.txt"


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):  # noqa: D103
    config.pluginmanager.register(EIPChecklistCollector(), "eip-checklist-collector")


@dataclass(kw_only=True)
class EIPItem:
    """Represents an EIP checklist item."""

    id: str
    line_number: int
    description: str
    tests: Set[str]
    not_applicable_reason: str = ""
    external_coverage_reason: str = ""

    @classmethod
    def from_checklist_line(cls, *, line: str, line_number: int) -> "EIPItem | None":
        """Create an EIP item from a checklist line."""
        match = re.match(r"\|\s*`([^`]+)`\s*\|\s*([^|]+)\s*\|", line)
        if not match:
            return None
        return cls(
            id=match.group(1),
            line_number=line_number,
            description=match.group(2),
            tests=set(),
        )

    @property
    def covered(self) -> bool:
        """Return True if the item is covered by at least one test."""
        return len(self.tests) > 0 or self.external_coverage

    @property
    def external_coverage(self) -> bool:
        """Return True if the item is covered by an external test/procedure."""
        return self.external_coverage_reason != ""

    @property
    def not_applicable(self) -> bool:
        """Return True if the item is not applicable."""
        return self.not_applicable_reason != ""

    def __str__(self) -> str:
        """Return a string representation of the EIP item."""
        status = " "
        tests = ""
        if self.external_coverage:
            status = "✅"
            tests = self.external_coverage_reason
        elif self.covered:
            status = "✅"
            tests = ", ".join(sorted(self.tests))
        elif self.not_applicable:
            status = "N/A"
            tests = self.not_applicable_reason

        return f"| `{self.id}` | {self.description} | {status} | {tests} |"


TEMPLATE_ITEMS: Dict[str, EIPItem] = {}
# Parse the template to extract checklist item IDs and descriptions
for i, line in enumerate(TEMPLATE_CONTENT.splitlines()):
    # Match lines that contain checklist items with IDs in backticks
    if item := EIPItem.from_checklist_line(line=line, line_number=i + 1):
        TEMPLATE_ITEMS[item.id] = item

ALL_IDS = set(TEMPLATE_ITEMS.keys())


def resolve_id(item_id: str) -> Set[str]:
    """Resolve an item ID to a set of checklist IDs."""
    covered_ids = {checklist_id for checklist_id in ALL_IDS if checklist_id.startswith(item_id)}
    return covered_ids


@dataclass(kw_only=True)
class EIP:
    """Represents an EIP and its checklist."""

    number: int
    items: Dict[str, EIPItem] = field(default_factory=TEMPLATE_ITEMS.copy)
    path: Path | None = None

    def add_covered_test(self, checklist_id: str, node_id: str) -> None:
        """Add a covered test to the EIP."""
        self.items[checklist_id].tests.add(node_id)

    @property
    def covered_items(self) -> int:
        """Return the number of covered items."""
        return sum(1 for item in self.items.values() if item.covered)

    @property
    def total_items(self) -> int:
        """Return the number of total items."""
        return sum(1 for item in self.items.values() if not item.not_applicable)

    @property
    def percentage(self) -> float:
        """Return the percentage of covered items."""
        return self.covered_items / self.total_items * 100 if self.total_items else 0

    @property
    def completness_emoji(self) -> str:
        """Return the completness emoji."""
        return "🟢" if self.percentage == 100 else "🟡" if self.percentage > 50 else "🔴"

    def mark_not_applicable(self):
        """Read the not-applicable items from the EIP."""
        if self.path is None:
            return
        not_applicable_path = self.path / NOT_APPLICABLE_FILE_NAME
        if not not_applicable_path.exists():
            return
        with not_applicable_path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                assert "=" in line
                item_id, reason = line.split("=", 1)
                item_id = item_id.strip()
                reason = reason.strip()
                assert reason, f"Reason is empty for {line}"
                assert item_id, f"Item ID is empty for {line}"
                ids = resolve_id(item_id)
                if not ids:
                    logger.warning(
                        f"Item ID {item_id} not found in the checklist template, "
                        f"for EIP {self.number}"
                    )
                    continue
                for id_covered in ids:
                    self.items[id_covered].not_applicable_reason = reason

    def mark_external_coverage(self):
        """Read the externally covered items from the EIP."""
        if self.path is None:
            return
        external_coverage_path = self.path / EXTERNAL_COVERAGE_FILE_NAME
        if not external_coverage_path.exists():
            return
        with external_coverage_path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                assert "=" in line
                item_id, reason = line.split("=", 1)
                item_id = item_id.strip()
                reason = reason.strip()
                assert item_id, f"Item ID is empty for {line}"
                assert reason, f"Reason is empty for {line}"
                ids = resolve_id(item_id)
                if not ids:
                    logger.warning(
                        f"Item ID {item_id} not found in the checklist template, "
                        f"for EIP {self.number}"
                    )
                    continue
                for id_covered in ids:
                    self.items[id_covered].external_coverage_reason = reason

    def generate_filled_checklist_lines(self) -> List[str]:
        """Generate the filled checklist lines for a specific EIP."""
        # Create a copy of the template content
        lines = TEMPLATE_CONTENT.splitlines()

        self.mark_not_applicable()
        self.mark_external_coverage()

        for checklist_item in self.items.values():
            # Find the line with this item ID
            lines[checklist_item.line_number - 1] = str(checklist_item)

        lines[lines.index(PERCENTAGE_LINE)] = (
            f"| {self.total_items} | {self.covered_items} | {self.completness_emoji} "
            f"{self.percentage:.2f}% |"
        )

        # Replace the title line with the EIP number
        lines[lines.index(TITLE_LINE)] = f"# EIP-{self.number} Test Checklist"

        return lines

    def generate_filled_checklist(self, output_dir: Path) -> Path:
        """Generate a filled checklist for a specific EIP."""
        lines = self.generate_filled_checklist_lines()

        output_dir = output_dir / f"eip{self.number}_checklist.md"

        # Write the filled checklist
        output_dir.parent.mkdir(exist_ok=True, parents=True)
        output_dir.write_text("\n".join(lines))

        return output_dir


class EIPChecklistCollector:
    """Collects and manages EIP checklist items from test markers."""

    def __init__(self: "EIPChecklistCollector"):
        """Initialize the EIP checklist collector."""
        self.eips: Dict[int, EIP] = {}

    def extract_eip_from_path(self, test_path: Path) -> Tuple[int | None, Path | None]:
        """Extract EIP number from test file path."""
        # Look for patterns like eip1234_ or eip1234/ in the path
        for part_idx, part in enumerate(test_path.parts):
            match = re.match(r"eip(\d+)", part)
            if match:
                eip = int(match.group(1))
                eip_path = test_path.parents[len(test_path.parents) - part_idx - 2]
                return eip, eip_path
        return None, None

    def get_eip_from_item(self, item: pytest.Item) -> EIP | None:
        """Get the EIP for a test item."""
        test_path = Path(item.location[0])
        for part_idx, part in enumerate(test_path.parts):
            match = re.match(r"eip(\d+)", part)
            if match:
                eip = int(match.group(1))
                if eip not in self.eips:
                    self.eips[eip] = EIP(
                        number=eip,
                        path=test_path.parents[len(test_path.parents) - part_idx - 2],
                    )
                else:
                    if self.eips[eip].path is None:
                        self.eips[eip].path = test_path.parents[
                            len(test_path.parents) - part_idx - 2
                        ]
                return self.eips[eip]
        return None

    def get_eip(self, eip: int) -> EIP:
        """Get the EIP for a given EIP number."""
        if eip not in self.eips:
            self.eips[eip] = EIP(number=eip, path=None)
        return self.eips[eip]

    def collect_from_item(self, item: pytest.Item, primary_eip: EIP | None) -> None:
        """Collect checklist markers from a test item."""
        for marker in item.iter_markers("eip_checklist"):
            if not marker.args:
                pytest.fail(
                    f"eip_checklist marker on {item.nodeid} must have at least one argument "
                    "(item_id)"
                )
            additional_eips = marker.kwargs.get("eip", [])
            if not isinstance(additional_eips, list):
                additional_eips = [additional_eips]

            eips: List[EIP] = [primary_eip] if primary_eip else []

            if additional_eips:
                if any(not isinstance(eip, int) for eip in additional_eips):
                    pytest.fail(
                        "EIP numbers must be integers. Found non-integer EIPs in "
                        f"{item.nodeid}: {additional_eips}"
                    )
                eips += [self.get_eip(eip) for eip in additional_eips]

            for item_id in marker.args:
                covered_ids = resolve_id(item_id.strip())
                if not covered_ids:
                    logger.warning(
                        f"Item ID {item_id} not found in the checklist template, "
                        f"for test {item.nodeid}"
                    )
                    continue
                for id_covered in covered_ids:
                    for eip in eips:
                        eip.add_covered_test(id_covered, item.nodeid)

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtestloop(self, session):
        """Skip test execution, only generate checklists."""
        session.testscollected = 0
        return True

    def pytest_collection_modifyitems(self, config: pytest.Config, items: List[pytest.Item]):
        """Collect checklist markers during test collection."""
        for item in items:
            eip = self.get_eip_from_item(item)
            if item.get_closest_marker("derived_test") or item.get_closest_marker("skip"):
                continue
            self.collect_from_item(item, eip)

        # Check which mode we are in
        checklist_doc_gen = config.getoption("checklist_doc_gen", False)
        checklist_output = config.getoption("checklist_output", Path("checklists"))
        checklist_eips = config.getoption("checklist_eips", [])

        checklist_props = {}
        # Generate a checklist for each EIP
        for eip in self.eips.values():
            # Skip if specific EIPs were requested and this isn't one of them
            if checklist_eips and eip.number not in checklist_eips:
                continue

            if checklist_doc_gen:
                assert eip.path is not None
                checklist_path = eip.path / "checklist.md"
                checklist_props[checklist_path] = EipChecklistPageProps(
                    title=f"EIP-{eip.number} Test Checklist",
                    source_code_url="",
                    target_or_valid_fork="mainnet",
                    path=checklist_path,
                    pytest_node_id="",
                    package_name="checklist",
                    eip=eip.number,
                    lines=eip.generate_filled_checklist_lines(),
                )
            else:
                checklist_path = eip.generate_filled_checklist(checklist_output)
                print(f"\nGenerated EIP-{eip.number} checklist: {checklist_path}")

        if checklist_doc_gen:
            config.checklist_props = checklist_props  # type: ignore
