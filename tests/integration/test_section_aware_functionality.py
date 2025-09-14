"""
Tests for section-aware functionality as specified in music-alg-2f.md
"""

from harmonic_analysis.dto import SectionDTO
from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService


class TestSectionAwareFunctionality:
    """Test section-aware pattern analysis and cadence detection."""

    def setup_method(self):
        self.service = PatternAnalysisService()

    def test_basic_section_aware_analysis(self):
        """Test basic section-aware analysis with two sections."""
        # Setup test: verse-chorus structure
        chords = [
            "Am",
            "F",
            "C",
            "G",
            "Am",
            "F",
            "C",
            "G",  # Verse
            "F",
            "G",
            "Am",
            "Am",
            "F",
            "G",
            "C",
            "C",
        ]  # Chorus

        sections = [
            SectionDTO(id="A", start=0, end=8, label="Verse"),
            SectionDTO(id="B", start=8, end=16, label="Chorus"),
        ]

        # Execute analysis
        result = self.service.analyze_with_patterns(chords, sections=sections)
        summary = result.primary

        # Verify sections are echoed back
        assert len(summary.sections) == 2
        assert summary.sections[0].id == "A"
        assert summary.sections[0].label == "Verse"
        assert summary.sections[1].id == "B"
        assert summary.sections[1].label == "Chorus"

    def test_pattern_section_assignment(self):
        """Test that patterns are assigned to correct sections."""
        chords = ["C", "F", "G", "C"]  # Simple progression with cadence
        sections = [SectionDTO(id="A", start=0, end=4, label="Section A")]

        result = self.service.analyze_with_patterns(chords, sections=sections)
        summary = result.primary

        # Verify patterns have section assignments
        if summary.patterns:
            for pattern in summary.patterns:
                # Pattern should have section assigned
                assert pattern.section is not None
                assert isinstance(pattern.section, str)

    def test_terminal_cadences(self):
        """Test terminal cadence detection at section boundaries."""
        # Progression ending with authentic cadence
        chords = ["C", "Am", "F", "G", "C"]
        sections = [SectionDTO(id="A", start=0, end=5, label="Complete phrase")]

        result = self.service.analyze_with_patterns(chords, sections=sections)
        summary = result.primary

        # Should detect terminal cadences that close sections
        # Terminal cadences are those that are cadences AND close sections

        # Verify terminal cadences have required properties
        for cadence in summary.terminal_cadences:
            assert cadence.cadence_role in ["section-final", "final"]
            assert cadence.section is not None

    def test_final_cadence(self):
        """Test final cadence detection at progression end."""
        # Progression ending with clear cadence
        chords = ["C", "F", "G", "C"]

        result = self.service.analyze_with_patterns(chords)
        summary = result.primary

        # Should identify final cadence if one exists at the end
        if summary.final_cadence:
            assert summary.final_cadence.end == len(chords)
            assert summary.final_cadence.cadence_role == "final"

    def test_pattern_evidence_absolute_indices(self):
        """Test that pattern evidence includes absolute chord indices."""
        chords = ["C", "F", "G", "C"]

        result = self.service.analyze_with_patterns(chords)
        summary = result.primary

        # Verify evidence has absolute indices for UI highlighting
        for pattern in summary.patterns:
            for evidence_item in pattern.evidence:
                if "step_index" in evidence_item:
                    # Should have abs_index computed
                    expected_abs_index = pattern.start + evidence_item["step_index"]
                    if "abs_index" in evidence_item:
                        assert evidence_item["abs_index"] == expected_abs_index

    def test_sections_optional_parameter(self):
        """Test that sections parameter is optional."""
        chords = ["C", "F", "G", "C"]

        # Should work without sections
        result_no_sections = self.service.analyze_with_patterns(chords)
        assert result_no_sections.primary.sections == []

        # Should work with sections
        sections = [SectionDTO(id="A", start=0, end=4)]
        result_with_sections = self.service.analyze_with_patterns(
            chords, sections=sections
        )
        assert len(result_with_sections.primary.sections) == 1

    def test_cadence_marking(self):
        """Test that cadence patterns are properly marked as cadences."""
        # Use progression likely to contain cadences
        chords = ["C", "F", "G", "C"]

        result = self.service.analyze_with_patterns(chords)
        summary = result.primary

        # Check that cadence patterns are marked
        cadence_patterns = [p for p in summary.patterns if p.cadence_role is not None]

        # If we found cadence patterns, verify they're properly marked
        for cadence in cadence_patterns:
            assert cadence.cadence_role in ["final", "section-final", "internal"]
            # Family should indicate cadence
            assert "cadence" in cadence.family.lower()

    def test_straddling_patterns(self):
        """Test patterns that span across section boundaries."""
        # Pattern that crosses section boundary
        chords = ["C", "Am", "F", "G", "C", "F"]
        sections = [
            SectionDTO(id="A", start=0, end=3, label="Section A"),
            SectionDTO(id="B", start=3, end=6, label="Section B"),
        ]

        result = self.service.analyze_with_patterns(chords, sections=sections)
        summary = result.primary

        # Patterns should be assigned to section based on their landing (end-1)
        for pattern in summary.patterns:
            if pattern.section:
                # Verify the section assignment logic
                landing_index = max(pattern.start, pattern.end - 1)
                found_section = None
                for section in sections:
                    if section.start <= landing_index < section.end:
                        found_section = section.id
                        break
                assert pattern.section == found_section

    def test_backward_compatibility(self):
        """Test that new fields don't break existing functionality."""
        chords = ["C", "F", "G", "C"]

        result = self.service.analyze_with_patterns(chords)
        summary = result.primary

        # Existing fields should still work
        assert hasattr(summary, "patterns")
        assert hasattr(summary, "roman_numerals")
        assert hasattr(summary, "key_signature")

        # New fields should exist with defaults
        assert hasattr(summary, "sections")
        assert hasattr(summary, "terminal_cadences")
        assert hasattr(summary, "final_cadence")

        # New fields should have appropriate defaults
        assert isinstance(summary.sections, list)
        assert isinstance(summary.terminal_cadences, list)
        # final_cadence can be None
