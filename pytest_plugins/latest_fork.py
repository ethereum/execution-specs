"""
A pytest plugin that allows the user to specify the latest fork to use for
filling tests via the command-line option --latest-fork=fork. This plugin
also provides a report header that indicates the latest fork being used.
"""
import pytest

from ethereum_test_forks import InvalidForkError, set_latest_fork_by_name


def pytest_addoption(parser):
    """
    Adds command-line options to pytest.
    """
    group = parser.getgroup("forks", "Arguments defining fork configuration")
    group.addoption(
        "--latest-fork",
        action="store",
        dest="latest_fork",
        default=None,
        help="Latest fork used to fill tests",
    )


def pytest_configure(config):
    """
    Check parameters and make session-wide configuration changes, such as
    setting the latest fork.
    """
    latest_fork = config.getoption("latest_fork")
    if latest_fork is not None:
        try:
            set_latest_fork_by_name(latest_fork)
        except InvalidForkError as e:
            pytest.exit(f"Error applying --latest-fork={latest_fork}: {e}.")
        except Exception as e:
            raise e
    return None


@pytest.hookimpl(trylast=True)
def pytest_report_header(config, start_path):
    """A pytest hook called to obtain the report header."""
    bold = "\033[1m"
    warning = "\033[93m"
    reset = "\033[39;49m"
    if config.getoption("latest_fork") is None:
        header = [
            (
                bold
                + warning
                + "Only executing fillers with stable/deployed forks: "
                "Specify an upcoming fork via --latest-fork=fork to "
                "run experimental fillers." + reset
            )
        ]
    else:
        header = [
            (
                bold + "Executing fillers up to and including "
                f"{config.getoption('latest_fork')}." + reset
            ),
        ]
    return header
