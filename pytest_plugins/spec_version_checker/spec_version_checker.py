"""
A pytest plugin that checks that the spec version specified in test/filler
modules matches that of https://github.com/ethereum/EIPs.
"""

import os
import re
import textwrap
from types import ModuleType
from typing import Any, List, Optional, Set

import pytest
from _pytest.nodes import Item, Node
from _pytest.python import Module

from ethereum_test_tools import ReferenceSpec, ReferenceSpecTypes

GITHUB_TOKEN_HELP = textwrap.dedent(
    "Either set the GITHUB_TOKEN environment variable or specify one via --github-token. "
    "The Github CLI can be used: `--github-token $(gh auth token)` (https://cli.github.com/) "
    "or a PAT can be generated at https://github.com/settings/personal-access-tokens/new."
)


def pytest_addoption(parser):
    """Add Github token option to pytest command line options."""
    group = parser.getgroup(
        "spec_version_checker", "Arguments defining the EIP spec version checker"
    )
    group.addoption(
        "--github-token",
        action="store",
        dest="github_token",
        default=None,
        help=(
            "Specify a Github API personal access token (PAT) to avoid rate limiting. "
            f"{GITHUB_TOKEN_HELP}"
        ),
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """
    Register the plugin's custom markers and process command-line options.

    Custom marker registration:
    https://docs.pytest.org/en/7.1.x/how-to/writing_plugins.html#registering-custom-markers
    """
    config.addinivalue_line(
        "markers",
        "eip_version_check: a test that tests the reference spec defined in an EIP test module.",
    )

    github_token = config.getoption("github_token") or os.environ.get("GITHUB_TOKEN")

    if not github_token:
        pytest.exit(
            "A Github personal access token (PAT) is required but has not been provided. "
            f"{GITHUB_TOKEN_HELP}"
        )

    config.github_token = github_token


def get_ref_spec_from_module(
    module: ModuleType, github_token: Optional[str] = None
) -> None | ReferenceSpec:
    """
    Return the reference spec object defined in a module.

    Args:
        module: The module to extract reference spec from
        github_token: Optional GitHub token for API authentication

    Raises:
        Exception: If the module path contains "eip" and the module
            does not define a reference spec.

    Returns:
        spec_obj: Return None if the module path does not contain "eip",
            i.e., the module is not required to define a reference spec,
            otherwise, return the ReferenceSpec object as defined by the
            module.

    """
    if not is_test_for_an_eip(str(module.__file__)):
        return None
    module_dict = module.__dict__
    parseable_ref_specs = [
        ref_spec_type
        for ref_spec_type in ReferenceSpecTypes
        if ref_spec_type.parseable_from_module(module_dict)
    ]
    if len(parseable_ref_specs) > 0:
        module_dict = module.__dict__
        try:
            spec_obj = parseable_ref_specs[0].parse_from_module(
                module_dict, github_token=github_token
            )
        except Exception as e:
            raise Exception(f"Error in spec_version_checker: {e} (this test is generated).") from e
    else:
        raise Exception("Test doesn't define REFERENCE_SPEC_GIT_PATH and REFERENCE_SPEC_VERSION")
    return spec_obj


def is_test_for_an_eip(input_string: str) -> bool:
    """Return True if `input_string` contains an EIP number, i.e., eipNNNN."""
    pattern = re.compile(r".*eip\d{1,4}", re.IGNORECASE)
    if pattern.match(input_string):
        return True
    return False


def test_eip_spec_version(module: ModuleType, github_token: Optional[str] = None):
    """
    Test that the ReferenceSpec object as defined in the test module
    is not outdated when compared to the remote hash from
    ethereum/EIPs.

    Args:
        module: Module to test
        github_token: Optional GitHub token for API authentication

    """
    ref_spec = get_ref_spec_from_module(module, github_token=github_token)
    assert ref_spec, "No reference spec object defined"

    message = (
        "The version of the spec referenced in "
        f"{module} does not match that from ethereum/EIPs, "
        f"tests might be outdated: Spec: {ref_spec.name()}. "
        f"Referenced version: {ref_spec.known_version()}. "
        f"Latest version: {ref_spec.latest_version()}. The "
        f"version was retrieved from {ref_spec.api_url()}."
    )
    try:
        is_up_to_date = not ref_spec.is_outdated()
    except Exception as e:
        raise Exception(
            f"Error in spec_version_checker: {e} (this test is generated). "
            f"Reference spec URL: {ref_spec.api_url()}."
        ) from e

    assert is_up_to_date, message


class EIPSpecTestItem(Item):
    """Custom pytest test item to test EIP spec versions."""

    module: ModuleType
    github_token: Optional[str]

    def __init__(self, name: str, parent: Node, **kwargs: Any):
        """
        Initialize the test item.

        Args:
            name: Name of the test
            parent: Parent node
            **kwargs: Additional keyword arguments

        """
        super().__init__(name, parent)
        self.module = None  # type: ignore
        self.github_token = None

    @classmethod
    def from_parent(cls, parent: Node, **kw: Any) -> "EIPSpecTestItem":
        """
        Public constructor to define new tests.
        https://docs.pytest.org/en/latest/reference/reference.html#pytest.nodes.Node.from_parent.

        Args:
            parent: The parent Node
            kw: Additional keyword arguments (module, github_token)

        """
        module = kw.pop("module", None)
        github_token = kw.pop("github_token", None)

        kw["name"] = "test_eip_spec_version"
        item = super(EIPSpecTestItem, cls).from_parent(parent, **kw)

        item.module = module
        item.github_token = github_token
        return item

    def runtest(self) -> None:
        """Define the test to execute for this item."""
        test_eip_spec_version(self.module, github_token=self.github_token)

    def reportinfo(self) -> tuple[str, int, str]:
        """
        Get location information for this test item to use test reports.

        Returns:
            A tuple of (path, line_number, description)

        """
        return "spec_version_checker", 0, f"{self.name}"


def pytest_collection_modifyitems(
    session: pytest.Session, config: pytest.Config, items: List[Item]
):
    """Insert a new test EIPSpecTestItem for every test module with 'eip' in its path."""
    github_token = config.github_token if hasattr(config, "github_token") else None

    modules: Set[Module] = {item.parent for item in items if isinstance(item.parent, Module)}
    new_test_eip_spec_version_items = [
        EIPSpecTestItem.from_parent(parent=module, module=module.obj, github_token=github_token)
        for module in sorted(modules, key=lambda module: module.path)
        if is_test_for_an_eip(str(module.path))
    ]
    for item in new_test_eip_spec_version_items:
        item.add_marker("eip_version_check", append=True)
    items.extend(new_test_eip_spec_version_items)
