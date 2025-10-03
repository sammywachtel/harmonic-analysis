"""
Pattern Matcher - Clean architecture with separation of concerns.

JSONified harmonic pattern recognition with focused, testable components
that maintain the core algorithm's effectiveness.
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Set, TypedDict

# --- Utility helpers ---------------------------------------------------------


def _strip_maj7_markers(s: str) -> str:
    """Remove common maj7 markers before generic '7' so 'Imaj7' can compare like 'I'.
    Covers: maj7, Maj7, MAJ7, ma7, M7, Δ, ∆ followed by a final plain '7'.
    """
    if not s:
        return s
    s = (
        s.replace("maj7", "")
        .replace("Maj7", "")
        .replace("MAJ7", "")
        .replace("ma7", "")
        .replace("M7", "")
        .replace("Δ", "")
        .replace("∆", "")
    )
    # Strip any remaining plain '7' (after specific markers)
    return s.replace("7", "")


# Type definitions for improved type safety
class StepEvidence(TypedDict):
    step_index: int
    roman: str
    role: str
    flags: List[str]


class PatternMatch(TypedDict):
    pattern_id: str
    name: str
    family: str
    score: float
    start: int
    end: int
    evidence: List[StepEvidence]


# Core data structures (unchanged from original)
@dataclass
class Token:
    """Single chord in harmonic analysis with functional information."""

    roman: str  # Roman numeral representation ("V7", "ii6", "♭VI")
    role: str  # Functional role: "T" (Tonic), "PD" (Predominant), "D" (Dominant)
    flags: List[str] = field(default_factory=list)  # Special markers
    mode: Optional[str] = None  # "major", "minor", or modal context
    bass_motion_from_prev: Optional[int] = None  # Semitone motion (-6 to +6)
    soprano_degree: Optional[int] = None  # Scale degree of soprano (1-7)
    secondary_of: Optional[str] = None  # Target of secondary dominant

    def roman_root(self) -> str:
        """Extract root roman numeral, keep inversions but remove extensions."""
        r = self.roman
        # Keep inversion figures – they affect function
        if r.endswith(("6", "65", "64", "43", "42")):
            return r
        # Strip maj7 markers first, then plain 7
        r = _strip_maj7_markers(r)
        return r

    def roman_base(self) -> str:
        """Extract base roman numeral with inversions and sevenths removed."""
        r = self.roman

        # Remove common inversion/figure indicators
        for suf in ("65", "64", "43", "42", "6"):
            if r.endswith(suf):
                r = r[: -len(suf)]
                break

        # Strip maj7 markers first, then plain 7
        r = _strip_maj7_markers(r)

        return r


@dataclass
class StepSpec:
    """Specification for a single step in a harmonic pattern."""

    role: Optional[str] = None  # Required functional role ("T", "PD", "D")
    roman_root_any_of: Optional[List[str]] = None  # Acceptable romans
    quality_any_of: Optional[List[str]] = None  # Chord qualities
    flags_any_of: Optional[List[str]] = None  # Required flags
    secondary_of: Optional[str] = None  # Secondary dominant target
    optional: bool = False  # Whether step can be skipped in matching
    descriptor: Optional[str] = None  # Special pattern type


@dataclass
class Pattern:
    """Complete harmonic pattern definition loaded from JSON."""

    id: str  # Unique identifier
    family: str  # Pattern category ("cadence", "sequence", "prolongation")
    name: str  # Human-readable name
    aliases: List[str]  # Alternative names for patterns
    profiles: List[str]  # jazz, pop, classical, etc
    window: Dict[str, int]  # Min/max length constraints
    sequence: List[StepSpec]  # Ordered sequence of chord specifications
    constraints: Dict[str, Any] = field(default_factory=dict)  # Extra requirements
    substitutions: Dict[str, List[str]] = field(default_factory=dict)  # Chord subs
    score: Dict[str, Any] = field(default_factory=dict)  # Scoring weights


class MatchFailureReason(Enum):
    """Enumeration of why a pattern match might fail."""

    STEP_MISMATCH = "step_mismatch"
    CONSTRAINT_VIOLATION = "constraint_violation"
    WINDOW_SIZE = "window_size"
    DESCRIPTOR_FAILED = "descriptor_failed"


@dataclass
class MatchResult:
    """Rich result object with success/failure information."""

    success: bool
    score: float = 0.0
    evidence: List[StepEvidence] = field(default_factory=list)
    failure_reason: Optional[MatchFailureReason] = None
    debug_info: Optional[Dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def success_result(
        cls, score: float, evidence: List[StepEvidence]
    ) -> "MatchResult":
        """Create successful match result."""
        return cls(success=True, score=score, evidence=evidence)

    @classmethod
    def failure_result(
        cls, reason: MatchFailureReason, debug_info: Optional[Dict[Any, Any]] = None
    ) -> "MatchResult":
        """Create failed match result with diagnostic information."""
        return cls(success=False, failure_reason=reason, debug_info=debug_info or {})


# Strategy Pattern for Pattern Matching
class MatchStrategy(ABC):
    """Abstract strategy for matching different types of patterns."""

    @abstractmethod
    def can_handle(self, pattern: Pattern) -> bool:
        """Check if this strategy can handle the given pattern type."""
        pass

    @abstractmethod
    def match(self, pattern: Pattern, tokens: List[Token]) -> MatchResult:
        """Attempt to match pattern against tokens."""
        pass


class SequenceMatchStrategy(MatchStrategy):
    """Handles sequence-based patterns that match chord-by-chord."""

    def __init__(
        self,
        constraint_validator: "ConstraintValidator",
        substitution_engine: "SubstitutionEngine",
    ):
        self.constraint_validator = constraint_validator
        self.substitution_engine = substitution_engine

    def can_handle(self, pattern: Pattern) -> bool:
        """
        Handle patterns without descriptors (standard chord sequences).
        Checks structural conditions like window length, profile allowlist, etc but
            doesn't assert that the actual roman steps match.
        """
        return not any(s.descriptor for s in pattern.sequence)

    def match(self, pattern: Pattern, tokens: List[Token]) -> MatchResult:
        """Match chord sequence step by step with substitutions."""
        i = j = 0  # i = token index, j = pattern step index
        evidence = []

        # Process pattern and tokens step by step
        while j < len(pattern.sequence) and i <= len(tokens):
            if j >= len(pattern.sequence):
                break
            step = pattern.sequence[j]

            if i >= len(tokens):
                # Check if remaining steps are all optional - graceful degradation
                if all(s.optional for s in pattern.sequence[j:]):
                    break
                return MatchResult.failure_result(
                    MatchFailureReason.STEP_MISMATCH,
                    {"missing_steps": len(pattern.sequence) - j},
                )

            tok = tokens[i]
            next_tok = tokens[i + 1] if (i + 1) < len(tokens) else None
            if self._step_matches_token(step, tok, pattern, next_tok=next_tok):
                # Record evidence of successful step match
                evidence.append(
                    StepEvidence(
                        step_index=j, roman=tok.roman, role=tok.role, flags=tok.flags
                    )
                )
                i += 1
                j += 1
            else:
                if step.optional:
                    j += 1  # Skip optional step, try next one
                else:
                    return MatchResult.failure_result(
                        MatchFailureReason.STEP_MISMATCH,
                        {"failed_at_step": j, "token": tok.roman, "expected": step},
                    )

        # Final check: do global constraints pass?
        if not self.constraint_validator.validate_all(pattern.constraints, tokens):
            return MatchResult.failure_result(
                MatchFailureReason.CONSTRAINT_VIOLATION,
                {"constraints": pattern.constraints},
            )

        # Calculate enhanced score with bonuses/penalties
        final_score = self._calculate_enhanced_score(pattern, tokens, evidence)

        return MatchResult.success_result(score=final_score, evidence=evidence)

    def _effective_role(
        self, tok: Token, pattern: Pattern, next_tok: Optional[Token] = None
    ) -> str:
        """Compute token role possibly remapped by pattern constraints
        (e.g., treat_I64_as_D).
        Local only: applies within the scope of a single pattern match attempt.
        """
        role = tok.role or ""
        cons = pattern.constraints or {}

        # Cadential 6-4 handling: optionally treat I64 as D within this pattern
        if cons.get("treat_I64_as_D"):
            roman = getattr(tok, "roman", "")
            base = tok.roman_base().upper()
            is_i64 = roman.endswith("64") and base == "I"
            has_cadential_flag = "cadential_64" in (tok.flags or [])
            next_is_V = bool(next_tok and next_tok.roman_base().upper().startswith("V"))
            if is_i64 and (has_cadential_flag or next_is_V):
                return "D"

        return role

    def _step_matches_token(
        self,
        step: StepSpec,
        tok: Token,
        pattern: Pattern,
        next_tok: Optional[Token] = None,
    ) -> bool:
        """Check if token satisfies step requirements with substitutions."""
        # Descriptor-based steps handled by different strategy
        if step.descriptor:
            return False

        # Check functional role match with flexibility for T_or_D and effective
        # role remapping
        if step.role:
            eff_role = self._effective_role(tok, pattern, next_tok=next_tok)
            if step.role == "T_or_D":
                if eff_role not in ("T", "D"):
                    return False
            elif step.role == "any":
                # "any" role matches any token - no restriction
                pass
            elif eff_role != step.role:
                return False

        # Check roman numeral with pattern and style substitutions
        if step.roman_root_any_of:
            allowed = self.substitution_engine.expand_allowed_chords(
                step.roman_root_any_of, pattern
            )
            # If any allowed value specifies an inversion/figure, require exact
            # root match;
            # otherwise, compare using inversion-insensitive base.
            inversion_sensitive = any(
                a.endswith(("6", "65", "64", "43", "42")) for a in allowed
            )
            token_cmp_raw = (
                tok.roman_root() if inversion_sensitive else tok.roman_base()
            )

            def strip_secondary(s: str) -> str:
                return s.split("/")[0] if s and "/" in s else s

            # normalize for comparison: case-insensitive and unify accidentals
            def norm(s: str) -> str:
                s = s or ""
                # normalize accidentals
                s = s.replace("♭", "b").replace("♯", "#")
                # normalize Unicode superscripts to ASCII
                supers = {
                    "⁰": "0",
                    "¹": "1",
                    "²": "2",
                    "³": "3",
                    "⁴": "4",
                    "⁵": "5",
                    "⁶": "6",
                    "⁷": "7",
                    "⁸": "8",
                    "⁹": "9",
                }
                for k, v in supers.items():
                    s = s.replace(k, v)
                # when inversion-insensitive, drop maj7 markers first, then '7'
                if not inversion_sensitive:
                    s = _strip_maj7_markers(s)
                return s

            # First check for regex patterns (before stripping secondaries)
            token_cmp_full = norm(
                token_cmp_raw
            ).lower()  # Keep full token for regex matching

            # Check if any allowed pattern is a regex (contains *, +, ?, etc.)
            regex_match_found = False
            for pattern_str in allowed:
                if any(
                    char in pattern_str
                    for char in ["*", "+", "?", "[", "]", "(", ")", "|", "^", "$"]
                ):
                    # This looks like a regex pattern
                    try:
                        if re.match(
                            pattern_str.replace(".*", ".*"),
                            token_cmp_full,
                            re.IGNORECASE,
                        ):
                            regex_match_found = True
                            break
                    except re.error:
                        # Invalid regex, skip
                        continue

            if regex_match_found:
                # Found a regex match, continue with rest of checks
                pass
            else:
                # No regex match found, use traditional exact matching with
                # secondary stripping
                # --- strip secondary dominants/targets (e.g., "V/ii" -> "V") ---
                if token_cmp_raw and "/" in token_cmp_raw:
                    token_cmp_raw = token_cmp_raw.split("/")[0]

                token_cmp = norm(token_cmp_raw).lower()
                normalized_allowed = {norm(strip_secondary(a)).lower() for a in allowed}

                if token_cmp not in normalized_allowed:
                    return False

        # Check chord quality flags
        if step.flags_any_of and not any(f in tok.flags for f in step.flags_any_of):
            return False

        # Check chord quality requirements (V7 vs V, triad vs seventh, etc.)
        if step.quality_any_of:
            token_quality = self._detect_chord_quality(tok)
            if token_quality not in step.quality_any_of:
                return False

        # Check secondary dominant target
        if step.secondary_of:
            if step.secondary_of != "*" and step.secondary_of != tok.secondary_of:
                return False

        return True

    def _detect_chord_quality(self, tok: Token) -> str:
        """
        Detect chord quality from roman numeral for quality_any_of matching.

        Distinguishes V7 from V, diminished from triad, etc.
        """
        roman = tok.roman.lower()

        # Detect quality indicators in roman numeral
        if "7" in roman:
            if "65" in roman or "43" in roman or "42" in roman:
                return "7_inv"  # Seventh chord inversion
            return "7"  # Seventh chord root position
        elif "dim" in roman or "°" in roman:
            return "dim"  # Diminished chord
        elif "aug" in roman or "+" in roman:
            return "aug"  # Augmented chord
        elif "6" in roman:
            return "6"  # First inversion triad or sixth chord
        else:
            return "triad"  # Basic triad

    def _calculate_enhanced_score(
        self, pattern: Pattern, tokens: List[Token], evidence: List[StepEvidence]
    ) -> float:
        """
        Calculate enhanced score with bonuses and penalties.

        Rewards good voice leading, penalizes awkward progressions.
        """
        base_score = float(pattern.score.get("base", 1.0))
        bonuses = pattern.score.get("bonuses", {})
        penalties = pattern.score.get("penalties", {})

        final_score = base_score

        # Voice leading bonuses
        if "smooth_voice_leading" in bonuses:
            smooth_motions = sum(
                1
                for t in tokens[1:]
                if t.bass_motion_from_prev is not None
                and abs(t.bass_motion_from_prev) <= 2
            )  # Step or skip
            if smooth_motions > 0:
                final_score += bonuses["smooth_voice_leading"] * smooth_motions

        # Inversion bonuses (first inversion often preferred for smooth bass)
        if "first_inversion_bonus" in bonuses:
            inversions = sum(1 for t in tokens if "6" in t.roman)
            final_score += bonuses["first_inversion_bonus"] * inversions

        # Strong cadence bonuses
        if "strong_cadence" in bonuses and len(tokens) >= 2:
            final_token = tokens[-1]
            if (
                final_token.role == "T" and final_token.soprano_degree == 1
            ):  # Soprano on tonic
                final_score += bonuses["strong_cadence"]

        # Awkward leap penalties
        if "large_leap_penalty" in penalties:
            large_leaps = sum(
                1
                for t in tokens[1:]
                if t.bass_motion_from_prev is not None
                and abs(t.bass_motion_from_prev) > 5
            )  # Larger than fourth
            final_score -= penalties["large_leap_penalty"] * large_leaps

        # Ensure score doesn't go negative
        return max(0.1, final_score)


class DescriptorMatchStrategy(MatchStrategy):
    """Handles descriptor-based patterns identified by structural characteristics."""

    def __init__(self, descriptor_registry: "DescriptorRegistry"):
        self.descriptor_registry = descriptor_registry

    def can_handle(self, pattern: Pattern) -> bool:
        """Handle patterns that use descriptors (structural patterns)."""
        return any(s.descriptor for s in pattern.sequence)

    def match(self, pattern: Pattern, tokens: List[Token]) -> MatchResult:
        """Match using structural descriptors rather than exact sequences."""
        # Check the first descriptor (patterns typically have one)
        descriptor = pattern.sequence[0].descriptor

        if descriptor and self.descriptor_registry.check(descriptor, tokens):
            # Create evidence for descriptor matches
            evidence = [
                StepEvidence(
                    step_index=0,
                    roman="descriptor_match",
                    role="structural",
                    flags=[str(descriptor)],
                )
            ]

            # Note: DescriptorMatchStrategy doesn't have enhanced scoring yet
            # TODO: Consider sharing scoring logic with SequenceMatchStrategy
            final_score = pattern.score.get("base", 1.0)

            return MatchResult.success_result(score=final_score, evidence=evidence)

        return MatchResult.failure_result(
            MatchFailureReason.DESCRIPTOR_FAILED,
            {"descriptor": descriptor, "token_count": len(tokens)},
        )


# Constraint System with Registry Pattern
class ConstraintChecker(ABC):
    """Abstract base for individual constraint checkers."""

    def __init__(self) -> None:
        self._events: Optional[Any] = None

    @abstractmethod
    def check(self, tokens: List[Token], constraint_value: Any) -> bool:
        """Check if tokens satisfy this specific constraint."""
        pass


class ModeConstraint(ConstraintChecker):
    """Require specific mode (major, minor, modal)."""

    def __init__(self) -> None:
        super().__init__()

    def check(self, tokens: List[Token], constraint_value: Any) -> bool:
        # If no tokens carry mode info, do not fail the constraint.
        modes = [t.mode for t in tokens if t.mode is not None]
        if not modes:
            return True

        # Special case: "both" means pattern works in major OR minor
        if constraint_value == "both":
            return any(m.lower() in {"major", "minor"} for m in modes)

        if constraint_value is None:
            return True

        constraint_norm = str(constraint_value).lower()
        return any(
            constraint_norm == m.lower() or constraint_norm in m.lower() for m in modes
        )


class SecondaryDominantConstraint(ConstraintChecker):
    """Require secondary dominant somewhere in pattern."""

    def check(self, tokens: List[Token], constraint_value: Any) -> bool:
        # constraint_value is boolean (requires_secondary)
        if not constraint_value:
            return True
        return any(t.secondary_of is not None for t in tokens)


class BassMotionConstraint(ConstraintChecker):
    """Require specific bass motion patterns."""

    def check(self, tokens: List[Token], constraint_value: Any) -> bool:
        # constraint_value is list of allowed semitone motions
        return any(
            t.bass_motion_from_prev in constraint_value
            for t in tokens
            if t.bass_motion_from_prev is not None
        )


class SopranoConstraint(ConstraintChecker):
    """
    Require soprano voice to include specific scale degrees **somewhere in the window**.

    NOTE: For arrival-only checks, use `ArrivalSopranoConstraint`. This constraint
    is intentionally permissive to support macro patterns that don't fix the
    cadence tone.
    """

    def check(self, tokens: List[Token], constraint_value: Any) -> bool:
        # constraint_value is list of acceptable soprano scale degrees
        return any(
            (t.soprano_degree in constraint_value)
            for t in tokens
            if t.soprano_degree is not None
        )


class CadentialSixFourConstraint(ConstraintChecker):
    """Require or forbid cadential 6/4 chords."""

    def check(self, tokens: List[Token], constraint_value: Any) -> bool:
        has_cadential_64 = any("cadential_64" in t.flags for t in tokens)
        if constraint_value == "required":
            return has_cadential_64
        elif constraint_value == "forbidden":
            return not has_cadential_64
        return True  # Unknown constraint value, allow it


class PhrygianStepConstraint(ConstraintChecker):
    """Check for Phrygian half-step bass motion (-1 semitone)."""

    def check(self, tokens: List[Token], constraint_value: Any) -> bool:
        if constraint_value:  # Require Phrygian step
            return any(
                t.bass_motion_from_prev == -1
                for t in tokens
                if t.bass_motion_from_prev is not None
            )
        return True


class ArrivalSopranoConstraint(ConstraintChecker):
    """Require soprano to arrive on specific degree at pattern end."""

    def check(self, tokens: List[Token], constraint_value: Any) -> bool:
        if not tokens or not constraint_value:
            return True
        # Check final token's soprano degree
        final_token = tokens[-1]
        return (
            final_token.soprano_degree is not None
            and final_token.soprano_degree in constraint_value
        )


# --- Insert flag constraints here ---
class RequireFlagConstraint(ConstraintChecker):
    """Passes if any token carries one of the required flags."""

    def check(self, tokens: List[Token], constraint_value: Any) -> bool:
        if not constraint_value:
            return True
        required = set(constraint_value)
        return any(required.intersection(t.flags) for t in tokens)


class ForbidFlagConstraint(ConstraintChecker):
    """Fails if any token carries any forbidden flag."""

    def check(self, tokens: List[Token], constraint_value: Any) -> bool:
        if not constraint_value:
            return True
        forbidden = set(constraint_value)
        return not any(forbidden.intersection(t.flags) for t in tokens)


# Event-based constraint checkers for Stage B
class EventsAnyConstraint(ConstraintChecker):
    """Passes if any of the specified events are present at specified positions.

    Format: ["cadential64@0", "pedal@1"] = cadential64 at position 0 OR
    pedal at position 1
    """

    def check(self, tokens: List[Token], constraint_value: Any) -> bool:
        if not constraint_value or not hasattr(self, "_events"):
            return True

        events = self._events
        if events is None:
            return True

        required_events = (
            constraint_value
            if isinstance(constraint_value, list)
            else [constraint_value]
        )

        for event_spec in required_events:
            if "@" in event_spec:
                event_type, pos_str = event_spec.split("@")
                pos = int(pos_str)

                # Check if event is present at specified position
                if pos < len(tokens):
                    if event_type == "cadential64" and pos < len(
                        events.has_cadential64
                    ):
                        if events.has_cadential64[pos]:
                            return True
                    elif event_type == "pedal" and pos < len(events.has_pedal_bass):
                        if events.has_pedal_bass[pos]:
                            return True

        return False


class BassDegreeAtConstraint(ConstraintChecker):
    """Passes if bass degree matches at specified positions.

    Format: {"0": "♭2", "2": "1"} = ♭2 at position 0 AND 1 at position 2
    """

    def check(self, tokens: List[Token], constraint_value: Any) -> bool:
        if not constraint_value:
            return True

        events = getattr(self, "_events", None)
        if events is None:
            return True

        def _norm_accidental_symbol(s: str) -> str:
            if not s:
                return s
            return s.replace("♭", "b").replace("♯", "#")

        for pos_str, expected_degree in constraint_value.items():
            pos = int(pos_str)
            if pos < len(events.bass_degree):
                actual_degree = events.bass_degree[pos]
                if _norm_accidental_symbol(actual_degree) != _norm_accidental_symbol(
                    expected_degree
                ):
                    return False

        return True


class ChainDescriptorConstraint(ConstraintChecker):
    """Passes if root motion chain descriptor matches requirements.

    Format: {"type": "circle5", "min_len": 3}
    """

    def check(self, tokens: List[Token], constraint_value: Any) -> bool:
        if not constraint_value or not hasattr(self, "_events"):
            return True

        from .low_level_events import get_circle_of_fifths_descriptor

        events = self._events
        if events is None:
            return True

        chain_type = constraint_value.get("type")
        min_len = constraint_value.get("min_len", 3)

        if chain_type == "circle5":
            descriptor = get_circle_of_fifths_descriptor(events, min_len)
            return bool(descriptor["found"])

        return False


class ConstraintValidator:
    """Registry-based constraint validation system."""

    def __init__(self) -> None:
        # Registry of constraint checkers - extensible architecture
        self.checkers: Dict[str, ConstraintChecker] = {
            "mode": ModeConstraint(),
            "requires_secondary": SecondaryDominantConstraint(),
            "bass_motion_any_of": BassMotionConstraint(),
            "soprano_any_of": SopranoConstraint(),
            "cadential_64": CadentialSixFourConstraint(),
            "phrygian_step": PhrygianStepConstraint(),
            "arrival_soprano": ArrivalSopranoConstraint(),
            "require_flag_any_of": RequireFlagConstraint(),
            "forbid_flag_any_of": ForbidFlagConstraint(),
            # Stage B event constraints
            "events_any": EventsAnyConstraint(),
            "bass_degree_at": BassDegreeAtConstraint(),
            "chain_descriptor": ChainDescriptorConstraint(),
        }
        self._events = None  # Store events for constraint checking

    def register_checker(self, name: str, checker: ConstraintChecker) -> None:
        """Register new constraint checker - plugin architecture."""
        self.checkers[name] = checker

    def set_events(self, events: Any) -> None:
        """Set low-level events for constraint checking."""
        self._events = events
        # Propagate events to constraint checkers that need them
        for checker in self.checkers.values():
            # All event-based checkers need events
            checker._events = events

    def validate_all(self, constraints: Dict[str, Any], tokens: List[Token]) -> bool:
        """Validate all constraints against tokens."""
        if not constraints:
            return True

        # Check each constraint using appropriate checker
        for constraint_name, constraint_value in constraints.items():
            checker = self.checkers.get(constraint_name)
            if checker and not checker.check(tokens, constraint_value):
                return False

        return True


# Descriptor Registry for Extensibility
class DescriptorRegistry:
    """Registry of structural pattern descriptors."""

    def __init__(self) -> None:
        self.descriptors: Dict[str, Callable[[List[Token]], bool]] = {
            "root_motion_-5_chain_min3": self._circle_of_fifths_checker,
            "pachelbel_core": self._pachelbel_checker,
            "chromatic_mediant": self._chromatic_mediant_checker,
        }

    def register(self, name: str, checker: Callable[[List[Token]], bool]) -> None:
        """Register new descriptor checker."""
        self.descriptors[name] = checker

    def check(self, descriptor: str, tokens: List[Token]) -> bool:
        """Check if tokens match descriptor pattern."""
        checker = self.descriptors.get(descriptor, lambda x: False)
        return bool(checker(tokens))

    def _circle_of_fifths_checker(self, tokens: List[Token]) -> bool:
        """Circle of fifths: requires 3+ chords with descending-fifth motion."""
        if len(tokens) < 3:
            return False

        # Count consecutive descending fifth motions
        consecutive_fifths = 0
        max_consecutive = 0

        for token in tokens[1:]:
            m = token.bass_motion_from_prev
            if m is not None and m in (
                -7,
                -5,
            ):  # accept semitone -7 or diatonic-coded -5
                consecutive_fifths += 1
                max_consecutive = max(max_consecutive, consecutive_fifths)
            else:
                consecutive_fifths = 0

        # Require at least 2 consecutive fifth motions (3 chord chain)
        return max_consecutive >= 2

    def _pachelbel_checker(self, tokens: List[Token]) -> bool:
        """Pachelbel's Canon core: I–V–vi–iii–IV–I–IV–V (inversion-insensitive)."""
        if len(tokens) != 8:
            return False
        roots = [t.roman_base() for t in tokens]
        low = [r.lower() for r in roots]
        return low == ["i", "v", "vi", "iii", "iv", "i", "iv", "v"]

    def _chromatic_mediant_checker(self, tokens: List[Token]) -> bool:
        """Chromatic mediant relationships (roots 3rd apart, different quality);
        conservative: look for common chromatic roman markers anywhere in window.
        Supports both Unicode (♭/♯) and ASCII (b/#).
        """
        if len(tokens) < 2:
            return False
        chromatic_indicators = [
            "♭VI",
            "♭III",
            "♯iv",
            "♭ii",
            "♯IV",
            "♭VII",
            "bVI",
            "bIII",
            "#iv",
            "bii",
            "#IV",
            "bVII",
        ]
        for token in tokens:
            r = token.roman.replace("♭", "b").replace("♯", "#")
            if any(ind in r for ind in chromatic_indicators):
                return True
        return False


