# Ethereum Execution Layer Specifications

Welcome to the documentation for @ethereum/execution-specs, which hosts the Ethereum Execution Layer Specification (EELS). EELS is implemented as an executable reference in Python and acts as a source of truth for test vector generation to verify Execution Layer client implementations.

@ethereum/execution-specs is a collaborative effort between EIP authors, researchers, protocol prototype developers and client developers, maintained by the [STEEL Team](https://steel.ethereum.foundation/).

## Where to Start

<div class="grid cards" markdown>

- :material-download-outline: **Getting Started**

    ---

    New here? Install the repository and run your first command.

    *First time user.*

    [:octicons-arrow-right-24: Installation](getting_started/installation.md)

- :material-file-code-outline: **Writing Specs**

    ---

    Implement an EIP as an executable Python specification.

    *For EIP authors and researchers.*

    [:octicons-arrow-right-24: Get started](writing_specs/index.md)

- :material-test-tube: **Writing Tests**

    ---

    Write test cases that verify EIP implementations across clients.

    *For EIP authors and test devs.*

    [:octicons-arrow-right-24: Get started](writing_tests/index.md)

- :material-play-circle-outline: **Running Tests**

    ---

    Generate JSON fixtures or run tests against an execution layer client.

    *For client developers.*

    [:octicons-arrow-right-24: Overview](running_tests/index.md)

- :material-book-open-variant: **Read the Specs**

    ---

    Browse the rendered Python specifications for the current fork and EIP.

    [:octicons-arrow-right-24: Specifications](spec/)

- :material-format-list-checks: **Test Case Reference**

    ---

    Browse all test cases organized by fork and EIP.

    [:octicons-arrow-right-24: Browse tests](tests/)

</div>

!!! bug "Reporting a Vulnerability"

    Care is required when adding PRs or issues for functionality that is live on Ethereum mainnet. Please report vulnerabilities and verify bounty eligibility via the [bug bounty program](https://bounty.ethereum.org).

    - **Please do not create a PR with a vulnerability visible.**
    - **Please do not file a public ticket mentioning the vulnerability.**
