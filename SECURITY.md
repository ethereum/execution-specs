# Security Policy

## Overview

While EELS (Ethereum Execution Layer Spec) is not intended to be a production
ready client, the software is intended to fully capable of running as an
execution layer client for local testing and acts as a point of reference for
the other EL (Execution Layer) clients. Therefore, a bug in this spec _could_
imply a bug in the production clients, though this is not necessarily the case.

## Supported Versions

Please see [Releases](https://github.com/ethereum/execution-specs/releases). We
recommend using the [latest version](https://github.com/ethereum/execution-specs/releases/latest).

## Reporting Vulnerabilities

### What Contitutes a Serious Vulnerability

- Issues which affect all EL clients (geth, Nethermind, Besu, etc.)
- EELS has inadvertantly leaked secure information into the codebase

### Issues That are Fine to Report Publicly

- Issues which are limited to EELS operation as a local EL test client

### How to Notify the Project of a Security Vulnerability

**Please do NOT file a public ticket** mentioning the vulnerability.

#### Normal Issues

File a issue in GitHub

#### Serious Issues

Visit [https://bounty.ethereum.org](https://bounty.ethereum.org) or email
bounty@ethereum.org. Please read the [disclosure
page](https://github.com/ethereum/go-ethereum/security/advisories?state=published)
for more information about publicly disclosed security vulnerabilities.

The following PGP key may be used to communicate sensitive information to
developers.

Fingerprint: `35C9 76D3 6149 A165 18EF A14B 3BCA C178 6B00 E477`

```
-----BEGIN PGP PUBLIC KEY BLOCK-----

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
=wIl4
-----END PGP PUBLIC KEY BLOCK-----
```
