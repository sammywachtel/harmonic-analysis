
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json

@dataclass
class Token:
    """
    Represents a single chord in harmonic analysis with functional information.

    A Token captures both the harmonic identity of a chord (roman numeral, role)
    and contextual voice-leading information (bass motion, soprano degree).
    """
    roman: str  # Roman numeral representation (e.g., "V7", "ii6", "♭VI")
    role: str   # Functional role: "T" (Tonic), "PD" (Predominant), "D" (Dominant)
    flags: List[str] = field(default_factory=list)  # Special markers
    mode: Optional[str] = None  # "major", "minor", or modal context
    bass_motion_from_prev: Optional[int] = None  # Semitone motion from prev (-6 to +6)
    soprano_degree: Optional[int] = None  # Scale degree of soprano voice (1-7)
    secondary_of: Optional[str] = None  # Target of secondary dominant ("V" in "V/V")

    def roman_root(self) -> str:
        """Extract root roman numeral, keep inversions but remove extensions."""
        r = self.roman
        # Keep inversion figures (6, 65, 64, etc.) as they affect harmonic function
        if r.endswith(("6","65","64","43","42")):
            return r
        # Strip seventh chord notation for root matching
        return r.replace("7","")

    def roman_base(self) -> str:
        """Extract root roman numeral with inversions and sevenths removed (inversion-insensitive)."""
        r = self.roman
        # Remove common inversion/figure indicators
        for suf in ("65","64","43","42","6"):
            if r.endswith(suf):
                r = r[: -len(suf)]
                break
        return r.replace("7", "")

@dataclass
class StepSpec:
    """
    Specification for a single step in a harmonic pattern.

    Defines what kinds of chords can match at this position in the pattern,
    using flexible criteria rather than exact matches.
    """
    role: Optional[str] = None  # Required functional role ("T", "PD", "D")
    roman_root_any_of: Optional[List[str]] = None  # Acceptable romans (["V", "V7"])
    quality_any_of: Optional[List[str]] = None  # Chord qualities ("triad", "7", "dim")
    flags_any_of: Optional[List[str]] = None  # Required flags (e.g., ["cadential_64"])
    secondary_of: Optional[str] = None  # Secondary dominant target
    optional: bool = False  # Whether this step can be skipped in pattern matching
    descriptor: Optional[str] = None  # Special pattern ("root_motion_-5_chain_min3")

@dataclass
class Pattern:
    """
    A complete harmonic pattern definition loaded from JSON.

    Patterns represent common harmonic progressions (cadences, sequences, etc.)
    with flexible matching criteria and contextual constraints.
    """
    id: str  # Unique identifier (e.g., "cadence_pac_root")
    family: str  # Pattern category ("cadence", "sequence", "prolongation", etc.)
    name: str  # Human-readable name ("Perfect Authentic Cadence")
    window: Dict[str,int]  # Min/max length constraints for pattern matching
    sequence: List[StepSpec]  # Ordered sequence of chord specifications
    constraints: Dict[str,Any] = field(default_factory=dict)  # Extra requirements
    substitutions: Dict[str,List[str]] = field(default_factory=dict)  # Chord subs
    score: Dict[str,Any] = field(default_factory=dict)  # Scoring weights and bonuses

class PatternLibrary:
    """
    Container for all harmonic patterns loaded from JSON configuration.

    The library converts raw JSON pattern definitions into structured Pattern
    objects that can be efficiently matched against chord progressions.
    """
    def __init__(self, patterns: List[Dict[str,Any]]):
        self.patterns: List[Pattern] = []
        # Convert each JSON pattern definition into a structured Pattern object
        for p in patterns:
            # Build sequence of chord specifications
            steps = [StepSpec(**s) for s in p.get("sequence", [])]
            self.patterns.append(Pattern(
                id=p["id"],
                family=p.get("family","misc"),
                name=p.get("name", p["id"]),
                window=p.get("window", {"min":1,"max":8}),
                sequence=steps,
                constraints=p.get("constraints",{}),
                substitutions=p.get("substitutions",{}),
                score=p.get("score",{"base":1.0})
            ))

