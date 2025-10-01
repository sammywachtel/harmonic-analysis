"""
Token Converter - Bridge between functional analysis and pattern engine.

Converts the output from FunctionalHarmonyAnalyzer into Token objects
that can be processed by the pattern matching engine.
"""

import re
from typing import Any, List, Optional

from ..utils.scales import NOTE_TO_PITCH_CLASS
from .matcher import Token


class TokenConverter:
    """Converts functional harmony analysis results to pattern engine tokens."""

    def __init__(self) -> None:
        # Use shared note-to-pitch-class mapping
        self.note_to_pc = NOTE_TO_PITCH_CLASS

        # Roman numeral patterns for extraction
        self.roman_pattern = re.compile(r"([b#]*)([ivxIVX]+)([°ø+]?)(\d*)")

    def convert_analysis_to_tokens(
        self,
        chord_symbols: List[str],
        analysis_result: Any,  # FunctionalAnalysisResult object
    ) -> List[Token]:
        """
        Convert functional harmony analysis result to Token objects.

        Pipeline (no key overrides - use analysis result):
          1) Use key+mode from analysis_result
          2) Use upstream Roman numerals if present & trustworthy; else generate once
          3) Apply normalizations (minor subtonic; backdoor preference in major)
          4) Derive roles (reuse upstream where valid, else recompute)
          5) Build Token list with ancillary info (bass motion, soprano
             estimate, secondary_of)
        """
        # ---- 1) Effective key+mode ----
        default_key = "C major"
        key_center = getattr(analysis_result, "key_center", default_key) or default_key
        chords_analysis = getattr(analysis_result, "chords", []) or []
        mode = getattr(
            analysis_result, "mode", None
        )  # may be None/'major'/'minor'/'modal'

        if mode is None or mode == "modal":
            # fall back to extracting from key_center string when analyzer
            # didn't set a concrete mode
            mode = self._extract_mode(key_center)

        # ---- 2) Base roman numerals ----
        upstream_romans = [getattr(ch, "roman_numeral", "") for ch in chords_analysis]
        have_upstream = any(bool(r) for r in upstream_romans)

        if have_upstream:
            # Use upstream romans if present & trustworthy
            roman_numerals = upstream_romans
            used_upstream_romans = True
        else:
            # Generate romans if analyzer did not provide them
            roman_numerals = self._generate_roman_numerals(chord_symbols, key_center)
            used_upstream_romans = False

        # ---- 3) Normalizations ----
        # 3a) Minor subtonic spelling (VII -> bVII when appropriate)
        roman_numerals = self._normalize_minor_subtonic(
            chord_symbols=chord_symbols,
            roman_numerals=roman_numerals,
            key_center=key_center,
        )
        roman_numerals = self._normalize_minor_flat_two(
            roman_numerals=roman_numerals,
            key_center=key_center,
        )
        # 3b) Prefer Backdoor spelling in major (Bb7 -> bVII7)
        roman_numerals = self._prefer_backdoor_bVII(
            chord_symbols=chord_symbols,
            roman_numerals=roman_numerals,
            key_center=key_center,
            mode=mode,
        )

        # ---- 4) Roles ----
        upstream_roles = (
            [
                self._function_to_role(getattr(ch, "function", None), rn)
                for ch, rn in zip(chords_analysis, roman_numerals)
            ]
            if chords_analysis
            else []
        )
        have_roles = any(bool(r) for r in upstream_roles)
        if not used_upstream_romans or not have_roles:
            # Recompute roles when romans were regenerated or upstream roles are missing
            chord_roles = self._generate_chord_roles(roman_numerals)
        else:
            chord_roles = upstream_roles

        # ---- 5) Build Tokens ----
        tokens: List[Token] = []
        for i, (chord_sym, roman, role) in enumerate(
            zip(chord_symbols, roman_numerals, chord_roles)
        ):
            # Bass motion from previous chord
            bass_motion = (
                self._calculate_bass_motion(chord_symbols[i - 1], chord_sym)
                if i > 0
                else None
            )

            # Interpret mode for token (resolve 'modal' lazily per token if needed)
            token_mode = mode if mode != "modal" else self._extract_mode(key_center)

            # Parse extra info from roman
            quality, inversion, flags = self._parse_roman_numeral(roman)
            soprano_degree = self._estimate_soprano_degree(
                roman, i == len(chord_symbols) - 1
            )
            secondary_of = self._detect_secondary_of(roman)

            tokens.append(
                Token(
                    roman=roman,
                    role=role,
                    flags=flags,
                    mode=token_mode,
                    bass_motion_from_prev=bass_motion,
                    soprano_degree=soprano_degree,
                    secondary_of=secondary_of,
                )
            )

        return tokens

    def _generate_roman_numerals(
        self, chord_symbols: List[str], key_center: str
    ) -> List[str]:
        """Generate Roman numerals from chord symbols and key center."""
        # This is a simplified implementation - in practice, we'd use
        # the existing roman numeral analysis from the library
        romans = []

        # Extract key root and mode
        key_parts = key_center.split()
        key_root = key_parts[0] if key_parts else "C"
        is_minor = len(key_parts) > 1 and "minor" in key_parts[1].lower()

        # Simple mapping (this would be much more sophisticated in practice)
        key_pc = self.note_to_pc.get(key_root, 0)

        for chord in chord_symbols:
            # Extract chord root
            chord_root = self._extract_chord_root(chord)
            chord_pc = self.note_to_pc.get(chord_root, 0)

            # Calculate interval from key root
            interval = (chord_pc - key_pc) % 12

            # Map to roman numeral (simplified)
            roman = self._interval_to_roman(interval, is_minor, chord)
            romans.append(roman)

        return romans

    def _generate_chord_roles(self, roman_numerals: List[str]) -> List[str]:
        """Generate T/PD/D roles from Roman numerals."""
        roles = []

        for roman in roman_numerals:
            # Extract the base roman numeral
            base_roman = re.sub(r"[^ivxIVX]", "", roman.lower())

            # Map to functional roles
            if base_roman in ["i", "iii", "vi"]:
                role = "T"  # Tonic
            elif base_roman in ["ii", "iv"]:
                role = "PD"  # Predominant
            elif base_roman in ["v", "vii"]:
                role = "D"  # Dominant
            else:
                # Default based on position - common in pop progressions
                role = "T"

            roles.append(role)

        return roles

    def _normalize_minor_subtonic(
        self, chord_symbols: List[str], roman_numerals: List[str], key_center: str
    ) -> List[str]:
        """Ensure subtonic in minor (scale degree ♭7) is spelled ♭VII rather than VII.
        This runs regardless of whether romans come from upstream or are generated here.

        Rules:
        - Only in minor mode (derived from key_center).
        - If a roman base is 'VII' but the chord root is the natural
          subtonic (a whole step below tonic),
          rewrite 'VII' -> 'bVII' (preserving any trailing figures like 7/6, etc.).
        - Do NOT change genuine leading-tone harmonies (e.g., diminished
          vii°) or obvious secondaries that clearly
          indicate a raised 7th context. We keep it conservative: we skip
          when the roman contains '°' or 'ø'.
        """
        try:
            is_minor = self._extract_mode(key_center) == "minor"
        except Exception:
            is_minor = False
        if not is_minor or not roman_numerals:
            return roman_numerals

        # Compute pitch class for tonic and natural subtonic (whole step below tonic)
        key_root = (key_center.split() or ["C"])[0]
        key_pc = self.note_to_pc.get(key_root, 0)
        natural_subtonic_pc = (key_pc - 2) % 12  # tonic minus whole step

        fixed = list(roman_numerals)
        for i, (ch, rn) in enumerate(zip(chord_symbols, roman_numerals)):
            if not rn:
                continue
            # skip clear leading-tone diminished/half-diminished chords
            if "°" in rn or "ø" in rn:
                continue
            # determine chord root pc
            root = self._extract_chord_root(ch)
            chord_pc = self.note_to_pc.get(root, None)
            if chord_pc is None:
                continue
            # base roman letters (strip accidentals and figures for base compare)
            base = re.sub(r"[^ivxIVX]", "", rn)
            if base.upper() == "VII" and chord_pc == natural_subtonic_pc:
                # If already flat (bVII or ♭VII), leave it alone
                if re.match(r"^[b♭]+\s*VII", rn, flags=re.IGNORECASE):
                    continue
                # Replace only a plain 'VII' (not already prefixed) with 'bVII'
                m = re.search(r"(?<![b♭])VII", rn, flags=re.IGNORECASE)
                if m:
                    start, end = m.start(), m.end()
                    new_rn = rn[:start] + "bVII" + rn[end:]
                    fixed[i] = new_rn
        return fixed

    def _prefer_backdoor_bVII(
        self,
        chord_symbols: List[str],
        roman_numerals: List[str],
        key_center: str,
        mode: str,
    ) -> List[str]:
        """Prefer bVII (or bVII7) over secondary labels on the natural
        subtonic in major keys.
        Example in C major: Bb7 should be bVII7 (not V7/bIII) for the backdoor cadence.
        """
        if not roman_numerals:
            return roman_numerals
        try:
            eff_mode = mode or self._extract_mode(key_center)
        except Exception:
            eff_mode = "major"
        if eff_mode != "major":
            return roman_numerals

        # Compute tonic and subtonic pitch classes in major
        key_root = (key_center.split() or ["C"])[0]
        tonic_pc = self.note_to_pc.get(key_root, 0)
        subtonic_pc = (tonic_pc - 2) % 12  # scale degree ♭7

        fixed = list(roman_numerals)
        for i, (ch, rn) in enumerate(zip(chord_symbols, roman_numerals)):
            if not rn:
                continue
            # Skip if already bVII/♭VII
            if re.match(r"^[b♭]\s*VII", rn, flags=re.IGNORECASE):
                continue
            # Only consider secondary-dominant labels like V/..., V7/...
            if not re.match(r"^V(7)?\/", rn, flags=re.IGNORECASE):
                continue
            # Check that the chord root is the natural subtonic
            root = self._extract_chord_root(ch)
            chord_pc = self.note_to_pc.get(root, None)
            if chord_pc is None or chord_pc != subtonic_pc:
                continue
            # Rewrite to bVII with same seventh marker if present
            has7 = bool(re.match(r"^V7\/", rn, flags=re.IGNORECASE))
            fixed[i] = "bVII7" if has7 else "bVII"
        return fixed

    def _normalize_minor_flat_two(
        self,
        roman_numerals: List[str],
        key_center: str,
    ) -> List[str]:
        """Rewrite applied dominants to ♭V as ♭II in minor contexts.

        Functional analysis sometimes reports the flat second in minor as
        ``V/♭V``. For modal detection (Phrygian), we prefer the simpler
        spelling ``♭II`` so the modal patterns can fire.
        """

        if not roman_numerals:
            return roman_numerals

        try:
            is_minor = self._extract_mode(key_center) == "minor"
        except Exception:
            is_minor = False

        if not is_minor:
            return roman_numerals

        fixed: List[str] = []
        pattern = re.compile(r"^(?P<prefix>V/)(?:♭|b)V(?P<suffix>.*)$", re.IGNORECASE)
        for rn in roman_numerals:
            if not rn:
                fixed.append(rn)
                continue

            match = pattern.match(rn)
            if match:
                suffix = match.group("suffix") or ""
                fixed.append(f"♭II{suffix}")
            else:
                fixed.append(rn)

        return fixed

    def _calculate_bass_motion(self, prev_chord: str, curr_chord: str) -> Optional[int]:
        """Calculate semitone bass motion between chords."""
        prev_root = self._extract_chord_root(prev_chord)
        curr_root = self._extract_chord_root(curr_chord)

        prev_pc = self.note_to_pc.get(prev_root)
        curr_pc = self.note_to_pc.get(curr_root)

        if prev_pc is not None and curr_pc is not None:
            motion = (curr_pc - prev_pc) % 12
            # Convert to signed motion (-6 to +6 range)
            if motion > 6:
                motion -= 12
            return motion

        return None

    def _extract_chord_root(self, chord: str) -> str:
        """Extract chord root, preserving accidentals."""
        if not chord:
            return ""

        # Handle two-character roots (with accidentals)
        if len(chord) >= 2 and chord[1] in ["b", "#"]:
            return chord[:2]
        else:
            return chord[0]

    def _extract_mode(self, key_center: str) -> str:
        """Extract mode from key center string."""
        if "minor" in key_center.lower():
            return "minor"
        else:
            return "major"

    def _parse_roman_numeral(self, roman: str) -> tuple:
        """Parse roman numeral for quality, inversion, and flags."""
        quality = "triad"  # Default
        inversion = None
        flags = []

        # Check for 7th chords
        if "7" in roman:
            quality = "7"

        # Check for diminished/half-diminished
        if "°" in roman:
            quality = "dim"
            flags.append("diminished")
        elif "ø" in roman:
            quality = "half_dim"
            flags.append("half_diminished")

        # Check for inversions (simplified)
        if "6" in roman and "64" not in roman:
            inversion = "6"
            flags.append("first_inversion")
        elif "64" in roman:
            inversion = "64"
            flags.append("second_inversion")
            # Check for cadential 6/4
            if roman.startswith("I") or roman.startswith("i"):
                flags.append("cadential_64")

        return quality, inversion, flags

    def _estimate_soprano_degree(self, roman: str, is_final: bool) -> Optional[int]:
        """Estimate soprano scale degree (placeholder implementation)."""
        # This is a very simplified estimation - real implementation would
        # require melodic analysis or voice-leading information

        if is_final:
            # Final chords often end on tonic (scale degree 1)
            if roman.upper().startswith("I"):
                return 1

        # Could be enhanced with voice-leading analysis
        return None

    def _detect_secondary_of(self, roman: str) -> Optional[str]:
        """Detect secondary dominants in roman numeral notation."""
        # Look for V/x or vii°/x patterns
        if "/" in roman:
            parts = roman.split("/")
            if len(parts) == 2:
                return parts[1]  # Return the target of the secondary

        return None

    def _interval_to_roman(self, interval: int, is_minor: bool, chord: str) -> str:
        """Convert interval to roman numeral (simplified mapping)."""
        # This is a very basic mapping - real implementation would be more sophisticated
        major_romans = [
            "I",
            "bII",
            "II",
            "bIII",
            "III",
            "IV",
            "bV",
            "V",
            "bVI",
            "VI",
            "bVII",
            "VII",
        ]
        # Minor-mode mapping adjusted so that:
        # - interval 10 (e.g., G in A minor) maps to ♭VII (subtonic), not VII
        # - interval 9 (e.g., F# in A minor) maps to ♯VI
        minor_romans = [
            "i",
            "bII",
            "ii",
            "III",
            "iv",
            "IV",
            "bVI",
            "v",
            "VI",
            "♯VI",
            "bVII",
            "vii°",
        ]

        if is_minor:
            base_roman = minor_romans[interval]
        else:
            base_roman = major_romans[interval]

        # --- Minor-key dominant correction: emit uppercase V when chord
        # quality is major/dominant.
        # Dominant is 7 semitones above tonic; if the chord symbol is
        # clearly major-ish, prefer 'V' over 'v'.
        if is_minor and interval == 7:
            name_l = chord.lower()
            is_majorish = ("maj" in name_l) or (
                "m" not in name_l
            )  # no explicit minor marker
            if is_majorish and base_roman.startswith("v"):
                base_roman = "V" + base_roman[1:]

        # Add chord quality indicators (triad quality + seventh type)
        cl = chord.lower()

        # Detect major-7 explicitly (maj7 / ma7 / M7 / Δ / ∆)
        is_maj7 = bool(
            re.search(r"maj7|ma7", cl)
            or re.search(r"\bM7\b", chord)
            or re.search(r"[∆Δ]", chord)
        )

        # Detect a minor triad symbol immediately after the root (avoid matching 'maj')
        # Examples that should match: Am, Fm7, D#m, Gbm7
        # Examples that should NOT match: Amaj7, CM7, C∆7
        is_minor_triad = bool(
            re.match(r"^[A-G](?:#|b)?m(?!aj)", chord, flags=re.IGNORECASE)
        )

        # Lowercase base roman for minor triads (e.g., Fm7 in C major -> iv7)
        if is_minor_triad:
            base_roman = base_roman.lower()

        # Append seventh quality
        if is_maj7:
            base_roman += "maj7"
        elif re.search(r"7(?![+])", chord):  # plain '7' (dominant/minor-7 contexts)
            base_roman += "7"

        return base_roman

    def _function_to_role(self, function: Any, roman: str = "") -> str:
        """Convert ChordFunction enum to T/PD/D role string."""
        # Import here to avoid circular imports
        try:
            from ...analysis_types import ChordFunction

            if function == ChordFunction.TONIC:
                return "T"
            elif function in [ChordFunction.PREDOMINANT, ChordFunction.SUBDOMINANT]:
                return "PD"
            elif function == ChordFunction.DOMINANT:
                return "D"
            elif function == ChordFunction.SUBMEDIANT:
                return "T"  # vi often functions as tonic substitute
            elif function == ChordFunction.MEDIANT:
                return "T"  # iii often functions as tonic substitute
            elif function == ChordFunction.LEADING_TONE:
                return "D"  # vii° functions as dominant
            elif function == ChordFunction.CHROMATIC:
                # Check if this is a chromatic dominant (like V7)
                if "V" in roman and "7" in roman:
                    return "D"
                else:
                    return "T"  # Default for other chromatic functions
            else:
                return "T"
        except ImportError:
            # Fallback if analysis_types not available
            function_str = str(function).lower()
            if "tonic" in function_str:
                return "T"
            elif "predominant" in function_str or "subdominant" in function_str:
                return "PD"
            elif "dominant" in function_str or "leading_tone" in function_str:
                return "D"
            elif "mediant" in function_str or "submediant" in function_str:
                return "T"  # Mediant/submediant often function as tonic substitutes
            else:
                return "T"


