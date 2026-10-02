# Hive

@ethereum/hive is a containerized testing framework that helps orchestrate test execution against Ethereum clients. Hive is incredibly extensible; new test suites can be implemented in a module manner as "simulators" that interact with clients to test certain aspects of their behavior. The execution-specs `testing` package implements several simulators, see [Running Tests](../running.md) for an overview.

For the EELS simulators, start with [Run a Simulator from Images](images/tutorial.md) or [Choose a tag](images/index.md#choose-a-tag). Existing source-build commands using `fixtures` and `branch` need the [Dockerfile.git configuration](images/how_to.md#build-from-source-with-dockerfilegit).

## Quick Start

### Prerequisites

1. Docker: <https://docs.docker.com/get-docker/>.
2. Golang 1.24+: <https://go.dev/doc/install>.

### Installation

Clone @ethereum/hive and build the `./hive` command:

```bash
git clone https://github.com/ethereum/hive
cd hive
go build .
```