# Substitution System Architecture
class SubstitutionProfile(ABC):
    """Abstract profile for style-specific chord substitutions."""

    @abstractmethod
    def get_substitutes(self, chord: str) -> Set[str]:
        """Get all possible substitutes for a chord in this style."""
        pass


class ClassicalProfile(SubstitutionProfile):
    """Classical harmony substitutions - conservative approach."""

    def __init__(self) -> None:
        # Conservative classical substitutions - mainly functional equivalents
        self.substitutions = {
            "IV": {"ii6"},  # Predominant: IV and ii6 often interchangeable
            "ii": {"IV"},  # Especially with ii6 vs IV
            "vi": {"I6"},  # Relative major/minor tonic function
            "I6": {"vi"},
        }

    def get_substitutes(self, chord: str) -> Set[str]:
        base_set = {chord}
        base_set.update(self.substitutions.get(chord, set()))
        return base_set


class JazzProfile(SubstitutionProfile):
    """Jazz harmony substitutions including tritone subs and extensions."""

    def __init__(self) -> None:
        self.substitutions = {
            # Tritone substitutions - defining feature of jazz harmony
            "V": {"♭II7", "V7", "V9", "V13"},
            "V7": {"♭II7", "V9", "V13", "V7alt"},
            "♭II7": {"V", "V7"},  # Reverse tritone sub
            # ii-V relationship - essential jazz progression
            "ii7": {"ii", "iiø7", "ii9"},
            "ii": {"ii7", "ii9"},
            # Extended dominant chords
            "V9": {"V7", "V13"},
            "V13": {"V7", "V9"},
            # Chord quality variations
            "I": {"Imaj7", "I6"},
            "Imaj7": {"I", "I6"},
        }

    def get_substitutes(self, chord: str) -> Set[str]:
        base_set = {chord}
        base_set.update(self.substitutions.get(chord, set()))
        return base_set


