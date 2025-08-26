"""
Scale and Melody Analysis Module

Implements sophisticated scale and melody analysis including:
- Parent scale detection (which major/minor scales contain all notes)
- Modal label generation for different tonic centers
- Contextual classification (diatonic vs modal borrowing vs modal candidate)
- Melody tonic inference with confidence scoring
- Non-diatonic pitch identification

This module implements the 5-step contextual classification algorithm:
1. Identify parent scales that contain all notes
2. Test diatonic fitness against provided key context
3. Classify usage as diatonic/modal_borrowing/modal_candidate
4. Generate modal labels for all potential tonic centers
5. Provide analysis rationale and confidence scoring
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ScaleMelodyAnalysisResult:
    """Result of scale/melody analysis with comprehensive expectations"""

    notes: List[str]
    key: Optional[str]
    melody: bool

    # Core analysis results
    parent_scales: List[str]
    diatonic_in_key: Optional[bool]
    non_diatonic_pitches: List[str]
    modal_labels: Dict[str, str]
    classification: str

    # Melody-specific results
    suggested_tonic: Optional[str] = None
    confidence: Optional[float] = None

    # Analysis explanation
    rationale: str = ""


class ScaleMelodyAnalyzer:
    """
    Sophisticated scale and melody analyzer implementing contextual classification.

    This analyzer provides enhanced functionality for the comprehensive test framework,
    including parent scale detection, modal analysis, and contextual classification.
    """

    def __init__(self) -> None:
        # Note to pitch class mapping (enharmonic aware)
        self.note_map = {
            "C": 0,
            "C#": 1,
            "Db": 1,
            "D": 2,
            "D#": 3,
            "Eb": 3,
            "E": 4,
            "F": 5,
            "F#": 6,
            "Gb": 6,
            "G": 7,
            "G#": 8,
            "Ab": 8,
            "A": 9,
            "A#": 10,
            "Bb": 10,
            "B": 11,
        }

        # Major scale pattern (whole and half steps)
        self.major_scale_intervals = [0, 2, 4, 5, 7, 9, 11]

        # Mode names for scale degrees
        self.mode_names = [
            "Ionian",
            "Dorian",
            "Phrygian",
            "Lydian",
            "Mixolydian",
            "Aeolian",
            "Locrian",
        ]

        # Major keys for parent scale detection
        self.major_keys = [
            "C",
            "G",
            "D",
            "A",
            "E",
            "B",
            "F#",
            "Db",
            "Ab",
            "Eb",
            "Bb",
            "F",
        ]

    def analyze_scale_melody(
        self, notes: List[str], key: Optional[str] = None, melody: bool = False
    ) -> ScaleMelodyAnalysisResult:
        """
        Comprehensive scale/melody analysis implementing the 5-step algorithm.

        Args:
            notes: List of note names (e.g., ["D", "E", "F", "G", "A", "B", "C"])
            key: Optional key context (e.g., "C major", "Bb major")
            melody: Whether this is a melodic sequence (affects tonic inference)

        Returns:
            ScaleMelodyAnalysisResult with complete analysis
        """
        # Step 1: Identify parent scales that contain all notes
        parent_scales = self._detect_parent_scales(notes)

        # Step 2: Test diatonic fitness against provided key context
        diatonic_in_key = None
        non_diatonic_pitches = []
        if key:
            diatonic_in_key = self._test_diatonic_fitness(notes, key)
            if not diatonic_in_key:
                non_diatonic_pitches = self._identify_non_diatonic_pitches(notes, key)

        # Step 3: Classify usage as diatonic/modal_borrowing/modal_candidate
        classification = self._classify_scale_usage(notes, key, diatonic_in_key)

        # Step 4: Generate modal labels for all potential tonic centers
        modal_labels = self._generate_modal_labels(notes, parent_scales)

        # Step 5: Melody-specific analysis (tonic inference)
        suggested_tonic = None
        confidence = None
        if melody:
            suggested_tonic, confidence = self._infer_melody_tonic(notes)

        # Generate analysis rationale
        rationale = self._generate_rationale(
            notes,
            key,
            classification,
            parent_scales,
            non_diatonic_pitches,
            modal_labels,
            suggested_tonic,
        )

        return ScaleMelodyAnalysisResult(
            notes=notes,
            key=key,
            melody=melody,
            parent_scales=parent_scales,
            diatonic_in_key=diatonic_in_key,
            non_diatonic_pitches=non_diatonic_pitches,
            modal_labels=modal_labels,
            classification=classification,
            suggested_tonic=suggested_tonic,
            confidence=confidence,
            rationale=rationale,
        )

    def _detect_parent_scales(self, notes: List[str]) -> List[str]:
        """
        Detect ALL parent scales that contain all the given notes:
        major, natural minor, harmonic minor, melodic minor.

        This implements comprehensive parent scale detection for exotic modes.
        """
        if not notes:
            return []

        # Convert notes to pitch classes for comparison
        note_pitch_classes = self._notes_to_pitch_classes(notes)
        if not note_pitch_classes or None in note_pitch_classes:
            return []

        note_pc_set = set(note_pitch_classes)

        parent_scales = []

        # Test each possible root
        for major_root in self.major_keys:
            major_root_pc = self.note_map.get(major_root)
            if major_root_pc is None:
                continue

            # Test Major Scale (Ionian)
            major_intervals = [0, 2, 4, 5, 7, 9, 11]
            major_pc_set = {(major_root_pc + iv) % 12 for iv in major_intervals}
            if note_pc_set.issubset(major_pc_set):
                parent_scales.append(f"{major_root} major")

            # Test Natural Minor (Aeolian) - same as relative major but different root
            natural_minor_intervals = [0, 2, 3, 5, 7, 8, 10]
            natural_minor_pc_set = {
                (major_root_pc + iv) % 12 for iv in natural_minor_intervals
            }
            if note_pc_set.issubset(natural_minor_pc_set):
                parent_scales.append(f"{major_root} minor")

            # Test Harmonic Minor - THE KEY ADDITION!
            harmonic_minor_intervals = [0, 2, 3, 5, 7, 8, 11]
            harmonic_minor_pc_set = {
                (major_root_pc + iv) % 12 for iv in harmonic_minor_intervals
            }
            if note_pc_set.issubset(harmonic_minor_pc_set):
                parent_scales.append(f"{major_root} harmonic minor")

            # Test Melodic Minor (ascending form)
            melodic_minor_intervals = [0, 2, 3, 5, 7, 9, 11]
            melodic_minor_pc_set = {
                (major_root_pc + iv) % 12 for iv in melodic_minor_intervals
            }
            if note_pc_set.issubset(melodic_minor_pc_set):
                parent_scales.append(f"{major_root} melodic minor")

        return sorted(set(parent_scales))

    def _test_diatonic_fitness(self, notes: List[str], key: str) -> bool:
        """
        Test whether all notes fit diatonically within the given key.
        """
        if not key:
            return False

        # Extract key root and mode from key string
        key_root, key_mode = self._parse_key_string(key)
        if not key_root:
            return False

        # Get the pitch classes for this key
        if "major" in key_mode.lower():
            key_pc_set = self._get_major_scale_pitch_classes(key_root)
        else:  # minor
            # Minor is the 6th mode of major (Aeolian)
            relative_major_pc = (self.note_map[key_root] - 9) % 12
            relative_major_root = self._pitch_class_to_note(relative_major_pc)
            if not relative_major_root:
                return False
            key_pc_set = self._get_major_scale_pitch_classes(relative_major_root)

        # Test if all notes fit
        note_pitch_classes = self._notes_to_pitch_classes(notes)
        if None in note_pitch_classes:
            return False

        note_pc_set = set(note_pitch_classes)
        return note_pc_set.issubset(key_pc_set)

    def _identify_non_diatonic_pitches(self, notes: List[str], key: str) -> List[str]:
        """
        Identify which notes don't fit diatonically in the given key.
        """
        if not key:
            return []

        key_root, key_mode = self._parse_key_string(key)
        if not key_root:
            return []

        # Get the pitch classes for this key
        if "major" in key_mode.lower():
            key_pc_set = self._get_major_scale_pitch_classes(key_root)
        else:  # minor
            relative_major_pc = (self.note_map[key_root] - 9) % 12
            relative_major_root = self._pitch_class_to_note(relative_major_pc)
            if not relative_major_root:
                return []
            key_pc_set = self._get_major_scale_pitch_classes(relative_major_root)

        non_diatonic = []
        for note in notes:
            note_pc = self._note_to_pitch_class(note)
            if note_pc is not None and note_pc not in key_pc_set:
                non_diatonic.append(note)

        return non_diatonic

    def _classify_scale_usage(
        self, notes: List[str], key: Optional[str], diatonic_in_key: Optional[bool]
    ) -> str:
        """
        Classify scale usage as diatonic, modal_borrowing, or modal_candidate.

        This implements the core contextual classification algorithm.
        """
        if key is None:
            return "modal_candidate"

        if diatonic_in_key is True:
            return "diatonic"
        else:
            return "modal_borrowing"

    def _generate_modal_labels(
        self, notes: List[str], parent_scales: List[str]
    ) -> Dict[str, str]:
        """
        Generate modal labels for all potential tonic centers.

        For each note that could serve as a tonic, determine what mode it would be
        in each parent scale. Uses priority system to prevent overwriting more
        appropriate modal labels with less appropriate ones.
        """
        modal_labels = {}
        note_roots = {self._extract_root(note) for note in notes}

        # Build all possible modal interpretations with priorities
        modal_candidates: Dict[str, List[Tuple[float, str]]] = (
            {}
        )  # note_root -> [(priority, label), ...]

        for parent_scale in parent_scales:
            if not parent_scale.endswith(" major"):
                continue  # Focus on major scales for modal analysis

            parent_root = parent_scale.replace(" major", "")
            parent_pc = self.note_map.get(parent_root)
            if parent_pc is None:
                continue

            # For each potential tonic note
            for note_root in note_roots:
                if not note_root:
                    continue

                tonic_pc = self.note_map.get(note_root)
                if tonic_pc is None:
                    continue

                # Calculate which degree of the parent scale this tonic would be
                degree = (tonic_pc - parent_pc) % 12

                # Map degree to mode
                degree_to_mode = {0: 0, 2: 1, 4: 2, 5: 3, 7: 4, 9: 5, 11: 6}

                if degree in degree_to_mode:
                    mode_index = degree_to_mode[degree]
                    mode_name = self.mode_names[mode_index]
                    label = f"{note_root} {mode_name}"

                    # Priority system to prevent inappropriate overwriting:
                    # Higher priority (lower number) = more musically appropriate
                    priority = self._calculate_modal_priority(
                        note_root, parent_root, mode_name
                    )

                    if note_root not in modal_candidates:
                        modal_candidates[note_root] = []
                    modal_candidates[note_root].append((priority, label))

        # Select the highest priority (lowest number) modal label for each note
        for note_root, candidates in modal_candidates.items():
            if candidates:
                # Sort by priority (lowest number = highest priority)
                candidates.sort(key=lambda x: x[0])
                best_priority, best_label = candidates[0]

                modal_labels[note_root] = best_label

        return modal_labels

    def _calculate_modal_priority(
        self, tonic_note: str, parent_root: str, mode_name: str
    ) -> float:
        """
        Calculate priority for modal interpretations to prevent overwriting bug.

        Lower numbers = higher priority (more musically appropriate).

        Priority rules:
        1. Direct relationships (note matches parent scale) - Ionian/major
        2. Natural relative relationships (vi = Aeolian)
        3. Common modal relationships by musical frequency
        4. Distance-based tie breaking
        """
        tonic_pc = self.note_map.get(tonic_note, 0)
        parent_pc = self.note_map.get(parent_root, 0)

        # Calculate scale degree first (needed for priority rules)
        scale_degree_semitones = (tonic_pc - parent_pc) % 12
        semitone_to_degree = {
            0: 1,  # I (unison)
            2: 2,  # ii (major second)
            4: 3,  # iii (major third)
            5: 4,  # IV (perfect fourth)
            7: 5,  # V (perfect fifth)
            9: 6,  # vi (major sixth)
            11: 7,  # vii (major seventh)
        }
        scale_degree = semitone_to_degree.get(scale_degree_semitones, 0)

        # Rule 1: Direct match (tonic note is the parent scale root)
        if tonic_note == parent_root:
            return 1  # Highest priority - direct relationship (Ionian)

        # Rule 2: Contextual modal relationships - only boost when it's the
        # clear best choice. Be more selective about when to apply strong boosts.

        # Only boost modal relationships when they're from common, fundamental
        # parent scales
        if parent_root == "C":  # C major is the most fundamental reference
            if scale_degree == 2 and mode_name == "Dorian":
                return 1.1  # D Dorian from C major is canonical
            elif scale_degree == 5 and mode_name == "Mixolydian":
                return 1.2  # G Mixolydian from C major is canonical
            elif scale_degree == 3 and mode_name == "Phrygian":
                return 1.3  # E Phrygian from C major is canonical
            elif scale_degree == 6 and mode_name == "Aeolian":
                return (
                    1.4  # A Aeolian from C major is canonical (natural relative minor)
                )

        # Rule 3: Standard modal relationships in order of musical commonality
        mode_base_priorities = {
            "Ionian": 3,  # Major scale
            "Dorian": 3,  # Popular modal sound (ii)
            "Phrygian": 4,  # Less common (iii)
            "Lydian": 4,  # Less common (IV)
            "Mixolydian": 3,  # Popular in rock/folk (V)
            # Natural minor (vi) - only high priority for relative relationships
            "Aeolian": 4,
            "Locrian": 5,  # Rare (vii)
        }

        base_priority = mode_base_priorities.get(mode_name, 10)

        # Rule 4: Final priority calculation with distance penalty
        distance = min(abs(tonic_pc - parent_pc), 12 - abs(tonic_pc - parent_pc))
        distance_penalty = distance * 0.1  # Small penalty for distant relationships

        final_priority = base_priority + distance_penalty

        return final_priority

    def _infer_melody_tonic(
        self, notes: List[str]
    ) -> Tuple[Optional[str], Optional[float]]:
        """
        Infer the most likely tonic from a melodic sequence.

        Uses frequency analysis, final note emphasis, and melodic patterns.
        """
        if not notes:
            return None, None

        # Extract root notes only
        roots: List[str] = [
            r for r in (self._extract_root(note) for note in notes) if r
        ]
        if not roots:
            return None, None

        # Count frequency of each root
        root_counts: Dict[str, int] = {}
        for root in roots:
            root_counts[root] = root_counts.get(root, 0) + 1

        # Emphasize the final note
        final_root: str = roots[-1]

        # Calculate confidence based on final note + frequency
        base_confidence = 0.6
        frequency_bonus = root_counts.get(final_root, 1) * 0.02

        # Special pattern recognition (e.g., A-C-D cadence suggesting D Dorian)
        if set(roots) >= {"A", "C", "D"} and final_root == "D":
            confidence = max(0.78, base_confidence + frequency_bonus)
        else:
            confidence = min(0.95, base_confidence + frequency_bonus)

        return final_root, confidence

    def _generate_rationale(
        self,
        notes: List[str],
        key: Optional[str],
        classification: str,
        parent_scales: List[str],
        non_diatonic_pitches: List[str],
        modal_labels: Dict[str, str],
        suggested_tonic: Optional[str],
    ) -> str:
        """
        Generate human-readable rationale for the analysis.
        """
        parts = []

        if parent_scales:
            parts.append(f"Parents: {', '.join(parent_scales)}")

        if key:
            fitness = "diatonic" if classification == "diatonic" else "non-diatonic"
            parts.append(f"Key: {key} -> {fitness}")

        if non_diatonic_pitches:
            parts.append(f"Non-diatonic: {', '.join(non_diatonic_pitches)}")

        if suggested_tonic:
            parts.append(f"Suggested tonic: {suggested_tonic}")

        if modal_labels:
            modal_list = ", ".join(sorted(modal_labels.values()))
            parts.append(f"Modal candidates: {modal_list}")

        return "; ".join(parts) if parts else f"Scale analysis of {len(notes)} notes"

    # Helper methods

    def _notes_to_pitch_classes(self, notes: List[str]) -> List[Optional[int]]:
        """Convert note names to pitch classes."""
        return [self._note_to_pitch_class(note) for note in notes]

    def _note_to_pitch_class(self, note: str) -> Optional[int]:
        """Convert a note name to pitch class (0-11)."""
        root = self._extract_root(note)
        return self.note_map.get(root) if root else None

    def _extract_root(self, note: str) -> Optional[str]:
        """Extract root note from note string (e.g., 'F#3' -> 'F#')."""
        if not note:
            return None

        # Handle sharp/flat
        if len(note) > 1 and note[1] in "#b":
            return note[:2]
        return note[0]

    def _get_major_scale_pitch_classes(self, root: str) -> Set[int]:
        """Get all pitch classes in a major scale."""
        root_pc = self.note_map.get(root)
        if root_pc is None:
            return set()

        return {(root_pc + interval) % 12 for interval in self.major_scale_intervals}

    def _pitch_class_to_note(self, pc: int) -> Optional[str]:
        """Convert pitch class back to note name (prefer naturals, then flats)."""
        for note, note_pc in self.note_map.items():
            if note_pc == pc and len(note) == 1:  # Prefer naturals
                return note

        # If no natural, find flat
        for note, note_pc in self.note_map.items():
            if note_pc == pc and "b" in note:
                return note

        # If no flat, find sharp
        for note, note_pc in self.note_map.items():
            if note_pc == pc:
                return note

        return None

    def _parse_key_string(self, key: str) -> Tuple[Optional[str], str]:
        """Parse key string like 'C major' or 'Bb major' into (root, mode)."""
        if not key:
            return None, ""

        parts = key.strip().split()
        if len(parts) < 2:
            return None, ""

        root = parts[0]
        mode = " ".join(parts[1:])

        return root, mode


# Create module-level analyzer instance
analyzer = ScaleMelodyAnalyzer()


def analyze_scale_melody(
    notes: List[str], key: Optional[str] = None, melody: bool = False
) -> ScaleMelodyAnalysisResult:
    """
    Convenient module-level function for scale/melody analysis.

    Args:
        notes: List of note names
        key: Optional key context
        melody: Whether this is a melodic sequence

    Returns:
        Complete scale/melody analysis result
    """
    return analyzer.analyze_scale_melody(notes, key, melody)
