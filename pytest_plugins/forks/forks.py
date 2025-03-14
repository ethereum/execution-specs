"""Pytest plugin to enable fork range configuration for the test session."""

import itertools
import re
import sys
import textwrap
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from types import FunctionType
from typing import Any, Callable, ClassVar, Iterable, List, Mapping, Set, Tuple, Type

import pytest
from _pytest.mark.structures import ParameterSet
from pytest import Mark, Metafunc

from ethereum_clis import TransitionTool
from ethereum_test_forks import (
    Fork,
    get_deployed_forks,
    get_forks,
    get_forks_with_no_parents,
    get_from_until_fork_set,
    get_last_descendants,
    get_transition_forks,
    transition_fork_to,
)


def pytest_addoption(parser):
    """Add command-line options to pytest."""
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
    """Value list for a fork covariant parameter in a given fork."""

    names: List[str]
    values: List[ParameterSet]


class ForkParametrizer:
    """A parametrizer for a test case that is parametrized by the fork."""

    fork: Fork
    fork_covariant_parameters: List[ForkCovariantParameter] = field(default_factory=list)

    def __init__(
        self,
        fork: Fork,
        marks: List[pytest.MarkDecorator | pytest.Mark] | None = None,
        fork_covariant_parameters: List[ForkCovariantParameter] | None = None,
    ):
        """
        Initialize a new fork parametrizer object for a given fork.

        Args:
            fork: The fork for which the test cases will be parametrized.
            marks: A list of pytest marks to apply to all the test cases parametrized by the fork.
            fork_covariant_parameters: A list of fork covariant parameters for the test case, for
                unit testing purposes only.

        """
        if marks is None:
            marks = []
        self.fork_covariant_parameters = [
            ForkCovariantParameter(
                names=["fork"],
                values=[
                    pytest.param(
                        fork,
                        marks=marks,
                    )
                ],
            )
        ]
        if fork_covariant_parameters is not None:
            self.fork_covariant_parameters.extend(fork_covariant_parameters)
        self.fork = fork

    @property
    def argnames(self) -> List[str]:
        """Return the parameter names for the test case."""
        argnames = []
        for p in self.fork_covariant_parameters:
            argnames.extend(p.names)
        return argnames

    @property
    def argvalues(self) -> List[ParameterSet]:
        """Return the parameter values for the test case."""
        parameter_set_combinations = itertools.product(
            # Add the values for each parameter, all of them are lists of at least one element.
            *[p.values for p in self.fork_covariant_parameters],
        )

        parameter_set_list: List[ParameterSet] = []
        for parameter_set_combination in parameter_set_combinations:
            params: List[Any] = []
            marks: List[pytest.Mark | pytest.MarkDecorator] = []
            test_id: str | None = None
            for p in parameter_set_combination:
                assert isinstance(p, ParameterSet)
                params.extend(p.values)
                if p.marks:
                    marks.extend(p.marks)
                if p.id:
                    if test_id is None:
                        test_id = f"fork_{self.fork.name()}-{p.id}"
                    else:
                        test_id = f"{test_id}-{p.id}"
            parameter_set_list.append(pytest.param(*params, marks=marks, id=test_id))

        return parameter_set_list


