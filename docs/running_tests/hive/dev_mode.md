# Hive Development Mode

This section explains how to run EELS simulators using their Python-based commands, e.g., `uv run consume engine`, against a Hive "development" server as apposed to using the standalone `./hive` command.

This avoids running the simulator in a dockerized environment and has several advantages:

1. A local directory containing fixtures can be specified (`--input=./fixtures/`).
2. Allows dropping into a Python debugger (via `--pdb`) upon test failure to inspect the response or ssh to the client container.
3. Provides access to a larger set of the simulator's command-line options,
4. Runs are faster; there are no docker image rebuilds in between runs. In particular, modifications to the simulator do not require a an image rebuild.

## Platform Support

- Linux: Direct development mode supported.
- macOS: Must be ran from a Linux environment or use a Docker-based workaround (see macOS Setup).

## Quick Start

### Prerequisites

- The execution-specs repo is setup in development mode, see [Installation](../../getting_started/installation.md)
- Hive is built, see [Hive](../hive/index.md#quick-start).

## Hive Dev Setup on Linux

1. Start Hive in development mode, e.g.:

    ```bash
    ./hive --dev --client go-ethereum --client-file clients.yaml --docker.output
    ```

2. In a separate shell, configure environment for execution-specs:

    === "bash/zsh"

        ```bash
        export HIVE_SIMULATOR=http://127.0.0.1:3000
        ```

    === "fish"

        ```console
        set -x HIVE_SIMULATOR http://127.0.0.1:3000
        ```

3. Run execution-specs `consume` commands

    ```bash
    uv run consume engine --input ./fixtures -k "test_chainid"
    uv run consume rlp --input stable@latest
    ```

## Hive Dev Setup on macOS

Due to Docker running within a VM on macOS, the host machine and Docker containers don't share the same network namespace, preventing direct communication with Hive's development server. To run development mode on macOS, you have the following options:

1. Linux VM: Run a Linux virtual machine on your macOS and execute the standard development workflow above from within the VM.
2. Remote Linux: SSH into a remote Linux environment (server or cloud instance) and run development mode there.
3. **Docker Development Image**: Create a containerized execution-specs environment that runs within Docker's network namespace (recommended).

The following section details the setup and usage of option 3.

### EELS Docker Development Image

Within the [`eels/`](https://github.com/ethereum/hive/tree/master/simulators/ethereum/eels) directory of hive, a new dockerfile must be created: `Dockerfile.dev`, with the following contents:

```docker
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
ARG branch=""

RUN apt-get update && apt-get install -y git
RUN git clone --depth 1 https://github.com/ethereum/execution-specs.git && \
    cd execution-specs && \
    if [ -n "$branch" ]; then \
        git fetch --depth 1 origin "$branch" && \
        git checkout FETCH_HEAD; \
    fi
WORKDIR /execution-specs/packages/testing
RUN uv sync
ENTRYPOINT ["/bin/bash"]
```

This dockerfile will be our entry point for running simulator commands.

### `eels/` Hive Directory Structure

```tree
├── eels
│   ├── Dockerfile.dev
│   ├── consume-block-rlp
│   │   └── Dockerfile
│   └── consume-engine
│       └── Dockerfile
```

### Running Consume

1. Get your local IP address:

    ```bash
    ipconfig getifaddr en0
    ```

2. Start Hive in development mode with your local IP:

    ```bash
    ./hive --dev --dev.addr <LOCAL_IP>:3000 --client go-ethereum --client-file clients.yaml 
    ```

3. In a separate terminal session, build the EELS development image:

    ```bash
    cd simulators/ethereum/eels/
    docker build -t macos-consume-dev -f Dockerfile.dev .
    ```

4. Run the container with the Hive simulator environment:

    ```bash
    docker run -it -e HIVE_SIMULATOR=http://<LOCAL_IP>:3000 macos-consume-dev
    ```

5. Inside the Docker container, run consume commands:

    ```bash
    uv run consume engine -v
    ```

## How Development Mode Works

When Hive runs in dev mode:

1. Starts the Hive API server (default: `http://127.0.0.1:3000`).
2. Builds and maintains client containers.
3. Keeps the Hive Proxy container running between test executions.
4. Waits for external simulator connections via the API.

This allows the EELS's consume commands to connect to the running Hive instance and execute tests interactively.

## More Options Available

There are many useful native pytest options available in dev mode, see [Useful Options](../useful_pytest_options.md).

### Custom API Endpoint

Specify a custom address and port via `--dev.addr`:

```bash
./hive --dev \
  --dev.addr 127.0.0.1:5000 \
  --client reth \
  --client-file clients.yaml
```

Then connect with:

```bash
export HIVE_SIMULATOR=http://127.0.0.1:5000
```
