# `extract_config` - Extract Client Configuration Files

The `extract_config` command generates client-native configuration files for Ethereum clients directly from a filled EEST fixture.

## Purpose

Ethereum clients each expect their own genesis/configuration file format, for example:

- Besu and go-ethereum: a single `genesis.json`
- Nethermind: a `chainspec.json` plus a node `config.json`

Each client's hive image derives its file(s) from the fixture's genesis block and pre-state via a fixed transform (hive's `mapper.jq`/`mkconfig.jq` scripts). `extract_config` reimplements those transforms directly in Python, so it produces the same files without spawning a client via Hive or Docker.

## Usage

```bash
uv run extract_config --fixture <FIXTURE_PATH> [OPTIONS]
```

### Options

- `--fixture, -f` (required): Path to a fixture JSON file or directory containing fixture files
- `--client, -c`: Only generate files for client names containing this substring (e.g., go-ethereum, besu, nethermind). If not specified, generates files for all supported clients
- `--output, -o`: Output directory for generated files (default: ./extracted_configs)
- `--help`: Show help message

### Examples

Generate configuration for all supported clients using a specific fixture:

```bash
uv run extract_config --fixture fixtures/blockchain_tests/paris/security/test_selfdestruct_balance_bug.json
```

Generate configuration for a specific client:

```bash
uv run extract_config --fixture fixtures/blockchain_tests/paris/security/test_selfdestruct_balance_bug.json --client besu
```

Generate configurations from all fixtures in a directory:

```bash
uv run extract_config --fixture fixtures/blockchain_tests/paris/security/
```

Generate to a specific output directory:

```bash
uv run extract_config --fixture my_fixture.json --output ./my_configs
```

## Output

The tool creates a hierarchical directory structure:

```console
<output_dir>/
  <fixture_name>/
    <client_name>/
      <client-native files>
```

For example:

```console
extracted_configs/
  test_selfdestruct_balance_bug/
    go-ethereum/
      genesis.json
    besu/
      genesis.json
    nethermind/
      chainspec.json
      config.json
```

## How It Works

1. Loads the fixture file(s) and extracts the genesis header, pre-state, chain ID, and fork
2. For each fixture and each selected client, builds that client's native genesis model from the fixture data (see `exportable_genesis.py` and `clients/`)
3. Writes the resulting file(s) to `<output_dir>/<fixture_name>/<client_name>/`

## Supported Fixture Formats

The tool supports:

- Individual fixture JSON files (BlockchainFixture format)
- PreAllocGroup JSON files
- Directories containing multiple fixture files

## Troubleshooting

- If a fixture file isn't in a recognized format, the tool reports it and continues with the remaining fixtures/clients
- Some client models omit fields real Docker-container output would carry over from full block execution (e.g. `stateRoot`) since they are computed directly from genesis, not a filled block header