class CovariantDescriptor:
    """
    A descriptor for a parameter that is covariant with the fork:
    the parametrized values change depending on the fork.
    """

    argnames: List[str] = []
    fn: Callable[[Fork], List[Any] | Iterable[Any]] | None = None

    selector: FunctionType | None = None
    marks: None | pytest.Mark | pytest.MarkDecorator | List[pytest.Mark | pytest.MarkDecorator] = (
        None
    )

    def __init__(
        self,
        argnames: List[str] | str,
        fn: Callable[[Fork], List[Any] | Iterable[Any]] | None = None,
        *,
        selector: FunctionType | None = None,
        marks: None
        | pytest.Mark
        | pytest.MarkDecorator
        | List[pytest.Mark | pytest.MarkDecorator] = None,
    ):
        """
        Initialize a new covariant descriptor.

        Args:
            argnames: The names of the parameters that are covariant with the fork.
            fn: A function that takes the fork as the single parameter and returns the values for
                the parameter for each fork.
            selector: A function that filters the values for the parameter.
            marks: A list of pytest marks to apply to the test cases parametrized by the parameter.

        """
        self.argnames = (
            [argname.strip() for argname in argnames.split(",")]
            if isinstance(argnames, str)
            else argnames
        )
        self.fn = fn
        self.selector = selector
        self.marks = marks

    def process_value(
        self,
        parameters_values: Any | List[Any] | Tuple[Any] | ParameterSet,
    ) -> ParameterSet | None:
        """
        Process a value for a covariant parameter.

        The `selector` is applied to parameters_values in order to filter them.
        """
        if isinstance(parameters_values, ParameterSet):
            return parameters_values

        if len(self.argnames) == 1:
            # Wrap values that are meant for a single parameter in a list
            parameters_values = [parameters_values]
        marks = self.marks
        if self.selector is None or self.selector(
            *parameters_values[: self.selector.__code__.co_argcount]  # type: ignore
        ):
            if isinstance(marks, FunctionType):
                marks = marks(*parameters_values[: marks.__code__.co_argcount])
            assert not isinstance(marks, FunctionType), "marks must be a list or None"
            if marks is None:
                marks = []
            elif not isinstance(marks, list):
                marks = [marks]  # type: ignore

            return pytest.param(*parameters_values, marks=marks)

        return None

    def process_values(self, values: Iterable[Any]) -> List[ParameterSet]:
        """
        Filter the values for the covariant parameter.

        I.e. if the marker has an argument, the argument is interpreted as a lambda function
        that filters the values.
        """
        processed_values: List[ParameterSet] = []
        for value in values:
            processed_value = self.process_value(value)
            if processed_value is not None:
                processed_values.append(processed_value)
        return processed_values

    def add_values(self, fork_parametrizer: ForkParametrizer) -> None:
        """Add the values for the covariant parameter to the parametrizer."""
        if self.fn is None:
            return
        fork = fork_parametrizer.fork
        values = self.fn(fork)
        values = self.process_values(values)
        assert len(values) > 0
        fork_parametrizer.fork_covariant_parameters.append(
            ForkCovariantParameter(names=self.argnames, values=values)
        )


class CovariantDecorator(CovariantDescriptor):
    """
    A marker used to parametrize a function by a covariant parameter with the values
    returned by a fork method.

    The decorator must be subclassed with the appropriate class variables before initialization.

    Attributes:
        marker_name: Name of the marker.
        description: Description of the marker.
        fork_attribute_name: Name of the method to call on the fork to get the values.
        marker_parameter_names: Names of the parameters to be parametrized in the test function.

    """

    marker_name: ClassVar[str]
    description: ClassVar[str]
    fork_attribute_name: ClassVar[str]
    marker_parameter_names: ClassVar[List[str]]

    def __init__(self, metafunc: Metafunc):
        """
        Initialize the covariant decorator.

        The decorator must already be subclassed with the appropriate class variables before
        initialization.

        Args:
            metafunc: The metafunc object that pytest uses when generating tests.

        """
        self.metafunc = metafunc

        m = metafunc.definition.iter_markers(self.marker_name)
        if m is None:
            return
        marker_list = list(m)
        assert len(marker_list) <= 1, f"Multiple markers {self.marker_name} found"
        if len(marker_list) == 0:
            return
        marker = marker_list[0]

        assert marker is not None
        assert len(marker.args) == 0, "Only keyword arguments are supported"

        kwargs = dict(marker.kwargs)

        selector = kwargs.pop("selector", lambda _: True)
        assert isinstance(selector, FunctionType), "selector must be a function"

        marks = kwargs.pop("marks", None)

        if len(kwargs) > 0:
            raise ValueError(f"Unknown arguments to {self.marker_name}: {kwargs}")

        def fn(fork: Fork) -> List[Any]:
            return getattr(fork, self.fork_attribute_name)(block_number=0, timestamp=0)

        super().__init__(
            argnames=self.marker_parameter_names,
            fn=fn,
            selector=selector,
            marks=marks,
        )


def covariant_decorator(
    *,
    marker_name: str,
    description: str,
    fork_attribute_name: str,
    argnames: List[str],
) -> Type[CovariantDecorator]:
    """Generate a new covariant decorator subclass."""
    return type(
        marker_name,
        (CovariantDecorator,),
        {
            "marker_name": marker_name,
            "description": description,
            "fork_attribute_name": fork_attribute_name,
            "marker_parameter_names": argnames,
        },
    )


