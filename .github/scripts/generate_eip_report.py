"""
Generate a markdown report of outdated EIP references from the EIP version
checker output.
"""

import os
import re
import sys
import textwrap
from string import Template
from typing import List, Tuple

# Report template using textwrap.dedent for clean multiline strings
REPORT_TEMPLATE = Template(
    textwrap.dedent("""\
    # EIP Version Check Report

    This automated check has detected that some EIP references in test files are outdated. This means that the EIPs have been updated in the [ethereum/EIPs](https://github.com/ethereum/EIPs) repository since our tests were last updated.

    ## Outdated EIP References

    ### Summary Table

    | File | EIP Link | Referenced Version | Latest Version |
    | ---- | -------- | ------------------ | -------------- |
    $summary_table

    ### Verbatim Failures

    ```
    $fail_messages
    ```

    ### Verbatim Errors

    ```
    $error_messages
    ```

    ## Action Required

    1. Please verify whether the affected tests need updating based on changes in the EIP spec.
    2. Update the `REFERENCE_SPEC_VERSION` in each file with the latest version shown above.
    3. For detailed instructions, see the [reference specification documentation](https://eest.ethereum.org/main/writing_tests/reference_specification/).

    ## Workflow Information

    For more details, see the [workflow run](https://github.com/ethereum/execution-spec-tests/actions/runs/$run_id).
""")  # noqa: E501
)


def extract_failures(output: str) -> List[Tuple[str, str, str, str, str, str]]:
    """Extract failure information from the output using regex."""
    failures = []

    for line in output.split("\n"):
        if not line.startswith("FAILED"):
            continue

        # Extract test file path
        file_match = re.search(r"FAILED (tests/[^:]+\.py)", line)
        if not file_match:
            continue
        file_path = file_match.group(1)

        # Extract EIP number
        eip_match = re.search(r"eip(\d+)", file_path, re.IGNORECASE)
        eip_num = f"EIP-{eip_match.group(1)}" if eip_match else "Unknown"

        # Extract full path
        full_path_match = re.search(r"from '([^']+)'", line)
        full_path = full_path_match.group(1) if full_path_match else "Unknown"

        # Extract EIP link
        eip_link_match = re.search(r"Spec: (https://[^ ]+)\.", line)
        eip_link = eip_link_match.group(1) if eip_link_match else ""
        eip_link = eip_link.replace("blob/", "commits/") if eip_link else ""

        # Extract versions
        ref_version_match = re.search(r"Referenced version: ([a-f0-9]+)", line)
        ref_version = ref_version_match.group(1) if ref_version_match else "Unknown"

        latest_version_match = re.search(r"Latest version: ([a-f0-9]+)", line)
        latest_version = latest_version_match.group(1) if latest_version_match else "Unknown"

        failures.append((file_path, eip_num, full_path, eip_link, ref_version, latest_version))

    return failures


def generate_summary_table(failures: List[Tuple[str, str, str, str, str, str]]) -> str:
    """Generate a markdown summary table from the failures."""
    rows = []
    for file_path, eip_num, _, eip_link, ref_version, latest_version in failures:
        rows.append(
            f"| `{file_path}` | [{eip_num}]({eip_link}) | `{ref_version}` | `{latest_version}` |"
        )
    return "\n".join(rows)


def main() -> None:
    """Generate the report."""
    if len(sys.argv) < 2:
        print("Usage: uv run python generate_eip_report.py <input_file> [output_file]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "./reports/outdated_eips.md"

    try:
        with open(input_file, "r") as f:
            output = f.read()
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)

    failures = extract_failures(output)

    fail_messages = "\n".join(line for line in output.split("\n") if line.startswith("FAILED"))
    if not fail_messages:
        fail_messages = (
            "No test failures were found in the pytest output: No lines start with 'FAILED'."
        )

    error_messages = "\n".join(line for line in output.split("\n") if line.startswith("ERROR"))
    if not error_messages:
        error_messages = (
            "No test errors were found in the pytest output: No lines start with 'ERROR'."
        )

    report_content = REPORT_TEMPLATE.substitute(
        summary_table=generate_summary_table(failures),
        fail_messages=fail_messages,
        error_messages=error_messages,
        run_id=os.environ.get("GITHUB_RUN_ID", ""),
    )

    try:
        with open(output_file, "w") as report:
            report.write(report_content)
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

    print(f"Report generated successfully: {output_file}")
    print(f"Found {len(failures)} outdated EIP references")


if __name__ == "__main__":
    main()
