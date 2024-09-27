"""
Pytest plugin to enable fork range configuration for the test session.
"""

import itertools
import sys
import textwrap
from dataclasses import dataclass, field
from types import FunctionType
from typing import Any, Callable, List, Set, Tuple

import pytest
from _pytest.mark.structures import ParameterSet
from pytest import Metafunc

from ethereum_test_forks import (
    Fork,
    ForkAttribute,
    get_deployed_forks,
    get_forks,
    get_forks_with_no_parents,
    get_from_until_fork_set,
    get_last_descendants,
    get_transition_forks,
    transition_fork_to,
)
from evm_transition_tool import TransitionTool


def pytest_addoption(parser):
    """
    Adds command-line options to pytest.
    """
    fork_group = parser.getgroup("Forks", "Specify the fork range to generate fixtures for")
    fork_group.addoption(
        "--forks",
        action="store_true",
        dest="show_fork_help",
        default=False,
        help="Display forks supported by the test framework and exit.",
    )
    fork_group.addoption(
        "--fork",
        action="store",
        dest="single_fork",
        default=None,
        help="Only fill tests for the specified fork.",
    )
    fork_group.addoption(
        "--from",
        action="store",
        dest="forks_from",
        default=None,
        help="Fill tests from and including the specified fork.",
    )
    fork_group.addoption(
        "--until",
        action="store",
        dest="forks_until",
        default=None,
        help="Fill tests until and including the specified fork.",
    )


@dataclass(kw_only=True)
class MarkedValue:
    """
    A processed value for a covariant parameter.

    Value can be a list for inclusive parameters.
    """

    value: Any
    marks: List[pytest.Mark | pytest.MarkDecorator] = field(default_factory=list)


@dataclass(kw_only=True)
class ForkCovariantParameter:
    """
    Value list for a fork covariant parameter in a given fork.
    """

    names: List[str]
    values: List[List[MarkedValue]]


@dataclass(kw_only=True)
class ForkParametrizer:
    """
    A parametrizer for a test case that is parametrized by the fork.
    """

    fork: Fork
    fork_covariant_parameters: List[ForkCovariantParameter] = field(default_factory=list)
    marks: List[pytest.MarkDecorator | pytest.Mark] = field(default_factory=list)

    @property
    def parameter_names(self) -> List[str]:
        """
        Return the parameter names for the test case.
        """
        parameter_names = ["fork"]
        for p in self.fork_covariant_parameters:
            parameter_names.extend(p.names)
        return parameter_names

    @property
    def parameter_values(self) -> List[ParameterSet]:
        """
        Return the parameter values for the test case.
        """
        param_value_combinations = [
            # Flatten the list of values for each parameter
            list(itertools.chain(*params))
            for params in itertools.product(
                # Add the fork so it is multiplied by the other parameters.
                # It's a list of lists because all parameters are, but it will
                # flattened after the product.
                [[MarkedValue(value=self.fork)]],
                # Add the values for each parameter, all of them are lists of at least one element.
                *[p.values for p in self.fork_covariant_parameters],
            )
        ]

        parameter_set_list: List[ParameterSet] = []
        for marked_params in param_value_combinations:
            marks = self.marks.copy()
            params: List[Any] = []
            for p in marked_params:
                params.append(p.value)
                if p.marks:
                    marks.extend(p.marks)
            parameter_set_list.append(pytest.param(*params, marks=marks))

        return parameter_set_list


