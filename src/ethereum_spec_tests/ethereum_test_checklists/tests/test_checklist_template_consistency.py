"""Test consistency between checklist template and EIPChecklist class."""

import re
from pathlib import Path
from typing import Set

import pytest

from ethereum_test_checklists.eip_checklist import EIPChecklist

TEMPLATE_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "docs"
    / "writing_tests"
    / "checklist_templates"
    / "eip_testing_checklist_template.md"
)


def extract_markdown_ids(markdown_content: str) -> Set[str]:
    """Extract all checklist IDs from markdown content."""
    # Pattern to match IDs in markdown tables (between backticks in ID column)
    pattern = r"\|\s*`([^`]+)`\s*\|"

    ids = set()
    for match in re.finditer(pattern, markdown_content):
        potential_id = match.group(1)
        # Filter out non-ID content - IDs should contain forward slashes
        if "/" in potential_id:
            ids.add(potential_id)

    return ids


def get_all_checklist_ids(obj, current_path="") -> Set[str]:
    """Recursively extract all checklist IDs from EIPChecklist and its children."""
    ids = set()

    # Iterate through all attributes of the object
    for attr_name in dir(obj):
        # Skip private attributes and methods
        if attr_name.startswith("_"):
            continue

        attr = getattr(obj, attr_name)

        # Check if this is a class with a _path attribute (our checklist items)
        if isinstance(attr, type) and hasattr(attr, "_path"):
            # Get the full path for this item
            item_path = str(attr)
            if item_path:  # Only add non-empty paths
                ids.add(item_path)

            # Recursively get IDs from nested classes
            nested_ids = get_all_checklist_ids(attr)
            ids.update(nested_ids)

    return ids


def test_checklist_template_consistency():
    """Test that all IDs in markdown template match EIPChecklist class exactly."""
    # Read the markdown template
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    # Extract IDs from both sources
    markdown_ids = extract_markdown_ids(markdown_content)
    checklist_ids = get_all_checklist_ids(EIPChecklist)

    # Find differences
    missing_in_checklist = markdown_ids - checklist_ids
    missing_in_markdown = checklist_ids - markdown_ids

    # Create detailed error messages
    errors = []

    if missing_in_checklist:
        errors.append(
            f"IDs found in markdown template but missing in EIPChecklist class "
            f"({len(missing_in_checklist)} items):\n"
            + "\n".join(f"  - `{id_}`" for id_ in sorted(missing_in_checklist))
        )

    if missing_in_markdown:
        for id_ in missing_in_markdown:
            if any(item.startswith(id_ + "/") for item in checklist_ids):
                continue

            errors.append(f"ID `{id_}` not found in markdown template")

    if errors:
        error_message = f"\nTotal markdown IDs: {len(markdown_ids)}\n"
        error_message += f"Total checklist IDs: {len(checklist_ids)}\n\n"
        error_message += "\n\n".join(errors)
        pytest.fail(error_message)


def test_checklist_template_exists():
    """Test that the checklist template file exists."""
    assert TEMPLATE_PATH.exists(), f"Checklist template not found at {TEMPLATE_PATH}"


def test_eip_checklist_class_structure():
    """Test that the EIPChecklist class has expected structure."""
    assert hasattr(EIPChecklist, "General"), "EIPChecklist should have General class"
    assert hasattr(EIPChecklist, "Opcode"), "EIPChecklist should have Opcode class"
    assert hasattr(EIPChecklist, "Precompile"), "EIPChecklist should have Precompile class"

    # Test that the metaclass is working correctly
    assert str(EIPChecklist.General.CodeCoverage.Eels) == "general/code_coverage/eels"
    assert (
        str(EIPChecklist.Opcode.Test.MemExp.ZeroBytesZeroOffset)
        == "opcode/test/mem_exp/zero_bytes_zero_offset"
    )


def test_id_extraction_functions():
    """Test that our ID extraction functions work correctly."""
    # Test markdown extraction
    sample_markdown = """
    | ID | Description | Status | Tests |
    | `test/example/id` | Test description | | |
    | `another/test/path` | Another test | | |
    """

    ids = extract_markdown_ids(sample_markdown)
    assert "test/example/id" in ids
    assert "another/test/path" in ids

    # Test checklist extraction
    checklist_ids = get_all_checklist_ids(EIPChecklist)
    assert len(checklist_ids) > 0
    assert "general/code_coverage/eels" in checklist_ids


def test_eip_checklist_decorator_usage():
    """Test EIPChecklist items work correctly as decorators both with and without parentheses."""

    # Test decorator with parentheses
    @EIPChecklist.Opcode.Test.StackComplexOperations()
    def test_function_with_parens():
        pass

    # Verify the marker was applied
    markers = list(test_function_with_parens.pytestmark)
    assert len(markers) >= 1
    eip_markers = [m for m in markers if m.name == "eip_checklist"]
    assert len(eip_markers) == 1
    assert eip_markers[0].args == ("opcode/test/stack_complex_operations",)

    # Test decorator without parentheses (direct usage - this is the key fix for issue #1)
    @EIPChecklist.Opcode.Test.StackOverflow
    def test_function_no_parens():
        pass

    # Verify the marker was applied
    markers = list(test_function_no_parens.pytestmark)
    eip_markers = [m for m in markers if m.name == "eip_checklist"]
    assert len(eip_markers) == 1
    assert eip_markers[0].args == ("opcode/test/stack_overflow",)


def test_eip_checklist_pytest_param_usage():
    """Test that EIPChecklist works correctly in pytest.param marks."""
    # Test that parentheses form works in pytest.param
    param_with_parens = pytest.param(
        "test_value", marks=EIPChecklist.Opcode.Test.GasUsage.Normal(), id="gas_test"
    )

    # Verify the parameter was created successfully
    assert param_with_parens.values == ("test_value",)
    assert param_with_parens.id == "gas_test"
    assert len(param_with_parens.marks) == 1
    assert param_with_parens.marks[0].name == "eip_checklist"
    assert param_with_parens.marks[0].args == ("opcode/test/gas_usage/normal",)

    # Test that multiple marks work
    param_multiple_marks = pytest.param(
        "test_value",
        marks=[EIPChecklist.Opcode.Test.StackComplexOperations(), pytest.mark.slow],
        id="complex_test",
    )

    # Verify multiple marks
    assert len(param_multiple_marks.marks) == 2
    eip_mark = next(m for m in param_multiple_marks.marks if m.name == "eip_checklist")
    assert eip_mark.args == ("opcode/test/stack_complex_operations",)

    # Test that non-parentheses form fails gracefully with pytest.param
    # (This documents the expected behavior - parentheses are required)
    with pytest.raises((TypeError, AssertionError)):
        pytest.param(
            "test_value",
            marks=EIPChecklist.Opcode.Test.StackOverflow,  # Without () should fail
            id="should_fail",
        )