class PopProfile(SubstitutionProfile):
    """Pop harmony substitutions - functional equivalences and common variants."""

    def __init__(self) -> None:
        self.substitutions = {
            # Predominant function - very flexible in pop
            "IV": {"ii", "ii6", "IV6"},
            "ii": {"IV", "ii6", "IV6"},
            "ii6": {"IV", "ii"},
            # Common pop chord variations
            "vi": {"vi7", "I6"},  # Relative minor flexibility
            "I": {"I6", "Iadd9"},  # Pop loves add9 chords
            "V": {"V7", "Vsus4"},  # Sus4 resolution very common
            # Modal borrowing common in pop
            "♭VII": {"vii°"},  # Mixolydian ♭VII vs leading tone
            "♭VI": {"vi"},  # Borrowed flat-VI
        }

    def get_substitutes(self, chord: str) -> Set[str]:
        base_set = {chord}
        base_set.update(self.substitutions.get(chord, set()))
        return base_set


class SubstitutionEngine:
    """Manages chord substitutions across different musical styles."""

    def __init__(self) -> None:
        self.profiles = {
            "classical": ClassicalProfile(),
            "jazz": JazzProfile(),
            "pop": PopProfile(),
        }
        self.current_profile = "classical"

    def set_profile(self, profile: str) -> None:
        """Switch to different substitution profile."""
        if profile in self.profiles:
            self.current_profile = profile

    def expand_allowed_chords(
        self, base_chords: List[str], pattern: Pattern
    ) -> Set[str]:
        """Expand base chords with pattern and style substitutions."""
        allowed = set(base_chords)

        # Add pattern-specific substitutions (IV ≈ ii for predominant)
        for chord in list(allowed):
            allowed.update(pattern.substitutions.get(chord, []))

        # Add style-specific substitutions (jazz tritone substitution)
        profile = self.profiles.get(self.current_profile)
        if profile:
            for chord in list(allowed):
                allowed.update(profile.get_substitutes(chord))

        return allowed


