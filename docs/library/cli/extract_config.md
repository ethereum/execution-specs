# `extract_config` - Extract Client Configuration Files

The `extract_config` command extracts configuration files from Ethereum clients by spawning them via Hive and retrieving the generated files from the Docker container.

## Purpose

When Ethereum clients start up with a genesis configuration, they generate various configuration files such as:

- `/chainspec/test.json` - Chain specification file
- `/configs/test.cfg` - Configuration file
- `/genesis.json` - Genesis block configuration

This tool automates the process of extracting these files from the client containers for analysis or debugging purposes.

## Usage

```bash
uv run extract_config --fixture <FIXTURE_PATH> [OPTIONS]
```

### Options

- `--fixture, -f` (required): Path to a fixture JSON file or directory containing fixture files
- `--client, -c`: Specific client name to extract from (e.g., go-ethereum, besu, nethermind). If not specified, extracts from all available clients
- `--output, -o`: Output directory for extracted files (default: ./extracted_configs)
- `--hive-url`: Hive server URL (default: http://127.0.0.1:3000)
- `--list-files, -l`: List files in the container root before extraction
- `--help`: Show help message

### Examples

Extract configuration from all clients using a specific fixture:

```bash
uv run extract_config --fixture fixtures/blockchain_tests/paris/security/test_selfdestruct_balance_bug.json
```

Extract configuration from a specific client:

```bash
uv run extract_config --fixture fixtures/blockchain_tests/paris/security/test_selfdestruct_balance_bug.json --client besu
```

Extract configurations from all fixtures in a directory:

```bash
uv run extract_config --fixture fixtures/blockchain_tests/paris/security/
```

Extract to a specific directory and list container files:

```bash
uv run extract_config --fixture my_fixture.json --output ./my_configs --list-files
```

## Prerequisites

1. Hive must be running in the background:

   ```bash
   ./hive --dev
   ```

2. Docker must be installed and accessible

## Output

The tool creates a hierarchical directory structure:

```console
<output_dir>/
  <fixture_name>/
    <client_name>/
      chainspec.json
      config.cfg
      genesis.json
```

For example:

```console
extracted_configs/
  test_selfdestruct_balance_bug/
    go-ethereum/
      genesis.json
    besu/
      genesis.json
      chainspec.json
    nethermind/
      chainspec.json
      config.cfg
```

Only files that exist in the client container will be extracted.

## How It Works

1. Loads the fixture file(s) to extract genesis configuration
2. Starts a Hive simulation
3. For each fixture and each client:
   - Captures the list of Docker containers before starting the client
   - Spawns the client with the genesis configuration
   - Compares Docker containers to identify the newly created container
   - Uses Docker exec commands to check for and extract configuration files
   - Saves the extracted files to the organized output directory
   - Stops the client container
4. Ends the Hive simulation

## Container ID Detection

Since Hive doesn't directly expose container IDs, the tool uses a detection mechanism:

1. Lists all Docker container IDs before starting the client
2. Starts the client through Hive
3. Lists all Docker container IDs after starting the client
4. The difference should be exactly one container - the client's container

## Supported Fixture Formats

The tool supports:

- Individual fixture JSON files (BlockchainFixture format)
- PreAllocGroup JSON files
- Directories containing multiple fixture files

## Troubleshooting

- If no files are extracted, use the `--list-files` flag to see what files are available in the container root
- Ensure Hive is running before executing the command
- Check that Docker is installed and the current user has permissions to run Docker commands
- If the tool fails to detect the container ID, ensure no other containers are being created simultaneously
- Some clients may not generate all configuration file types - this is normal