# Shared entry point for external callers (e.g., FunctionalHarmonyAnalyzer)
# to obtain a Roman numeral using the same logic as the pattern engine
# (including minor subtonic normalization).


def romanize_chord(
    chord_symbol: str, key_center: str, profile: str = "classical"
) -> str:
    """Return a Roman numeral for a single chord in the given key.

    This uses TokenConverter's internal mapping plus normalization so that
    minor-mode subtonic is spelled ♭VII (not VII).
    """
    tc = TokenConverter()
    romans = tc._generate_roman_numerals([chord_symbol], key_center)
    romans = tc._normalize_minor_subtonic([chord_symbol], romans, key_center)
    return romans[0] if romans else ""


def roman_to_chord(roman_numeral: str, key_center: str) -> str:
    """Convert a Roman numeral to a chord symbol in the given key.

    Args:
        roman_numeral: Roman numeral (e.g., "vi", "V7", "bVII", "V/V")
        key_center: Key context (e.g., "C major", "A minor")

    Returns:
        Chord symbol (e.g., "Am", "G7", "Bb", "D7")

    Examples:
        >>> roman_to_chord("vi", "C major")
        "Am"
        >>> roman_to_chord("V7", "C major")
        "G7"
        >>> roman_to_chord("bVII", "C major")
        "Bb"
        >>> roman_to_chord("V/V", "C major")
        "D7"
    """
    # Main play: parse the key context to get tonic and mode
    key_parts = key_center.split()
    key_root = key_parts[0] if key_parts else "C"
    is_minor = len(key_parts) > 1 and "minor" in key_parts[1].lower()

    # Get tonic pitch class
    from ..utils.scales import NOTE_TO_PITCH_CLASS

    key_pc = NOTE_TO_PITCH_CLASS.get(key_root, 0)

    # Handle secondary dominants first (V/V, vii°/V, etc.)
    if "/" in roman_numeral:
        return _handle_secondary_roman(roman_numeral, key_center, key_pc, is_minor)

    # Parse the roman numeral components
    roman_info = _parse_roman_components(roman_numeral)

    # Calculate the chord root pitch class and spelling
    chord_pc, use_flat = _calculate_chord_pitch_class(roman_info, key_pc, is_minor)

    # Big play: also check key context for better enharmonic spelling
    key_context_flat = _should_use_flat_in_key_context(chord_pc, key_center)
    final_use_flat = use_flat or key_context_flat

    chord_root = _get_note_name(chord_pc, final_use_flat)

    # Build the chord symbol
    chord_symbol = _build_chord_symbol(chord_root, roman_info, is_minor)

    return chord_symbol