fork_covariant_decorators: List[Type[CovariantDecorator]] = [
    covariant_decorator(
        marker_name="with_all_tx_types",
        description="marks a test to be parametrized for all tx types at parameter named tx_type"
        " of type int",
        fork_attribute_name="tx_types",
        argnames=["tx_type"],
    ),
    covariant_decorator(
        marker_name="with_all_contract_creating_tx_types",
        description="marks a test to be parametrized for all tx types that can create a contract"
        " at parameter named tx_type of type int",
        fork_attribute_name="contract_creating_tx_types",
        argnames=["tx_type"],
    ),
    covariant_decorator(
        marker_name="with_all_precompiles",
        description="marks a test to be parametrized for all precompiles at parameter named"
        " precompile of type int",
        fork_attribute_name="precompiles",
        argnames=["precompile"],
    ),
    covariant_decorator(
        marker_name="with_all_evm_code_types",
        description="marks a test to be parametrized for all EVM code types at parameter named"
        " `evm_code_type` of type `EVMCodeType`, such as `LEGACY` and `EOF_V1`",
        fork_attribute_name="evm_code_types",
        argnames=["evm_code_type"],
    ),
    covariant_decorator(
        marker_name="with_all_call_opcodes",
        description="marks a test to be parametrized for all *CALL opcodes at parameter named"
        " call_opcode, and also the appropriate EVM code type at parameter named evm_code_type",
        fork_attribute_name="call_opcodes",
        argnames=["call_opcode", "evm_code_type"],
    ),
    covariant_decorator(
        marker_name="with_all_create_opcodes",
        description="marks a test to be parametrized for all *CREATE* opcodes at parameter named"
        " create_opcode, and also the appropriate EVM code type at parameter named evm_code_type",
        fork_attribute_name="create_opcodes",
        argnames=["create_opcode", "evm_code_type"],
    ),
    covariant_decorator(
        marker_name="with_all_system_contracts",
        description="marks a test to be parametrized for all system contracts at parameter named"
        " system_contract of type int",
        fork_attribute_name="system_contracts",
        argnames=["system_contract"],
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
            "valid_at_transition_to(fork, subsequent_forks: bool = False, "
            "until: str | None = None): specifies a test case is only valid "
            "at the specified fork transition boundaries"
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
    config.addinivalue_line(
        "markers",
        (
            "parametrize_by_fork(names, values_fn): parametrize a test case by fork using the "
            "specified names and values returned by the function values_fn(fork)"
        ),
    )
    for d in fork_covariant_decorators:
        config.addinivalue_line("markers", f"{d.marker_name}: {d.description}")

    forks = {fork for fork in get_forks() if not fork.ignore()}
    config.all_forks = forks  # type: ignore
    config.all_forks_by_name = {fork.name(): fork for fork in forks}  # type: ignore
    config.all_forks_with_transitions = {  # type: ignore
        fork for fork in set(get_forks()) | get_transition_forks() if not fork.ignore()
    }

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
        forks_str = [s.strip() for s in config_str.split(",")]
        # Alias for "Merge"
        forks_str = [("Paris" if s.lower() == "merge" else s) for s in forks_str]

        resulting_forks = set()
        for fork in config.all_forks_with_transitions:
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
        "specified explicitly via --until=FORK.\n"
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
        selected_fork_set = single_fork
    else:
        if not forks_from:
            forks_from = get_forks_with_no_parents(forks)
        if not forks_until:
            forks_until = get_last_descendants(set(get_deployed_forks()), forks_from)
        selected_fork_set = get_from_until_fork_set(forks, forks_from, forks_until)
        for fork in list(selected_fork_set):
            transition_fork_set = transition_fork_to(fork)
            selected_fork_set |= transition_fork_set

    config.selected_fork_set = selected_fork_set  # type: ignore

    if not selected_fork_set:
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

    evm_bin = config.getoption("evm_bin", None)
    if evm_bin is not None:
        t8n = TransitionTool.from_binary_path(binary_path=evm_bin)
        config.unsupported_forks = frozenset(  # type: ignore
            fork for fork in selected_fork_set if not t8n.is_fork_supported(fork)
        )


@pytest.hookimpl(trylast=True)
def pytest_report_header(config, start_path):
    """Pytest hook called to obtain the report header."""
    bold = "\033[1m"
    warning = "\033[93m"
    reset = "\033[39;49m"
    header = [
        (
            bold
            + "Generating fixtures for: "
            + ", ".join([f.name() for f in sorted(config.selected_fork_set)])
            + reset
        ),
    ]
    if all(fork.is_deployed() for fork in config.selected_fork_set):
        header += [
            (
                bold + warning + "Only generating fixtures with stable/deployed forks: "
                "Specify an upcoming fork via --until=fork to "
                "add forks under development." + reset
            )
        ]
    return header


@pytest.fixture(autouse=True)
def fork(request):
    """Parametrize test cases by fork."""
    pass


ALL_VALIDITY_MARKERS: List["Type[ValidityMarker]"] = []

MARKER_NAME_REGEX = re.compile(r"(?<!^)(?=[A-Z])")


@dataclass(kw_only=True)
class ValidityMarker(ABC):
    """
    Abstract class to represent any fork validity marker.

    Subclassing this class allows for the creation of new validity markers.

    Instantiation must be done per test function, and the `process` method must be called to
    process the fork arguments.

    When subclassing, the following optional parameters can be set:
    - marker_name: Name of the marker, if not set, the class name is converted to underscore.
    - mutually_exclusive: Whether the marker must be used in isolation.
    """

    marker_name: ClassVar[str]
    mutually_exclusive: ClassVar[bool]

    test_name: str
    all_forks: Set[Fork]
    all_forks_by_name: Mapping[str, Fork]
    mark: Mark

    def __init_subclass__(
        cls, *, marker_name: str | None = None, mutually_exclusive=False
    ) -> None:
        """Register the validity marker subclass."""
        super().__init_subclass__()
        if marker_name is not None:
            cls.marker_name = marker_name
        else:
            # Use the class name converted to underscore: https://stackoverflow.com/a/1176023
            cls.marker_name = MARKER_NAME_REGEX.sub("_", cls.__name__).lower()
        cls.mutually_exclusive = mutually_exclusive
        if cls in ALL_VALIDITY_MARKERS:
            raise ValueError(f"Duplicate validity marker class: {cls}")
        ALL_VALIDITY_MARKERS.append(cls)

    def process_fork_arguments(self, *fork_args: str) -> Set[Fork]:
        """Process the fork arguments."""
        fork_names: Set[str] = set()
        for fork_arg in fork_args:
            fork_names_list = fork_arg.strip().split(",")
            expected_length_after_append = len(fork_names) + len(fork_names_list)
            fork_names |= set(fork_names_list)
            if len(fork_names) != expected_length_after_append:
                pytest.fail(
                    f"'{self.test_name}': Duplicate argument specified in '{self.marker_name}'."
                )
        forks: Set[Fork] = set()
        for fork_name in fork_names:
            if fork_name not in self.all_forks_by_name:
                pytest.fail(f"'{self.test_name}': Invalid fork '{fork_name}' specified.")
            forks.add(self.all_forks_by_name[fork_name])
        return forks

    @classmethod
    def get_validity_marker(cls, metafunc: Metafunc) -> "ValidityMarker | None":
        """
        Instantiate a validity marker for the test function.

        If the test function does not contain the marker, return None.
        """
        test_name = metafunc.function.__name__
        validity_markers = list(metafunc.definition.iter_markers(cls.marker_name))
        if not validity_markers:
            return None

        if len(validity_markers) > 1:
            pytest.fail(f"'{test_name}': Too many '{cls.marker_name}' markers applied to test. ")
        mark = validity_markers[0]
        if len(mark.args) == 0:
            pytest.fail(f"'{test_name}': Missing fork argument with '{cls.marker_name}' marker. ")

        all_forks_by_name: Mapping[str, Fork] = metafunc.config.all_forks_by_name  # type: ignore
        all_forks: Set[Fork] = metafunc.config.all_forks  # type: ignore

        return cls(
            test_name=test_name,
            all_forks_by_name=all_forks_by_name,
            all_forks=all_forks,
            mark=mark,
        )

    @staticmethod
    def get_all_validity_markers(metafunc: Metafunc) -> List["ValidityMarker"]:
        """Get all the validity markers applied to the test function."""
        test_name = metafunc.function.__name__

        validity_markers: List[ValidityMarker] = []
        for validity_marker_class in ALL_VALIDITY_MARKERS:
            if validity_marker := validity_marker_class.get_validity_marker(metafunc):
                validity_markers.append(validity_marker)

        if len(validity_markers) > 1:
            mutually_exclusive_markers = [
                validity_marker
                for validity_marker in validity_markers
                if validity_marker.mutually_exclusive
            ]
            if mutually_exclusive_markers:
                names = [
                    f"'{validity_marker.marker_name}'" for validity_marker in validity_markers
                ]
                concatenated_names = " and ".join([", ".join(names[:-1])] + names[-1:])
                pytest.fail(f"'{test_name}': The markers {concatenated_names} can't be combined. ")

        return validity_markers

    def process(self) -> Set[Fork]:
        """Process the fork arguments."""
        return self._process_with_marker_args(*self.mark.args, **self.mark.kwargs)

    @abstractmethod
    def _process_with_marker_args(self, *args, **kwargs) -> Set[Fork]:
        """
        Process the fork arguments as specified for the marker.

        Method must be implemented by the subclass.
        """
        pass


class ValidFrom(ValidityMarker):
    """
    Marker used to specify the fork from which the test is valid. The test will not be filled for
    forks before the specified fork.

    ```python
    import pytest

    from ethereum_test_tools import Alloc, StateTestFiller

    @pytest.mark.valid_from("London")
    def test_something_only_valid_after_london(
        state_test: StateTestFiller,
        pre: Alloc
    ):
        pass
    ```

    In this example, the test will only be filled for the London fork and after, e.g. London,
    Paris, Shanghai, Cancun, etc.
    """

    def _process_with_marker_args(self, *fork_args) -> Set[Fork]:
        """Process the fork arguments."""
        forks: Set[Fork] = self.process_fork_arguments(*fork_args)
        resulting_set: Set[Fork] = set()
        for fork in forks:
            resulting_set |= {f for f in self.all_forks if f >= fork}
        return resulting_set


class ValidUntil(ValidityMarker):
    """
    Marker to specify the fork until which the test is valid. The test will not be filled for
    forks after the specified fork.

    ```python
    import pytest

    from ethereum_test_tools import Alloc, StateTestFiller

    @pytest.mark.valid_until("London")
    def test_something_only_valid_until_london(
        state_test: StateTestFiller,
        pre: Alloc
    ):
        pass
    ```

    In this example, the test will only be filled for the London fork and before, e.g. London,
    Berlin, Istanbul, etc.
    """

    def _process_with_marker_args(self, *fork_args) -> Set[Fork]:
        """Process the fork arguments."""
        forks: Set[Fork] = self.process_fork_arguments(*fork_args)
        resulting_set: Set[Fork] = set()
        for fork in forks:
            resulting_set |= {f for f in self.all_forks if f <= fork}
        return resulting_set


class ValidAtTransitionTo(ValidityMarker, mutually_exclusive=True):
    """
    Marker to specify that a test is only meant to be filled at the transition to the specified
    fork.

    The test usually starts at the fork prior to the specified fork at genesis and at block 5 (for
    pre-merge forks) or at timestamp 15,000 (for post-merge forks) the fork transition occurs.

    ```python
    import pytest

    from ethereum_test_tools import Alloc, BlockchainTestFiller

    @pytest.mark.valid_at_transition_to("London")
    def test_something_that_happens_during_the_fork_transition_to_london(
        blockchain_test: BlockchainTestFiller,
        pre: Alloc
    ):
        pass
    ```

    In this example, the test will only be filled for the fork that transitions to London at block
    number 5, `BerlinToLondonAt5`, and no other forks.

    To see or add a new transition fork, see the `ethereum_test_forks.forks.transition` module.

    Note that the test uses a `BlockchainTestFiller` fixture instead of a `StateTestFiller`,
    as the transition forks are used to test changes throughout the blockchain progression, and
    not just the state change of a single transaction.

    This marker also accepts the following keyword arguments:

    - `subsequent_transitions`: Force the test to also fill for subsequent fork transitions.
    - `until`: Implies `subsequent_transitions` and puts a limit on which transition fork will the
        test filling will be limited to.

    For example:
    ```python
    @pytest.mark.valid_at_transition_to("Cancun", subsequent_transitions=True)
    ```

    produces tests on `ShanghaiToCancunAtTime15k` and `CancunToPragueAtTime15k`, and any transition
    fork after that.

    And:
    ```python
    @pytest.mark.valid_at_transition_to("Cancun", subsequent_transitions=True, until="Prague")
    ```

    produces tests on `ShanghaiToCancunAtTime15k` and `CancunToPragueAtTime15k`, but no forks after
    Prague.
    """

    def _process_with_marker_args(
        self, *fork_args, subsequent_forks: bool = False, until: str | None = None
    ) -> Set[Fork]:
        """Process the fork arguments."""
        forks: Set[Fork] = self.process_fork_arguments(*fork_args)
        until_forks: Set[Fork] | None = (
            None if until is None else self.process_fork_arguments(until)
        )
        if len(forks) == 0:
            pytest.fail(
                f"'{self.test_name}': Missing fork argument with 'valid_at_transition_to' marker."
            )

        if len(forks) > 1:
            pytest.fail(
                f"'{self.test_name}': Too many forks specified to 'valid_at_transition_to' marker."
            )

        resulting_set: Set[Fork] = set()
        for fork in forks:
            resulting_set |= transition_fork_to(fork)
            if subsequent_forks:
                for transition_forks in (
                    transition_fork_to(f) for f in self.all_forks if f > fork
                ):
                    for transition_fork in transition_forks:
                        if transition_fork and (
                            until_forks is None
                            or any(transition_fork <= until_fork for until_fork in until_forks)
                        ):
                            resulting_set.add(transition_fork)
        return resulting_set


def pytest_generate_tests(metafunc: pytest.Metafunc):
    """Pytest hook used to dynamically generate test cases."""
    test_name = metafunc.function.__name__

    validity_markers: List[ValidityMarker] = ValidityMarker.get_all_validity_markers(metafunc)

    if not validity_markers:
        # Limit to non-transition forks if no validity markers were applied
        test_fork_set: Set[Fork] = metafunc.config.all_forks  # type: ignore
    else:
        # Start with all forks and transitions if any validity markers were applied
        test_fork_set: Set[Fork] = metafunc.config.all_forks_with_transitions  # type: ignore
        for validity_marker in validity_markers:
            # Apply the validity markers to the test function if applicable
            test_fork_set = test_fork_set & validity_marker.process()

    if not test_fork_set:
        pytest.fail(
            "The test function's "
            f"'{test_name}' fork validity markers generate "
            "an empty fork range. Please check the arguments to its "
            f"markers:  @pytest.mark.valid_from and "
            f"@pytest.mark.valid_until."
        )

    intersection_set = test_fork_set & metafunc.config.selected_fork_set  # type: ignore

    if "fork" not in metafunc.fixturenames:
        return

    pytest_params: List[Any]
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
                if fork in sorted(unsupported_forks)
                else ForkParametrizer(fork=fork)
            )
            for fork in sorted(intersection_set)
        ]
        add_fork_covariant_parameters(metafunc, pytest_params)
        parametrize_fork(metafunc, pytest_params)