@dataclass(kw_only=True)
class CovariantDescriptor:
    """
    A descriptor for a parameter that is covariant with the fork:
    the parametrized values change depending on the fork.
    """

    marker_name: str
    description: str
    fork_attribute_name: str
    parameter_names: List[str]

    def get_marker(self, metafunc: Metafunc) -> pytest.Mark | None:
        """
        Get the marker for the given test function.
        """
        m = metafunc.definition.iter_markers(self.marker_name)
        if m is None:
            return None
        marker_list = list(m)
        assert len(marker_list) <= 1, f"Multiple markers {self.marker_name} found"
        if len(marker_list) == 0:
            return None
        return marker_list[0]

    def check_enabled(self, metafunc: Metafunc) -> bool:
        """
        Check if the marker is enabled for the given test function.
        """
        return self.get_marker(metafunc) is not None

    @staticmethod
    def process_value(
        values: Any | List[Any] | Tuple[Any],
        selector: FunctionType,
        marks: None
        | pytest.Mark
        | pytest.MarkDecorator
        | List[pytest.Mark | pytest.MarkDecorator]
        | Callable[
            [Any],
            List[pytest.Mark | pytest.MarkDecorator] | pytest.Mark | pytest.MarkDecorator | None,
        ],
    ) -> List[List[MarkedValue]]:
        """
        Process a value for a covariant parameter.

        The `selector` is applied to values in order to filter them.
        """
        if not isinstance(values, tuple) and not isinstance(values, list):
            values = [values]

        if selector(*values[: selector.__code__.co_argcount]):
            if isinstance(marks, FunctionType):
                marks = marks(*values[: marks.__code__.co_argcount])
            assert not isinstance(marks, FunctionType), "marks must be a list or None"
            if marks is None:
                marks = []
            elif not isinstance(marks, list):
                marks = [marks]  # type: ignore

            return [[MarkedValue(value=v, marks=marks) for v in values]]

        return []

    def process_values(self, metafunc: Metafunc, values: List[Any]) -> List[List[MarkedValue]]:
        """
        Filter the values for the covariant parameter.

        I.e. if the marker has an argument, the argument is interpreted as a lambda function
        that filters the values.
        """
        marker = self.get_marker(metafunc)
        assert marker is not None
        assert len(marker.args) == 0, "Only keyword arguments are supported"

        kwargs = dict(marker.kwargs)

        selector = kwargs.pop("selector", lambda _: True)
        assert isinstance(selector, FunctionType), "selector must be a function"

        marks = kwargs.pop("marks", None)

        if len(kwargs) > 0:
            raise ValueError(f"Unknown arguments to {self.marker_name}: {kwargs}")

        processed_values: List[List[MarkedValue]] = []
        for value in values:
            processed_values.extend(self.process_value(value, selector, marks))

        return processed_values

    def add_values(self, metafunc: Metafunc, fork_parametrizer: ForkParametrizer) -> None:
        """
        Add the values for the covariant parameter to the parametrizer.
        """
        if not self.check_enabled(metafunc=metafunc):
            return
        fork = fork_parametrizer.fork
        get_fork_covariant_values: ForkAttribute = getattr(fork, self.fork_attribute_name)
        values = get_fork_covariant_values(block_number=0, timestamp=0)
        assert isinstance(values, list)
        assert len(values) > 0
        values = self.process_values(metafunc, values)
        fork_parametrizer.fork_covariant_parameters.append(
            ForkCovariantParameter(names=self.parameter_names, values=values)
        )