def _handle_secondary_roman(
    roman_numeral: str, key_center: str, key_pc: int, is_minor: bool
) -> str:
    """Handle secondary dominants and applied chords (V/V, vii°/ii, etc.)."""
    parts = roman_numeral.split("/")
    if len(parts) != 2:
        # Fallback: treat as regular roman if parsing fails
        return roman_to_chord(parts[0], key_center)

    function_part, target_part = parts

    # Big play: calculate the target chord's root first
    target_info = _parse_roman_components(target_part)
    target_pc, _ = _calculate_chord_pitch_class(target_info, key_pc, is_minor)

    # Then calculate the secondary function relative to that target
    function_info = _parse_roman_components(function_part)

    # Special case: V/x becomes dominant 7th of target
    if function_info["base_numeral"].upper() == "V":
        # V/V in C major: target is V (G), so we want the dominant of G (D7)
        secondary_pc = (target_pc + 7) % 12  # Perfect fifth above target
        chord_root = _get_note_name(
            secondary_pc, False
        )  # Default to sharp for dominants
        return chord_root + "7"  # Secondary dominants are typically 7th chords

    # For other secondary functions, calculate relative to target
    # This is a simplified implementation - could be expanded
    secondary_pc, use_flat = _calculate_chord_pitch_class(
        function_info, target_pc, False
    )  # Treat target as major context
    chord_root = _get_note_name(secondary_pc, use_flat)

    return _build_chord_symbol(chord_root, function_info, False)


