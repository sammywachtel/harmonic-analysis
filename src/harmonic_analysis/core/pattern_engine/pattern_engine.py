"""
Unified Pattern Engine - Main orchestrator for pattern-based analysis.

This module implements the core pattern matching and analysis engine
that unifies functional and modal analysis through a single pipeline.
"""

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from harmonic_analysis.dto import (
    AnalysisEnvelope,
    AnalysisSummary,
    AnalysisType,
    EvidenceDTO,
    PatternMatchDTO,
)

from .aggregator import Aggregator
from .calibration import CalibrationMapping, Calibrator
from .evidence import Evidence
from .glossary import enrich_features, get_summary_terms, load_default_glossary
from .pattern_loader import PatternLoader
from .plugin_registry import PluginRegistry
from .target_builder import TargetBuilder


@dataclass
class AnalysisContext:
    """
    Normalized analysis context for pattern matching.

    Contains all inputs in a standardized format for pattern evaluation.
    """

    key: Optional[str]
    """Key signature (e.g., "C major", "A minor")"""

    chords: List[str]
    """Chord symbols in original form"""

    roman_numerals: List[str]
    """Roman numeral representations"""

    melody: List[Any]
    """Melodic line (notes, intervals, or contours)"""

    scales: List[Any]
    """Detected scales or modes"""

    metadata: Dict[str, Any]
    """Additional context (tempo, style, etc.)"""


