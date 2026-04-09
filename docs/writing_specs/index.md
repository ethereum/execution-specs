# Writing Specs

The [ethereum/execution-specs](https://github.com/ethereum/execution-specs) repository contains the Python reference specifications for the Ethereum execution layer. Each hard fork has its own complete implementation under `src/ethereum/<fork_name>/`.

## Folder Structure

### Forks live on mainnet

The `src/ethereum/` directory contains specifications for each execution layer fork. Each fork folder is a **complete copy** of its predecessor (the WET principle). The `state_transition` function in `src/ethereum/<fork_name>/fork.py` is the entry point for each fork's transition logic.

### Fork under development

At any given time, there is a single fork under active development. New EIPs are implemented in the folder for that fork (`src/ethereum/<fork_name>/`).

## Branch Structure

| Branch pattern | Purpose |
|---|---|
| `mainnet` | Stable specs for all forks live on mainnet |
| `forks/<fork_name>` | Main branch for a fork under development |
| `eips/<fork_name>/<eip_number>` | Branch for a specific EIP within a fork |

For example, `forks/amsterdam` is the main branch for the Amsterdam fork, and `eips/amsterdam/eip-XXXX` would be the branch for a specific EIP targeting Amsterdam.

## Next Steps

- [Adding a New EIP](adding_a_new_eip.md) -- step-by-step guide to implementing an EIP in this repository.
- [Read the specifications](../spec/) -- browse the rendered specs for the current fork.
