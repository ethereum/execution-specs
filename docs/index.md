# Ethereum Execution Layer Specifications and Tests

Welcome to the documentation for [ethereum/execution-specs](https://github.com/ethereum/execution-specs) -- the Python reference specifications and test suite for the Ethereum execution layer.

## Where to Start

| I want to... | Go to |
|---|---|
| Write or modify an EL specification | [Writing Specs](writing_specs/index.md) |
| Write test cases for EIPs | [Writing Tests](writing_tests/index.md) |
| Generate or run test fixtures | [Running Tests](running_tests/index.md) |
| Read the rendered specifications | [Specifications](spec/) |
| Browse the test cases | [Test Case Reference](tests/) |

## Overview

```mermaid
---
title: Test Fixture Generation
---
flowchart LR
  style C stroke:#333,stroke-width:2px
  style D stroke:#333,stroke-width:2px
  style G stroke:#F9A825,stroke-width:2px
  style H stroke:#F9A825,stroke-width:2px

  subgraph ethereum/go-ethereum
    C[<code>evm t8n</code><br/>external executable]
  end

  subgraph ethereum/solidity
    D[<code>solc</code><br/>external executable]
  end

  subgraph ethereum/EIPs
    E(<code>EIPS/EIP-*.md</code><br/>SHA digest via Github API)
  end

  subgraph "ethereum/execution-specs"
    A(<code>./tests/**/*.py</code><br/>Python Test Cases)
    B([<code>$ fill ./tests/</code><br/>Python Framework])
    S(<code>./src/ethereum/</code><br/>Python Specifications)
  end

  subgraph Test Fixture Consumers
    subgraph ethereum/hive
      G([<code>$ hive ...</code><br/>Go Test Framework])
    end
    H([Client executables])
  end

  C <-.-> B
  D <-.-> B
  S <-.-> B
  A --> B
  E <-.-> |retrieve latest spec version\ncheck tested spec version| B
  B -->|output| F(<code>./fixtures/**/*.json</code>\nJSON Test Fixtures)
  F -->|input| G
  F -->|input| H
```

## For EIP Authors

Start with [Writing Specs](writing_specs/index.md) to learn how to implement your EIP as an executable Python specification. An EIP needs a reference implementation here before it can be Considered For Inclusion (CFI) in a fork.

## For Test Developers

See [Writing Tests](writing_tests/index.md) for the test framework and [Filling Tests](filling_tests/index.md) to generate JSON test fixtures from your Python test cases.

## For Client Developers

See [Running Tests](running_tests/index.md) for how to consume test fixtures and verify your client implementation. Pre-built fixtures are available as [releases](https://github.com/ethereum/execution-specs/releases).

!!! bug "Reporting a Vulnerability"

    Care is required when adding PRs or issues for functionality that is live on Ethereum mainnet. Please report vulnerabilities and verify bounty eligibility via the [bug bounty program](https://bounty.ethereum.org).

    - **Please do not create a PR with a vulnerability visible.**
    - **Please do not file a public ticket mentioning the vulnerability.**