fork_covariant_descriptors = [
    CovariantDescriptor(
        marker_name="with_all_tx_types",
        description="marks a test to be parametrized for all tx types at parameter named tx_type"
        " of type int",
        fork_attribute_name="tx_types",
        parameter_names=["tx_type"],
    ),
    CovariantDescriptor(
        marker_name="with_all_contract_creating_tx_types",
        description="marks a test to be parametrized for all tx types that can create a contract"
        " at parameter named tx_type of type int",
        fork_attribute_name="contract_creating_tx_types",
        parameter_names=["tx_type"],
    ),
    CovariantDescriptor(
        marker_name="with_all_precompiles",
        description="marks a test to be parametrized for all precompiles at parameter named"
        " precompile of type int",
        fork_attribute_name="precompiles",
        parameter_names=["precompile"],
    ),
    CovariantDescriptor(
        marker_name="with_all_evm_code_types",
        description="marks a test to be parametrized for all EVM code types at parameter named"
        " `evm_code_type` of type `EVMCodeType`, such as `LEGACY` and `EOF_V1`",
        fork_attribute_name="evm_code_types",
        parameter_names=["evm_code_type"],
    ),
    CovariantDescriptor(
        marker_name="with_all_call_opcodes",
        description="marks a test to be parametrized for all *CALL opcodes at parameter named"
        " call_opcode, and also the appropriate EVM code type at parameter named evm_code_type",
        fork_attribute_name="call_opcodes",
        parameter_names=["call_opcode", "evm_code_type"],
    ),
    CovariantDescriptor(
        marker_name="with_all_create_opcodes",
        description="marks a test to be parametrized for all *CREATE* opcodes at parameter named"
        " create_opcode, and also the appropriate EVM code type at parameter named evm_code_type",
        fork_attribute_name="create_opcodes",
        parameter_names=["create_opcode", "evm_code_type"],
    ),
    CovariantDescriptor(
        marker_name="with_all_system_contracts",
        description="marks a test to be parametrized for all system contracts at parameter named"
        " system_contract of type int",
        fork_attribute_name="system_contracts",
        parameter_names=["system_contract"],
    ),
]


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config):
    """
    Register the plugin's custom markers and process command-line options.

    Custom marker registration:
    https://docs.pytest.org/en/7.1.x/how-to/writing_plugins.html#registering-custom-markers
    """
    config.addinivalue_line(
        "markers",
        (
            "valid_at_transition_to(fork): specifies a test case is valid "
            "only at fork transition boundary to the specified fork"
        ),
    )
    config.addinivalue_line(
        "markers",
        "valid_from(fork): specifies from which fork a test case is valid",
    )
    config.addinivalue_line(
        "markers",
        "valid_until(fork): specifies until which fork a test case is valid",
    )

    for d in fork_covariant_descriptors:
        config.addinivalue_line("markers", f"{d.marker_name}: {d.description}")

    forks = set([fork for fork in get_forks() if not fork.ignore()])
    config.forks = forks  # type: ignore
    config.fork_names = set([fork.name() for fork in sorted(list(forks))])  # type: ignore
    config.forks_by_name = {fork.name(): fork for fork in forks}  # type: ignore

    available_forks_help = textwrap.dedent(
        f"""\
        Available forks:
        {", ".join(fork.name() for fork in forks)}
        """
    )
    available_forks_help += textwrap.dedent(
        f"""\
        Available transition forks:
        {", ".join([fork.name() for fork in get_transition_forks()])}
        """
    )

    def get_fork_option(config, option_name: str, parameter_name: str) -> Set[Fork]:
        """Post-process get option to allow for external fork conditions."""
        config_str = config.getoption(option_name)
        if not config_str:
            return set()
        forks_str = config_str.split(",")
        for i in range(len(forks_str)):
            forks_str[i] = forks_str[i].strip()
            if forks_str[i] == "Merge":
                forks_str[i] = "Paris"

        resulting_forks = set()

        for fork in get_forks():
            if fork.name() in forks_str:
                resulting_forks.add(fork)

        if len(resulting_forks) != len(forks_str):
            print(
                f"Error: Unsupported fork provided to {parameter_name}:",
                config_str,
                "\n",
                file=sys.stderr,
            )
            print(available_forks_help, file=sys.stderr)
            pytest.exit("Invalid command-line options.", returncode=pytest.ExitCode.USAGE_ERROR)

        return resulting_forks

    single_fork = get_fork_option(config, "single_fork", "--fork")
    forks_from = get_fork_option(config, "forks_from", "--from")
    forks_until = get_fork_option(config, "forks_until", "--until")
    show_fork_help = config.getoption("show_fork_help")

    dev_forks_help = textwrap.dedent(
        "To run tests for a fork under active development, it must be "
        "specified explicitly via --forks-until=FORK.\n"
        "Tests are only ran for deployed mainnet forks by default, i.e., "
        f"until {get_deployed_forks()[-1].name()}.\n"
    )
    if show_fork_help:
        print(available_forks_help)
        print(dev_forks_help)
        pytest.exit("After displaying help.", returncode=0)

    if single_fork and (forks_from or forks_until):
        print(
            "Error: --fork cannot be used in combination with --from or --until", file=sys.stderr
        )
        pytest.exit("Invalid command-line options.", returncode=pytest.ExitCode.USAGE_ERROR)

    if single_fork:
        forks_from = single_fork
        forks_until = single_fork
    else:
        if not forks_from:
            forks_from = get_forks_with_no_parents(forks)
        if not forks_until:
            forks_until = get_last_descendants(set(get_deployed_forks()), forks_from)

    fork_set = get_from_until_fork_set(forks, forks_from, forks_until)
    config.fork_set = fork_set  # type: ignore

    if not fork_set:
        print(
            f"Error: --from {','.join(fork.name() for fork in forks_from)} "
            f"--until {','.join(fork.name() for fork in forks_until)} "
            "creates an empty fork range.",
            file=sys.stderr,
        )
        pytest.exit(
            "Command-line options produce empty fork range.",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )

    # with --collect-only, we don't have access to these config options
    config.unsupported_forks: Set[Fork] = set()  # type: ignore
    if config.option.collectonly:
        return

    evm_bin = config.getoption("evm_bin")
    t8n = TransitionTool.from_binary_path(binary_path=evm_bin)
    config.unsupported_forks = frozenset(  # type: ignore
        filter(lambda fork: not t8n.is_fork_supported(fork), fork_set)
    )


