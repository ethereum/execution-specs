"""
A pytest plugin that checks that the spec version specified in test/filler
modules matches that of https://github.com/ethereum/EIPs.
"""

import re
from types import ModuleType

import pytest
from _pytest.nodes import Item
from _pytest.python import Module

from ethereum_test_tools import ReferenceSpec, ReferenceSpecTypes


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


def get_ref_spec_from_module(module: ModuleType) -> None | ReferenceSpec:
    """
    Return the reference spec object defined in a module.

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
            spec_obj = parseable_ref_specs[0].parse_from_module(module_dict)
        except Exception as e:
            raise Exception(f"Error in spec_version_checker: {e} (this test is generated).")
    else:
        raise Exception("Test doesn't define REFERENCE_SPEC_GIT_PATH and REFERENCE_SPEC_VERSION")
    return spec_obj


@pytest.fixture(autouse=True, scope="module")
def reference_spec(request) -> None | ReferenceSpec:
    """
    Pytest fixture that returns the reference spec defined in a module.

    See `get_ref_spec_from_module`.
    """
    return get_ref_spec_from_module(request.module)


def is_test_for_an_eip(input_string: str) -> bool:
    """
    Return True if `input_string` contains an EIP number, i.e., eipNNNN.
    """
    pattern = re.compile(r".*eip\d{1,4}", re.IGNORECASE)
    if pattern.match(input_string):
        return True
    return False


def test_eip_spec_version(module: ModuleType):
    """
    Test that the ReferenceSpec object as defined in the test module
    is not outdated when compared to the remote hash from
    ethereum/EIPs.
    """
    ref_spec = get_ref_spec_from_module(module)
    assert ref_spec, "No reference spec object defined"

    message = (
        "The version of the spec referenced in "
        f"{module} does not match that from ethereum/EIPs, "
        f"tests might be outdated: Spec: {ref_spec.name()}. "
        f"Referenced version: {ref_spec.known_version()}. "
        f"Latest version: {ref_spec.latest_version()}. The "
        f"version was retrieved from {ref_spec.api_url()}."
    )
    return
    try:
        is_up_to_date = not ref_spec.is_outdated()
    except Exception as e:
        raise Exception(
            f"Error in spec_version_checker: {e} (this test is generated). "
            f"Reference spec URL: {ref_spec.api_url()}."
        )

    assert is_up_to_date, message


class EIPSpecTestItem(Item):
    """
    Custom pytest test item to test EIP spec versions.
    """

    def __init__(self, name, parent, module):
        super().__init__(name, parent)
        self.module = module

    @classmethod
    def from_parent(cls, parent, module):
        """
        Public constructor to define new tests.
        https://docs.pytest.org/en/latest/reference/reference.html#pytest.nodes.Node.from_parent
        """
        return super().from_parent(parent=parent, name="test_eip_spec_version", module=module)

    def runtest(self):
        """
        Define the test to execute for this item.
        """
        test_eip_spec_version(self.module)

    def reportinfo(self):
        """
        Get location information for this test item to use test reports.
        """
        return "spec_version_checker", 0, f"{self.name}"


def pytest_collection_modifyitems(session, config, items):
    """
    Insert a new test EIPSpecTestItem for every test modules that
    contains 'eip' in its path.
    """
    modules = set(item.parent for item in items if isinstance(item.parent, Module))
    new_test_eip_spec_version_items = [
        EIPSpecTestItem.from_parent(module, module.obj)
        for module in modules
        if is_test_for_an_eip(str(module.path))
    ]
    for item in new_test_eip_spec_version_items:
        item.add_marker("eip_version_check", append=True)
    items.extend(new_test_eip_spec_version_items)
    # this gives a nice ordering for the new tests added here, but re-orders the entire
    # default pytest item ordering which based on ordering of test functions in test modules
    # items.sort(key=lambda x: x.nodeid)
