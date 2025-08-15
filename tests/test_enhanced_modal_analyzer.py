"""
Tests for Enhanced Modal Analyzer

Tests the sophisticated modal detection capabilities including:
- Pattern recognition (I-bVII-IV-I, etc.)
- Evidence-based confidence scoring
- Mode determination with chord quality discrimination
- Foil pattern detection
"""

from harmonic_analysis import (EnhancedModalAnalyzer, EvidenceType,
                               analyze_modal_progression)


class TestEnhancedModalAnalyzer:
    """Test suite for Enhanced Modal Analyzer"""

    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = EnhancedModalAnalyzer()

    def test_basic_modal_detection(self):
        """Test basic modal characteristic detection"""
        # Test Mixolydian progression (I-bVII-I)
        result = self.analyzer.analyze_modal_characteristics(["G", "F", "G"], "C major")

        assert result is not None
        assert result.mode_name == "G Mixolydian"
        assert "bVII" in result.roman_numerals
        assert result.confidence > 0.7
        assert any("bVII-I cadence" in e.description for e in result.evidence)

    def test_dorian_detection(self):
        """Test Dorian mode detection"""
        # Test Dorian progression (i-IV-i)
        result = self.analyzer.analyze_modal_characteristics(
            ["Am", "D", "Am"], "C major"
        )

        assert result is not None
        assert result.mode_name == "A Dorian"
        assert result.roman_numerals == ["i", "IV", "i"]
        assert result.confidence > 0.7

    def test_phrygian_detection(self):
        """Test Phrygian mode detection"""
        # Test Phrygian progression (i-bII-i)
        result = self.analyzer.analyze_modal_characteristics(
            ["Em", "F", "Em"], "C major"
        )

        assert result is not None
        assert result.mode_name == "E Phrygian"
        assert "bII" in result.roman_numerals
        assert result.confidence > 0.8
        assert any("bII-I cadence" in e.description for e in result.evidence)

    def test_lydian_detection(self):
        """Test Lydian mode detection"""
        # Test Lydian progression (I-II-I)
        result = self.analyzer.analyze_modal_characteristics(["F", "G", "F"], "C major")

        assert result is not None
        assert result.mode_name == "F Lydian"
        assert "II" in result.roman_numerals
        assert result.confidence > 0.7

    def test_ionian_vamp_pattern(self):
        """Test Ionian vamp pattern (I-IV)"""
        result = self.analyzer.analyze_modal_characteristics(["C", "F"], "C major")

        assert result is not None
        assert result.mode_name == "C Ionian"
        assert result.roman_numerals == ["I", "IV"]
        assert result.confidence > 0.6
        assert any("I-IV vamp pattern" in e.description for e in result.evidence)

    def test_dorian_vamp_pattern(self):
        """Test Dorian vamp pattern (i-IV)"""
        result = self.analyzer.analyze_modal_characteristics(["Dm", "G"], "C major")

        assert result is not None
        assert result.mode_name == "D Dorian"
        assert result.roman_numerals == ["i", "IV"]
        assert result.confidence > 0.7
        assert any("i-IV vamp pattern" in e.description for e in result.evidence)

    def test_functional_pattern_blocking(self):
        """Test that clear functional patterns are blocked from modal analysis"""
        # Test I-V-I (pure functional)
        result = self.analyzer.analyze_modal_characteristics(["C", "G", "C"], "C major")

        assert result is None  # Should be blocked as functional

    def test_foil_pattern_detection(self):
        """Test foil pattern detection reduces confidence"""
        # Test I-IV-V-I (functional foil)
        result = self.analyzer.analyze_modal_characteristics(["C", "F", "G", "C"])

        # Should either be None or very low confidence
        if result is not None:
            assert result.confidence < 0.4

    def test_mixolydian_with_dominant7(self):
        """Test Mixolydian detection enhanced by dominant 7th chord"""
        result = self.analyzer.analyze_modal_characteristics(
            ["G7", "F", "G7"], "C major"
        )

        assert result is not None
        assert result.mode_name == "G Mixolydian"
        assert result.confidence > 0.8

    def test_locrian_with_half_diminished(self):
        """Test Locrian detection with half-diminished tonic"""
        result = self.analyzer.analyze_modal_characteristics(["Bm7b5", "C", "Bm7b5"])

        assert result is not None
        assert result.mode_name == "B Locrian"
        assert result.confidence > 0.6  # Locrian detection can be challenging

    def test_evidence_collection(self):
        """Test evidence collection for modal analysis"""
        result = self.analyzer.analyze_modal_characteristics(
            ["G", "F", "C", "G"], "C major"
        )

        assert result is not None
        assert len(result.evidence) > 0

        # Check for structural evidence (starts and ends on same chord)
        structural_evidence = [
            e for e in result.evidence if e.type == EvidenceType.STRUCTURAL
        ]
        assert len(structural_evidence) > 0

        # Check for intervallic evidence (bVII chord)
        intervallic_evidence = [
            e for e in result.evidence if e.type == EvidenceType.INTERVALLIC
        ]
        assert any("bVII chord" in e.description for e in intervallic_evidence)

    def test_parent_key_context(self):
        """Test that parent key context influences mode determination"""
        # Same progression, different parent keys should yield different modes
        chords = ["G", "F", "G"]

        # In C major context - G Mixolydian
        result1 = self.analyzer.analyze_modal_characteristics(chords, "C major")
        assert result1 is not None
        assert result1.mode_name == "G Mixolydian"

        # In G major context - G Ionian
        result2 = self.analyzer.analyze_modal_characteristics(chords, "G major")
        assert result2 is not None
        # Should be different mode or at least different confidence
        assert (
            result1.mode_name != result2.mode_name
            or result1.confidence != result2.confidence
        )

    def test_chord_parsing(self):
        """Test chord parsing with various qualities"""
        # Test various chord types
        test_cases = [
            ("C", "major"),
            ("Cm", "minor"),
            ("C7", "dominant7"),
            ("Cmaj7", "major7"),
            ("Cm7", "minor7"),
            ("Cdim", "diminished"),
            ("Cm7b5", "half_diminished"),
            ("Caug", "augmented"),
            ("Csus4", "suspended"),
        ]

        for chord_symbol, expected_quality in test_cases:
            chord_analysis = self.analyzer._parse_chord(chord_symbol)
            assert chord_analysis.quality == expected_quality
            assert chord_analysis.root == "C"

    def test_roman_numeral_generation(self):
        """Test Roman numeral generation relative to tonic"""
        # Test in C as tonic
        test_cases = [
            ("C", "major", "I"),
            ("Dm", "minor", "ii"),
            ("F", "major", "IV"),
            ("G", "major", "V"),
            ("Bb", "major", "bVII"),
            ("Db", "major", "bII"),
        ]

        for chord_symbol, quality, expected_roman in test_cases:
            chord_analysis = self.analyzer._parse_chord(chord_symbol)
            roman = self.analyzer._generate_modal_roman_numeral(
                chord_analysis, 0
            )  # C = pitch class 0
            assert roman == expected_roman

    def test_empty_input(self):
        """Test handling of empty input"""
        result = self.analyzer.analyze_modal_characteristics([])
        assert result is None

    def test_single_chord(self):
        """Test handling of single chord input"""
        result = self.analyzer.analyze_modal_characteristics(["C"])
        assert result is None

    def test_all_same_chords(self):
        """Test handling of static harmony (all same chords)"""
        result = self.analyzer.analyze_modal_characteristics(["C", "C", "C"])
        assert result is None

    def test_invalid_chord_symbols(self):
        """Test handling of invalid chord symbols"""
        # Mix of valid and invalid chords
        result = self.analyzer.analyze_modal_characteristics(["C", "INVALID", "F"])

        # Should still process valid chords
        if result is not None:
            assert len(result.roman_numerals) == 2  # Only valid chords processed

    def test_convenience_function(self):
        """Test the convenience function export"""
        import asyncio

        async def test_async():
            result = await analyze_modal_progression(["G", "F", "G"], "C major")
            assert result is not None
            assert result.mode_name == "G Mixolydian"

        asyncio.run(test_async())


