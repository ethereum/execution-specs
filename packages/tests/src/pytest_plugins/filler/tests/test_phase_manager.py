"""Unit tests for the PhaseManager class."""

from typing import Any

import pytest

from ethereum_test_fixtures import FixtureFillingPhase

from ..filler import PhaseManager


class MockConfig:
    """Mock pytest config for testing."""

    def __init__(
        self,
        generate_pre_alloc_groups: bool = False,
        use_pre_alloc_groups: bool = False,
        generate_all_formats: bool = False,
    ) -> None:
        """Initialize with flag values."""
        self._options = {
            "generate_pre_alloc_groups": generate_pre_alloc_groups,
            "use_pre_alloc_groups": use_pre_alloc_groups,
            "generate_all_formats": generate_all_formats,
        }

    def getoption(self, name: str, default: Any = None) -> Any:
        """Mock getoption method."""
        return self._options.get(name, default)


class TestPhaseManager:
    """Test cases for PhaseManager class."""

    def test_init(self) -> None:
        """Test basic initialization."""
        phase_manager = PhaseManager(
            current_phase=FixtureFillingPhase.FILL,
            previous_phases={FixtureFillingPhase.PRE_ALLOC_GENERATION},
        )
        assert phase_manager.current_phase == FixtureFillingPhase.FILL
        assert phase_manager.previous_phases == {
            FixtureFillingPhase.PRE_ALLOC_GENERATION
        }

    def test_from_config_normal_fill(self) -> None:
        """Test normal single-phase filling (no flags set)."""
        config = MockConfig()
        phase_manager = PhaseManager.from_config(
            config  # type: ignore[arg-type]
        )

        assert phase_manager.current_phase == FixtureFillingPhase.FILL
        assert phase_manager.previous_phases == set()
        assert phase_manager.is_single_phase_fill
        assert not phase_manager.is_pre_alloc_generation
        assert not phase_manager.is_fill_after_pre_alloc

    def test_from_config_generate_pre_alloc(self) -> None:
        """Test phase 1: generate pre-allocation groups."""
        config = MockConfig(generate_pre_alloc_groups=True)
        phase_manager = PhaseManager.from_config(
            config  # type: ignore[arg-type]
        )

        assert (
            phase_manager.current_phase
            == FixtureFillingPhase.PRE_ALLOC_GENERATION
        )
        assert phase_manager.previous_phases == set()
        assert phase_manager.is_pre_alloc_generation
        assert not phase_manager.is_single_phase_fill
        assert not phase_manager.is_fill_after_pre_alloc

    def test_from_config_use_pre_alloc(self) -> None:
        """Test phase 2: use pre-allocation groups."""
        config = MockConfig(use_pre_alloc_groups=True)
        phase_manager = PhaseManager.from_config(
            config  # type: ignore[arg-type]
        )

        assert phase_manager.current_phase == FixtureFillingPhase.FILL
        assert phase_manager.previous_phases == {
            FixtureFillingPhase.PRE_ALLOC_GENERATION
        }
        assert phase_manager.is_fill_after_pre_alloc
        assert not phase_manager.is_pre_alloc_generation
        assert not phase_manager.is_single_phase_fill

    def test_from_config_generate_all_formats(self) -> None:
        """Generate_all_formats should trigger PRE_ALLOC_GENERATION phase."""
        config = MockConfig(generate_all_formats=True)
        phase_manager = PhaseManager.from_config(
            config  # type: ignore[arg-type]
        )

        assert (
            phase_manager.current_phase
            == FixtureFillingPhase.PRE_ALLOC_GENERATION
        )
        assert phase_manager.previous_phases == set()
        assert phase_manager.is_pre_alloc_generation
        assert not phase_manager.is_single_phase_fill
        assert not phase_manager.is_fill_after_pre_alloc

    def test_from_config_generate_all_and_pre_alloc(self) -> None:
        """Test both generate_all_formats and generate_pre_alloc_groups set."""
        config = MockConfig(
            generate_pre_alloc_groups=True, generate_all_formats=True
        )
        phase_manager = PhaseManager.from_config(
            config  # type: ignore[arg-type]
        )

        assert (
            phase_manager.current_phase
            == FixtureFillingPhase.PRE_ALLOC_GENERATION
        )
        assert phase_manager.previous_phases == set()
        assert phase_manager.is_pre_alloc_generation

    def test_from_config_use_pre_alloc_with_generate_all(self) -> None:
        """Test phase 2 with generate_all_formats (passed by CLI)."""
        config = MockConfig(
            use_pre_alloc_groups=True, generate_all_formats=True
        )
        phase_manager = PhaseManager.from_config(
            config  # type: ignore[arg-type]
        )

        # use_pre_alloc_groups takes precedence
        assert phase_manager.current_phase == FixtureFillingPhase.FILL
        assert phase_manager.previous_phases == {
            FixtureFillingPhase.PRE_ALLOC_GENERATION
        }
        assert phase_manager.is_fill_after_pre_alloc

    def test_all_flag_combinations(self) -> None:
        """
        Test all 8 possible flag combinations to ensure correct phase
        determination.
        """
        test_cases = [
            # (generate_pre_alloc, use_pre_alloc, generate_all) ->
            # (current_phase, has_previous)
            # Normal fill
            (False, False, False, FixtureFillingPhase.FILL, False),
            # Generate all triggers phase 1
            (
                False,
                False,
                True,
                FixtureFillingPhase.PRE_ALLOC_GENERATION,
                False,
            ),
            (False, True, False, FixtureFillingPhase.FILL, True),  # Phase 2
            # Phase 2 with generate all
            (False, True, True, FixtureFillingPhase.FILL, True),
            (
                True,
                False,
                False,
                FixtureFillingPhase.PRE_ALLOC_GENERATION,
                False,
            ),  # Phase 1
            # Phase 1 with generate all
            (
                True,
                False,
                True,
                FixtureFillingPhase.PRE_ALLOC_GENERATION,
                False,
            ),
            # Invalid but use_pre_alloc wins
            (True, True, False, FixtureFillingPhase.FILL, True),
            # Invalid but use_pre_alloc wins
            (True, True, True, FixtureFillingPhase.FILL, True),
        ]

        for (
            gen_pre,
            use_pre,
            gen_all,
            expected_phase,
            has_previous,
        ) in test_cases:
            config = MockConfig(
                generate_pre_alloc_groups=gen_pre,
                use_pre_alloc_groups=use_pre,
                generate_all_formats=gen_all,
            )
            phase_manager = PhaseManager.from_config(
                config  # type: ignore[arg-type]
            )

            assert phase_manager.current_phase == expected_phase, (
                f"Failed for flags: generate_pre_alloc={gen_pre}, "
                f"use_pre_alloc={use_pre}, generate_all={gen_all}"
            )

            if has_previous:
                assert (
                    FixtureFillingPhase.PRE_ALLOC_GENERATION
                    in phase_manager.previous_phases
                )
            else:
                assert phase_manager.previous_phases == set()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
