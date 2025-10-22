# Client Configuration Guide

Clients ran in Hive are configured via the following `./hive` options:

1. `--client-file=client_config.yaml`: Specifies a YAML file defining which and how clients are built.
2. `--client=client1,client2`: Selects a subset of clients to run from the YAML via `nametag`.

## Client YAML File Format

Multiple client configurations can be defined as a list in a client YAML file with the following structure:

```yaml
- client: <client-name-1>
  nametag: <unique-identifier>
  dockerfile: <dockerfile-variant>
  build_args:
    <key>: <value>
    ...
- client: <client-name-2>
  ...
```

## Client Build Variants

Hive runs client images in Docker containers. There are three different ways to specify how a client image should be built:

| Dockerfile | Purpose | Example Usage |
|------------|---------|---------------|
| `Dockerfile` | Default production build | `dockerfile: ""` (default) |
| `Dockerfile.git` | Clone from Github and build from source | `dockerfile: git` |
| `Dockerfile.local` | Build from local source | `dockerfile: local` |

These Dockerfiles are maintained for each supported client in @ethereum/hive in the [`./clients/`](https://github.com/ethereum/hive/tree/master/clients) subfolder.

### Production Image

A pre-built image can be specified, for example, for Besu with:

```yaml
- client: besu
  nametag: pectra
  build_args:
    baseimage: hyperledger/besu
    tag: 25.4.1
```

### Git Dockerfile

"Git Dockerfiles" clone a branch of the client from Github and build it from source, for example:

```yaml
- client: go-ethereum
  nametag: experimental
  dockerfile: git
  build_args:
    github: your-username/go-ethereum
    tag: experimental-branch
```

### Using A "Local Dockerfile"

"Local Dockerfiles" can be used to build a client from local source for testing local modifications:

```yaml
- client: go-ethereum
  nametag: local-dev
  dockerfile: local
  build_args:
    local_path: ./clients/go-ethereum/go-ethereum-local
```

This requires copying the local client source code to the Hive directory:

```bash
cp -r /path/to/your/go-ethereum ./clients/go-ethereum/go-ethereum-local
```

### Required Fields

- **`client`**: Must match a directory name in `clients/` within the Hive repository
- **`nametag`**: Unique identifier for this client configuration

### Optional Fields

- **`dockerfile`**: Alternative Dockerfile to use (default: `Dockerfile`)
- **`build_args`**: Docker build arguments passed to the Dockerfile

## Build Arguments

### Common Build Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `tag` | Git commit/tag/branch or Docker tag | `master`, `v1.13.8`, `latest` |
| `github` | GitHub repository for source builds | `ethereum/go-ethereum` |
| `baseimage` | Docker Hub image for binary builds | `ethereum/client-go` |

## Troubleshooting

### Build Issues

Force rebuild base images:

```bash
./hive --docker.pull --sim ethereum/eest/consume-engine
```

Force rebuild specific client:

```bash
./hive --docker.nocache "clients/go-ethereum" --sim ethereum/eest/consume-engine
```

Show the docker container build output:

```bash
./hive --docker.buildoutput --sim ethereum/eest/consume-engine
```