def add_fork_covariant_parameters(
    metafunc: Metafunc, fork_parametrizers: List[ForkParametrizer]
) -> None:
    """Iterate over the fork covariant descriptors and add their values to the test function."""
    for covariant_descriptor in fork_covariant_decorators:
        for fork_parametrizer in fork_parametrizers:
            covariant_descriptor(metafunc=metafunc).add_values(fork_parametrizer=fork_parametrizer)

    for marker in metafunc.definition.iter_markers():
        if marker.name == "parametrize_by_fork":
            descriptor = CovariantDescriptor(
                *marker.args,
                **marker.kwargs,
            )
            for fork_parametrizer in fork_parametrizers:
                descriptor.add_values(fork_parametrizer=fork_parametrizer)


def parameters_from_fork_parametrizer_list(
    fork_parametrizers: List[ForkParametrizer],
) -> Tuple[List[str], List[ParameterSet]]:
    """Get the parameters from the fork parametrizers."""
    param_names: List[str] = []
    param_values: List[ParameterSet] = []

    for fork_parametrizer in fork_parametrizers:
        if not param_names:
            param_names = fork_parametrizer.argnames
        else:
            assert param_names == fork_parametrizer.argnames
        param_values.extend(fork_parametrizer.argvalues)

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
    """Add the fork parameters to the test function."""
    metafunc.parametrize(
        *parameters_from_fork_parametrizer_list(fork_parametrizers), scope="function"
    )
