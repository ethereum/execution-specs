"""
Classes and helpers used for templates, navigation menus and file output.

The dataclass fields are used to define the page properties fields which
are used in the jinja2 templates when generating site content (located in
docs/templates). The classes also define each page's navigation menu entry
and target output file.

A few helpers are defined with EEST logic in order to sanitize strings from
file paths for use in navigation menu.
"""
import re
from abc import abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import mkdocs_gen_files  # type: ignore
from jinja2 import Environment

from ethereum_test_tools import Opcodes


def apply_name_filters(input_string: str):
    """
    Apply a list of capitalizations/regexes to names used in titles & nav menus.

    Note: As of PragueEIP7692 With 634 doc pages, this function constitutes ~2.0s
    of the total runtime (~5.5s). This seems to be insignificant with the time
    taken by mkdocstrings to include the docstrings in the final output (which)
    is a separate mkdocs "build-step" occurs outside the scope of this plugin.
    """
    word_replacements = {
        "acl": "ACL",
        "bls 12": "BLS12",
        "bls12 g1add": "BLS12_G1ADD",
        "bls12 g1msm": "BLS12_G1MSM",
        "bls12 g1mul": "BLS12_G1MUL",
        "bls12 g2add": "BLS12_G2ADD",
        "bls12 g2msm": "BLS12_G2MSM",
        "bls12 g2mul": "BLS12_G2MUL",
        "bls12 map fp2 to g2": "BLS12_MAP_FP2_TO_G2",
        "bls12 map fp to g1": "BLS12_MAP_FP_TO_G1",
        "bls12 pairing": "BLS12_PAIRING_CHECK",
        "eips": "EIPs",
        "eof": "EOF",
        "vm": "VM",
    }
    # adding these is the expensive part
    opcode_replacements = {str(opcode): str(opcode) for opcode in Opcodes if str(opcode) != "GAS"}
    all_replacements = {**word_replacements, **opcode_replacements}
    for word, replacement in all_replacements.items():
        input_string = re.sub(rf"(?i)\b{re.escape(word)}\b", replacement, input_string)

    regex_patterns = [
        (r"eip-?([1-9]{1,5})", r"EIP-\1"),  # Matches "eip-123" or "eip123"
    ]
    for pattern, replacement in regex_patterns:
        input_string = re.sub(pattern, replacement, input_string, flags=re.IGNORECASE)

    return input_string


def snake_to_capitalize(string: str) -> str:  # noqa: D103
    """
    Converts valid identifiers to a capitalized string, otherwise leave as-is.
    """
    if string.isidentifier():
        return " ".join(word.capitalize() for word in string.split("_"))
    return string


def sanitize_string_title(string: str) -> str:
    """
    Sanitize a string to be used as a title.
    """
    return apply_name_filters(snake_to_capitalize(string))


def nav_path_to_sanitized_str_tuple(nav_path: Path) -> tuple:
    """
    Convert a nav path to a tuple of sanitized strings for use in mkdocs navigation.
    """
    return tuple(sanitize_string_title(part) for part in nav_path.parts)


