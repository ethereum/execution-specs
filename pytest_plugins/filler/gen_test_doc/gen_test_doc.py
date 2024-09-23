"""
A pytest plugin that generates test case documentation for use in mkdocs.

It generates the top-level "Test Case Reference" section in EEST's mkdocs
site.

Note:
-----
- No output directory is specified for the generated output; file IO occurs
    via the `mkdocs-gen-files` plugin. `mkdocs serve` writes intermediate files
    to our local `docs/` directory and then copies it to the site directory.
    We modify `docs/navigation.md` and write all other output underneath
    `docs/tests`. If mkdocs is interrupted, these intermediate artifacts are
    left in `docs/`.

Usage:
------

!!! note "Ensuring a clean build"

    In case mkdocs has polluted the `docs/` directory with intermediate files, run:

    ```console
    git restore docs/navigation.md  # Careful if you have local modifications!
    rm -rf docs/tests docs/docs site
    ```

To test doc generation, run the plugin without mkdocs:

```console
uv run fill -p pytest_plugins.filler.gen_test_doc.gen_test_doc --gen-docs --fork=<fork> tests
```

Or to build and view the site:

```console
uv run mkdocs serve
```
"""

import glob
import logging
import sys
import textwrap
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple, cast

import mkdocs_gen_files  # type: ignore
import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from pytest import Item

from ethereum_test_forks import get_forks
from ethereum_test_specs import SPEC_TYPES
from ethereum_test_tools.utility.versioning import (
    generate_github_url,
    get_current_commit_hash_or_tag,
)

from .page_props import (
    DirectoryPageProps,
    FunctionPageProps,
    FunctionPagePropsLookup,
    MarkdownPageProps,
    ModulePageProps,
    ModulePagePropsLookup,
    PageProps,
    PagePropsLookup,
    TestCase,
    TestFunction,
    sanitize_string_title,
)

logger = logging.getLogger("mkdocs")

docstring_test_function_history: Dict[str, str] = {}


def pytest_addoption(parser):  # noqa: D103
    gen_docs = parser.getgroup(
        "gen_docs", "Arguments related to generating test case documentation"
    )
    gen_docs.addoption(
        "--gen-docs",
        action="store_true",
        dest="generate_docs",
        default=False,
        help="Generate documentation for all collected tests for use in for mkdocs",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):  # noqa: D103
    if config.getoption("--gen-docs"):
        config.option.disable_html = True
        config.pluginmanager.register(TestDocsGenerator(config), "test-case-doc-generator")


def get_test_function_id(item: Item) -> str:
    """
    Get the test function's ID from the item.
    """
    return item.nodeid.split("[")[0]


def get_test_function_name(item: Item) -> str:
    """
    Get the test function's name from the item.
    """
    return item.name.split("[")[0]


def get_test_case_id(item: Item) -> str:
    """
    Get the test case's ID from the item.
    """
    return item.nodeid.split("[")[-1].rstrip("]")


def get_test_function_import_path(item: pytest.Item) -> str:
    """
    Retrieve the fully qualified import path for an item's test function.

    This is used in jinja2 templates to get the test function, respectively
    the test function's class, documentation with mkdocstrings.
    """
    item = cast(pytest.Function, item)  # help mypy infer type
    module_name = item.module.__name__
    if hasattr(item.obj, "__self__"):
        # it's a method bound to a class
        test_class = item.obj.__self__.__class__.__name__
        test_function = item.obj.__name__
        full_path = f"{module_name}.{test_class}"
    else:
        # it's a standalone function, no class
        test_function = item.obj.__name__
        full_path = f"{module_name}.{test_function}"
    return full_path


def get_import_path(path: Path) -> str:
    """
    Get the import path for a given path.

    - For modules, strip the file extension.
    - For directories (i.e., packages such as `tests.berlin`), `with_suffix()` is ignored.

    To do:
    ------

    - This should be combined with `get_test_function_import_path`.
    """
    return str(path.with_suffix("")).replace("/", ".")


def create_github_issue_url(title: str) -> str:
    """
    Create a GitHub issue URL for the given title.
    """
    url_base = "https://github.com/ethereum/execution-spec-tests/issues/new?"
    title = title.replace(" ", "%20")
    labels = "scope:docs,type:bug"
    return f"{url_base}title={title}&labels={labels}"


