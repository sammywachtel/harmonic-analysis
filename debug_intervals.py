#!/usr/bin/env python3
"""
Debug interval calculations for roman numeral generation.
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from harmonic_analysis.utils.scales import NOTE_TO_PITCH_CLASS

def debug_intervals():
    print("🔍 Debug Interval Calculations")
    print("=" * 50)

    chord_symbols = ["Fm7", "Bb7", "Cmaj7"]
    key_center = "C major"

    # Extract key pitch
    key_tonic = key_center.split()[0]  # "C"
    key_pitch = NOTE_TO_PITCH_CLASS.get(key_tonic, 0)
    print(f"Key: {key_center}")
    print(f"Key tonic: {key_tonic}")
    print(f"Key pitch class: {key_pitch}")
    print()

    for chord_symbol in chord_symbols:
        # Extract chord root (simplified)
        root_name = chord_symbol[0]
        if len(chord_symbol) > 1 and chord_symbol[1] in ['#', 'b']:
            root_name = chord_symbol[:2]

        root_pitch = NOTE_TO_PITCH_CLASS.get(root_name, 0)
        interval = (root_pitch - key_pitch) % 12

        print(f"Chord: {chord_symbol}")
        print(f"  Root: {root_name}")
        print(f"  Root pitch: {root_pitch}")
        print(f"  Interval from key: {interval} semitones")

        # Expected scale degree
        scale_degrees = {0: "I", 2: "ii", 4: "iii", 5: "IV", 7: "V", 9: "vi", 10: "bVII", 11: "vii°"}
        expected = scale_degrees.get(interval, f"chromatic({interval})")
        print(f"  Expected roman: {expected}")
        print()

if __name__ == "__main__":
    debug_intervals()
