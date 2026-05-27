"""
Hive session bootstrap for the fill-stateful plugin.
"""

import os

import pytest

from execution_testing.forks import (
    Fork,
    ForkSetAdapter,
    InvalidForkError,
    TransitionFork,
)
from execution_testing.logging import get_logger
from execution_testing.rpc import EngineRPC
from execution_testing.test_types.chain_config_types import (
    ChainConfigDefaults,
)

from ..execute.rpc.hive import (
    build_client_files,
    build_client_genesis_dict,
    build_genesis_header,
    build_hive_environment,
)

logger = get_logger(__name__)


def _resolve_session_fork(
    config: pytest.Config,
) -> Fork | TransitionFork:
    """
    Resolve the single fork from ``--fork`` in hive mode.
    """
    fork_arg = config.getoption("single_fork", default="")
    if not fork_arg:
        pytest.exit(
            "--fork is required in --hive-mode (single-fork only).",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )
    try:
        fork_set = ForkSetAdapter.validate_python(fork_arg)
    except InvalidForkError:
        pytest.exit(
            f"Unsupported fork provided to --fork: {fork_arg!r}",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )
    if len(fork_set) != 1:
        pytest.exit(
            f"Expected exactly one fork in --hive-mode, got {len(fork_set)} "
            f"({sorted(f.name() for f in fork_set)}).",
            returncode=pytest.ExitCode.USAGE_ERROR,
        )
    return next(iter(fork_set))


def _hive_chain_id(config: pytest.Config) -> int:
    """Resolve chain id from CLI/env, defaulting to ChainConfigDefaults."""
    cli_value = config.getoption("chain_id", default=None)
    if cli_value is not None:
        return int(cli_value)
    env_value = os.environ.get("CHAIN_ID")
    if env_value is not None:
        return int(env_value)
    return ChainConfigDefaults.chain_id


def configure_hive(config: pytest.Config) -> None:
    """
    Start a hive simulator session and a single execution client, then
    rewrite ``config.option`` so the rest of the plugin stack (remote.py
    in particular) connects to the hive-managed client.
    """
    hive_simulator_url = config.getoption("hive_simulator")
    if hive_simulator_url is None:
        pytest.exit(
            "The HIVE_SIMULATOR environment variable is not set.\n\n"
            "If running locally, start hive in --dev mode, for example:\n"
            "./hive --dev --client go-ethereum\n\n"
            "and set the HIVE_SIMULATOR to the reported URL. For example, "
            "in bash:\n"
            "export HIVE_SIMULATOR=http://127.0.0.1:3000\n"
            "or in fish:\n"
            "set -x HIVE_SIMULATOR http://127.0.0.1:3000"
        )
    from hive.simulation import Simulation

    session_fork = _resolve_session_fork(config)
    chain_id = _hive_chain_id(config)

    simulator = Simulation(url=hive_simulator_url)
    suite = simulator.start_suite(
        name="fill-stateful test suite",
        description="Test suite used to drive a fill-stateful session",
    )
    config.hive_test_suite = suite  # type: ignore[attr-defined]
    base_test = suite.start_test(
        name="fill-stateful base test",
        description=(
            "Base test in the fill-stateful suite hosting the long-lived "
            "execution client."
        ),
    )
    config.hive_base_test = base_test  # type: ignore[attr-defined]

    # base_pre=None: seed key funded via CL withdrawal and deterministic
    # factory deployed on-chain by ``_session_pre_run``, so genesis only
    # needs the fork's required system contracts.
    pre_alloc, genesis_header = build_genesis_header(session_fork, None)
    genesis_dict = build_client_genesis_dict(pre_alloc, genesis_header)

    client_type = simulator.client_types()[0]
    client = base_test.start_client(
        client_type=client_type,
        environment=build_hive_environment(session_fork, chain_id),
        files=build_client_files(genesis_dict),
    )
    if client is None:
        pytest.exit(
            f"Unable to start hive client {client_type.name}. Check the "
            "hive server logs for more information."
        )
    config.hive_client = client  # type: ignore[attr-defined]
    logger.info(
        f"Started hive client {client_type.name} at {client.ip} "
        f"(fork={session_fork.name()}, chain_id={chain_id})"
    )

    config.option.rpc_endpoint = f"http://{client.ip}:8545"
    config.option.engine_endpoint = f"http://{client.ip}:8551"
    if (
        config.getoption("engine_jwt_secret", default=None) is None
        and config.getoption("engine_jwt_secret_file", default=None) is None
    ):
        config.option.engine_jwt_secret = EngineRPC.DEFAULT_JWT_SECRET
    if config.getoption("chain_id", default=None) is None:
        config.option.chain_id = chain_id


def teardown_hive(config: pytest.Config) -> None:
    """Tear down hive resources started in ``configure_hive``."""
    client = getattr(config, "hive_client", None)
    if client is not None:
        try:
            client.stop()
        except Exception as e:
            logger.warning(f"Failed to stop hive client: {e}")
        config.hive_client = None  # type: ignore[attr-defined]

    base_test = getattr(config, "hive_base_test", None)
    if base_test is not None:
        from hive.testing import HiveTestResult

        test_pass = (
            getattr(config, "_fill_stateful_session_failed", False) is False
        )
        try:
            base_test.end(
                result=HiveTestResult(
                    test_pass=test_pass,
                    details=(
                        "fill-stateful session complete"
                        if test_pass
                        else "fill-stateful session had failures"
                    ),
                )
            )
        except Exception as e:
            logger.warning(f"Failed to end hive base test: {e}")
        config.hive_base_test = None  # type: ignore[attr-defined]

    suite = getattr(config, "hive_test_suite", None)
    if suite is not None:
        try:
            suite.end()
        except Exception as e:
            logger.warning(f"Failed to end hive test suite: {e}")
        config.hive_test_suite = None  # type: ignore[attr-defined]
