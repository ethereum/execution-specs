"""
Put the JSON schema of each client runner output model into the runner page.

The page marks each place with `<!-- schema: <model> -->`, and the schema is
generated from the model in `execution_testing.client_clis.runner_interface`,
so the page and the models cannot drift apart.
"""

import json
import re
import textwrap

import mkdocs_gen_files
from execution_testing.client_clis import runner_interface

PAGE = "running_tests/consume/client_runners.md"
MARKER = re.compile(r"^<!-- schema: (\w+) -->$", re.MULTILINE)


def schema_block(match: re.Match[str]) -> str:
    """Render the named model's schema as a collapsed JSON block."""
    model = getattr(runner_interface, match.group(1))
    schema = json.dumps(model.model_json_schema(by_alias=True), indent=2)
    code = f"```json\n{schema}\n```"
    return f'??? info "JSON schema"\n\n{textwrap.indent(code, "    ")}'


with mkdocs_gen_files.open(PAGE, "r") as page:
    content = page.read()
rendered, count = MARKER.subn(schema_block, content)
if count == 0:
    raise ValueError(f"no schema markers in {PAGE}")
with mkdocs_gen_files.open(PAGE, "w") as page:
    page.write(rendered)
