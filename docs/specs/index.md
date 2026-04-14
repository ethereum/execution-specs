# Specifications

The Ethereum Execution Layer Specifications (EELS) are an executable Python reference implementation of Ethereum's execution layer. They serve as a source of truth for client developers, EIP authors, researchers, and anyone else trying to understand how an Ethereum execution node actually processes a block.

Unlike a traditional prose specification, EELS is expressed as Python code. It can be executed, it can be imported, it can be tested, and it can be stepped through in a debugger. When the protocol changes, the change lands in EELS first and can be studied by client teams.

## Client Diversity requires Coordination

Ethereum runs on at least half a dozen independent execution clients (Geth, Nethermind, Besu, Erigon, Reth, ...). This diversity is a [feature, not an accident](https://ethereum.org/developers/docs/nodes-and-clients/client-diversity/): a flaw in any one client is contained, no single team holds the keys to the network, and permissionless participation is preserved. The price of that resilience is coordination: every client must agree, byte for byte, on every state transition, or the chain splits.

For most of Ethereum's history the only "specification" was the Yellow Paper, a LaTeX document of dense mathematical notation, supplemented by individual EIPs and by the behavior of the reference clients themselves. Human language is ambiguous, and even mathematical notation leaves room for interpretation.

Python offers a different contract. A Python function does not leave room for interpretation: either it returns the same value for the same input or it does not. By writing the specification as a program, every edge case is forced into the open, and every client team has a concrete reference to compare against.

## Why Python

Python is not the fastest language: EELS trades performance for readability, because the spec's job is to be understood, not to run fast. Production clients in Go, Rust, and C++ handle the performance; the spec's job is to describe what those clients are supposed to do.

Python was chosen because:

- It reads close to pseudocode, so readers who are not Python programmers can still follow it.
- It has a mature testing ecosystem (`pytest`, `hypothesis`, ...), which lets the spec be validated the same way any other library is validated.
- It is widely known among protocol researchers, making it approachable for new EIP authors.

EELS is a "spiritual successor to the Yellow Paper" that trades dense notation for code a reader can step through.

## Design principles

EELS aims to be:

1. **Correct.** The spec describes the *intended* behaviour of Ethereum. Any deviation is a bug.
2. **Complete.** Every consensus-critical behaviour is captured. If it affects state, it belongs in EELS.
3. **Accessible.** Readability, clarity, and plain language win over cleverness, performance, and brevity.

The third principle is where EELS departs most sharply from production code. In a production client you minimise duplication (DRY, "don't repeat yourself"), because duplicated logic is expensive to maintain. In EELS you deliberately repeat yourself ("write everything twice", WET), because duplication is easier to read than a network of abstractions. A reader should be able to open a single fork's `state_transition` and follow it top to bottom without jumping files.

## The fork-as-a-copy model

Each hardfork under `src/ethereum/forks/` is a **complete copy** of the previous fork's code, edited in place. There is no shared base class, no feature-flag plumbing, no framework. When a reader wants to know what changed between, say, Cancun and Prague, they read the diff between `src/ethereum/forks/cancun/` and `src/ethereum/forks/prague/`.

This has two concrete benefits:

- Every fork is self-contained. Paris is Paris, forever; nothing a future fork does can change it.
- Changes are reviewable as diffs. The cost of an EIP, in terms of spec surface area, is immediately visible.

The trade-off is that a bug fix that applies to every fork must be applied to every fork, by hand or with the patch tool. That cost is paid deliberately.

## Where to go from here

- [Writing Specs](writing_specs.md): style rules, cross-fork discipline, and the `ethereum_spec_tools` CLI utilities.
- [Adding a New EIP](adding_a_new_eip.md): the EIP lifecycle from pre-draft to final, and how to land a new EIP in EELS.
- [Spec Releases](spec_releases.md): how EELS versions relate to Ethereum hardforks and devnets.
- [Protocol History](protocol_history.md): the full table of mainnet hardforks, their included EIPs, and their fork manifests.
- [Rendered specification](https://ethereum.github.io/execution-specs/): the `docc`-rendered narrative view of the Python spec, with side-by-side diffs between forks.

!!! bug "Reporting a vulnerability"
    Care is required when filing issues or PRs for functionality that is live on Ethereum mainnet. Please report vulnerabilities and verify bounty eligibility via the [bug bounty program](https://bounty.ethereum.org).

    - **Please do not create a PR with a vulnerability visible.**
    - **Please do not file a public ticket mentioning the vulnerability.**