class Matcher:
    """
    Main pattern matching machine that finds harmonic patterns in chord progressions.

    Uses dynamic programming to find the optimal non-overlapping set of pattern
    matches, maximizing total score while covering the progression efficiently.
    """
    def __init__(self, lib: PatternLibrary, profile: str = "default"):
        self.lib = lib
        self.profile = profile
        # Style-specific chord substitutions (e.g., jazz tritone substitution)
        self.profile_subs = {
            "default": {},
            "classical": {},
            "jazz": {"V": ["♭II7"]},  # Tritone substitution: ♭II7 can substitute for V
            "pop": {}
        }

    def match(self, tokens: List[Token],
              best_cover: bool = True) -> List[Dict[str,Any]]:
        """
        Find all pattern matches in a sequence of harmonic tokens.

        Args:
            tokens: Sequence of harmonic tokens representing chord progression
            best_cover: If True, return optimal non-overlapping set; else all

        Returns:
            List of pattern match dictionaries with score, evidence, and position info
        """
        raw_hits = []
        # Try each pattern against all possible windows in the token sequence
        for pat in self.lib.patterns:
            minw, maxw = pat.window.get("min",1), pat.window.get("max",8)
            # Slide pattern window across token sequence
            for start in range(len(tokens)):
                for end in range(start+minw, min(len(tokens), start+maxw)+1):
                    window_tokens = tokens[start:end]
                    m = self._match_pattern(pat, window_tokens)
                    if m:
                        # Attach pattern metadata to successful matches
                        m.update({"pattern_id": pat.id, "name": pat.name,
                                  "family": pat.family, "start": start,
                                  "end": end, "len": end-start})
                        raw_hits.append(m)

        # Return either all matches or optimal non-overlapping subset
        if not best_cover:
            return raw_hits
        return self._best_non_overlapping_cover(raw_hits)

    def _best_non_overlapping_cover(
        self, hits: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
        """
        Find the highest-scoring non-overlapping subset of pattern matches.

        Uses dynamic programming to solve the weighted interval scheduling problem,
        maximizing total score while ensuring no two patterns overlap.
        """
        # Sort by end position, then start position for efficient processing
        hits = sorted(hits, key=lambda h: (h["end"], h["start"]))

        def p(idx):
            """Find the latest non-overlapping pattern before this one."""
            s = hits[idx]["start"]
            lo, hi, ans = 0, idx-1, -1
            # Binary search for rightmost pattern that ends before this one starts
            while lo <= hi:
                mid = (lo+hi)//2
                if hits[mid]["end"] <= s:
                    ans = mid; lo = mid+1
                else:
                    hi = mid-1
            return ans

        n = len(hits)
        dp = [0.0]*(n+1)  # dp[i] = max score using first i patterns
        choose = [False]*n  # choose[i] = include pattern i in optimal solution

        # Dynamic programming: for each pattern, choose to include or exclude
        for i in range(1, n+1):
            incl = hits[i-1].get("score",1.0) + dp[p(i-1)+1]  # Include this pattern
            excl = dp[i-1]  # Exclude this pattern
            if incl >= excl:
                dp[i] = incl; choose[i-1] = True
            else:
                dp[i] = excl

        # Backtrack to build optimal solution
        sol = []
        i = n
        while i > 0:
            if choose[i-1]:
                sol.append(hits[i-1]); i = p(i-1) + 1
            else:
                i -= 1
        sol.reverse()
        return sol

    def _match_pattern(
        self, pat: Pattern, toks: List[Token]) -> Optional[Dict[str,Any]]:
        """
        Attempt to match a specific pattern against a sequence of tokens.

        Returns match details if successful, None if pattern doesn't fit.
        Handles both sequence-based patterns and descriptor-based patterns.
        """
        # Handle descriptor-based patterns (e.g., "circle of fifths sequence")
        if any(s.descriptor for s in pat.sequence):
            if self._descriptor_ok(pat.sequence[0].descriptor, toks):
                return {"score": pat.score.get("base", 1.0), "evidence": "descriptor"}
            return None

        # Handle sequence-based patterns - match each step in order
        i = j = 0  # i = token index, j = pattern step index
        evidence = []
        while j < len(pat.sequence) and i <= len(toks):
            if j >= len(pat.sequence): break
            step = pat.sequence[j]
            if i >= len(toks):
                # Check if remaining steps are all optional
                if all(s.optional for s in pat.sequence[j:]):
                    break
                return None
            tok = toks[i]
            if self._step_ok(step, tok, pat):
                # Record evidence of successful step match
                evidence.append((j, tok.roman, tok.role, tok.flags))
                i += 1; j += 1
            else:
                if step.optional: j += 1  # Skip optional step
                else: return None  # Required step failed

        # Check global constraints (voice-leading, mode, etc.)
        if not self._constraints_ok(pat.constraints, toks):
            return None

        return {"score": pat.score.get("base", 1.0), "evidence": evidence}

    def _step_ok(self, step: StepSpec, tok: Token, pat: Pattern) -> bool:
        """
        Check if a token matches the requirements of a pattern step.

        Considers functional role, roman numeral, chord quality, flags,
        secondary dominants, and style-specific substitutions.
        """
        # Descriptor-based steps are handled elsewhere
        if step.descriptor: return False

        # Check functional role match (T, PD, D) with special "T_or_D" flexibility
        if (step.role and step.role != tok.role and
            not (step.role == "T_or_D" and tok.role in ("T","D"))):
            return False

        # Check roman numeral with substitutions and style variations
        if step.roman_root_any_of:
            root = tok.roman_root()
            allowed = set(step.roman_root_any_of)
            # Add pattern-specific substitutions (IV ≈ ii for predominant)
            for a in list(allowed): allowed.update(pat.substitutions.get(a, []))
            # Add style-specific substitutions (e.g., jazz tritone substitution)
            for a in list(allowed):
                allowed.update(self.profile_subs.get(self.profile, {})
                              .get(a, []))
            if root not in allowed: return False

        # Check chord quality flags (e.g., "diminished", "cadential_64")
        if step.flags_any_of and not any(f in tok.flags for f in step.flags_any_of):
            return False

        # Check secondary dominant target (e.g., "V/V" requires secondary_of="V")
        if step.secondary_of:
            if step.secondary_of != "*" and step.secondary_of != tok.secondary_of:
                return False

        return True

    def _constraints_ok(self, cons: Dict[str,Any], toks: List[Token]) -> bool:
        """
        Check if tokens satisfy pattern's global constraints.

        Validates mode requirements, voice-leading, secondary dominants,
        and other contextual requirements beyond basic chord matching.
        """
        if not cons: return True

        # Require specific mode (major, minor, modal)
        if "mode" in cons and not any(t.mode == cons["mode"] for t in toks):
            return False

        # Require secondary dominant somewhere in pattern
        if (cons.get("requires_secondary") and
            not any(t.secondary_of is not None for t in toks)):
            return False

        # Require specific bass motion patterns (e.g., descending fifths)
        if "bass_motion_any_of" in cons:
            if not any(t.bass_motion_from_prev in cons["bass_motion_any_of"]
                      for t in toks if t.bass_motion_from_prev is not None):
                return False

        # Require soprano voice to end on specific scale degrees
        # NOTE: Assumes soprano info from chord symbols - may not be accurate
        if "soprano_any_of" in cons:
            if not any((t.soprano_degree in cons["soprano_any_of"])
                      for t in toks if t.soprano_degree is not None):
                return False

        return True

    def _descriptor_ok(self, descriptor: str, toks: List[Token]) -> bool:
        """
        Check if tokens match special descriptor-based patterns.

        Descriptors identify patterns by structural characteristics rather than
        exact chord sequences (e.g., "circle of fifths" or "chromatic sequence").
        """
        if descriptor == "root_motion_-5_chain_min3":
            # Circle of fifths: requires 3+ chords with descending-fifth motion
            return len(toks) >= 3
        if descriptor == "pachelbel_core":
            # Pachelbel's Canon progression: I-V-vi-iii-IV-I-IV-V
            # TODO: implement explicit root template check for bass line
            return False
        if descriptor == "chromatic_mediant":
            # Chromatic mediant relationships (roots a third apart, different quality)
            return len(toks) >= 1
        return False

def load_library(json_path: str) -> PatternLibrary:
    """Load pattern library from JSON file."""
    with open(json_path, "r") as f:
        data = json.load(f)
    return PatternLibrary(data)

if __name__ == "__main__":
    # Example usage: match patterns against a simple ii-V-I progression
    lib = load_library("patterns.json")
    matcher = Matcher(lib, profile="classical")
    tokens = [
        Token(roman="ii6", role="PD"),  # Predominant function in first inversion
        Token(roman="V7", role="D", bass_motion_from_prev=-5),  # Dominant -5th
        Token(roman="I", role="T", soprano_degree=1),  # Tonic, soprano on 1
    ]
    for h in matcher.match(tokens):
        print(h)
