"""Unit tests for the FormatSelector class."""

from typing import List, Set, Tuple

from ethereum_test_fixtures import BaseFixture, FixtureFillingPhase, LabeledFixtureFormat

from ..filler import FormatSelector, PhaseManager


class TestFormatSelector:
    """Test cases for FormatSelector class."""

    def test_init(self):
        """Test basic initialization."""
        phase_manager = PhaseManager(current_phase=FixtureFillingPhase.FILL)
        format_selector = FormatSelector(phase_manager=phase_manager, generate_all_formats=False)
        assert format_selector.phase_manager is phase_manager

    def test_should_generate_pre_alloc_phase_with_pre_alloc_format(self):
        """Test pre-alloc phase with format that supports pre-alloc."""
        phase_manager = PhaseManager(current_phase=FixtureFillingPhase.PRE_ALLOC_GENERATION)
        format_selector = FormatSelector(phase_manager=phase_manager, generate_all_formats=False)

        # MySub = type("MySub", (BaseClass,), {"MY_CLASSVAR": 42})
        format_with_pre_alloc = type(
            "MockFixtureFormat",
            (BaseFixture,),
            {
                "format_phases": {
                    FixtureFillingPhase.PRE_ALLOC_GENERATION,
                    FixtureFillingPhase.FILL,
                }
            },
        )

        assert format_selector.should_generate(format_with_pre_alloc)

    def test_should_generate_pre_alloc_phase_without_pre_alloc_format(self):
        """Test pre-alloc phase with format that doesn't support pre-alloc."""
        phase_manager = PhaseManager(current_phase=FixtureFillingPhase.PRE_ALLOC_GENERATION)
        format_selector = FormatSelector(phase_manager=phase_manager, generate_all_formats=False)

        format_without_pre_alloc = type(
            "MockFixtureFormat",
            (BaseFixture,),
            {"format_phases": {FixtureFillingPhase.FILL}},
        )

        assert not format_selector.should_generate(format_without_pre_alloc)

    def test_should_generate_single_phase_fill_only_format(self):
        """Test single-phase fill with fill-only format."""
        phase_manager = PhaseManager(current_phase=FixtureFillingPhase.FILL)
        format_selector = FormatSelector(phase_manager=phase_manager, generate_all_formats=False)

        fill_only_format = type(
            "MockFixtureFormat",
            (BaseFixture,),
            {"format_phases": {FixtureFillingPhase.FILL}},
        )

        assert format_selector.should_generate(fill_only_format)

    def test_should_generate_single_phase_pre_alloc_format(self):
        """Test single-phase fill with format that supports pre-alloc."""
        phase_manager = PhaseManager(current_phase=FixtureFillingPhase.FILL)
        format_selector = FormatSelector(phase_manager=phase_manager, generate_all_formats=False)

        format_with_pre_alloc = type(
            "MockFixtureFormat",
            (BaseFixture,),
            {
                "format_phases": {
                    FixtureFillingPhase.PRE_ALLOC_GENERATION,
                    FixtureFillingPhase.FILL,
                }
            },
        )

        # Should not generate because it needs pre-alloc but we're in single phase
        assert not format_selector.should_generate(format_with_pre_alloc)

    def test_should_generate_phase2_with_pre_alloc_format(self):
        """Test phase 2 (after pre-alloc) with format that supports pre-alloc."""
        phase_manager = PhaseManager(
            current_phase=FixtureFillingPhase.FILL,
            previous_phases={FixtureFillingPhase.PRE_ALLOC_GENERATION},
        )
        format_selector = FormatSelector(phase_manager=phase_manager, generate_all_formats=False)

        format_with_pre_alloc = type(
            "MockFixtureFormat",
            (BaseFixture,),
            {
                "format_phases": {
                    FixtureFillingPhase.PRE_ALLOC_GENERATION,
                    FixtureFillingPhase.FILL,
                }
            },
        )

        # Should generate in phase 2
        assert format_selector.should_generate(format_with_pre_alloc)

    def test_should_generate_phase2_without_pre_alloc_format(self):
        """Test phase 2 (after pre-alloc) with fill-only format."""
        phase_manager = PhaseManager(
            current_phase=FixtureFillingPhase.FILL,
            previous_phases={FixtureFillingPhase.PRE_ALLOC_GENERATION},
        )
        format_selector = FormatSelector(phase_manager=phase_manager, generate_all_formats=False)

        fill_only_format = type(
            "MockFixtureFormat",
            (BaseFixture,),
            {"format_phases": {FixtureFillingPhase.FILL}},
        )

        # Should not generate because it doesn't need pre-alloc
        assert not format_selector.should_generate(fill_only_format)

    def test_should_generate_phase2_with_generate_all(self):
        """Test phase 2 with --generate-all-formats flag."""
        phase_manager = PhaseManager(
            current_phase=FixtureFillingPhase.FILL,
            previous_phases={FixtureFillingPhase.PRE_ALLOC_GENERATION},
        )
        format_selector = FormatSelector(phase_manager=phase_manager, generate_all_formats=True)

        fill_only_format = type(
            "MockFixtureFormat",
            (BaseFixture,),
            {"format_phases": {FixtureFillingPhase.FILL}},
        )
        format_with_pre_alloc = type(
            "MockFixtureFormat",
            (BaseFixture,),
            {
                "format_phases": {
                    FixtureFillingPhase.PRE_ALLOC_GENERATION,
                    FixtureFillingPhase.FILL,
                }
            },
        )

        # With generate_all=True, both formats should be generated
        assert format_selector.should_generate(fill_only_format)
        assert format_selector.should_generate(format_with_pre_alloc)

    def test_should_generate_labeled_format(self):
        """Test with LabeledFixtureFormat wrapper."""
        phase_manager = PhaseManager(current_phase=FixtureFillingPhase.FILL)
        format_selector = FormatSelector(phase_manager=phase_manager, generate_all_formats=False)

        fill_only_format = type(
            "MockFixtureFormat",
            (BaseFixture,),
            {"format_phases": {FixtureFillingPhase.FILL}},
        )
        labeled_format = LabeledFixtureFormat(
            fill_only_format,
            "mock_labeled_format",
            "A mock labeled fixture format",
        )

        assert format_selector.should_generate(labeled_format)

    def test_comprehensive_scenarios(self):
        """Test comprehensive scenarios covering all phase and format combinations."""
        # Test matrix: (current_phase, previous_phases, format_phases, generate_all) -> expected
        test_cases: List[
            Tuple[
                FixtureFillingPhase, Set[FixtureFillingPhase], Set[FixtureFillingPhase], bool, bool
            ]
        ] = [
            # Pre-alloc generation phase
            (
                FixtureFillingPhase.PRE_ALLOC_GENERATION,
                set(),
                {FixtureFillingPhase.PRE_ALLOC_GENERATION, FixtureFillingPhase.FILL},
                False,
                True,
            ),
            (
                FixtureFillingPhase.PRE_ALLOC_GENERATION,
                set(),
                {FixtureFillingPhase.FILL},
                False,
                False,
            ),
            # Single-phase fill
            (FixtureFillingPhase.FILL, set(), {FixtureFillingPhase.FILL}, False, True),
            (
                FixtureFillingPhase.FILL,
                set(),
                {FixtureFillingPhase.PRE_ALLOC_GENERATION, FixtureFillingPhase.FILL},
                False,
                False,
            ),
            # Phase 2 without generate_all
            (
                FixtureFillingPhase.FILL,
                {FixtureFillingPhase.PRE_ALLOC_GENERATION},
                {FixtureFillingPhase.PRE_ALLOC_GENERATION, FixtureFillingPhase.FILL},
                False,
                True,
            ),
            (
                FixtureFillingPhase.FILL,
                {FixtureFillingPhase.PRE_ALLOC_GENERATION},
                {FixtureFillingPhase.FILL},
                False,
                False,
            ),
            # Phase 2 with generate_all
            (
                FixtureFillingPhase.FILL,
                {FixtureFillingPhase.PRE_ALLOC_GENERATION},
                {FixtureFillingPhase.PRE_ALLOC_GENERATION, FixtureFillingPhase.FILL},
                True,
                True,
            ),
            (
                FixtureFillingPhase.FILL,
                {FixtureFillingPhase.PRE_ALLOC_GENERATION},
                {FixtureFillingPhase.FILL},
                True,
                True,
            ),
        ]

        for current, previous, format_phases, gen_all, expected in test_cases:
            phase_manager = PhaseManager(current_phase=current, previous_phases=previous)
            format_selector = FormatSelector(
                phase_manager=phase_manager, generate_all_formats=gen_all
            )
            fixture_format = type(
                "MockFixtureFormat",
                (BaseFixture,),
                {"format_phases": format_phases},
            )

            result = format_selector.should_generate(fixture_format)
            assert result == expected, (
                f"Failed for phase={current}, previous={previous}, "
                f"format_phases={format_phases}, generate_all={gen_all}"
            )