def get_docstring_one_liner(item: pytest.Item) -> str:
    """
    Extracts either the first 100 characters or the first line of the docstring
    from the function associated with the given pytest.Item.
    """
    item = cast(pytest.Function, item)  # help mypy infer type
    func_obj = item.obj
    docstring = func_obj.__doc__
    test_function_name = get_test_function_name(item)

    if not docstring:
        github_issue_url = create_github_issue_url(
            f"docs(bug): No docstring available for `{test_function_name}`"
        )
        logger.warning(f"No docstring available for `{test_function_name}`.")
        return f"[📖🐛 No docstring available]({github_issue_url})"
    docstring = docstring.strip()
    test_function_id = get_test_function_id(item)
    if (
        docstring in docstring_test_function_history
        and docstring_test_function_history[docstring] != test_function_id
    ):
        logger.info(
            f"Duplicate docstring for {test_function_id}: "
            f"{docstring_test_function_history[docstring]} and {test_function_id}"
        )
    else:
        docstring_test_function_history[docstring] = test_function_id
    lines = docstring.splitlines()

    bad_oneliner_issue_url = create_github_issue_url(
        f"docs(bug): Bad docstring oneliner for `{test_function_name}`"
    )
    report_bad_oneliner_link = f"([📖🐛?]({bad_oneliner_issue_url}))"
    if lines:
        first_line = lines[0].strip()
        if len(first_line) <= 100:
            return (
                first_line
                if not first_line.endswith(":")
                else first_line + report_bad_oneliner_link
            )
        else:
            return first_line[:100] + f"... {report_bad_oneliner_link}"
    else:
        return docstring[:100] + f"... {report_bad_oneliner_link}"


def get_test_function_test_type(item: pytest.Item) -> str:
    """
    Get the test type for the test function based on its fixtures.
    """
    test_types: List[str] = [spec_type.pytest_parameter_name() for spec_type in SPEC_TYPES]
    item = cast(pytest.Function, item)  # help mypy infer type
    fixture_names = item.fixturenames
    for test_type in test_types:
        if test_type in fixture_names:
            return test_type
    assert 0
    logger.warning(f"Could not determine the test function type for {item.nodeid}")
    return f"unknown ([📖🐛]({create_github_issue_url('docs(bug): unknown test function type')}))"