class TestModalPatterns:
    """Test modal pattern recognition"""

    def setup_method(self):
        self.analyzer = EnhancedModalAnalyzer()

    def test_mixolydian_patterns(self):
        """Test various Mixolydian patterns"""
        patterns = [
            (["G", "F", "G"], "I-bVII-I"),
            (["G", "F", "C", "G"], "I-bVII-IV-I"),
            (["G", "C", "F", "G"], "I-IV-bVII-I"),
        ]

        for chords, pattern_name in patterns:
            result = self.analyzer.analyze_modal_characteristics(chords, "C major")
            assert result is not None
            assert result.mode_name == "G Mixolydian"
            assert result.confidence > 0.7

    def test_dorian_patterns(self):
        """Test various Dorian patterns"""
        patterns = [
            (["Am", "D", "Am"], "i-IV-i"),
            (["Am", "D", "G", "Am"], "i-IV-bVII-i"),
            (["Am", "G", "D", "Am"], "i-bVII-IV-i"),
        ]

        for chords, pattern_name in patterns:
            result = self.analyzer.analyze_modal_characteristics(chords, "C major")
            assert result is not None
            assert result.mode_name == "A Dorian"
            assert result.confidence > 0.7


class TestConfidenceScoring:
    """Test confidence scoring system"""

    def setup_method(self):
        self.analyzer = EnhancedModalAnalyzer()

    def test_clear_modal_high_confidence(self):
        """Test that clear modal patterns have high confidence"""
        # Clear Mixolydian pattern
        result = self.analyzer.analyze_modal_characteristics(
            ["G", "F", "C", "G"], "C major"
        )
        assert result is not None
        assert result.confidence > 0.8

    def test_ambiguous_moderate_confidence(self):
        """Test that ambiguous patterns have moderate confidence"""
        # Ambiguous two-chord pattern
        result = self.analyzer.analyze_modal_characteristics(["C", "F"])
        if result is not None:
            assert 0.4 <= result.confidence <= 0.8

    def test_vamp_pattern_confidence_boost(self):
        """Test confidence boost for valid vamp patterns"""
        # Dorian vamp should get confidence boost
        result = self.analyzer.analyze_modal_characteristics(["Dm", "G"], "C major")
        assert result is not None
        assert result.confidence > 0.7

    def test_seventh_chord_confidence_boost(self):
        """Test confidence boost for characteristic 7th chords"""
        # Mixolydian with dominant 7th
        result = self.analyzer.analyze_modal_characteristics(
            ["G7", "F", "G7"], "C major"
        )
        assert result is not None
        assert result.confidence > 0.8
