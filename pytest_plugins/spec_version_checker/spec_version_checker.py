"""
A pytest plugin that checks that the spec version specified in test/filler
modules matches that of https://github.com/ethereum/EIPs.
"""
import warnings

import pytest

from ethereum_test_tools import ReferenceSpec, ReferenceSpecTypes

IGNORE_PACKAGES = [
    "tests.vm.",
    "tests.example.",
    "tests.security.",
]


class OutdatedReferenceSpec(Warning):
    """
    Warning when the spec version found in a filler module is out of date.
    """

    def __init__(self, filler_module: str, spec_obj: ReferenceSpec):
        super().__init__(
            "There is newer version of the spec referenced in filler "
            f"{filler_module}, tests might be outdated: "
            f"Spec: {spec_obj.name()}. "
            "Referenced version: "
            f"{spec_obj.known_version()}. "
            "Latest version: "
            f"{spec_obj.latest_version()}."
        )


class NoReferenceSpecDefined(Warning):
    """
    Warning when no spec version was found in a filler module.
    """

    def __init__(self, filler_module: str):
        super().__init__(f"No reference spec defined in {filler_module}.")


class UnableToCheckReferenceSpec(Warning):
    """
    Warnings when the current spec version can not be determined.
    """

    def __init__(self, filler_module: str, error: Exception):
        super().__init__(
            f"Reference spec could not be determined for " f"{filler_module}: {error}."
        )


@pytest.fixture(autouse=True, scope="module")
def reference_spec(request):
    """
    Returns the reference spec used for the generated test fixtures in a
    given module.
    """
    module_dict = request.module.__dict__
    parseable_ref_specs = [
        ref_spec_type
        for ref_spec_type in ReferenceSpecTypes
        if ref_spec_type.parseable_from_module(module_dict)
    ]
    filler_module = request.module.__name__
    if any(filler_module.startswith(package) for package in IGNORE_PACKAGES):
        return None
    if len(parseable_ref_specs) > 0:
        spec_obj = parseable_ref_specs[0].parse_from_module(module_dict)
        try:
            if spec_obj.is_outdated():
                warnings.warn(OutdatedReferenceSpec(filler_module, spec_obj))
            return spec_obj
        except Exception as e:
            warnings.warn(UnableToCheckReferenceSpec(filler_module, e))
            return None
    warnings.warn(NoReferenceSpecDefined(filler_module))
    return None
