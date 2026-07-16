"""
SSZ static-vector generation on top of the base_types SSZ engine.

A faithful port of the consensus-specs ssz_static generator
(get_random_ssz_object + RandomizationMode), driven by the engine's SszType
descriptors instead of remerkleable types: values are built as plain pydantic
models and all serialization / merkleization is delegated to the engine
(encode / hash_tree_root), so no encoding logic lives here.

Suites mirror consensus-specs exactly, one per RandomizationMode plus a chaos
suite (ssz_random, ssz_zero, ssz_max, ssz_nil, ssz_one, ssz_lengthy,
ssz_random_chaos). Mode semantics are the consensus ones:
zero/max pin scalar CONTENT (0 / all-ones) but keep collections short
(1-byte byte-lists), while emptiness and saturation are their own modes
(nil_count / max_count). Changing modes (random / one_count / max_count /
chaos) yield several cases; the rest are fully determined by one.

A case is the consensus triple value.yaml / serialized.ssz / roots.yaml
(serialized bytes are uncompressed -- a deliberate deviation from the
consensus .ssz_snappy, avoiding a libsnappy dependency). Seeding is
sha256(container / suite / case_index), so output is fully deterministic.
"""

import hashlib
import random
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    Sequence,
    Tuple,
    Type,
    TypeVar,
)

from execution_testing.base_types.ssz import (
    SszBitlist,
    SszBitvector,
    SszBool,
    SszByteList,
    SszByteVector,
    SszContainer,
    SszList,
    SszModel,
    SszProgressiveBitlist,
    SszProgressiveContainer,
    SszProgressiveList,
    SszType,
    SszUint,
    SszVector,
    encode,
    hash_tree_root,
    spec_of,
)

# Caps for variable-length fields; the consensus-specs ssz_static values.
MAX_LIST_LENGTH = 10
MAX_BYTES_LENGTH = 1000

# Cases per changing (non-deterministic) mode, as consensus-specs' minimal
# preset (cases_if_random). Deterministic modes get one.
RANDOM_CASE_COUNT = 30

_M = TypeVar("_M", bound=SszModel)

# The consensus-specs random_mode_names, verbatim (suites are ssz_<name>).
_MODE_NAMES = (
    "random",
    "zero",
    "max",
    "nil",
    "one",
    "lengthy",
)


class RandomizationMode(Enum):
    """
    How a value's scalar and collection fields are filled.

    Mirrors the consensus-specs RandomizationMode.
    """

    mode_random = 0
    mode_zero = 1
    mode_max = 2
    mode_nil_count = 3
    mode_one_count = 4
    mode_max_count = 5

    def is_changing(self) -> bool:
        """
        Return whether the mode yields varying values across cases.

        True for random, one_count and max_count -- those randomize content,
        so several cases are worth generating; the rest are fully determined
        by a single case.
        """
        return self in (
            RandomizationMode.mode_random,
            RandomizationMode.mode_one_count,
            RandomizationMode.mode_max_count,
        )

    def to_name(self) -> str:
        """Return the canonical short name for this mode."""
        return _MODE_NAMES[self.value]


def deterministic_seed(*parts: object) -> int:
    """
    Return a stable integer seed derived from parts.

    Uses SHA-256 over the slash-joined string parts.
    """
    joined = "/".join(str(part) for part in parts)
    digest = hashlib.sha256(joined.encode("utf-8")).digest()
    return int.from_bytes(digest, "big")


@dataclass(frozen=True)
class VectorCase:
    """One ssz_static case: the value, its SSZ bytes, and its root."""

    value: Any  # value.yaml
    serialized: bytes  # serialized.ssz
    root: bytes  # roots.yaml


def _random_bytes(rng: random.Random, length: int) -> bytes:
    return bytes(rng.getrandbits(8) for _ in range(length))


def _bits(rng: random.Random, length: int, mode: RandomizationMode) -> Any:
    if mode == RandomizationMode.mode_zero:
        return [False] * length
    if mode == RandomizationMode.mode_max:
        return [True] * length
    return [bool(rng.getrandbits(1)) for _ in range(length)]


def _bitlist_length(
    rng: random.Random, cap: int, one_cap: int, mode: RandomizationMode
) -> int:
    if mode == RandomizationMode.mode_nil_count:
        return 0
    if mode == RandomizationMode.mode_max_count:
        return cap
    if mode in (
        RandomizationMode.mode_one_count,
        RandomizationMode.mode_zero,
        RandomizationMode.mode_max,
    ):
        return one_cap
    return rng.randint(0, cap)