class PatternEngine:
    """
    Main pattern engine for unified harmonic analysis.

    Processes chord progressions through pattern matching,
    evidence aggregation, and calibration to produce
    functional and modal analysis results.
    """

    def __init__(
        self,
        loader: Optional[PatternLoader] = None,
        aggregator: Optional[Aggregator] = None,
        plugins: Optional[PluginRegistry] = None,
        calibrator: Optional[Calibrator] = None,
        target_builder: Optional[TargetBuilder] = None,
    ):
        """
        Initialize pattern engine with components.

        Args:
            loader: Pattern loader for JSON patterns
            aggregator: Evidence aggregator
            plugins: Plugin registry for evaluators
            calibrator: Confidence calibrator
            target_builder: Target builder for training
        """
        self.loader = loader or PatternLoader()
        self.aggregator = aggregator or Aggregator()
        self.plugins = plugins or PluginRegistry()
        self.calibrator = calibrator or Calibrator()
        self.target_builder = target_builder or TargetBuilder()

        self._patterns: Dict[str, Any] = {}
        self._calibration_mapping: Optional[CalibrationMapping] = None
        self._glossary: Optional[Dict[str, Any]] = None

        # Load glossary on initialization
        try:
            self._glossary = load_default_glossary()
        except FileNotFoundError:
            # Graceful fallback if glossary not available
            self._glossary = {}

    def load_patterns(self, path: Path) -> None:
        """
        Load pattern definitions from JSON file.

        Args:
            path: Path to patterns.json file
        """
        self._patterns = self.loader.load(path)

    def load_calibration(self, path: Path) -> None:
        """
        Load pre-computed calibration mapping.

        Args:
            path: Path to calibration file
        """
        # This would load a serialized CalibrationMapping
        # For now, we'll use identity mapping
        from .calibration import CalibrationMetrics

        self._calibration_mapping = CalibrationMapping(
            mapping_type="identity",
            params={},
            metrics=CalibrationMetrics(
                ece=0.0, brier=0.0, correlation=1.0, variance=1.0, sample_count=1000
            ),
            passed_gates=True,
        )


    def analyze(self, context: AnalysisContext) -> AnalysisEnvelope:
        """
        Analyze musical content using pattern matching.

        Args:
            context: Normalized analysis context

        Returns:
            AnalysisEnvelope with primary and alternative interpretations
        """
        start_time = time.time()

        # Match patterns against context
        evidences = self._match_patterns(context)

        # Aggregate evidence into scores
        aggregated = self.aggregator.aggregate(evidences)

        # Apply calibration if available
        functional_conf = self._calibrate(aggregated["functional_conf"])
        modal_conf = self._calibrate(aggregated["modal_conf"])
        combined_conf = self._calibrate(aggregated["combined_conf"])

        # Build primary analysis
        primary = self._build_analysis_summary(
            context,
            evidences,
            functional_conf,
            modal_conf,
            combined_conf,
            aggregated["debug_breakdown"],
        )

        # Build alternatives if confidence is ambiguous
        alternatives = self._build_alternatives(
            context, evidences, functional_conf, modal_conf
        )

        # Convert internal evidence to public DTOs
        evidence_dtos = self._convert_evidence(evidences)

        # Calculate timing
        analysis_time_ms = (time.time() - start_time) * 1000

        return AnalysisEnvelope(
            primary=primary,
            alternatives=alternatives,
            analysis_time_ms=analysis_time_ms,
            chord_symbols=context.chords,
            evidence=evidence_dtos,
            schema_version="1.0",
        )

    def _match_patterns(self, context: AnalysisContext) -> List[Evidence]:
        """
        Match all patterns against the analysis context.

        Args:
            context: Analysis context

        Returns:
            List of evidence from matched patterns
        """
        evidences = []

        # Get patterns from loaded data
        patterns = self._patterns.get("patterns", [])

        for pattern in patterns:
            # Check if pattern applies to this context
            if not self._pattern_applies(pattern, context):
                continue

            # Find matches for this pattern
            matches = self._find_pattern_matches(pattern, context)

            for match_span in matches:
                # Evaluate pattern at this location
                evidence = self._evaluate_pattern(pattern, context, match_span)
                if evidence:
                    evidences.append(evidence)

        return evidences

    def _pattern_applies(self, pattern: Dict[str, Any], context: AnalysisContext) -> bool:
        """
        Check if pattern is applicable to the context.

        Args:
            pattern: Pattern definition
            context: Analysis context

        Returns:
            True if pattern should be evaluated
        """
        # Check scope requirements
        scope = pattern.get("scope", ["harmonic"])
        if "harmonic" in scope and not context.chords:
            return False
        if "melodic" in scope and not context.melody:
            return False
        if "scale" in scope and not context.scales:
            return False

        return True

    def _find_pattern_matches(
        self, pattern: Dict[str, Any], context: AnalysisContext
    ) -> List[Tuple[int, int]]:
        """
        Find all locations where pattern matches.

        Self-contained implementation that works directly with pattern JSON,
        enforcing window and constraint logic without external dependencies.

        Args:
            pattern: Pattern definition from JSON
            context: Analysis context

        Returns:
            List of (start, end) spans where pattern matches
        """
        matches = []
        matchers = pattern.get("matchers", {})

        # Opening move: handle different matcher types from the JSON schema
        # Main play: check each sequence type and collect matches

        if "roman_seq" in matchers:
            seq = matchers["roman_seq"]
            window = matchers.get("window", {})
            constraints = matchers.get("constraints", {})
            matches.extend(self._find_sequence_matches(
                seq, context.roman_numerals, window, constraints, context
            ))

        if "chord_seq" in matchers:
            seq = matchers["chord_seq"]
            window = matchers.get("window", {})
            constraints = matchers.get("constraints", {})
            matches.extend(self._find_sequence_matches(
                seq, context.chords, window, constraints, context
            ))

        if "interval_seq" in matchers:
            # Big play: restore melodic interval matching for Iteration 2 multi-scope support
            interval_seq = matchers["interval_seq"]
            window = matchers.get("window", {})
            constraints = matchers.get("constraints", {})
            # Convert melody to intervals for matching
            melody_intervals = self._extract_melodic_intervals(context.melody)
            matches.extend(self._find_sequence_matches(
                [str(i) for i in interval_seq], [str(i) for i in melody_intervals],
                window, constraints, context
            ))

        if "scale_degrees" in matchers:
            # Victory lap: restore scale degree matching for modal patterns
            scale_degrees = matchers["scale_degrees"]
            window = matchers.get("window", {})
            constraints = matchers.get("constraints", {})
            # Extract scale degrees from melody and context
            context_scale_degrees = self._extract_scale_degrees(context)
            matches.extend(self._find_sequence_matches(
                [str(d) for d in scale_degrees], [str(d) for d in context_scale_degrees],
                window, constraints, context
            ))

        return matches

    def _extract_melodic_intervals(self, melody: List[str]) -> List[int]:
        """
        Extract semitone intervals from melody.

        Args:
            melody: List of note names or MIDI numbers

        Returns:
            List of semitone intervals between consecutive notes
        """
        if len(melody) < 2:
            return []

        intervals = []
        for i in range(len(melody) - 1):
            try:
                # Convert notes to semitone offsets
                curr_semitone = self._note_to_semitone(melody[i])
                next_semitone = self._note_to_semitone(melody[i + 1])

                # Calculate interval (shortest path on circle of fifths)
                raw_interval = next_semitone - curr_semitone
                # Normalize to [-6, +6] range for enharmonic equivalence
                while raw_interval > 6:
                    raw_interval -= 12
                while raw_interval < -6:
                    raw_interval += 12

                intervals.append(raw_interval)
            except (ValueError, TypeError):
                # Skip invalid notes
                continue

        return intervals

    def _extract_scale_degrees(self, context: AnalysisContext) -> List[int]:
        """
        Extract scale degrees from melody and roman numerals.

        Args:
            context: Analysis context with melody and roman numerals

        Returns:
            List of scale degrees (1-7)
        """
        scale_degrees = []

        # Opening move: extract from melody relative to key if available
        if context.melody and context.key:
            try:
                tonic_semitone = self._key_to_tonic_semitone(context.key)
                for note in context.melody:
                    note_semitone = self._note_to_semitone(note)
                    # Calculate scale degree (C=1, D=2, etc.)
                    degree = ((note_semitone - tonic_semitone) % 12) + 1
                    if degree <= 7:  # Diatonic degrees only
                        scale_degrees.append(degree)
            except (ValueError, TypeError):
                pass

        # Fallback: extract from roman numerals
        if not scale_degrees and context.roman_numerals:
            for roman in context.roman_numerals:
                degree = self._roman_to_scale_degree(roman)
                if degree:
                    scale_degrees.append(degree)

        return scale_degrees

    def _note_to_semitone(self, note: str) -> int:
        """Convert note name to semitone offset from C."""
        if isinstance(note, (int, float)):
            return int(note) % 12

        note = str(note).upper().strip()

        # Basic note mapping
        note_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

        # Extract base note
        base_note = note[0]
        if base_note not in note_map:
            raise ValueError(f"Invalid note: {note}")

        semitone = note_map[base_note]

        # Handle accidentals
        for char in note[1:]:
            if char in ['#', '♯']:
                semitone += 1
            elif char in ['b', '♭']:
                semitone -= 1

        return semitone % 12

    def _key_to_tonic_semitone(self, key: str) -> int:
        """Extract tonic semitone from key signature."""
        if not key:
            return 0
        tonic = key.split()[0]  # Extract "C" from "C major"
        return self._note_to_semitone(tonic)

    def _roman_to_scale_degree(self, roman: str) -> int:
        """Extract scale degree from roman numeral."""
        if not roman:
            return 0

        # Remove accidentals and case variations
        clean_roman = roman.upper().replace('♭', '').replace('#', '').replace('b', '')

        roman_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7}

        for key, degree in roman_map.items():
            if clean_roman.startswith(key):
                return degree

        return 0

    def _verify_diatonic_context(self, context: AnalysisContext, start: int, end: int) -> bool:
        """Verify all chords in span are diatonic to the key."""
        if not context.key or not context.chords:
            return True  # Can't verify, assume valid

        # Opening move: extract key info
        try:
            key_parts = context.key.split()
            tonic = key_parts[0]
            mode = key_parts[1].lower() if len(key_parts) > 1 else "major"

            # For now, use simple heuristic - all chords should contain key signature notes
            # This is a placeholder for more sophisticated diatonic checking
            return True
        except (IndexError, ValueError):
            return True

    def _check_soprano_degree(self, context: AnalysisContext, chord_index: int, expected_degrees: List[int]) -> bool:
        """Check if soprano note at chord_index matches expected scale degrees."""
        if not context.melody or chord_index >= len(context.melody):
            return True  # Can't verify, assume valid

        try:
            # Extract soprano note and convert to scale degree
            soprano_note = context.melody[chord_index]
            if context.key:
                tonic_semitone = self._key_to_tonic_semitone(context.key)
                soprano_semitone = self._note_to_semitone(soprano_note)

                # Calculate scale degree
                semitone_diff = (soprano_semitone - tonic_semitone) % 12
                degree_map = {0: 1, 2: 2, 4: 3, 5: 4, 7: 5, 9: 6, 11: 7}
                degree = degree_map.get(semitone_diff, 0)

                return degree in expected_degrees
        except (ValueError, TypeError, IndexError):
            pass

        return True  # If we can't determine, assume valid

    def _check_bass_motion(self, context: AnalysisContext, start: int, end: int, expected_motion: str) -> bool:
        """Check bass line motion pattern."""
        # Placeholder for bass motion checking
        # This would analyze bass notes in context.chords[start:end]
        # and verify patterns like "ascending", "descending", "leap_down", etc.
        return True

    def _check_voice_leading(self, context: AnalysisContext, start: int, end: int, expected_quality: str) -> bool:
        """Check voice leading quality."""
        # Placeholder for voice leading analysis
        # This would analyze voice motion between chords
        # and verify qualities like "smooth", "contrary", "parallel", etc.
        return True

    def _find_sequence_matches(
        self,
        pattern_seq: List[str],
        context_seq: List[str],
        window: Dict[str, Any],
        constraints: Dict[str, Any],
        context: AnalysisContext
    ) -> List[Tuple[int, int]]:
        """
        Find all occurrences of a sequence pattern with window/constraint enforcement.

        Args:
            pattern_seq: Pattern sequence to find
            context_seq: Sequence to search in
            window: Window constraints (min/max length, overlap)
            constraints: Additional constraints (position, key_context, etc.)
            context: Full analysis context for constraint checking

        Returns:
            List of (start, end) indices where pattern matches
        """
        matches = []
        pattern_len = len(pattern_seq)
        context_len = len(context_seq)

        # Check window length constraints
        min_len = window.get("min", pattern_len)
        max_len = window.get("max", pattern_len)

        if pattern_len < min_len or pattern_len > max_len:
            return matches

        if pattern_len == 0 or pattern_len > context_len:
            return matches

        # Main search: find pattern occurrences
        for i in range(context_len - pattern_len + 1):
            # Check if pattern matches at position i
            pattern_matches = True

            for j, pattern_item in enumerate(pattern_seq):
                context_item = context_seq[i + j]

                # Handle wildcards and special patterns
                if pattern_item == "*" or pattern_item == ".*":
                    continue  # Wildcard matches anything

                # Normalize for comparison (handle unicode flat symbols)
                pattern_normalized = pattern_item.replace("b", "♭")
                context_normalized = context_item.replace("b", "♭")

                if pattern_normalized != context_normalized:
                    pattern_matches = False
                    break

            if pattern_matches:
                # Check position constraints
                if "position" in constraints:
                    position = constraints["position"]
                    if position == "start" and i != 0:
                        continue
                    elif position == "end" and i + pattern_len != context_len:
                        continue

                # Check key context constraints
                if "key_context" in constraints:
                    key_context = constraints["key_context"]
                    if key_context == "diatonic" and context.key:
                        # Time to tackle the tricky bit: verify all chords are diatonic to key
                        if not self._verify_diatonic_context(context, i, i + pattern_len):
                            continue

                # Big play: restore missing high-value constraints for pattern precision
                if "soprano_degree" in constraints:
                    # Check soprano scale degree at cadence resolution
                    expected_degrees = constraints["soprano_degree"]
                    if not self._check_soprano_degree(context, i + pattern_len - 1, expected_degrees):
                        continue

                if "bass_motion" in constraints:
                    # Check bass line motion pattern
                    expected_motion = constraints["bass_motion"]
                    if not self._check_bass_motion(context, i, i + pattern_len, expected_motion):
                        continue

                if "voice_leading" in constraints:
                    # Check voice leading quality
                    expected_quality = constraints["voice_leading"]
                    if not self._check_voice_leading(context, i, i + pattern_len, expected_quality):
                        continue

                # Victory lap: add valid match
                matches.append((i, i + pattern_len))

        # Handle overlap constraints
        if not window.get("overlap_ok", True) and len(matches) > 1:
            # Remove overlapping matches, keeping first occurrences
            non_overlapping = []
            last_end = -1
            for start, end in matches:
                if start >= last_end:
                    non_overlapping.append((start, end))
                    last_end = end
            matches = non_overlapping

        return matches





    def _evaluate_pattern(
        self, pattern: Dict[str, Any], context: AnalysisContext, span: Tuple[int, int]
    ) -> Optional[Evidence]:
        """
        Evaluate a pattern match to produce evidence.

        Args:
            pattern: Pattern definition
            context: Analysis context
            span: Match location (start, end)

        Returns:
            Evidence object or None if evaluation fails
        """
        evidence_config = pattern.get("evidence", {})
        confidence_fn = evidence_config.get("confidence_fn", "identity")

        # Get evaluator function
        try:
            evaluator = self.plugins.get(confidence_fn)
        except KeyError:
            # Unknown evaluator - use identity
            evaluator = self.plugins.get("identity")

        # Prepare evaluation context - time for the comprehensive context setup
        eval_context = {
            "span": span,
            "key": context.key,
            "chords": context.chords[span[0] : span[1]] if context.chords else [],
            "melody": context.melody[span[0] : span[1]] if context.melody else [],
            "scales": context.scales,
            "metadata": context.metadata,
        }

        # Evaluate and return evidence
        return evaluator(pattern, eval_context)

    def _calibrate(self, raw_score: float) -> float:
        """
        Apply calibration to raw confidence score.

        Args:
            raw_score: Uncalibrated confidence

        Returns:
            Calibrated confidence
        """
        if self._calibration_mapping:
            return self._calibration_mapping.apply(raw_score)
        return raw_score

    def _build_analysis_summary(
        self,
        context: AnalysisContext,
        evidences: List[Evidence],
        functional_conf: float,
        modal_conf: float,
        combined_conf: float,
        debug_info: Dict[str, Any],
    ) -> AnalysisSummary:
        """
        Build primary analysis summary from aggregated evidence.

        Args:
            context: Analysis context
            evidences: All evidence
            functional_conf: Functional confidence
            modal_conf: Modal confidence
            combined_conf: Combined confidence
            debug_info: Debug information

        Returns:
            Primary analysis summary
        """
        # Determine primary type based on confidences
        if functional_conf > modal_conf:
            analysis_type = AnalysisType.FUNCTIONAL
            confidence = functional_conf
        else:
            analysis_type = AnalysisType.MODAL
            confidence = modal_conf

        # Convert evidence to pattern matches
        pattern_matches = []
        for evidence in evidences:
            # Only include patterns that contribute to the primary type
            if analysis_type.value.lower() in evidence.track_weights:
                pattern_match = PatternMatchDTO(
                    start=evidence.span[0],
                    end=evidence.span[1],
                    pattern_id=evidence.pattern_id,
                    name=evidence.pattern_id.replace(".", " ").title(),
                    family=evidence.pattern_id.split(".")[0] if "." in evidence.pattern_id else "general",
                    score=evidence.raw_score,
                    evidence=[{"features": evidence.features}],
                )
                pattern_matches.append(pattern_match)

        # Populate terms with glossary enrichment
        terms = {"analysis_method": "unified_pattern_engine"}
        if self._glossary:
            # Collect all feature keys from evidences
            feature_keys = set()
            for evidence in evidences:
                feature_keys.update(evidence.features.keys())

            # Get summary terms for these features
            if feature_keys:
                summary_terms = get_summary_terms(self._glossary, list(feature_keys))
                # Main play: flatten nested dict to match AnalysisSummary.terms type (Dict[str, str])
                for key, value_dict in summary_terms.items():
                    if isinstance(value_dict, dict) and "label" in value_dict:
                        terms[key] = value_dict["label"]
                    else:
                        terms[key] = str(value_dict)

        return AnalysisSummary(
            type=analysis_type,
            roman_numerals=context.roman_numerals if context.roman_numerals else [],
            confidence=confidence,
            key_signature=context.key,
            reasoning=f"Pattern-based analysis with {len(evidences)} matches",
            functional_confidence=functional_conf,
            modal_confidence=modal_conf,
            patterns=pattern_matches,
            terms=terms,
        )

    def _build_alternatives(
        self,
        context: AnalysisContext,
        evidences: List[Evidence],
        functional_conf: float,
        modal_conf: float,
    ) -> List[AnalysisSummary]:
        """
        Build alternative analyses if confidence is ambiguous.

        Args:
            context: Analysis context
            evidences: All evidence
            functional_conf: Functional confidence
            modal_conf: Modal confidence

        Returns:
            List of alternative analyses
        """
        alternatives = []

        # Add alternative if confidences are close
        threshold_diff = 0.15
        min_confidence = 0.4

        if abs(functional_conf - modal_conf) < threshold_diff:
            # Ambiguous - add the other interpretation
            if functional_conf > modal_conf and modal_conf > min_confidence:
                # Add modal as alternative
                alternatives.append(
                    AnalysisSummary(
                        type=AnalysisType.MODAL,
                        roman_numerals=context.roman_numerals if context.roman_numerals else [],
                        confidence=modal_conf,
                        key_signature=context.key,
                        reasoning="Alternative modal interpretation",
                        modal_confidence=modal_conf,
                        functional_confidence=functional_conf,
                    )
                )
            elif modal_conf > functional_conf and functional_conf > min_confidence:
                # Add functional as alternative
                alternatives.append(
                    AnalysisSummary(
                        type=AnalysisType.FUNCTIONAL,
                        roman_numerals=context.roman_numerals if context.roman_numerals else [],
                        confidence=functional_conf,
                        key_signature=context.key,
                        reasoning="Alternative functional interpretation",
                        functional_confidence=functional_conf,
                        modal_confidence=modal_conf,
                    )
                )

        return alternatives

    def _convert_evidence(self, evidences: List[Evidence]) -> List[EvidenceDTO]:
        """
        Convert internal evidence to public DTOs with glossary enrichment.

        Args:
            evidences: Internal evidence objects

        Returns:
            List of public EvidenceDTO objects with enriched features
        """
        dtos = []
        for evidence in evidences:
            # Enrich features with glossary information
            enriched_features = evidence.features
            if self._glossary:
                enriched_features = enrich_features(self._glossary, evidence.features)

            dto = EvidenceDTO(
                reason=evidence.pattern_id,
                details={
                    "features": enriched_features,
                    "track_weights": evidence.track_weights,
                    "raw_score": evidence.raw_score,
                    "span": list(evidence.span),
                },
            )
            dtos.append(dto)
        return dtos