# Standalone Dynamic Programming Solver
@dataclass
class ScoredInterval:
    """Interval with score for weighted interval scheduling."""

    start: int
    end: int
    score: float
    data: Any  # Pattern match data

    def overlaps_with(self, other: "ScoredInterval") -> bool:
        """Check if this interval overlaps with another."""
        return not (self.end <= other.start or other.end <= self.start)


class IntervalSchedulingSolver:
    """
    Standalone weighted interval scheduling solver.

    Clean, testable implementation of the classic dynamic programming algorithm
    that can be reused for any weighted interval scheduling problem.
    """

    def solve(self, intervals: List[ScoredInterval]) -> List[ScoredInterval]:
        """
        Find maximum weight non-overlapping subset of intervals.

        The classic DP solution to weighted interval scheduling - separate from
        pattern matching concerns for better testability and reusability.
        """
        if not intervals:
            return []

        # Sort by end time for efficient processing
        sorted_intervals = sorted(intervals, key=lambda x: (x.end, x.start))
        n = len(sorted_intervals)

        # DP table: dp[i] = max score using first i intervals
        dp = [0.0] * (n + 1)
        choose = [False] * n  # Track which intervals to include

        # For each interval, decide whether to include it
        for i in range(1, n + 1):
            current_interval = sorted_intervals[i - 1]

            # Option 1: Include this interval + best solution up to latest
            # non-overlapping
            latest_non_overlapping = self._find_latest_non_overlapping(
                sorted_intervals, i - 1
            )
            include_score = current_interval.score + dp[latest_non_overlapping + 1]

            # Option 2: Exclude this interval (take previous best)
            exclude_score = dp[i - 1]

            # Choose the better option
            if include_score >= exclude_score:
                dp[i] = include_score
                choose[i - 1] = True
            else:
                dp[i] = exclude_score

        # Backtrack to build optimal solution
        return self._backtrack_solution(sorted_intervals, choose)

    def _find_latest_non_overlapping(
        self, intervals: List[ScoredInterval], current_idx: int
    ) -> int:
        """
        Binary search for latest interval that doesn't overlap with current.

        Classic optimization - O(log n) search instead of O(n) linear scan.
        """
        current_start = intervals[current_idx].start
        lo, hi, ans = 0, current_idx - 1, -1

        while lo <= hi:
            mid = (lo + hi) // 2
            if intervals[mid].end <= current_start:
                ans = mid
                lo = mid + 1
            else:
                hi = mid - 1

        return ans

    def _backtrack_solution(
        self, intervals: List[ScoredInterval], choose: List[bool]
    ) -> List[ScoredInterval]:
        """Reconstruct optimal solution from DP choices."""
        solution = []
        i = len(choose)

        while i > 0:
            if choose[i - 1]:
                # Include this interval
                solution.append(intervals[i - 1])
                # Jump to latest non-overlapping
                i = self._find_latest_non_overlapping(intervals, i - 1) + 1
            else:
                i -= 1

        solution.reverse()
        return solution