class TestDocsGenerator:
    """
    Pytest plugin class for generating test case documentation.
    """

    def __init__(self, config) -> None:
        self.config = config
        self._setup_logger()
        self.jinja2_env = Environment(
            loader=FileSystemLoader("docs/templates"),
            trim_blocks=True,
            undefined=StrictUndefined,
        )
        self.source_dir = Path("tests")
        self.ref = get_current_commit_hash_or_tag()
        self.top_level_nav_entry = "Test Case Reference"
        self.skip_params = ["fork"] + [
            spec_type.pytest_parameter_name() for spec_type in SPEC_TYPES
        ]
        # intermediate collected pages and their properties
        self.function_page_props: FunctionPagePropsLookup = {}
        self.module_page_props: ModulePagePropsLookup = {}
        # the complete set of pages and their properties
        self.page_props: PagePropsLookup = {}

    @pytest.hookimpl(hookwrapper=True, trylast=True)
    def pytest_collection_modifyitems(self, session, config, items):
        """
        Generate html doc for each test item that pytest has collected.
        """
        yield

        self.add_global_page_props_to_env()

        functions = defaultdict(list)
        for item in items:  # group test case by test function
            functions[get_test_function_id(item)].append(item)

        # the heavy work
        self.create_function_page_props(functions)
        self.create_module_page_props()
        # add the pages to the page_props dict
        self.page_props = {**self.function_page_props, **self.module_page_props}
        # this adds pages for the intermediate directory structure (tests, tests/berlin)
        self.add_directory_page_props()
        # add other interesting pages
        self.add_spec_page_props()
        self.add_markdown_page_props()
        # write pages and navigation menu
        self.write_pages()
        self.update_mkdocs_nav()

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtestloop(self, session):
        """
        Skip test execution, only generate docs.
        """
        session.testscollected = 0
        return True

    def pytest_terminal_summary(self, terminalreporter, exitstatus, config):
        """
        Add a summary line for the docs.
        """
        terminalreporter.write_sep("=", f"{len(self.page_props)} doc pages generated", bold=True)

    def _setup_logger(self):
        """
        Configures the mkdocs logger and adds a StreamHandler if outside mkdocs.

        We use the mkdocs logger to report warnings if conditions are invalid -
        this will inform the user and fail the build with `mkdocs build --strict`.
        """
        if not logger.hasHandlers() or logger.level == logging.NOTSET:
            stream_handler = logging.StreamHandler(sys.stdout)
            stream_handler.setLevel(logging.INFO)
            logger.addHandler(stream_handler)
            logger.setLevel(logging.INFO)

    def add_global_page_props_to_env(self):
        """
        Populate global page properties used in j2 templates.
        """
        global_page_props = dict(
            deployed_forks=[fork.name().lower() for fork in get_forks() if fork.is_deployed()],
            short_git_ref=get_current_commit_hash_or_tag(shorten_hash=True),
            test_function_parameter_table_skipped_parameters=", ".join(
                f"`{p}`" for p in self.skip_params
            ),
        )

        self.jinja2_env.globals.update(global_page_props)

    def create_function_page_props(self, test_functions: Dict["str", List[Item]]) -> None:
        """
        Traverse all test items and create a lookup of doc pages & required props

        To do: Needs refactor.
        """
        for function_id, function_items in test_functions.items():
            assert all(isinstance(item, pytest.Function) for item in function_items)
            items = cast(List[pytest.Function], function_items)  # help mypy infer type
            # extract parametrized test cases for each test function
            test_cases = []
            if getattr(items[0], "callspec", None):
                for item in items:
                    param_set = item.callspec.params
                    # Filter out unwanted parameters from the param set
                    keys = [key for key in param_set.keys() if key not in self.skip_params]
                    values = [param_set[key] for key in keys]
                    values = [
                        # " ".join(f"<code>{byte:02x}</code>" for byte in value)  # noqa: SC100
                        " ".join(
                            f"<code>{chunk}</code>" for chunk in textwrap.wrap(value.hex(), 32)
                        )
                        if isinstance(value, bytes)
                        else str(value)
                        for value in values
                    ]

                    # Create the filtered test ID
                    original_test_id = item.nodeid.split("[")[-1].rstrip("]")
                    filtered_test_id_parts = []
                    for part in original_test_id.split("-"):
                        param_name = part.split("_")[0] if "_" in part else None
                        if (param_name not in self.skip_params) and (part not in self.skip_params):
                            filtered_test_id_parts.append(part)
                    filtered_test_id = "-".join(filtered_test_id_parts).strip("-")

                    if filtered_test_id_parts:
                        test_cases.append(
                            TestCase(id=filtered_test_id, params=dict(zip(keys, values)))
                        )

            module_relative_path = Path(items[0].module.__file__).relative_to(Path.cwd())
            source_url = generate_github_url(
                module_relative_path,
                branch_or_commit_or_tag=self.ref,
                line_number=items[0].function.__code__.co_firstlineno,
            )
            valid_from_marker = items[0].get_closest_marker("valid_from")
            if not valid_from_marker:
                valid_from_fork = "Frontier"
            else:
                # NOTE: The EOF tests cases contain two fork names in their valid_from marker,
                # separated by a comma. Take the last.
                valid_from_fork = valid_from_marker.args[0].split(",")[-1]

            self.function_page_props[function_id] = FunctionPageProps(
                title=get_test_function_name(items[0]),
                source_code_url=source_url,
                valid_from_fork=valid_from_fork,
                path=module_relative_path,
                pytest_node_id=function_id,
                package_name=get_test_function_import_path(items[0]),
                cases=test_cases,
                test_type=get_test_function_test_type(items[0]),
                docstring_one_liner=get_docstring_one_liner(items[0]),
                html_static_page_target=f"./{get_test_function_name(items[0])}.html",
            )

    def create_module_page_props(self) -> None:
        """
        Discover the test module doc pages and extract their properties.
        """
        for function_id, function_page in self.function_page_props.items():
            if str(function_page.path) not in self.module_page_props:
                module_path = function_page.path
                self.module_page_props[str(function_page.path)] = ModulePageProps(
                    title=sanitize_string_title(function_page.path.stem),
                    source_code_url=function_page.source_code_url,
                    valid_from_fork=function_page.valid_from_fork,
                    path=module_path,
                    pytest_node_id=str(module_path),
                    package_name=get_import_path(module_path),
                    test_functions=[
                        TestFunction(
                            name=function_page.title,
                            test_type=function_page.test_type,
                            test_case_count=len(function_page.cases) if function_page.cases else 1,
                            docstring_one_liner=function_page.docstring_one_liner,
                        )
                    ],
                )
            else:
                existing_module_page = self.module_page_props[str(function_page.path)]
                existing_module_page.test_functions.append(
                    TestFunction(
                        name=function_page.title,
                        test_type=function_page.test_type,
                        test_case_count=len(function_page.cases) if function_page.cases else 1,
                        docstring_one_liner=function_page.docstring_one_liner,
                    )
                )

    def add_directory_page_props(self) -> None:
        """
        Discover the intermediate directory pages and extract their properties.

        These directories may not have any test modules within them, e.g., tests/berlin/.
        """
        sub_paths: Set[Path] = set()
        for module_page in self.module_page_props.values():
            module_path_parts = module_page.path.parent.parts
            sub_paths.update(
                Path(*module_path_parts[: i + 1]) for i in range(len(module_path_parts))
            )
        for directory in sub_paths:
            fork = (
                directory.relative_to(self.source_dir).parts[0]
                if directory != self.source_dir
                # set any deployed fork for tests/index.md (to avoid dev-fork in command args)
                else "cancun"
            )
            self.page_props[str(directory)] = DirectoryPageProps(
                title=sanitize_string_title(str(directory.name)),
                path=directory,
                pytest_node_id=str(directory),
                source_code_url=generate_github_url(directory, branch_or_commit_or_tag=self.ref),
                # TODO: This won't work in all cases; should be from the development fork
                # Currently breaks for `test/prague/eip7692_eof_v1/index.md`  # noqa: SC100
                valid_from_fork=fork,
                package_name=get_import_path(directory),  # init.py will be used for docstrings
            )

    def find_files_within_collection_scope(self, file_pattern: str) -> List[Path]:
        """
        Find all files that match the scope of the collected test modules

        This to avoid adding matching files in uncollected test directories.

        Note: could be optimized!
        """
        files = []
        for module_page in self.module_page_props.values():
            # all files found in and under the modules' directory
            files += glob.glob(f"{module_page.path.parent}/**/{file_pattern}", recursive=True)
            for parent in module_page.path.parent.parents:
                if parent == self.source_dir:
                    break
                # add files in a module's parent directory
                files += glob.glob(f"{parent}/{file_pattern}")
        return [Path(file) for file in set(files)]

    def add_spec_page_props(self) -> None:
        """
        Add page path properties for spec files discovered in the collection scope.
        """
        for spec_path in self.find_files_within_collection_scope("spec.py"):
            self.page_props[str(spec_path)] = ModulePageProps(
                title="Spec",
                path=spec_path,
                source_code_url=generate_github_url(spec_path, branch_or_commit_or_tag=self.ref),
                pytest_node_id=str(spec_path),
                package_name=get_import_path(spec_path),
                valid_from_fork="",
                test_functions=[],
            )

    def add_markdown_page_props(self) -> None:
        """
        Add page path properties for markdown files discovered in the collection scope.
        """
        for md_path in self.find_files_within_collection_scope("*.md"):
            self.page_props[str(md_path)] = MarkdownPageProps(
                title=md_path.stem,
                path=md_path,
                source_code_url=generate_github_url(md_path, branch_or_commit_or_tag=self.ref),
                pytest_node_id=str(md_path),  # abuse: not a test, but used in source code link
                valid_from_fork="",
                package_name="",
            )

    def update_mkdocs_nav(self) -> None:
        """
        Add the generated 'Test Case Reference' entries to the mkdocs navigation menu.
        """
        fork_order = {fork.name().lower(): i for i, fork in enumerate(reversed(get_forks()))}

        def sort_by_fork_deployment_and_path(x: PageProps) -> Tuple[Any, ...]:
            """
            Key function used to sort navigation menu entries for test case ref docs.

            Nav entries / output files contain special cases such as:

            - ("Test Case Reference",) -> tests/index.md
            - ("Test Case Reference", "Berlin") -> tests/berlin/index.md
            - ("Test Case Reference", "Prague", "EIP-7692 EOF V1", tracker.md")
                tests/prague/eip7692_eof_v1/tracker.md
            - ("Test Case Reference", "Shanghai", "EIP-3855 PUSH0", "Spec") ->
                tests/shanghai/eip3855_push0/spec.py

            This function provides and ordering to sort nav men entries as follows:

            1. Forks are listed in the chronological order that they were deployed.
            2. Special files listed first (before test pages): "*.md" and `Spec.py`,
            3. The page's corresponding file path under `./tests/`.
            """
            length = len(x.path.parts)
            if length > 1:
                fork = str(x.path.parts[1]).lower()  # the fork folder from the relative path
            if length == 1:
                return (0,)
            elif length == 2:
                return (1, fork_order[fork])
            elif x.path.name == "spec.py":
                return (2, fork_order[fork], length, 0, x.path)
            elif x.path.suffix == ".md":
                return (2, fork_order[fork], length, 1, x.path)
            else:
                return (2, fork_order[fork], length, 2, x.path)

        nav = mkdocs_gen_files.Nav()
        for page in sorted(self.page_props.values(), key=sort_by_fork_deployment_and_path):
            nav[page.nav_entry(self.top_level_nav_entry)] = str(page.target_output_file)
        with mkdocs_gen_files.open("navigation.md", "a") as nav_file:
            nav_file.writelines(nav.build_literate_nav())

    def write_pages(self) -> None:
        """
        Write all pages to the target directory.
        """
        for page in self.page_props.values():
            page.write_page(self.jinja2_env)