def _parse_roman_components(roman: str) -> dict:
    """Parse roman numeral into components for conversion."""
    # Victory lap: extract all the pieces we need for chord building

    # Handle accidentals (b, #, ♭, ♯)
    accidental_match = re.match(r"^([b♭#♯]*)", roman)
    accidentals = accidental_match.group(1) if accidental_match else ""

    # Clean accidentals and extract the core roman
    clean_roman = re.sub(r"^[b♭#♯]*", "", roman)

    # Extract base roman numeral (I, ii, V, etc.)
    base_match = re.search(r"([ivxIVX]+)", clean_roman)
    base_numeral = base_match.group(1) if base_match else "I"

    # Determine if it's major or minor based on case
    is_major_quality = base_numeral.isupper()

    # Extract figured bass and extensions (6, 7, maj7, etc.)
    extensions = re.sub(r"[ivxIVX]+", "", clean_roman)

    # Check for diminished/half-diminished
    is_diminished = "°" in extensions
    is_half_diminished = "ø" in extensions

    # Check for seventh chords
    has_seventh = "7" in extensions
    is_major_seventh = (
        "maj7" in extensions.lower() or "∆" in extensions or "M7" in extensions
    )

    # Check for inversions
    inversion = None
    if "64" in extensions:
        inversion = "64"
    elif "6" in extensions and "64" not in extensions:
        inversion = "6"
    elif "43" in extensions:
        inversion = "43"
    elif "42" in extensions:
        inversion = "42"
    elif "65" in extensions:
        inversion = "65"

    return {
        "accidentals": accidentals,
        "base_numeral": base_numeral,
        "is_major_quality": is_major_quality,
        "extensions": extensions,
        "is_diminished": is_diminished,
        "is_half_diminished": is_half_diminished,
        "has_seventh": has_seventh,
        "is_major_seventh": is_major_seventh,
        "inversion": inversion,
    }