@pytest.hookimpl(trylast=True)
def pytest_report_header(config, start_path):
    """A pytest hook called to obtain the report header."""
    bold = "\033[1m"
    warning = "\033[93m"
    reset = "\033[39;49m"
    header = [
        (
            bold
            + "Executing tests for: "
            + ", ".join([f.name() for f in sorted(list(config.fork_set))])
            + reset
        ),
    ]
    if all(fork.is_deployed() for fork in config.fork_set):
        header += [
            (
                bold + warning + "Only executing tests with stable/deployed forks: "
                "Specify an upcoming fork via --until=fork to "
                "add forks under development." + reset
            )
        ]
    return header


@pytest.fixture(autouse=True)
def fork(request):
    """
    Parametrize test cases by fork.
    """
    pass


def get_validity_marker_args(
    metafunc: Metafunc,
    validity_marker_name: str,
    test_name: str,
) -> Set[Fork]:
    """Check and return the arguments specified to validity markers.

    Check that the validity markers:

    - `pytest.mark.valid_from`
    - `pytest.mark.valid_until`
    - `pytest.mark.valid_at_transition_to`

    are applied at most once and have been provided with exactly one
    argument which is a valid fork name.

    Args:
        metafunc: Pytest's metafunc object.
        validity_marker_name: Name of the validity marker to validate
            and return.
        test_name: The name of the test being parametrized by
            `pytest_generate_tests`.

    Returns:
        The name of the fork specified to the validity marker.
    """
    validity_markers = [
        marker for marker in metafunc.definition.iter_markers(validity_marker_name)
    ]
    if not validity_markers:
        return set()
    if len(validity_markers) > 1:
        pytest.fail(f"'{test_name}': Too many '{validity_marker_name}' markers applied to test. ")
    if len(validity_markers[0].args) == 0:
        pytest.fail(f"'{test_name}': Missing fork argument with '{validity_marker_name}' marker. ")
    if len(validity_markers[0].args) > 1:
        pytest.fail(
            f"'{test_name}': Too many arguments specified to '{validity_marker_name}' marker. "
        )
    fork_names_string = validity_markers[0].args[0]
    fork_names = fork_names_string.split(",")
    resulting_set: Set[Fork] = set()
    for fork_name in fork_names:  # type: ignore
        if fork_name not in metafunc.config.fork_names:  # type: ignore
            pytest.fail(
                f"'{test_name}' specifies an invalid fork '{fork_names_string}' to the "
                f"'{validity_marker_name}'. "
                "List of valid forks: "
                ", ".join(name for name in metafunc.config.fork_names)  # type: ignore
            )

        resulting_set.add(metafunc.config.forks_by_name[fork_name])  # type: ignore

    return resulting_set


