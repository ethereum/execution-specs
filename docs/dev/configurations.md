# Managing Configurations

Configurations are managed by the `config` package. It provides both environment and application configurations.

```console
.
├── src
│   └── 📁 config  [Application wide environment and configurations]
│       ├── 📄 __init__.py
│       ├── 📄 app.py [Configurations for application framework]
│       ├── 📄 docs.py [Configurations for documentation]
│       └── 📄 env.py  [Exposes `env.yaml` to the application]
└── 📄 env.yaml [Environment file (git ignored)]
```

## Environment Configurations

Application-wide [environment configuration](https://www.12factor.net/config), which varies across staging, production, and development environments are read from `env.yaml` in the project root.

This file will not be tracked by git, making it safe for storing local secrets.

To get started, run the command `eest make env` cli to initialize your environment configuration.

### Usage

#### 1. Generate env file

Run the `eest make env` cli tool.

```console
uv run eest make env
🎉 Success! Config file created at: <path>/env.yaml
```

which should generate an `env.yaml` in the project root.

```yaml
remote_nodes:
  - name: mainnet_archive
    # Replace with your Ethereum RPC node URL
    node_url: http://example.com
    # Optional: Headers for RPC requests
    rpc_headers:
      client-secret: <secret>
```

#### 2. Import `EnvConfig`

```console
from config import EnvConfig
EnvConfig().remote_nodes[0].name
'mainnet_archive'
```

## Application configuration

Application configuration are pydantic classes.

```console
from config import DocsConfig
DocsConfig().TARGET_FORK
'Prague'
```