def _calculate_chord_pitch_class(
    roman_info: dict, key_pc: int, is_minor_key: bool
) -> tuple:
    """Calculate the pitch class and enharmonic spelling of the chord root."""
    # Time to tackle the tricky bit: roman numerals to scale degrees

    base_numeral = roman_info["base_numeral"].upper()

    # Map roman numerals to scale degrees (0-based semitones from tonic)
    scale_degrees = {
        "I": 0,  # Tonic
        "II": 2,  # Supertonic
        "III": 4,  # Mediant
        "IV": 5,  # Subdominant
        "V": 7,  # Dominant
        "VI": 9,  # Submediant
        "VII": 11,  # Leading tone
    }

    # Get base interval
    base_interval = scale_degrees.get(base_numeral, 0)

    # Apply accidentals
    accidentals = roman_info["accidentals"]
    accidental_offset = 0
    for acc in accidentals:
        if acc in ["b", "♭"]:
            accidental_offset -= 1
        elif acc in ["#", "♯"]:
            accidental_offset += 1

    # Special minor key adjustments
    if is_minor_key:
        # In minor, naturally flatten III, VI, VII relative to parallel major
        if base_numeral == "III":
            base_interval = 3  # ♭III in minor
        elif base_numeral == "VI":
            base_interval = 8  # ♭VI in minor
        elif base_numeral == "VII":
            base_interval = 10  # ♭VII in minor (natural VII)

    # Calculate final pitch class
    final_pc = (key_pc + base_interval + accidental_offset) % 12

    # Determine preferred enharmonic spelling
    use_flat = _should_use_flat_spelling(base_numeral, accidentals, is_minor_key)

    return final_pc, use_flat