def random_value(
    rng: random.Random,
    spec: SszType,
    mode: RandomizationMode,
    *,
    max_bytes_length: int = MAX_BYTES_LENGTH,
    max_list_length: int = MAX_LIST_LENGTH,
    chaos: bool = False,
) -> Any:
    """
    Build a pydantic value of spec filled with random data per mode.

    A port of the consensus-specs get_random_ssz_object, branching on the
    engine's SszType descriptors. With chaos, the mode is re-drawn at every
    level of the value tree.
    """
    if chaos:
        mode = rng.choice(list(RandomizationMode))
    if isinstance(spec, SszByteList):
        if mode == RandomizationMode.mode_nil_count:
            return b""
        if mode == RandomizationMode.mode_max_count:
            return _random_bytes(rng, min(max_bytes_length, spec.limit))
        if mode == RandomizationMode.mode_one_count:
            return _random_bytes(rng, min(1, spec.limit))
        if mode == RandomizationMode.mode_zero:
            return b"\x00" * min(1, spec.limit)
        if mode == RandomizationMode.mode_max:
            return b"\xff" * min(1, spec.limit)
        return _random_bytes(
            rng, rng.randint(0, min(max_bytes_length, spec.limit))
        )
    if isinstance(spec, SszByteVector):
        # Byte vectors are fixed length; no max-bytes cap applies.
        if mode == RandomizationMode.mode_zero:
            return b"\x00" * spec.length
        if mode == RandomizationMode.mode_max:
            return b"\xff" * spec.length
        return _random_bytes(rng, spec.length)
    if isinstance(spec, SszUint):
        if mode == RandomizationMode.mode_zero:
            return 0
        if mode == RandomizationMode.mode_max:
            return (1 << spec.bits) - 1
        return rng.randint(0, (1 << spec.bits) - 1)
    if isinstance(spec, SszBool):
        if mode == RandomizationMode.mode_zero:
            return False
        if mode == RandomizationMode.mode_max:
            return True
        return bool(rng.getrandbits(1))
    if isinstance(spec, SszBitvector):
        # Bit vectors are fixed length; no cap applies.
        return _bits(rng, spec.length, mode)
    if isinstance(spec, SszBitlist):
        cap = min(max_bytes_length, spec.limit)
        length = _bitlist_length(rng, cap, min(1, spec.limit), mode)
        return _bits(rng, length, mode)
    if isinstance(spec, SszProgressiveBitlist):
        # Progressive bit lists are uncapped; the byte cap bounds them.
        length = _bitlist_length(rng, max_bytes_length, 1, mode)
        return _bits(rng, length, mode)
    if isinstance(spec, (SszList, SszProgressiveList)):
        # Progressive lists are uncapped; the list cap bounds them.
        limit = max_list_length
        if isinstance(spec, SszList) and spec.limit < limit:
            limit = spec.limit
        length = rng.randint(0, limit)
        if mode == RandomizationMode.mode_one_count:
            length = 1
        elif mode == RandomizationMode.mode_max_count:
            length = limit
        elif mode == RandomizationMode.mode_nil_count:
            length = 0
        # Shrink the cap for nested collections, as consensus-specs does.
        max_list_length = 1 << (max_list_length.bit_length() >> 1)
        return [
            random_value(
                rng,
                spec.element,
                mode,
                max_bytes_length=max_bytes_length,
                max_list_length=max_list_length,
                chaos=chaos,
            )
            for _ in range(length)
        ]
    if isinstance(spec, SszVector):
        return [
            random_value(
                rng,
                spec.element,
                mode,
                max_bytes_length=max_bytes_length,
                max_list_length=max_list_length,
                chaos=chaos,
            )
            for _ in range(spec.length)
        ]
    if isinstance(spec, (SszContainer, SszProgressiveContainer)):
        return random_model(
            rng,
            spec.model,
            mode,
            max_bytes_length=max_bytes_length,
            max_list_length=max_list_length,
            chaos=chaos,
        )
    raise TypeError(f"no random value for SSZ type {spec!r}")


