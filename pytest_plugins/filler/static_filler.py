"""
Static filler pytest plugin that reads test cases from static files and fills them into test
fixtures.
"""

import inspect
import itertools
import json
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Tuple, Type

import pytest
import yaml
from _pytest.fixtures import FixtureRequest
from _pytest.mark import ParameterSet

from ethereum_test_fixtures import BaseFixture, LabeledFixtureFormat
from ethereum_test_forks import Fork
from ethereum_test_specs import SPEC_TYPES, BaseStaticTest

from ..forks.forks import ValidityMarker, get_intersection_set
from ..shared.helpers import labeled_format_parameter_set


def get_test_id_from_arg_names_and_values(
    arg_names: List[str], arg_values: List[Any] | Tuple[Any, ...]
) -> str:
    """Get the test id from argument names and values."""
    return "-".join(
        [
            f"{arg_name}={arg_value}"
            for arg_name, arg_value in zip(arg_names, arg_values, strict=True)
        ]
    )


def get_argument_names_and_values_from_parametrize_mark(
    mark: pytest.Mark,
) -> Tuple[List[str], List[ParameterSet]]:
    """Get the argument names and values from a parametrize mark."""
    if mark.name != "parametrize":
        raise Exception("Mark is not a parametrize mark")
    kwargs_dict = dict(mark.kwargs)
    ids: Callable | List[str] | None = kwargs_dict.pop("ids") if "ids" in kwargs_dict else None
    marks: List[pytest.Mark] = kwargs_dict.pop("marks") if "marks" in kwargs_dict else []
    if kwargs_dict:
        raise Exception("Mark has kwargs which is not supported")
    args = mark.args
    if not isinstance(args, tuple):
        raise Exception("Args is not a tuple")
    if len(args) != 2:
        raise Exception("Args does not have 2 elements")
    arg_names = args[0] if isinstance(args[0], list) else args[0].split(",")
    arg_values = []
    for arg_index, arg_value in enumerate(args[1]):
        if not isinstance(arg_value, ParameterSet):
            original_arg_value = arg_value
            if not isinstance(arg_value, tuple) and not isinstance(arg_value, list):
                arg_value = (arg_value,)
            test_id: str = get_test_id_from_arg_names_and_values(arg_names, arg_value)
            if ids:
                if callable(ids):
                    test_id = ids(original_arg_value)
                else:
                    test_id = ids[arg_index]
            arg_values.append(ParameterSet(arg_value, marks, id=test_id))
        else:
            arg_values.append(arg_value)
    return arg_names, arg_values


def get_all_combinations_from_parametrize_marks(
    parametrize_marks: List[pytest.Mark],
) -> Tuple[List[str], List[ParameterSet]]:
    """Get all combinations of arguments from multiple parametrize marks."""
    assert parametrize_marks, "No parametrize marks found"
    list_of_values: List[List[ParameterSet]] = []
    all_argument_names = []
    for mark in parametrize_marks:
        arg_names, arg_values = get_argument_names_and_values_from_parametrize_mark(mark)
        list_of_values.append(arg_values)
        all_argument_names.extend(arg_names)
    all_value_combinations: List[ParameterSet] = []
    # use itertools to get all combinations
    test_ids = set()
    for combination in itertools.product(*list_of_values):
        values: List[Any] = []
        marks: List[pytest.Mark | pytest.MarkDecorator] = []
        for param_set in combination:
            values.extend(param_set.values)
            marks.extend(param_set.marks)
        test_id = "-".join([param.id or "" for param in combination])
        if test_id in test_ids:
            current_int = 2
            while f"{test_id}-{current_int}" in test_ids:
                current_int += 1
            test_id = f"{test_id}-{current_int}"
        all_value_combinations.append(
            ParameterSet(
                values=values,
                marks=marks,
                id=test_id,
            )
        )
        test_ids.add(test_id)

    return all_argument_names, all_value_combinations


def pytest_addoption(parser: pytest.Parser):
    """Add command-line options to pytest."""
    static_filler_group = parser.getgroup("static", "Arguments defining static filler behavior")
    static_filler_group.addoption(
        "--fill-static-tests",
        action="store_true",
        dest="fill_static_tests_enabled",
        default=None,
        help=("Enable reading and filling from static test files."),
    )


def pytest_collect_file(file_path: Path, parent) -> pytest.Collector | None:
    """Pytest hook that collects test cases from static files and fills them into test fixtures."""
    fill_static_tests_enabled = parent.config.getoption("fill_static_tests_enabled")
    if not fill_static_tests_enabled:
        return None
    if not BaseStaticTest.formats:
        # No formats registered, so no need to collect any files.
        return None
    if file_path.suffix in (".json", ".yml", ".yaml"):
        return FillerFile.from_parent(parent, path=file_path)
    return None


class NoIntResolver(yaml.SafeLoader):
    """Class that tells yaml to not resolve int values."""

    pass


