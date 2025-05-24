# Security Policy

## Overview

While the Ethereum Execution Layer Specification (EELS) is not intended to be a
production ready client, the software is intended to fully capable of applying
state transitions for local testing and acts as a point of reference for the
other Execution Layer (EL) clients. Therefore, a bug in this spec _could_ imply
a bug in the production clients, though this is not necessarily the case.

## Supported Versions

Please see [Releases](https://github.com/ethereum/execution-specs/releases). We
recommend using the [latest version](https://github.com/ethereum/execution-specs/releases/latest).

## Reporting Issues

### What Contitutes a Serious Issue

- Issues which affect all EL clients (geth, Nethermind, Besu, etc.)
- EELS has inadvertantly leaked secure information into the codebase

### What Does _Not_ Constitute a Serious Issue

- Issues which are limited to EELS operation as a local EL test client

### How to Notify the Project of an Issue

#### Normal Issues

File a issue in GitHub

#### Serious Issues

**Please do NOT file a public ticket** mentioning the issue.

If the issue affects all EL clients (I.e. there is an issue with the
specification at the EIP level rather than the implementation level) or
sensitive information has been leaked into the code base, please visit
[https://bounty.ethereum.org](https://bounty.ethereum.org) or email
bounty@ethereum.org. Please read the [disclosure
page](https://github.com/ethereum/go-ethereum/security/advisories?state=published)
for more information about publicly disclosed security vulnerabilities.
