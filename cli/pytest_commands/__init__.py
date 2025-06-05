"""
CLI entry points for the main pytest-based commands provided by
execution-spec-tests.

These can be directly accessed in a prompt if the user has directly installed
the package via:

```
python -m venv venv
source venv/bin/activate
pip install -e .
# or
pip install -e .[docs,lint,test]
```

Then, the entry points can be executed via:

```
fill --help
# for example, or
consume engine
# or
checklist --help
```

They can also be executed (and debugged) directly in an interactive python
shell:

```
from src.cli.pytest_commands.fill import fill
from click.testing import CliRunner

runner = CliRunner()
result = runner.invoke(fill, ["--help"])
print(result.output)
```
"""
