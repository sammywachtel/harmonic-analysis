"""
Low-Level Event Detection for Pattern Engine

Extracts bass-driven and voice-leading events from harmonic analysis tokens
to enhance pattern matching with texture and voice-leading constraints.

Stage B implementation as outlined in music-alg.md
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple
from .matcher import Token
from ...analysis_types import MelodicEvents


@dataclass
class LowLevelEvents:
    """Per-index event flags for pattern constraint matching.

    Each list has the same length as the token sequence, with boolean/string
    values indicating whether the event is present at each chord position.
    """

    # Bass-driven events (implemented first)
    has_cadential64: List[bool]          # I64 with dominant bass texture
    has_pedal_bass: List[bool]           # Bass pitch class unchanged ≥2 chords
    bass_degree: List[Optional[str]]     # Scale degree in bass: '♭2','5','1','♯4'
    root_motion: List[str]               # '-5', '+2', 'chromatic', 'same', etc.

    # Voice-leading events (stubbed for future)
    voice_4_to_3: List[bool]             # 4→3 suspension resolution
    voice_7_to_1: List[bool]             # 7→1 leading tone resolution
    fi_to_sol: List[bool]                # ♯4→5 (augmented sixth resolution)
    le_to_sol: List[bool]                # ♭6→5 (Phrygian II6 resolution)

    @classmethod
    def create_empty(cls, length: int) -> 'LowLevelEvents':
        """Create empty events structure for given sequence length."""
        return cls(
            has_cadential64=[False] * length,
            has_pedal_bass=[False] * length,
            bass_degree=[None] * length,
            root_motion=[''] * length,
            voice_4_to_3=[False] * length,
            voice_7_to_1=[False] * length,
            fi_to_sol=[False] * length,
            le_to_sol=[False] * length,
        )


class LowLevelEventExtractor:
    """Extracts low-level events from token sequences for pattern constraints.

    Focuses on bass-driven events first (B2 minimal detectors):
    - Root motion chain detection
    - Cadential 64 texture verification
    - Neapolitan cue (♭2 in bass)
    - Pedal point detection
    """

    def __init__(self):
        # Note to pitch class mapping
        self.note_to_pc = {
            'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4,
            'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9,
            'A#': 10, 'Bb': 10, 'B': 11
        }

        # Pitch class to scale degree mapping (relative to key tonic)
        self.pc_to_degree_names = {
            0: '1', 1: '♭2', 2: '2', 3: '♭3', 4: '3', 5: '4',
            6: '♯4', 7: '5', 8: '♭6', 9: '6', 10: '♭7', 11: '7'
        }

    def extract_events(
        self,
        tokens: List[Token],
        chord_symbols: List[str],
        key_center: str
    ) -> LowLevelEvents:
        """Extract all low-level events from token sequence.

        Args:
            tokens: Harmonic analysis tokens
            chord_symbols: Original chord symbols
            key_center: Key center string (e.g., "C major")

        Returns:
            LowLevelEvents with detected events at each position
        """
        if not tokens:
            return LowLevelEvents.create_empty(0)

        events = LowLevelEvents.create_empty(len(tokens))

        # Extract key information
        tonic_pc = self._parse_key_tonic_pc(key_center)

        # Extract bass pitch classes from chord symbols
        bass_pcs = self._extract_bass_pitch_classes(chord_symbols)

        # Detect events
        events.root_motion = self._detect_root_motion(tokens)
        events.bass_degree = self._detect_bass_degrees(bass_pcs, tonic_pc)
        events.has_cadential64 = self._detect_cadential64(tokens, bass_pcs, tonic_pc)
        events.has_pedal_bass = self._detect_pedal_points(bass_pcs)

        # Voice-leading events: use inference when no explicit melody available
        voice_leading = self._infer_voice_leading_events(tokens, chord_symbols, tonic_pc)
        events.voice_4_to_3 = voice_leading.voice_4_to_3
        events.voice_7_to_1 = voice_leading.voice_7_to_1
        events.fi_to_sol = voice_leading.fi_to_sol
        events.le_to_sol = voice_leading.le_to_sol

        return events

    def _infer_voice_leading_events(
        self,
        tokens: List[Token],
        chord_symbols: List[str],
        tonic_pc: int
    ) -> MelodicEvents:
        """Infer voice-leading events from chord progression patterns.

        This provides voice-leading analysis when no explicit melody is available,
        based on common harmonic patterns that imply specific voice motions.

        Args:
            tokens: Harmonic analysis tokens
            chord_symbols: Original chord symbols
            tonic_pc: Tonic pitch class

        Returns:
            MelodicEvents with inferred voice-leading patterns
        """
        length = len(tokens)

        # Initialize all events as empty/false
        melodic_events = MelodicEvents(
            soprano_degree=[None] * length,
            voice_4_to_3=[False] * length,
            voice_7_to_1=[False] * length,
            fi_to_sol=[False] * length,
            le_to_sol=[False] * length,
            source="inference"
        )

        # Detect voice-leading patterns from chord progressions
        melodic_events.voice_4_to_3 = self._detect_4_to_3_inference(tokens)
        melodic_events.voice_7_to_1 = self._detect_7_to_1_inference(tokens, chord_symbols)
        melodic_events.fi_to_sol = self._detect_fi_to_sol_inference(tokens, chord_symbols)
        melodic_events.le_to_sol = self._detect_le_to_sol_inference(tokens, chord_symbols)

        return melodic_events

    def _detect_4_to_3_inference(self, tokens: List[Token]) -> List[bool]:
        """Detect 4→3 suspension resolution from cadential 6/4 → V patterns."""
        voice_4_to_3 = [False] * len(tokens)

        for i in range(len(tokens) - 1):
            current_token = tokens[i]
            next_token = tokens[i + 1]

            # Look for I64 → V pattern (classic 4→3 suspension)
            current_roman = current_token.roman.lower()
            next_roman = next_token.roman.lower()

            if (current_roman.startswith('i') and ('64' in current_roman or '6/4' in current_roman or '⁶⁴' in current_roman) and
                next_roman.startswith('v') and next_token.role == "D"):
                # Mark 4→3 resolution at the V chord
                voice_4_to_3[i + 1] = True

        return voice_4_to_3

    def _detect_7_to_1_inference(self, tokens: List[Token], chord_symbols: List[str]) -> List[bool]:
        """Detect 7→1 leading tone resolution from V7 → I patterns."""
        voice_7_to_1 = [False] * len(tokens)

        for i in range(len(tokens) - 1):
            current_token = tokens[i]
            next_token = tokens[i + 1]
            current_chord = chord_symbols[i] if i < len(chord_symbols) else ""

            # Look for V7 → I pattern (classic 7→1 leading tone resolution)
            current_roman = current_token.roman.lower()
            next_roman = next_token.roman.lower()

            if (current_token.role == "D" and
                (current_roman.startswith('v') and '7' in current_chord.lower()) and
                next_token.role == "T" and next_roman.startswith('i')):
                # Mark 7→1 resolution at the I chord
                voice_7_to_1[i + 1] = True

        return voice_7_to_1

    def _detect_fi_to_sol_inference(self, tokens: List[Token], chord_symbols: List[str]) -> List[bool]:
        """Detect ♯4→5 resolution from augmented sixth → V patterns."""
        fi_to_sol = [False] * len(tokens)

        for i in range(len(tokens) - 1):
            current_token = tokens[i]
            next_token = tokens[i + 1]
            current_chord = chord_symbols[i] if i < len(chord_symbols) else ""

            # Look for augmented sixth chords → V pattern
            next_roman = next_token.roman.lower()

            # Check for augmented sixth chord indicators
            aug6_indicators = ['+6', 'it+6', 'fr+6', 'ger+6', 'aug6']
            is_aug6 = any(indicator in current_chord.lower() for indicator in aug6_indicators)

            if (is_aug6 and next_token.role == "D" and next_roman.startswith('v')):
                # Mark ♯4→5 resolution at the V chord
                fi_to_sol[i + 1] = True

        return fi_to_sol

    def _detect_le_to_sol_inference(self, tokens: List[Token], chord_symbols: List[str]) -> List[bool]:
        """Detect ♭6→5 resolution from Phrygian ii6 → V patterns."""
        le_to_sol = [False] * len(tokens)

        for i in range(len(tokens) - 1):
            current_token = tokens[i]
            next_token = tokens[i + 1]

            # Look for Phrygian ii6 → V pattern (characteristic of minor keys)
            current_roman = current_token.roman.lower()
            next_roman = next_token.roman.lower()

            if (current_token.role == "PD" and
                current_roman.startswith('ii') and '6' in current_roman and
                next_token.role == "D" and next_roman.startswith('v')):
                # Mark ♭6→5 resolution at the V chord
                le_to_sol[i + 1] = True

        return le_to_sol

    def _parse_key_tonic_pc(self, key_center: str) -> int:
        """Extract tonic pitch class from key center string."""
        tonic_name = key_center.split()[0] if key_center else 'C'
        return self.note_to_pc.get(tonic_name, 0)

    def _parse_note_pc(self, note: str) -> int:
        """Parse a note token like 'E#', 'Gb', 'C##', 'Dbb' (Unicode ♯/♭ supported) to a pitch class 0–11.
        Only the leading letter A–G and a run of accidentals are considered; any trailing quality/octave is ignored.
        """
        if not note:
            return 0
        s = note.strip()
        # Normalize Unicode accidentals and double symbols
        s = (
            s.replace('♯', '#')
             .replace('♭', 'b')
             .replace('𝄪', '##')
             .replace('𝄫', 'bb')
        )
        # Take leading letter
        if not s or s[0].upper() not in 'ABCDEFG':
            # Fallback: if malformed, return 0 to avoid crashes
            return 0
        letter = s[0].upper()
        base_map = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
        pc = base_map[letter]
        # Count consecutive accidentals after the letter
        i = 1
        acc = 0
        while i < len(s) and s[i] in ('#', 'b'):
            acc += 1 if s[i] == '#' else -1
            i += 1
        return (pc + acc) % 12

    def _extract_bass_pitch_classes(self, chord_symbols: List[str]) -> List[int]:
        """Extract bass note pitch class from each chord symbol.

        Handles slash chords (e.g., C/G) and basic chord symbols.
        """
        pcs: List[int] = []
        for chord in chord_symbols:
            if not chord:
                pcs.append(0)
                continue
            s = chord.strip()
            # Prefer explicit bass of slash chords
            if '/' in s:
                parts = s.split('/')
                bass_tok = parts[-1] or parts[0]
            else:
                bass_tok = s
            # Parse only the leading note+accidentals of the bass token
            pc = self._parse_note_pc(bass_tok)
            pcs.append(pc)
        return pcs

    def _detect_root_motion(self, tokens: List[Token]) -> List[str]:
        """Detect root motion patterns between adjacent chords."""
        if len(tokens) < 2:
            return [''] * len(tokens)

        motions = ['']  # First chord has no previous motion

        for i in range(1, len(tokens)):
            prev_motion = tokens[i-1].bass_motion_from_prev
            curr_motion = tokens[i].bass_motion_from_prev

            # Use current token's bass motion if available
            if curr_motion is not None:
                interval = curr_motion % 12  # Normalize to 0-11

                # Categorize motion
                if interval == 0:
                    motion = 'same'
                elif interval == 7:  # +7 semitones = ascending fifth
                    motion = '-5'  # Circle of fifths descending (standard notation)
                elif interval == 5:  # +5 semitones = ascending fourth
                    motion = '+4'  # Fourth up (equivalent to fifth down)
                elif interval == 2:
                    motion = '+2'  # Step up
                elif interval == 10:  # -2 mod 12
                    motion = '-2'  # Step down
                elif interval == 1 or interval == 11:
                    motion = 'chromatic'
                else:
                    motion = f'{curr_motion:+d}'  # Generic interval
            else:
                motion = 'unknown'

            motions.append(motion)

        return motions

    def _detect_bass_degrees(self, bass_pcs: List[int], tonic_pc: int) -> List[Optional[str]]:
        """Detect scale degree in bass relative to key tonic."""
        degrees = []
        for bass_pc in bass_pcs:
            interval = (bass_pc - tonic_pc) % 12
            degree_name = self.pc_to_degree_names.get(interval)
            degrees.append(degree_name)
        return degrees

    def _detect_cadential64(
        self,
        tokens: List[Token],
        bass_pcs: List[int],
        tonic_pc: int
    ) -> List[bool]:
        """Detect cadential 6/4 texture: I64 with dominant bass function.

        True cadential 6/4 has:
        1. Roman numeral I64 (or I6/4)
        2. Bass on dominant (5th degree)
        3. Functions as dominant preparation
        """
        cadential64_flags = []

        for i, token in enumerate(tokens):
            is_cadential64 = False

            # Check for I64 roman numeral pattern
            roman = token.roman.lower()
            if roman.startswith('i') and ('64' in roman or '6/4' in roman or '⁶⁴' in roman):
                # Check if bass is on dominant (5th degree)
                if i < len(bass_pcs):
                    bass_pc = bass_pcs[i]
                    dominant_pc = (tonic_pc + 7) % 12  # 5th degree

                    if bass_pc == dominant_pc:
                        # For cadential 6/4, the chord typically functions as dominant preparation
                        # but the role might still be T (tonic) because it's still I chord
                        # The key is that it's I64 with dominant bass
                        is_cadential64 = True

            cadential64_flags.append(is_cadential64)

        return cadential64_flags

    def _detect_pedal_points(self, bass_pcs: List[int]) -> List[bool]:
        """Detect pedal points: bass pitch unchanged for ≥2 consecutive chords."""
        if len(bass_pcs) < 2:
            return [False] * len(bass_pcs)

        pedal_flags = [False] * len(bass_pcs)

        # Find runs of same bass pitch
        for i in range(len(bass_pcs)):
            # Count consecutive same pitches starting from current position
            run_length = 1
            for j in range(i + 1, len(bass_pcs)):
                if bass_pcs[j] == bass_pcs[i]:
                    run_length += 1
                else:
                    break

            # Mark as pedal if run is ≥2 chords
            if run_length >= 2:
                for k in range(i, i + run_length):
                    pedal_flags[k] = True

        return pedal_flags

    def _detect_circle_of_fifths_chains(self, events: LowLevelEvents, min_length: int = 3) -> Dict[str, Any]:
        """
        Detect circle-of-fifths chains from the precomputed root-motion events.

        A qualifying link is a motion of '-5' (down a fifth) or '+4' (up a fourth),
        which are enharmonically the same functional motion.

        Args:
            events: LowLevelEvents containing `root_motion` (one entry per chord; first entry may be empty).
            min_length: Minimum number of consecutive qualifying transitions to count as a chain.
                        Note this counts *transitions*, so a chain with 3 transitions spans 4 chords.

        Returns:
            A descriptor dict identical to `get_circle_of_fifths_descriptor`, e.g.:
            {
                "type": "circle5",
                "min_length": 3,
                "chains": [{"start": 2, "length": 4}, ...],  # start index and number of chords in chain
                "found": true
            }
        """
        # Keep single source of truth: delegate to the module-level helper so tests and constraints
        # use the same semantics.
        return get_circle_of_fifths_descriptor(events, min_length=min_length)


# Descriptor generators for pattern constraints
def get_circle_of_fifths_descriptor(events: LowLevelEvents, min_length: int = 3) -> Dict[str, Any]:
    """Generate circle of fifths chain descriptor from root motion events.

    Args:
        min_length: Minimum number of consecutive fifth transitions required
                   (e.g., min_length=3 means ≥3 transitions, requiring ≥4 chords)

    Returns descriptor dict for pattern constraints:
    {"type": "circle5", "chains": [{"start": i, "length": chord_count}]}

    Note: "length" in chains refers to number of chords, not transitions.
    For min_length transitions, we need min_length+1 chords.
    """
    chains = []
    current_chain_start = None
    current_chord_count = 0  # Number of chords in current chain

    for i, motion in enumerate(events.root_motion):
        if motion == '-5' or motion == '+4':  # Fifth motion
            if current_chain_start is None:
                current_chain_start = i - 1 if i > 0 else i  # Include previous chord
                current_chord_count = 2  # Previous chord + current chord
            else:
                current_chord_count += 1  # Add another chord to chain
        else:
            # Chain broken - check if we have enough transitions
            transitions_count = current_chord_count - 1 if current_chord_count > 0 else 0
            if transitions_count >= min_length:
                chains.append({
                    "start": current_chain_start,
                    "length": current_chord_count  # Number of chords
                })
            current_chain_start = None
            current_chord_count = 0

    # Check final chain
    transitions_count = current_chord_count - 1 if current_chord_count > 0 else 0
    if transitions_count >= min_length:
        chains.append({
            "start": current_chain_start,
            "length": current_chord_count  # Number of chords
        })

    return {
        "type": "circle5",
        "min_length": min_length,
        "chains": chains,
        "found": len(chains) > 0
    }
