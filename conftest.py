
def pytest_addoption(parser):
    parser.addoption("--evm-trace", dest='vmtrace', default=1, action='store_const', const=10, help="Run trace")


def pytest_configure(config):
    if config.getoption("vmtrace", default=1) == 10:
        config.option.__dict__["log_cli_level"] = "10"
        config.option.__dict__["log_format"] = "%(message)s"