# Pattern Library with improved loading
class PatternLibrary:
    """Container for harmonic patterns with lazy loading and validation."""

    def __init__(self, patterns: List[Dict[str, Any]]):
        self.patterns: List[Pattern] = []
        self._pattern_index: Dict[str, Pattern] = {}

        # Convert and index patterns for fast lookup
        for p in patterns:
            pattern = self._create_pattern_from_dict(p)
            self.patterns.append(pattern)
            self._pattern_index[pattern.id] = pattern

    def get_pattern_by_id(self, pattern_id: str) -> Optional[Pattern]:
        """Fast O(1) pattern lookup by ID."""
        return self._pattern_index.get(pattern_id)

    def get_patterns_by_family(self, family: str) -> List[Pattern]:
        """Get all patterns of a specific family."""
        return [p for p in self.patterns if p.family == family]

    def _create_pattern_from_dict(self, p: Dict[str, Any]) -> Pattern:
        """Convert JSON pattern dict to structured Pattern object."""
        steps = [StepSpec(**s) for s in p.get("sequence", [])]
        return Pattern(
            id=p["id"],
            family=p.get("family", "misc"),
            name=p.get("name", p["id"]),
            aliases=p.get("aliases", []),
            profiles=p.get("profiles", []),
            window=p.get("window", {"min": 1, "max": 8}),
            sequence=steps,
            constraints=p.get("constraints", {}),
            substitutions=p.get("substitutions", {}),
            score=p.get("score", {"base": 1.0}),
        )


