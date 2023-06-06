"""
Pytest plugin to enable fork range configuration for the test session.
"""
import textwrap

import pytest

from ethereum_test_forks import (
    ArrowGlacier,
    Cancun,
    Frontier,
    all_transition_forks,
    forks_from_until,
    latest_fork_resolver,
    transition_fork_to,
)
from evm_transition_tool import EvmTransitionTool


def pytest_addoption(parser):
    """
    Adds command-line options to pytest.
    """
    fork_group = parser.getgroup(
        "Forks", "Specify the fork range to generate fixtures for"
    )
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


def pytest_configure(config):
    """
    Process command-line options.
    """
    single_fork = config.getoption("single_fork")
    forks_from = config.getoption("forks_from")
    forks_until = config.getoption("forks_until")
    show_fork_help = config.getoption("show_fork_help")

    first_fork = Frontier
    last_fork = Cancun
    config.implemented_forks = forks_from_until(first_fork, last_fork)
    config.fork_map = {
        fork().name(): fork for fork in config.implemented_forks
    }
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
        {", ".join([fork.name() for fork in all_transition_forks()])}
        """
    )
    dev_forks_help = textwrap.dedent(
        "To run tests for a fork under active development, it must be "
        "specified explicitly via --forks-until=FORK.\n"
        "Tests are only "
        f"ran for deployed mainnet forks by default, i.e., until "
        f"{latest_fork_resolver.latest_fork().name()}.\n"
    )
    if show_fork_help:
        print(available_forks_help)
        print(dev_forks_help)
        pytest.exit("After displaying help.", returncode=0)

    if single_fork and single_fork not in config.fork_map.keys():
        print("Error: Unsupported fork provided to --fork:", single_fork, "\n")
        print(available_forks_help)
        pytest.exit("Invalid command-line options.", returncode=1)

    if single_fork and (forks_from or forks_until):
        print(
            "Error: --fork cannot be used in combination with --forks-from or "
            "--forks-until"
        )
        pytest.exit("Invalid command-line options.", returncode=1)

    if single_fork:
        forks_from = single_fork
        forks_until = single_fork
    else:
        if not forks_from:
            forks_from = first_fork().name()
        if not forks_until:
            # latest deployed fork
            forks_until = latest_fork_resolver.latest_fork().name()

    if forks_from not in config.fork_map.keys():
        print(
            "Error: Unsupported fork provided to --forks-from:",
            forks_from,
            "\n",
        )
        print(available_forks_help)
        pytest.exit("Invalid command-line options.", returncode=1)

    if forks_until not in config.fork_map.keys():
        print(
            "Error: Unsupported fork provided to --forks-until:",
            forks_until,
            "\n",
        )
        print(available_forks_help)
        pytest.exit("Invalid command-line options.", returncode=1)

    config.fork_range = config.fork_names[
        config.fork_names.index(forks_from) : config.fork_names.index(
            forks_until
        )
        + 1
    ]

    if not config.fork_range:
        print(
            f"Error: --forks-from {forks_from} --forks-until {forks_until} "
            "creates an empty fork range."
        )
        pytest.exit(
            "Command-line options produce empty fork range.", returncode=1
        )

    # with --collect-only, we don't have access to these config options
    if config.option.collectonly:
        return
    t8n = EvmTransitionTool(
        binary=config.getoption("evm_bin"),
        trace=config.getoption("evm_collect_traces"),
    )
    unsupported_forks = [
        fork
        for fork in config.fork_range
        if not t8n.is_fork_supported(config.fork_map[fork])
    ]
    if unsupported_forks:
        print(
            "Error: The configured evm tool doesn't support the following "
            f"forks: {', '.join(unsupported_forks)}."
        )
        print(
            "\nPlease specify a version of the evm tool which supports these "
            "forks or use --until FORK to specify a supported fork.\n"
        )
        pytest.exit("Incompatible evm tool with fork range.", returncode=1)


@pytest.hookimpl(trylast=True)
def pytest_report_header(config, start_path):
    """A pytest hook called to obtain the report header."""
    bold = "\033[1m"
    warning = "\033[93m"
    reset = "\033[39;49m"
    header = [
        (
            bold
            + f"Executing tests for: {', '.join(config.fork_range)} "
            + reset
        ),
    ]
    if config.getoption("forks_until") is None:
        header += [
            (
                bold
                + warning
                + "Only executing tests with stable/deployed forks: "
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


def pytest_generate_tests(metafunc):
    """
    Pytest hook used to dynamically generate test cases.
    """
    valid_at_transition_to = [
        marker.args[0]
        for marker in metafunc.definition.iter_markers(
            name="valid_at_transition_to"
        )
    ]
    valid_from = [
        marker.args[0]
        for marker in metafunc.definition.iter_markers(name="valid_from")
    ]
    valid_until = [
        marker.args[0]
        for marker in metafunc.definition.iter_markers(name="valid_until")
    ]
    if valid_at_transition_to and (valid_from or valid_until):
        pytest.fail(
            "The test function "
            f"{metafunc.function.__name__} specifies both a "
            "pytest.mark.valid_at_transition_to and a pytest.mark.valid_from or "
            "pytest.mark.valid_until marker. "
        )

    intersection_range = []

    if valid_at_transition_to:
        fork_to = valid_at_transition_to[0]
        if fork_to not in metafunc.config.fork_names:
            pytest.fail(
                "The test function "
                f"{metafunc.function.__name__} specifies an invalid fork "
                f"{fork_to} to the pytest.mark.valid_at_transition_to marker. "
            )
        if fork_to in metafunc.config.fork_range:
            to_fork = metafunc.config.fork_map[fork_to]
            intersection_range = transition_fork_to(to_fork)

    else:
        if not valid_from:
            valid_from = [metafunc.config.fork_names[0]]

        if valid_from[0] not in metafunc.config.fork_names:
            pytest.fail(
                "The test function "
                f"{metafunc.function.__name__} specifies an invalid fork "
                f"{valid_from[0]} to the pytest.mark.valid_from marker. "
            )
        if valid_until and valid_until[0] not in metafunc.config.fork_names:
            pytest.fail(
                "The test function "
                f"{metafunc.function.__name__} specifies an invalid fork "
                f"{valid_until[0]} to the pytest.mark.valid_until marker. "
            )
        if not valid_until:
            valid_until = [metafunc.config.fork_names[-1]]

        test_fork_range = set(
            metafunc.config.fork_names[
                metafunc.config.fork_names.index(
                    valid_from[0]
                ) : metafunc.config.fork_names.index(valid_until[0])
                + 1
            ]
        )

        if not test_fork_range:
            pytest.fail(
                "The test function's "
                f"{metafunc.function.__name__} fork validity markers generate "
                "an empty fork range. Please check the arguments to it's "
                f"markers:  @pytest.mark.valid_from ({valid_from[0]}) and "
                f"@pytest.mark.valid_until ({valid_until[0]})."
            )

        intersection_range = list(
            set(metafunc.config.fork_range) & test_fork_range
        )

        intersection_range.sort(key=metafunc.config.fork_range.index)
        intersection_range = [
            metafunc.config.fork_map[fork] for fork in intersection_range
        ]

    if "fork" in metafunc.fixturenames:
        metafunc.parametrize("fork", intersection_range, scope="function")


def pytest_runtest_call(item):
    """
    Pytest hook called in the context of test execution.
    """
    fork = item.funcargs["fork"]
    if fork == ArrowGlacier:
        pytest.skip(f"Fork '{fork}' not supported by hive, skipped")
