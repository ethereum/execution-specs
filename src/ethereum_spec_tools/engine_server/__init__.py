"""
Run the execution specification as an Engine API client.

Loads a hive genesis file into the genesis fork's `BlockChain` and
serves the Engine API and `eth` JSON-RPC methods needed by a
consensus-layer driver, allowing tools like the hive `consume engine`
and `consume enginex` simulators to feed blocks directly to the
specification. All post-merge forks are supported; the fork schedule
is read from the hive `HIVE_<FORK>_TIMESTAMP` environment variables.
"""

import argparse
import os
import threading
from pathlib import Path

from ethereum_types.numeric import U64

from .forks import schedule_from_env
from .genesis import load_genesis_chain
from .server import DEFAULT_JWT_SECRET, EngineBackend, serve


def parse_arguments() -> argparse.Namespace:
    """Parse the engine server's command line arguments."""
    parser = argparse.ArgumentParser(
        prog="ethereum-spec-engine",
        description="Run the execution specs as an Engine API client.",
    )
    parser.add_argument(
        "--genesis",
        type=Path,
        required=True,
        help="Path to the hive genesis JSON file.",
    )
    parser.add_argument(
        "--chain-id",
        type=lambda value: int(value, 0),
        default=int(os.environ.get("HIVE_CHAIN_ID", "1")),
        help="Chain id (defaults to $HIVE_CHAIN_ID or 1).",
    )
    parser.add_argument(
        "--address",
        default="0.0.0.0",
        help="Address to bind the HTTP listeners to.",
    )
    parser.add_argument(
        "--rpc-port",
        type=int,
        default=8545,
        help="Port for the unauthenticated eth namespace.",
    )
    parser.add_argument(
        "--engine-port",
        type=int,
        default=8551,
        help="Port for the JWT-authenticated engine namespace.",
    )
    parser.add_argument(
        "--jwt-secret",
        type=lambda value: bytes.fromhex(value.removeprefix("0x")),
        default=DEFAULT_JWT_SECRET,
        help="JWT secret as a hex string (defaults to the hive secret).",
    )
    return parser.parse_args()


def main() -> None:
    """Start the engine server and serve until interrupted."""
    options = parse_arguments()

    schedule = schedule_from_env(os.environ)
    chain, genesis_fork = load_genesis_chain(
        options.genesis, U64(options.chain_id), schedule
    )
    engine = genesis_fork.engine.create_execution_engine(chain)
    backend = EngineBackend(engine, genesis_fork, schedule)
    serve(
        backend,
        options.address,
        options.rpc_port,
        options.engine_port,
        options.jwt_secret,
    )
    print(
        f"engine server listening on {options.address}:"
        f"{options.rpc_port} (eth) and {options.address}:"
        f"{options.engine_port} (engine)",
        flush=True,
    )
    threading.Event().wait()