def _should_use_flat_spelling(
    base_numeral: str, accidentals: str, is_minor_key: bool
) -> bool:
    """Determine if we should use flat spelling instead of sharp."""
    # Opening move: check if we have a flat accidental in the roman
    if "b" in accidentals or "♭" in accidentals:
        return True

    # For certain scale degrees, prefer flat spelling contextually
    # bVII is almost always Bb in C major, not A#
    if base_numeral == "VII" and accidentals:
        return True

    # bII, bIII, bVI are typically flats
    if base_numeral in ["II", "III", "VI"] and accidentals:
        return True

    return False


def _should_use_flat_in_key_context(pitch_class: int, key_center: str) -> bool:
    """Determine if a note should use flat spelling based on key context."""
    # Victory lap: use key signature to determine if flats are more natural
    from ..utils.scales import KEY_SIGNATURES

    # Get the key signature accidentals
    key_sig = KEY_SIGNATURES.get(key_center, [])

    # Map pitch classes to potential flat/sharp names
    flat_names = {1: "Db", 3: "Eb", 6: "Gb", 8: "Ab", 10: "Bb"}
    sharp_names = {1: "C#", 3: "D#", 6: "F#", 8: "G#", 10: "A#"}

    if pitch_class not in flat_names:
        return False  # Natural note, no choice needed

    flat_name = flat_names[pitch_class]
    sharp_name = sharp_names[pitch_class]

    # Check if the flat version appears in the key signature
    if flat_name in key_sig:
        return True

    # Check if the sharp version appears in the key signature
    if sharp_name in key_sig:
        return False

    # Default preference based on key: flat keys prefer flats, sharp keys prefer sharps
    flat_keys = [
        "F major",
        "Bb major",
        "Eb major",
        "Ab major",
        "Db major",
        "Gb major",
        "Cb major",
        "D minor",
        "G minor",
        "C minor",
        "F minor",
        "Bb minor",
        "Eb minor",
        "Ab minor",
    ]

    return key_center in flat_keys