# Main Pattern Matcher with Caching
class PatternMatcher:
    """
    Main pattern matching orchestrator with clean architecture.

    Coordinates the various components while providing caching and
    efficient pattern recognition across different musical styles.
    """

    def __init__(self, library: PatternLibrary, profile: str = "classical"):
        self.library = library
        self.profile = profile

        # Initialize component systems - clean separation of concerns
        self.constraint_validator = ConstraintValidator()
        self.substitution_engine = SubstitutionEngine()
        self.descriptor_registry = DescriptorRegistry()
        self.interval_solver = IntervalSchedulingSolver()

        # Stage B: Low-level event extraction for enhanced constraints
        from .low_level_events import LowLevelEventExtractor

        self.event_extractor = LowLevelEventExtractor()

        # Initialize matching strategies
        self.strategies = [
            SequenceMatchStrategy(self.constraint_validator, self.substitution_engine),
            DescriptorMatchStrategy(self.descriptor_registry),
        ]

        # Set initial profile
        self.substitution_engine.set_profile(profile)

    def match(self, tokens: List[Token], best_cover: bool = True) -> List[PatternMatch]:
        """
        Main entry point - find patterns with improved architecture.

        Public interface matches original matcher for backwards compatibility
        while using clean internal architecture.
        """
        # Phase 1: Find all possible matches using appropriate strategies
        raw_matches = self._find_all_matches(tokens)

        # Phase 2: Return either all matches or optimal subset
        if not best_cover:
            return raw_matches

        return self._find_optimal_cover(raw_matches)

    def _find_all_matches(self, tokens: List[Token]) -> List[PatternMatch]:
        """Find all pattern matches using strategy pattern."""
        matches = []

        # Try each pattern against all possible windows
        for pattern in self.library.patterns:
            # Profile filter: if a pattern declares profiles, it must include the
            # active profile
            if pattern.profiles and self.profile not in pattern.profiles:
                continue

            # Check window constraints
            min_len = pattern.window.get("min", 1)
            max_len = pattern.window.get("max", 8)

            # Slide window across token sequence
            for start in range(len(tokens)):
                for end in range(
                    start + min_len, min(len(tokens), start + max_len) + 1
                ):
                    window_tokens = tokens[start:end]

                    # Try matching with appropriate strategy
                    match_result = self._try_match_pattern(pattern, window_tokens)

                    if match_result.success:
                        # Convert to final format with position metadata
                        pattern_match: PatternMatch = {
                            "pattern_id": pattern.id,
                            "name": pattern.name,
                            "family": pattern.family,
                            "score": match_result.score,
                            "start": start,
                            "end": end,
                            "evidence": match_result.evidence,
                        }
                        matches.append(pattern_match)

        return matches

    def _try_match_pattern(self, pattern: Pattern, tokens: List[Token]) -> MatchResult:
        """Try matching pattern using appropriate strategy."""
        # Find the right strategy for this pattern type
        for strategy in self.strategies:
            if strategy.can_handle(pattern):
                return strategy.match(pattern, tokens)

        # Fallback - no strategy can handle this pattern
        return MatchResult.failure_result(
            MatchFailureReason.DESCRIPTOR_FAILED,
            {"message": "No strategy available for pattern", "pattern_id": pattern.id},
        )

    def _find_optimal_cover(self, matches: List[PatternMatch]) -> List[PatternMatch]:
        """Use interval scheduling to find optimal non-overlapping subset."""
        if not matches:
            return []

        # Convert to scored intervals for the solver
        intervals = [
            ScoredInterval(
                start=match["start"], end=match["end"], score=match["score"], data=match
            )
            for match in matches
        ]

        # Solve the weighted interval scheduling problem
        optimal_intervals = self.interval_solver.solve(intervals)

        # Extract the pattern matches from optimal solution
        return [interval.data for interval in optimal_intervals]

    # ==== DEBUG ACCESSORS (safe to remove later) ====
    def get_pattern_library(self) -> "PatternLibrary":
        """[DEBUG] Expose the loaded pattern library for tooling/inspection."""
        return self.library

    def get_loaded_pattern_ids(self, limit: Optional[int] = None) -> List[str]:
        """[DEBUG] Return loaded pattern IDs (optionally truncated)."""
        ids = [p.id for p in self.library.patterns]
        return ids[:limit] if limit is not None else ids

    def get_substitution_engine(self) -> "SubstitutionEngine":
        """[DEBUG] Expose the substitution engine (for profile checks)."""
        return self.substitution_engine

    def get_current_profile(self) -> str:
        """[DEBUG] Return the currently active profile name."""
        return getattr(self.substitution_engine, "current_profile", self.profile)

    def get_constraint_validator(self) -> "ConstraintValidator":
        """[DEBUG] Expose the constraint validator instance."""
        return self.constraint_validator

    def get_descriptor_registry(self) -> "DescriptorRegistry":
        """[DEBUG] Expose the descriptor registry instance."""
        return self.descriptor_registry

    def try_match_pattern(self, pattern_id: str, tokens: List[Token]) -> "MatchResult":
        """[DEBUG] Public wrapper around internal `_try_match_pattern` by ID."""
        pat = self.library.get_pattern_by_id(pattern_id)
        if not pat:
            return MatchResult.failure_result(
                MatchFailureReason.DESCRIPTOR_FAILED,
                {"message": "Pattern not found", "pattern_id": pattern_id},
            )
        return self._try_match_pattern(pat, tokens)

    # Optional: small helper to build token debug signature
    def tokens_signature(self, tokens: List[Token]) -> str:
        """[DEBUG] Human-friendly signature of tokens (roman:role:flags)."""
        parts = []
        for t in tokens:
            flags = ",".join(t.flags or [])
            parts.append(f"{t.roman}:{t.role}:{flags}")
        return "|".join(parts)

    # ==== END DEBUG ACCESSORS ====

    @lru_cache(maxsize=1000)
    def _cached_pattern_match(
        self, pattern_id: str, token_signature: str
    ) -> MatchResult:
        """
        Cache expensive pattern matches.

        Performance optimization - cache based on pattern ID and token signature
        to avoid recomputing the same matches repeatedly.
        """
        pattern = self.library.get_pattern_by_id(pattern_id)
        if not pattern:
            return MatchResult.failure_result(MatchFailureReason.DESCRIPTOR_FAILED)

        # Reconstruct tokens from signature (simplified for caching demo)
        tokens = self._tokens_from_signature(token_signature)
        return self._try_match_pattern(pattern, tokens)

    def _create_token_signature(self, tokens: List[Token]) -> str:
        """Create hashable signature for token sequence for caching."""
        # Simple signature based on roman numerals and roles
        return "|".join(f"{t.roman}:{t.role}" for t in tokens)

    def _tokens_from_signature(self, signature: str) -> List[Token]:
        """Reconstruct basic tokens from signature (for caching)."""
        tokens = []
        for token_str in signature.split("|"):
            if ":" in token_str:
                roman, role = token_str.split(":", 1)
                tokens.append(Token(roman=roman, role=role))
        return tokens


