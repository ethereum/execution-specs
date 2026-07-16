"""
SSZ static-vector generation on top of the base_types SSZ engine.

Because any SszModel already yields its three artifacts -- the value (as JSON),
the serialized SSZ bytes (encode), and the hash_tree_root -- a consensus-style
ssz_static case is just those three, and the generator is a reflection loop
over models x randomization modes. The old approach generated at the
remerkleable-container level; here the SszModel *is* both the value producer
and the serializer, so the generator carries no SSZ knowledge of its own.

A case mirrors the consensus layout: value.yaml / serialized.ssz / roots.yaml.
The randomization modes are ours (remerkleable ships no random producer):
ZERO uses ssz_default; RANDOM/MAX walk the field specs deterministically.
"""

import random
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterator, Sequence, Tuple, Type

from .ssz import (
    SSZ_BOOL,
    SszBitlist,
    SszBitvector,
    SszByteList,
    SszByteVector,
    SszContainer,
    SszList,
    SszModel,
    SszProgressiveBitlist,
    SszProgressiveContainer,
    SszProgressiveList,
    SszSpec,
    SszUint,
    SszVector,
    _spec_of,
    encode,
    hash_tree_root,
    ssz_default,
)

# Caps for variable-length fields in random/max modes (keep vectors small).
_MAX_LIST = 4
_MAX_BYTES = 8


class RandomizationMode(Enum):
    """How a case's value is produced."""

    ZERO = "zero"
    RANDOM = "random"
    MAX = "max"


@dataclass(frozen=True)
class VectorCase:
    """One ssz_static case: the value, its SSZ bytes, and its root."""

    value: Any  # JSON-ready dict (value.yaml)
    serialized: bytes  # serialized.ssz
    root: bytes  # roots.yaml


def _rand_uint(bits: int, mode: RandomizationMode, rng: random.Random) -> int:
    if mode is RandomizationMode.MAX:
        return (1 << bits) - 1
    return rng.randrange(0, 1 << bits)


def _random_value(
    spec: SszSpec, mode: RandomizationMode, rng: random.Random
) -> Any:
    """Produce a random (or max) pydantic value for ``spec``."""
    if isinstance(spec, SszUint):
        return _rand_uint(spec.bits, mode, rng)
    if isinstance(spec, SszByteVector):
        return bytes(rng.randrange(256) for _ in range(spec.length))
    if isinstance(spec, SszByteList):
        n = min(spec.limit, _MAX_BYTES)
        return bytes(rng.randrange(256) for _ in range(n))
    if isinstance(spec, (SszList, SszProgressiveList)):
        limit = getattr(spec, "limit", _MAX_LIST)
        n = min(limit, _MAX_LIST)
        return [_random_value(spec.element, mode, rng) for _ in range(n)]
    if isinstance(spec, SszVector):
        return [
            _random_value(spec.element, mode, rng) for _ in range(spec.length)
        ]
    if isinstance(spec, SszBitvector):
        return [rng.random() < 0.5 for _ in range(spec.length)]
    if isinstance(spec, (SszBitlist, SszProgressiveBitlist)):
        return [rng.random() < 0.5 for _ in range(_MAX_LIST)]
    if isinstance(spec, (SszContainer, SszProgressiveContainer)):
        return _random_model(spec.model, mode, rng)
    if spec is SSZ_BOOL:
        return mode is RandomizationMode.MAX or rng.random() < 0.5
    raise TypeError(f"no random value for spec {spec!r}")


def _random_model(
    model_cls: Type[SszModel], mode: RandomizationMode, rng: random.Random
) -> SszModel:
    return model_cls(
        **{
            name: _random_value(_spec_of(model_cls, name), mode, rng)
            for name in model_cls.model_fields
        }
    )


def build_value(
    model_cls: Type[SszModel], mode: RandomizationMode, rng: random.Random
) -> SszModel:
    """Build a model instance for ``mode`` (ZERO uses the SSZ default)."""
    if mode is RandomizationMode.ZERO:
        return ssz_default(model_cls)
    return _random_model(model_cls, mode, rng)


def make_case(model: SszModel) -> VectorCase:
    """Turn a model instance into its ssz_static case triple."""
    return VectorCase(
        value=model.model_dump(mode="json"),
        serialized=encode(model),
        root=hash_tree_root(model),
    )


def generate_cases(
    models: Sequence[Type[SszModel]],
    *,
    modes: Sequence[RandomizationMode] = tuple(RandomizationMode),
    count: int = 3,
) -> Iterator[Tuple[str, str, int, VectorCase]]:
    """
    Yield ``(model_name, mode, case_index, case)`` for every vector.

    ZERO yields a single case; changing modes yield ``count`` cases each. The
    RNG is seeded per (model, mode, index) so output is deterministic.
    """
    for model_cls in models:
        for mode in modes:
            n = 1 if mode is RandomizationMode.ZERO else count
            for i in range(n):
                rng = random.Random(f"{model_cls.__name__}:{mode.value}:{i}")
                yield (
                    model_cls.__name__,
                    mode.value,
                    i,
                    make_case(build_value(model_cls, mode, rng)),
                )


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


__all__ = [
    "RandomizationMode",
    "VectorCase",
    "build_value",
    "case_files",
    "generate_cases",
    "make_case",
]
