"""
Pytest plugin to enable fork range configuration for the test session.
"""
import sys
import textwrap

import pytest
from pytest import Metafunc

from ethereum_test_forks import (
    forks_from_until,
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


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
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

    single_fork = config.getoption("single_fork")
    forks_from = config.getoption("forks_from")
    forks_until = config.getoption("forks_until")
    show_fork_help = config.getoption("show_fork_help")

    all_forks = get_forks()
    # TODO: Tricky, this removes the *Glacier forks.
    config.all_forks = forks_from_until(all_forks[0], all_forks[-1])
    config.fork_map = {fork.name(): fork for fork in config.all_forks}
    config.fork_names = list(config.fork_map.keys())

    available_forks_help = textwrap.dedent(
        f"""\
        Available forks:
        {", ".join(config.fork_names)}
        """
    )
    available_forks_help += textwrap.dedent(
        f"""\
        Available transition forks:
        {", ".join([fork.name() for fork in get_transition_forks()])}
        """
    )
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

    if single_fork and single_fork not in config.fork_map.keys():
        print("Error: Unsupported fork provided to --fork:", single_fork, "\n", file=sys.stderr)
        print(available_forks_help, file=sys.stderr)
        pytest.exit("Invalid command-line options.", returncode=pytest.ExitCode.USAGE_ERROR)

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
            forks_from = config.fork_names[0]
        if not forks_until:
            forks_until = get_deployed_forks()[-1].name()

    if forks_from not in config.fork_map.keys():
        print(f"Error: Unsupported fork provided to --from: {forks_from}\n", file=sys.stderr)
        print(available_forks_help, file=sys.stderr)
        pytest.exit("Invalid command-line options.", returncode=pytest.ExitCode.USAGE_ERROR)

    if forks_until not in config.fork_map.keys():
        print(f"Error: Unsupported fork provided to --until: {forks_until}\n", file=sys.stderr)
        print(available_forks_help, file=sys.stderr)
        pytest.exit("Invalid command-line options.", returncode=pytest.ExitCode.USAGE_ERROR)

    config.fork_range = config.fork_names[
        config.fork_names.index(forks_from) : config.fork_names.index(forks_until) + 1
    ]

    if not config.fork_range:
        print(
            f"Error: --from {forks_from} --until {forks_until} creates an empty fork range.",
            file=sys.stderr,
        )
        pytest.exit(
            "Command-line options produce empty fork range.",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )

    # with --collect-only, we don't have access to these config options
    if config.option.collectonly:
        config.unsupported_forks = []
        return

    evm_bin = config.getoption("evm_bin")
    t8n = TransitionTool.from_binary_path(binary_path=evm_bin)
    config.unsupported_forks = [
        fork for fork in config.fork_range if not t8n.is_fork_supported(config.fork_map[fork])
    ]


@pytest.hookimpl(trylast=True)
def pytest_report_header(config, start_path):
    """A pytest hook called to obtain the report header."""
    bold = "\033[1m"
    warning = "\033[93m"
    reset = "\033[39;49m"
    header = [
        (bold + f"Executing tests for: {', '.join(config.fork_range)} " + reset),
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
) -> str | None:
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
        return None
    if len(validity_markers) > 1:
        pytest.fail(f"'{test_name}': Too many '{validity_marker_name}' markers applied to test. ")
    if len(validity_markers[0].args) == 0:
        pytest.fail(f"'{test_name}': Missing fork argument with '{validity_marker_name}' marker. ")
    if len(validity_markers[0].args) > 1:
        pytest.fail(
            f"'{test_name}': Too many arguments specified to '{validity_marker_name}' marker. "
        )
    fork_name = validity_markers[0].args[0]
    if fork_name not in metafunc.config.fork_names:  # type: ignore
        pytest.fail(
            f"'{test_name}' specifies an invalid fork '{fork_name}' to the "
            f"'{validity_marker_name}'. "
            f"List of valid forks: {', '.join(metafunc.config.fork_names)}"  # type: ignore
        )

    return fork_name


def pytest_generate_tests(metafunc):
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

    intersection_range = []

    if valid_at_transition_to:
        if valid_at_transition_to in metafunc.config.fork_range:
            to_fork = metafunc.config.fork_map[valid_at_transition_to]
            intersection_range = transition_fork_to(to_fork)

    else:
        if not valid_from:
            valid_from = metafunc.config.fork_names[0]

        if not valid_until:
            valid_until = metafunc.config.fork_names[-1]

        test_fork_range = set(
            metafunc.config.fork_names[
                metafunc.config.fork_names.index(valid_from) : metafunc.config.fork_names.index(
                    valid_until
                )
                + 1
            ]
        )

        if not test_fork_range:
            pytest.fail(
                "The test function's "
                f"'{test_name}' fork validity markers generate "
                "an empty fork range. Please check the arguments to its "
                f"markers:  @pytest.mark.valid_from ({valid_from}) and "
                f"@pytest.mark.valid_until ({valid_until})."
            )

        intersection_range = list(set(metafunc.config.fork_range) & test_fork_range)

        intersection_range.sort(key=metafunc.config.fork_range.index)
        intersection_range = [metafunc.config.fork_map[fork] for fork in intersection_range]

    if "fork" in metafunc.fixturenames:
        if not intersection_range:
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
                # This will not be reported in the test execution output; it will be listed
                # in the pytest collection summary at the start of the test run.
                pytest.skip(
                    f"{test_name} is not valid for any any of forks specified on the command-line."
                )
        else:
            pytest_params = [
                pytest.param(
                    fork,
                    marks=[
                        pytest.mark.skip(
                            reason=(
                                f"Fork '{fork}' unsupported by "
                                f"'{metafunc.config.getoption('evm_bin')}'."
                            )
                        )
                    ],
                )
                if fork.name() in metafunc.config.unsupported_forks
                else pytest.param(fork)
                for fork in intersection_range
            ]
            metafunc.parametrize("fork", pytest_params, scope="function")
