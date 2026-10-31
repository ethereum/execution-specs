"""Shared paths for the deployed-idiom corpus.

The corpus lives inside the execution-spec repo at `tests/deployed_idioms/`,
alongside the other non-fork suites (`benchmark/`, `ported_static/`). Two
waves, each a directory of archetypes:

    wave1/<archetype>/test_*.py      EIP-8037 / EIP-8038 era
    expansion/<archetype>/test_*.py  Fusaka and Glamsterdam surfaces
    <wave>/instruments/test_*.py     measurement probes -- NOT corpus tests,
                                     their failures are the measurement
    tools/mutations/*.json           mutation definitions, one file per author
    docs/                            invariants, mutation matrix, alarm semantics
"""

import os
from pathlib import Path

CORPUS = Path(__file__).resolve().parents[1]
WAVES = ("wave1", "expansion")
INSTRUMENTS = "instruments"


def spec_root() -> Path:
    """The execution-spec checkout: walk up for src/ethereum/forks."""
    env = os.environ.get("EELS_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if not (p / "src" / "ethereum" / "forks").is_dir():
            raise SystemExit(f"EELS_ROOT={p} has no src/ethereum/forks/")
        return p
    for p in [CORPUS, *CORPUS.parents]:
        if (p / "src" / "ethereum" / "forks").is_dir():
            return p
    raise SystemExit(
        "Not inside an execution-spec checkout and EELS_ROOT is unset. "
        "Set EELS_ROOT=/path/to/execution-specs."
    )


def fill_bin() -> Path:
    import shutil
    venv = spec_root() / ".venv" / "bin" / "fill"
    if venv.exists():
        return venv
    found = shutil.which("fill")
    if found:
        return Path(found)
    raise SystemExit(f"No `fill`: looked in {venv} and on PATH.")


def forks_dir() -> Path:
    return spec_root() / "src" / "ethereum" / "forks"


def wave_dirs(wave: str | None = None) -> list[Path]:
    names = WAVES if wave in (None, "all") else (wave,)
    out = []
    for n in names:
        d = CORPUS / n
        if not d.is_dir():
            raise SystemExit(f"no such wave: {n} (have: {', '.join(WAVES)})")
        out.append(d)
    return out


def archetypes(wave: str | None = None) -> dict[str, Path]:
    """name -> directory, for every archetype in the selected wave(s)."""
    out = {}
    for wd in wave_dirs(wave):
        for d in sorted(wd.iterdir()):
            if d.is_dir() and d.name != INSTRUMENTS and any(d.glob("test_*.py")):
                out[f"{wd.name}/{d.name}"] = d
    return out


def mutations_dir() -> Path:
    return CORPUS / "tools" / "mutations"


def lock_path() -> Path:
    return CORPUS / "tools" / ".mutate.lock"