# NOTE [DEBUG]: This module exposes temporary debug accessors on PatternMatcher/Matcher
# (get_loaded_pattern_ids, try_match_pattern, etc.) to aid the unified debug system.
# These are safe to remove once validation is green.
def load_library(json_path: str) -> PatternLibrary:
    """Load pattern library from JSON file - same interface as original."""
    with open(json_path, "r") as f:
        data = json.load(f)
    return PatternLibrary(data)


# Backwards compatibility - same interface as original matcher
class Matcher(PatternMatcher):
    """
    Primary pattern matching interface.

    Provides comprehensive harmonic pattern recognition with support for
    multiple musical styles and extensible constraint validation.
    """

    def __init__(self, lib: PatternLibrary, profile: str = "classical"):
        # Initialize with profile support for different musical styles
        # Map legacy "default" profile to classical for consistency
        if profile == "default":
            profile = "classical"
        super().__init__(lib, profile)

    # ==== DEBUG ACCESSORS (safe to remove later) ====
    def get_pattern_library(self) -> "PatternLibrary":
        return super().get_pattern_library()

    def get_loaded_pattern_ids(self, limit: Optional[int] = None) -> List[str]:
        return super().get_loaded_pattern_ids(limit)

    def get_substitution_engine(self) -> "SubstitutionEngine":
        return super().get_substitution_engine()

    def get_current_profile(self) -> str:
        return super().get_current_profile()

    def get_constraint_validator(self) -> "ConstraintValidator":
        return super().get_constraint_validator()

    def get_descriptor_registry(self) -> "DescriptorRegistry":
        return super().get_descriptor_registry()

    def try_match_pattern(self, pattern_id: str, tokens: List[Token]) -> MatchResult:
        return super().try_match_pattern(pattern_id, tokens)

    def tokens_signature(self, tokens: List[Token]) -> str:
        return super().tokens_signature(tokens)

    # ==== END DEBUG ACCESSORS ====