@dataclass
class PagePropsBase:
    """
    Common test reference doc page properties and definitions.

    The dataclass attributes are made directly available in the jinja2
    found in `docs/templates/*.j2`.
    """

    title: str
    source_code_url: str
    valid_from_fork: str
    path: Path
    pytest_node_id: str
    package_name: str

    @property
    @abstractmethod
    def template(self) -> str:
        """
        Get the jinja2 template used to render this page.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def target_output_file(self) -> Path:
        """
        Get the target output file for this page.
        """
        raise NotImplementedError

    def nav_entry(self, top_level_nav_entry: str) -> tuple:
        """
        Get the mkdocs navigation entry for this page.
        """
        if len(self.path.parts) == 1:
            return (top_level_nav_entry,)
        path = top_level_nav_entry / Path(*self.path.parts[1:]).with_suffix("")
        return nav_path_to_sanitized_str_tuple(path)

    def write_page(self, jinja2_env: Environment):
        """
        Write the page to the target directory.
        """
        template = jinja2_env.get_template(self.template)
        rendered_content = template.render(**asdict(self))
        with mkdocs_gen_files.open(self.target_output_file, "w") as destination:
            for line in rendered_content.splitlines(keepends=True):
                destination.write(line)


@dataclass
class TestCase:
    """
    Properties used to define a single test case in test function parameter tables.
    """

    id: str
    params: Dict[str, Any]


@dataclass
class FunctionPageProps(PagePropsBase):
    """
    Definitions used for to generate test function (markdown) pages and their
    corresponding static HTML pages.
    """

    test_type: str
    docstring_one_liner: str
    html_static_page_target: str
    cases: Optional[List[TestCase]]

    @property
    def template(self) -> str:
        """
        Get the filename of the jinja2 template used to render this page.
        """
        return "function.md.j2"

    @property
    def target_output_file(self) -> Path:
        """
        Get the target output file for this page.
        """
        return self.path.with_suffix("") / f"{self.title}.md"

    def nav_entry(self, top_level_nav_entry) -> tuple:
        """
        Get the mkdocs navigation entry for this page.
        """
        nav_path_prefix = super().nav_entry(top_level_nav_entry)  # already sanitized
        return tuple([*nav_path_prefix, f"<code>{self.title}</code>"])

    def write_page(self, jinja2_env: Environment):
        """
        Test functions also get a static HTML page with parametrized test cases.

        This is intended for easier viewing (without mkdocs styling) of the data-table
        that documents the parametrized test cases.
        """
        super().write_page(jinja2_env)
        if not self.cases:
            return
        html_template = jinja2_env.get_template("function.html.j2")
        rendered_html_content = html_template.render(**asdict(self))
        html_output_file = self.target_output_file.with_suffix(".html")
        with mkdocs_gen_files.open(html_output_file, "w") as destination:
            for line in rendered_html_content.splitlines(keepends=True):
                destination.write(line)


@dataclass
class TestFunction:
    """
    Properties used to build the test function overview table in test module pages.
    """

    name: str
    test_type: str
    test_case_count: int
    docstring_one_liner: str


@dataclass
class ModulePageProps(PagePropsBase):
    """
    Definitions used for test modules, e.g., `tests/berlin/eip2930_access_list/test_acl.py`.
    """

    test_functions: List[TestFunction]

    @property
    def template(self) -> str:
        """
        Get the filename of the jinja2 template used to render this page.
        """
        return "module.md.j2"

    @property
    def target_output_file(self) -> Path:
        """
        Get the target output file for this page.
        """
        if self.path.suffix == "spec.py":
            return self.path.with_suffix(".md")
        return self.path.with_suffix("") / "index.md"


@dataclass
class DirectoryPageProps(PagePropsBase):
    """
    Definitions used for parent directories in test paths, e.g., `tests/berlin`.
    """

    @property
    def template(self) -> str:
        """
        Get the filename of the jinja2 template used to render this page.
        """
        return "directory.md.j2"

    @property
    def target_output_file(self) -> Path:
        """
        Get the target output file for this page.
        """
        return self.path / "index.md"


@dataclass
class MarkdownPageProps(PagePropsBase):
    """
    Definitions used to verbatim include markdown files included in test paths.
    """

    @property
    def template(self) -> str:
        """
        Get the filename of the jinja2 template used to render this page.
        """
        return "markdown_header.md.j2"

    @property
    def target_output_file(self) -> Path:
        """
        Get the target output file for this page.
        """
        return self.path

    def write_page(self, jinja2_env: Environment):
        """
        Write the page to the target directory.

        We read the md file and write it with `mkdocs_gen_files`.
        """
        template = jinja2_env.get_template(self.template)
        rendered_content = template.render(**asdict(self))
        with open(self.path, "r") as md_source:
            with mkdocs_gen_files.open(self.target_output_file, "w") as destination:
                for line in rendered_content.splitlines(keepends=True):
                    destination.write(line)
                for line in md_source:
                    destination.write(line)


PageProps = DirectoryPageProps | ModulePageProps | FunctionPageProps | MarkdownPageProps
PagePropsLookup = Dict[str, PageProps]
ModulePagePropsLookup = Dict[str, ModulePageProps]
FunctionPagePropsLookup = Dict[str, FunctionPageProps]
