# Hive

@ethereum/hive is a containerized testing framework that helps orchestrate test execution against Ethereum clients. Hive is incredibly extensible; new test suites can be implemented in a module manner as "simulators" that interact with clients to test certain aspects of their behavior. EEST implements several simulators, see [Running Tests](../running.md) for an overview.

## Quick Start

### Prerequisites

1. Docker: <https://docs.docker.com/get-docker/>.
2. Golang 1.22+: <https://go.dev/doc/install>.

### Installation

Clone @ethereum/hive and build the `./hive` command:

```bash
git clone https://github.com/ethereum/hive
cd hive
go build .
```