def random_model(
    rng: random.Random,
    model_cls: Type[_M],
    mode: RandomizationMode,
    *,
    max_bytes_length: int = MAX_BYTES_LENGTH,
    max_list_length: int = MAX_LIST_LENGTH,
    chaos: bool = False,
) -> _M:
    """Build a model_cls instance filled with random data per mode."""
    return model_cls(
        **{
            name: random_value(
                rng,
                spec_of(model_cls, name),
                mode,
                max_bytes_length=max_bytes_length,
                max_list_length=max_list_length,
                chaos=chaos,
            )
            for name in model_cls.model_fields
        }
    )


def make_case(model: SszModel) -> VectorCase:
    """Turn a model instance into its ssz_static case triple."""
    return VectorCase(
        value=model.model_dump(mode="json"),
        serialized=encode(model),
        root=hash_tree_root(model),
    )


def suite_name(mode: RandomizationMode, chaos: bool = False) -> str:
    """Return the consensus suite name for a mode (ssz_random, ...)."""
    return f"ssz_{mode.to_name()}" + ("_chaos" if chaos else "")


def suite_plan(
    count: int = RANDOM_CASE_COUNT,
) -> List[Tuple[str, RandomizationMode, bool, int]]:
    """
    Return every suite as (name, mode, chaos, case_count).

    One suite per RandomizationMode plus ssz_random_chaos; changing modes
    get count cases, deterministic ones a single case.
    """
    plan = [
        (
            suite_name(mode),
            mode,
            False,
            count if mode.is_changing() else 1,
        )
        for mode in RandomizationMode
    ]
    plan.append(
        (
            suite_name(RandomizationMode.mode_random, chaos=True),
            RandomizationMode.mode_random,
            True,
            count,
        )
    )
    return plan


def generate_cases(
    models: Sequence[Type[SszModel]],
    *,
    count: int = RANDOM_CASE_COUNT,
    max_bytes_length: int = MAX_BYTES_LENGTH,
    max_list_length: int = MAX_LIST_LENGTH,
) -> Iterator[Tuple[str, str, int, VectorCase]]:
    """
    Yield (container_name, suite, case_index, case) for every vector.

    The RNG is seeded per (container, suite, index) so output is fully
    deterministic across runs.
    """
    for model_cls in models:
        for suite, mode, chaos, n in suite_plan(count):
            for i in range(n):
                rng = random.Random(
                    deterministic_seed(model_cls.__name__, suite, i)
                )
                model = random_model(
                    rng,
                    model_cls,
                    mode,
                    max_bytes_length=max_bytes_length,
                    max_list_length=max_list_length,
                    chaos=chaos,
                )
                yield model_cls.__name__, suite, i, make_case(model)


def case_files(case: VectorCase) -> Dict[str, bytes]:
    """The on-disk files for a case (bytes), mirroring the consensus layout."""
    import yaml

    return {
        "value.yaml": yaml.safe_dump(case.value, sort_keys=False).encode(),
        "serialized.ssz": case.serialized,
        "roots.yaml": yaml.safe_dump(
            {"root": "0x" + case.root.hex()}
        ).encode(),
    }


def case_dir(
    output_dir: Path, container_name: str, suite: str, case_index: int
) -> Path:
    """Return the per-case output directory for a given case."""
    return output_dir / container_name / suite / f"case_{case_index}"


def write_case(directory: Path, case: VectorCase) -> None:
    """Write a case's value.yaml / serialized.ssz / roots.yaml."""
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in case_files(case).items():
        (directory / name).write_bytes(data)


def write_vectors(
    models: Sequence[Type[SszModel]],
    output_dir: Path,
    *,
    count: int = RANDOM_CASE_COUNT,
) -> int:
    """Write every vector case under output_dir; return the count."""
    written = 0
    for container_name, suite, case_index, case in generate_cases(
        models, count=count
    ):
        write_case(
            case_dir(output_dir, container_name, suite, case_index), case
        )
        written += 1
    return written


__all__ = [
    "MAX_BYTES_LENGTH",
    "MAX_LIST_LENGTH",
    "RANDOM_CASE_COUNT",
    "RandomizationMode",
    "VectorCase",
    "case_dir",
    "case_files",
    "deterministic_seed",
    "generate_cases",
    "make_case",
    "random_model",
    "random_value",
    "suite_name",
    "suite_plan",
    "write_case",
    "write_vectors",
]
