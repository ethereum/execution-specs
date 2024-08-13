"""
Pytest plugin to enable fork range configuration for the test session.
"""

import itertools
import sys
import textwrap
from dataclasses import dataclass, field
from typing import Any, List, Set

import pytest
from pytest import Metafunc

from ethereum_test_forks import (
    Fork,
    ForkAttribute,
    get_deployed_forks,
    get_forks,
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
class ForkCovariantParameter:
    """
    Value list for a fork covariant parameter in a given fork.
    """

    name: str
    values: List[Any]


@dataclass(kw_only=True)
class ForkParametrizer:
    """
    A parametrizer for a test case that is parametrized by the fork.
    """

    fork: Fork
    mark: pytest.MarkDecorator | None = None
    fork_covariant_parameters: List[ForkCovariantParameter] = field(default_factory=list)

    def get_parameter_names(self) -> List[str]:
        """
        Return the parameter names for the test case.
        """
        parameter_names = ["fork"]
        for p in self.fork_covariant_parameters:
            if "," in p.name:
                parameter_names.extend(p.name.split(","))
            else:
                parameter_names.append(p.name)
        return parameter_names

    def get_parameter_values(self) -> List[Any]:
        """
        Return the parameter values for the test case.
        """
        param_value_combinations = [
            params
            for params in itertools.product(
                [self.fork],
                *[p.values for p in self.fork_covariant_parameters],
            )
        ]
        for i in range(len(param_value_combinations)):
            # if the parameter is a tuple, we need to flatten it
            param_value_combinations[i] = list(
                itertools.chain.from_iterable(
                    [v] if not isinstance(v, tuple) else v for v in param_value_combinations[i]
                )
            )
        return [
            pytest.param(*params, marks=[self.mark] if self.mark else [])
            for params in param_value_combinations
        ]


@dataclass(kw_only=True)
class CovariantDescriptor:
    """
    A descriptor for a parameter that is covariant with the fork:
    the parametrized values change depending on the fork.
    """

    marker_name: str
    description: str
    fork_attribute_name: str
    parameter_name: str

    def check_enabled(self, metafunc: Metafunc) -> bool:
        """
        Check if the marker is enabled for the given test function.
        """
        m = metafunc.definition.iter_markers(self.marker_name)
        return m is not None and len(list(m)) > 0

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
        fork_parametrizer.fork_covariant_parameters.append(
            ForkCovariantParameter(name=self.parameter_name, values=values)
        )


fork_covariant_descriptors = [
    CovariantDescriptor(
        marker_name="with_all_tx_types",
        description="marks a test to be parametrized for all tx types at parameter named tx_type"
        " of type int",
        fork_attribute_name="tx_types",
        parameter_name="tx_type",
    ),
    CovariantDescriptor(
        marker_name="with_all_contract_creating_tx_types",
        description="marks a test to be parametrized for all tx types that can create a contract"
        " at parameter named tx_type of type int",
        fork_attribute_name="contract_creating_tx_types",
        parameter_name="tx_type",
    ),
    CovariantDescriptor(
        marker_name="with_all_precompiles",
        description="marks a test to be parametrized for all precompiles at parameter named"
        " precompile of type int",
        fork_attribute_name="precompiles",
        parameter_name="precompile",
    ),
    CovariantDescriptor(
        marker_name="with_all_evm_code_types",
        description="marks a test to be parametrized for all EVM code types at parameter named"
        " `evm_code_type` of type `EVMCodeType`, such as `LEGACY` and `EOF_V1`",
        fork_attribute_name="evm_code_types",
        parameter_name="evm_code_type",
    ),
    CovariantDescriptor(
        marker_name="with_all_call_opcodes",
        description="marks a test to be parametrized for all *CALL opcodes at parameter named"
        " call_opcode, and also the appropriate EVM code type at parameter named evm_code_type",
        fork_attribute_name="call_opcodes",
        parameter_name="call_opcode,evm_code_type",
    ),
]


def get_from_until_fork_set(
    forks: Set[Fork], forks_from: Set[Fork], forks_until: Set[Fork]
) -> Set[Fork]:
    """
    Get the fork range from forks_from to forks_until.
    """
    resulting_set = set()
    for fork_from in forks_from:
        for fork_until in forks_until:
            for fork in forks:
                if fork <= fork_until and fork >= fork_from:
                    resulting_set.add(fork)
    return resulting_set


def get_forks_with_no_parents(forks: Set[Fork]) -> Set[Fork]:
    """
    Get the forks with no parents in the inheritance hierarchy.
    """
    resulting_forks: Set[Fork] = set()
    for fork in forks:
        parents = False
        for next_fork in forks - {fork}:
            if next_fork < fork:
                parents = True
                break
        if not parents:
            resulting_forks = resulting_forks | {fork}
    return resulting_forks


def get_forks_with_no_descendants(forks: Set[Fork]) -> Set[Fork]:
    """
    Get the forks with no descendants in the inheritance hierarchy.
    """
    resulting_forks: Set[Fork] = set()
    for fork in forks:
        descendants = False
        for next_fork in forks - {fork}:
            if next_fork > fork:
                descendants = True
                break
        if not descendants:
            resulting_forks = resulting_forks | {fork}
    return resulting_forks


def get_last_descendants(forks: Set[Fork], forks_from: Set[Fork]) -> Set[Fork]:
    """
    Get the last descendant of a class in the inheritance hierarchy.
    """
    resulting_forks: Set[Fork] = set()
    forks = get_forks_with_no_descendants(forks)
    for fork_from in forks_from:
        for fork in forks:
            if fork >= fork_from:
                resulting_forks = resulting_forks | {fork}
    return resulting_forks


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
    config.unsupported_forks = filter(  # type: ignore
        lambda fork: not t8n.is_fork_supported(fork), fork_set
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
    if config.getoption("forks_until") is None:
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
                        mark=pytest.mark.skip(
                            reason=(
                                f"Fork '{fork}' unsupported by "
                                f"'{metafunc.config.getoption('evm_bin')}'."
                            )
                        ),
                    )
                    if fork.name() in sorted(list(unsupported_forks))
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


def parametrize_fork(metafunc: Metafunc, fork_parametrizers: List[ForkParametrizer]) -> None:
    """
    Add the fork parameters to the test function.
    """
    param_names: List[str] = []
    param_values: List[Any] = []

    for fork_parametrizer in fork_parametrizers:
        if not param_names:
            param_names = fork_parametrizer.get_parameter_names()
        else:
            assert param_names == fork_parametrizer.get_parameter_names()
        param_values.extend(fork_parametrizer.get_parameter_values())
    metafunc.parametrize(param_names, param_values, scope="function")