# Remove the implicit resolver for integers
# Because yaml treat unquoted numbers 000001000 as oct numbers
# Treat all numbers as str instead
for ch in list(NoIntResolver.yaml_implicit_resolvers):
    resolvers = NoIntResolver.yaml_implicit_resolvers[ch]
    NoIntResolver.yaml_implicit_resolvers[ch] = [
        (tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:int"
    ]


class FillerFile(pytest.File):
    """
    Filler file that reads test cases from static files and fills them into test
    fixtures.
    """

    def collect(self: "FillerFile") -> Generator["FillerTestItem", None, None]:
        """Collect test cases from a single static file."""
        if not self.path.stem.endswith("Filler"):
            return
        with open(self.path, "r") as file:
            try:
                loaded_file = (
                    json.load(file)
                    if self.path.suffix == ".json"
                    else yaml.load(file, Loader=NoIntResolver)
                )
                for key in loaded_file:
                    filler = BaseStaticTest.model_validate(loaded_file[key])
                    func = filler.fill_function()

                    function_marks: List[pytest.Mark] = []
                    if hasattr(func, "pytestmark"):
                        function_marks = func.pytestmark[:]
                    parametrize_marks: List[pytest.Mark] = [
                        mark for mark in function_marks if mark.name == "parametrize"
                    ]

                    func_parameters = inspect.signature(func).parameters

                    fixture_formats: List[Type[BaseFixture] | LabeledFixtureFormat] = []
                    spec_parameter_name = ""
                    for test_type in SPEC_TYPES:
                        if test_type.pytest_parameter_name() in func_parameters:
                            assert spec_parameter_name == "", "Multiple spec parameters found"
                            spec_parameter_name = test_type.pytest_parameter_name()
                            fixture_formats.extend(test_type.supported_fixture_formats)

                    validity_markers: List[ValidityMarker] = (
                        ValidityMarker.get_all_validity_markers(key, self.config, function_marks)
                    )
                    intersection_set = get_intersection_set(key, validity_markers, self.config)

                    extra_function_marks: List[pytest.Mark] = [
                        mark
                        for mark in function_marks
                        if mark.name != "parametrize"
                        and (mark.name not in [v.mark.name for v in validity_markers])
                    ]

                    for format_with_or_without_label in fixture_formats:
                        fixture_format_parameter_set = labeled_format_parameter_set(
                            format_with_or_without_label
                        )
                        fixture_format = (
                            format_with_or_without_label.format
                            if isinstance(format_with_or_without_label, LabeledFixtureFormat)
                            else format_with_or_without_label
                        )
                        for fork in sorted(intersection_set):
                            params: Dict[str, Any] = {spec_parameter_name: fixture_format}
                            fixturenames = [
                                spec_parameter_name,
                            ]
                            marks: List[pytest.Mark] = [
                                mark  # type: ignore
                                for mark in fixture_format_parameter_set.marks
                                if mark.name != "parametrize"
                            ]
                            test_id = f"fork_{fork.name()}-{fixture_format_parameter_set.id}"
                            if "fork" in func_parameters:
                                params["fork"] = fork
                            if "pre" in func_parameters:
                                fixturenames.append("pre")

                            if parametrize_marks:
                                parameter_names, parameter_set_list = (
                                    get_all_combinations_from_parametrize_marks(parametrize_marks)
                                )
                                for parameter_set in parameter_set_list:
                                    # Copy and extend the params with the parameter set
                                    case_marks = (
                                        marks[:]
                                        + [
                                            mark
                                            for mark in parameter_set.marks
                                            if mark.name != "parametrize"
                                        ]
                                        + extra_function_marks
                                    )
                                    case_params = params.copy() | dict(
                                        zip(parameter_names, parameter_set.values, strict=True)
                                    )

                                    yield FillerTestItem.from_parent(
                                        self,
                                        original_name=key,
                                        func=func,
                                        params=case_params,
                                        fixturenames=fixturenames,
                                        name=f"{key}[{test_id}-{parameter_set.id}]",
                                        fork=fork,
                                        fixture_format=fixture_format,
                                        marks=case_marks,
                                    )
                            else:
                                yield FillerTestItem.from_parent(
                                    self,
                                    original_name=key,
                                    func=func,
                                    params=params,
                                    fixturenames=fixturenames,
                                    name=f"{key}[{test_id}]",
                                    fork=fork,
                                    fixture_format=fixture_format,
                                    marks=marks,
                                )
            except Exception as e:
                pytest.fail(f"Error loading file {self.path} as a test: {e}")
                warnings.warn(f"Error loading file {self.path} as a test: {e}", stacklevel=1)
                return


class FillerTestItem(pytest.Item):
    """Filler test item produced from a single test from a static file."""

    originalname: str
    func: Callable
    params: Dict[str, Any]
    fixturenames: List[str]
    github_url: str = ""
    fork: Fork
    fixture_format: Type[BaseFixture]

    def __init__(
        self,
        *args,
        original_name: str,
        func: Callable,
        params: Dict[str, Any],
        fixturenames: List[str],
        fork: Fork,
        fixture_format: Type[BaseFixture],
        marks: List[pytest.Mark],
        **kwargs,
    ):
        """Initialize the filler test item."""
        super().__init__(*args, **kwargs)
        self.originalname = original_name
        self.func = func
        self.params = params
        self.fixturenames = fixturenames
        self.fork = fork
        self.fixture_format = fixture_format
        for marker in marks:
            if type(marker) is pytest.Mark:
                self.own_markers.append(marker)
            else:
                self.add_marker(marker)  # type: ignore

    def setup(self):
        """Resolve and apply fixtures before test execution."""
        self._fixtureinfo = self.session._fixturemanager.getfixtureinfo(
            self,
            None,
            None,
            funcargs=False,
        )
        request = FixtureRequest(self, _ispytest=True)
        for fixture_name in self.fixturenames:
            self.params[fixture_name] = request.getfixturevalue(fixture_name)

    def runtest(self):
        """Execute the test logic for this specific static test."""
        self.func(**self.params)

    def reportinfo(self):
        """Provide information for test reporting."""
        return self.fspath, 0, f"Static file test: {self.name}"