def _get_note_name(pitch_class: int, use_flat: bool) -> str:
    """Get the appropriate note name for a pitch class."""
    from ..utils.scales import PITCH_CLASS_NAMES

    # Standard sharp-based names
    if not use_flat:
        return PITCH_CLASS_NAMES[pitch_class]

    # Flat-based enharmonic equivalents
    flat_names = {
        1: "Db",  # C#/Db
        3: "Eb",  # D#/Eb
        6: "Gb",  # F#/Gb
        8: "Ab",  # G#/Ab
        10: "Bb",  # A#/Bb
    }

    return flat_names.get(pitch_class, PITCH_CLASS_NAMES[pitch_class])


def _build_chord_symbol(chord_root: str, roman_info: dict, is_minor_key: bool) -> str:
    """Build the final chord symbol from root and roman numeral info."""
    # Final whistle: piece together the chord symbol

    chord_symbol = chord_root

    # Determine chord quality from roman case and context
    if roman_info["is_diminished"]:
        chord_symbol += "dim"
        if roman_info["has_seventh"]:
            chord_symbol += "7"
    elif roman_info["is_half_diminished"]:
        chord_symbol += "m7b5"  # Standard notation for half-diminished
    elif not roman_info["is_major_quality"]:
        # Lowercase roman = minor chord
        chord_symbol += "m"
        if roman_info["has_seventh"]:
            if roman_info["is_major_seventh"]:
                chord_symbol += "maj7"
            else:
                chord_symbol += "7"
    else:
        # Uppercase roman = major chord
        if roman_info["has_seventh"]:
            if roman_info["is_major_seventh"]:
                chord_symbol += "maj7"
            else:
                chord_symbol += "7"  # Dominant 7th

    # Add inversion notation if present
    # Note: This is simplified - full implementation might use slash notation
    if roman_info["inversion"]:
        pass  # Could add slash chord notation here

    return chord_symbol


# ============================================================================
# Scale Analysis Functions (Iteration 12)
# ============================================================================


def normalize_scale_input(notes: List[str], key_hint: str) -> dict:
    """
    Normalize and validate scale input, detecting mode and scale degrees.

    Args:
        notes: List of note names (e.g., ['C', 'D', 'E', 'F', 'G', 'A', 'B'])
        key_hint: Key context (e.g., 'C major', 'D dorian') - required for validation

    Returns:
        Dictionary containing:
        - canonical_notes: List of canonical note names
        - scale_degrees: List of scale degrees relative to key
        - detected_mode: Detected mode name (e.g., 'Ionian', 'Dorian')
        - intervals: Interval pattern in semitones
        - is_valid: Whether the scale is valid for the given key
        - validation_errors: List of validation error messages

    Raises:
        ValueError: If key_hint is missing or invalid
    """
    from ..utils.scales import NOTE_TO_PITCH_CLASS

    if not key_hint:
        raise ValueError("Scale analysis requires key_hint parameter")

    # Parse input notes - support various formats
    canonical_notes = _parse_scale_notes(notes)

    # Extract key info from hint
    key_info = _parse_key_hint(key_hint)

    # Convert notes to pitch classes and degrees
    note_pitch_classes = []
    validation_errors = []

    for note in canonical_notes:
        if note not in NOTE_TO_PITCH_CLASS:
            validation_errors.append(f"Invalid note: {note}")
            continue
        note_pitch_classes.append(NOTE_TO_PITCH_CLASS[note])

    if validation_errors:
        return {
            "canonical_notes": canonical_notes,
            "scale_degrees": [],
            "detected_mode": None,
            "intervals": [],
            "is_valid": False,
            "validation_errors": validation_errors,
        }

    # Calculate intervals from first note
    if note_pitch_classes:
        tonic_pc = note_pitch_classes[0]
        intervals = [(pc - tonic_pc) % 12 for pc in note_pitch_classes]
    else:
        intervals = []

    # Calculate step intervals for mode detection
    step_intervals = []
    if len(note_pitch_classes) > 1:
        for i in range(1, len(note_pitch_classes)):
            step = (note_pitch_classes[i] - note_pitch_classes[i - 1]) % 12
            step_intervals.append(step)

    # Detect mode by comparing step interval pattern
    detected_mode = _detect_mode_from_intervals(step_intervals)

    # Calculate scale degrees relative to the key hint
    key_tonic = _extract_key_tonic(key_info["key"])
    key_pc = NOTE_TO_PITCH_CLASS.get(key_tonic, 0)

    scale_degrees = []
    for pc in note_pitch_classes:
        degree = ((pc - key_pc) % 12) + 1  # 1-based scale degrees
        scale_degrees.append(degree)

    # Validate against expected scale for the key
    is_valid = _validate_scale_against_key(step_intervals, key_info, detected_mode)

    return {
        "canonical_notes": canonical_notes,
        "scale_degrees": scale_degrees,
        "detected_mode": detected_mode,
        "intervals": intervals,
        "is_valid": is_valid,
        "validation_errors": validation_errors,
        "key_info": key_info,
    }


