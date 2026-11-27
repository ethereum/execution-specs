"""
Write the JSON schemas of the client runner output models to a docs page.

The schemas come from the models in
`execution_testing.client_clis.runner_interface`, and the runner page
(`running_tests/consume/client_runners.md`) links to each one, so the page
and the models cannot drift apart.
"""

import json
import logging
from pathlib import Path
from typing import List, Tuple, Type

from execution_testing.client_clis.runner_interface import (
    BalExecution,
    BalFallback,
    BuildRunnerResults,
    RunnerResults,
)
from pydantic import BaseModel

logger = logging.getLogger("gen_docs")

PAGE = Path("running_tests/consume/client_runner_schemas.md")
SECTIONS: List[Tuple[str, Type[BaseModel]]] = [
    ("Results", RunnerResults),
    ("Build test results", BuildRunnerResults),
    ("BAL execution lines", BalExecution),
    ("BAL fallback lines", BalFallback),
]


def generate_runner_interface_schemas(docs_dir: Path) -> None:
    """Write one section per runner output model with its JSON schema."""
    parts = [
        "# Client Runner Output Schemas",
        "JSON schemas of the output described in "
        "[Client Test Runners](client_runners.md), generated from the "
        "models in `execution_testing.client_clis.runner_interface`.",
    ]
    for title, model in SECTIONS:
        schema = json.dumps(model.model_json_schema(by_alias=True), indent=2)
        parts += [f"## {title}", f"```json\n{schema}\n```"]
    page = docs_dir / PAGE
    page.parent.mkdir(parents=True, exist_ok=True)
    page.write_text("\n\n".join(parts) + "\n")
    logger.info(f"Wrote the runner output schemas to {page}.")