def pytest_generate_tests(metafunc: pytest.Metafunc):
    """
    Pytest hook used to dynamically generate test cases.
    """
    test_name = metafunc.function.__name__
    valid_at_transition_to = get_validity_marker_args(
        metafunc, "valid_at_transition_to", test_name
    )
    valid_from = get_validity_marker_args(metafunc, "valid_from", test_name)
    valid_until = get_validity_marker_args(metafunc, "valid_until", test_name)

    if valid_at_transition_to and valid_from:
        pytest.fail(
            f"'{test_name}': "
            "The markers 'valid_from' and 'valid_at_transition_to' can't be combined. "
        )
    if valid_at_transition_to and valid_until:
        pytest.fail(
            f"'{test_name}': "
            "The markers 'valid_until' and 'valid_at_transition_to' can't be combined. "
        )

    fork_set: Set[Fork] = metafunc.config.fork_set  # type: ignore
    forks: Set[Fork] = metafunc.config.forks  # type: ignore

    intersection_set: Set[Fork] = set()
    if valid_at_transition_to:
        for fork in valid_at_transition_to:
            if fork in fork_set:
                intersection_set = intersection_set | set(transition_fork_to(fork))

    else:
        if not valid_from:
            valid_from = get_forks_with_no_parents(forks)

        if not valid_until:
            valid_until = get_last_descendants(forks, valid_from)

        test_fork_set = get_from_until_fork_set(forks, valid_from, valid_until)

        if not test_fork_set:
            pytest.fail(
                "The test function's "
                f"'{test_name}' fork validity markers generate "
                "an empty fork range. Please check the arguments to its "
                f"markers:  @pytest.mark.valid_from ({valid_from}) and "
                f"@pytest.mark.valid_until ({valid_until})."
            )

        intersection_set = fork_set & test_fork_set

    pytest_params: List[Any]
    if "fork" in metafunc.fixturenames:
        if not intersection_set:
            if metafunc.config.getoption("verbose") >= 2:
                pytest_params = [
                    pytest.param(
                        None,
                        marks=[
                            pytest.mark.skip(
                                reason=(
                                    f"{test_name} is not valid for any any of forks specified on "
                                    "the command-line."
                                )
                            )
                        ],
                    )
                ]
                metafunc.parametrize("fork", pytest_params, scope="function")
        else:
            unsupported_forks: Set[Fork] = metafunc.config.unsupported_forks  # type: ignore
            pytest_params = [
                (
                    ForkParametrizer(
                        fork=fork,
                        marks=[
                            pytest.mark.skip(
                                reason=(
                                    f"Fork '{fork}' unsupported by "
                                    f"'{metafunc.config.getoption('evm_bin')}'."
                                )
                            )
                        ],
                    )
                    if fork in sorted(list(unsupported_forks))
                    else ForkParametrizer(fork=fork)
                )
                for fork in sorted(list(intersection_set))
            ]
            add_fork_covariant_parameters(metafunc, pytest_params)
            parametrize_fork(metafunc, pytest_params)


def add_fork_covariant_parameters(
    metafunc: Metafunc, fork_parametrizers: List[ForkParametrizer]
) -> None:
    """
    Iterate over the fork covariant descriptors and add their values to the test function.
    """
    for covariant_descriptor in fork_covariant_descriptors:
        for fork_parametrizer in fork_parametrizers:
            covariant_descriptor.add_values(metafunc=metafunc, fork_parametrizer=fork_parametrizer)


def parameters_from_fork_parametrizer_list(
    fork_parametrizers: List[ForkParametrizer],
) -> Tuple[List[str], List[ParameterSet]]:
    """
    Get the parameters from the fork parametrizers.
    """
    param_names: List[str] = []
    param_values: List[ParameterSet] = []

    for fork_parametrizer in fork_parametrizers:
        if not param_names:
            param_names = fork_parametrizer.parameter_names
        else:
            assert param_names == fork_parametrizer.parameter_names
        param_values.extend(fork_parametrizer.parameter_values)

    # Remove duplicate parameters
    param_1 = 0
    while param_1 < len(param_names):
        param_2 = param_1 + 1
        while param_2 < len(param_names):
            if param_names[param_1] == param_names[param_2]:
                i = 0
                while i < len(param_values):
                    if param_values[i].values[param_1] != param_values[i].values[param_2]:
                        del param_values[i]
                    else:
                        param_values[i] = pytest.param(
                            *param_values[i].values[:param_2],
                            *param_values[i].values[(param_2 + 1) :],
                            id=param_values[i].id,
                            marks=param_values[i].marks,
                        )
                        i += 1

                del param_names[param_2]
            else:
                param_2 += 1
        param_1 += 1

    return param_names, param_values


def parametrize_fork(metafunc: Metafunc, fork_parametrizers: List[ForkParametrizer]) -> None:
    """
    Add the fork parameters to the test function.
    """
    metafunc.parametrize(
        *parameters_from_fork_parametrizer_list(fork_parametrizers), scope="function"
    )