def _parse_scale_notes(notes: List[str]) -> List[str]:
    """Parse and normalize note names from various input formats."""
    canonical_notes = []

    # Handle comma-separated strings
    if len(notes) == 1 and "," in notes[0]:
        notes = [note.strip() for note in notes[0].split(",")]

    # Handle space-separated strings
    elif len(notes) == 1 and " " in notes[0]:
        notes = [note.strip() for note in notes[0].split()]

    for note in notes:
        if not note.strip():
            continue

        # Normalize note name
        note = note.strip()

        # Handle flat notation (both 'b' and '♭')
        note = note.replace("♭", "b")

        # Handle sharp notation (both '#' and '♯')
        note = note.replace("♯", "#")

        # Capitalize first letter
        if note:
            note = note[0].upper() + note[1:]

        canonical_notes.append(note)

    return canonical_notes


def _parse_key_hint(key_hint: str) -> dict:
    """Parse key hint into components."""
    key_hint = key_hint.strip().lower()

    # Handle modal key hints (e.g., "D dorian", "G mixolydian")
    # Check longer mode names first to avoid substring matching issues
    modal_modes = [
        "mixolydian",
        "phrygian",
        "aeolian",
        "locrian",
        "dorian",
        "lydian",
        "ionian",
    ]

    for mode in modal_modes:
        if mode in key_hint:
            tonic = key_hint.replace(mode, "").strip()
            return {
                "key": f"{tonic.capitalize()} {mode}",
                "tonic": tonic.capitalize(),
                "mode": mode.capitalize(),
                "is_modal": True,
            }

    # Handle standard major/minor keys
    if "major" in key_hint:
        tonic = key_hint.replace("major", "").strip()
        return {
            "key": f"{tonic.capitalize()} major",
            "tonic": tonic.capitalize(),
            "mode": "Ionian",
            "is_modal": False,
        }
    elif "minor" in key_hint:
        tonic = key_hint.replace("minor", "").strip()
        return {
            "key": f"{tonic.capitalize()} minor",
            "tonic": tonic.capitalize(),
            "mode": "Aeolian",
            "is_modal": False,
        }

    # Default to major if no mode specified
    return {
        "key": f"{key_hint.capitalize()} major",
        "tonic": key_hint.capitalize(),
        "mode": "Ionian",
        "is_modal": False,
    }


def _extract_key_tonic(key: str) -> str:
    """Extract tonic note from key string."""
    return key.split()[0]


def _detect_mode_from_intervals(intervals: List[int]) -> Optional[str]:
    """Detect mode name from interval pattern between consecutive notes."""
    from ..utils.scales import ALL_SCALE_SYSTEMS

    if not intervals:
        return None

    # Convert step intervals to cumulative intervals for comparison
    cumulative = [0]
    current = 0
    for step in intervals:
        current += step
        cumulative.append(current % 12)

    # For scale matching, we want all scale degrees including the last one
    scale_degrees = cumulative

    # Search through all scale systems
    for system_name, modes in ALL_SCALE_SYSTEMS.items():
        for mode_name, mode_intervals in modes.items():
            if scale_degrees == mode_intervals:
                return mode_name

    return None


def _validate_scale_against_key(
    intervals: List[int], key_info: dict, detected_mode: Optional[str]
) -> bool:
    """Validate that the scale makes sense for the given key context."""
    if not detected_mode:
        return False

    # Normalize case for comparison (modes are case-insensitive)
    detected_mode_lower = detected_mode.lower()
    expected_mode_lower = key_info["mode"].lower() if key_info["mode"] else ""

    # If the key hint specifies a mode, check if detected mode matches
    if key_info["is_modal"]:
        return detected_mode_lower == expected_mode_lower

    # For major/minor keys, accept related modes
    if expected_mode_lower == "ionian":
        # Accept any major scale mode
        major_modes = ["ionian", "lydian", "mixolydian"]
        return detected_mode_lower in major_modes
    elif expected_mode_lower == "aeolian":
        # Accept any minor scale mode
        minor_modes = ["aeolian", "dorian", "phrygian"]
        return detected_mode_lower in minor_modes

    return True
