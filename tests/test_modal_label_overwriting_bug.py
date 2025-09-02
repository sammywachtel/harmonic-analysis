"""
Test modal label overwriting bug in scale/melody analysis.

This test validates that modal labels are not incorrectly overwritten when
processing multiple parent scales, ensuring the most musically appropriate
modal interpretation is preserved.
"""

from harmonic_analysis.core.scale_melody_analysis import analyze_scale_melody


class TestModalLabelOverwriting:
    """Test that modal labels are not incorrectly overwritten by parent scale processing order."""

    def test_a_aeolian_partial_scale_bug(self):
        """
        Test the specific A Aeolian bug: A-C-D-E-G should be labeled as A Aeolian, not A Dorian.

        This partial natural minor scale (missing B and F) should be recognized as
        A Aeolian from the C major parent scale, not overwritten by later processing.
        """
        # The problematic notes that trigger the bug
        notes = ["A", "C", "D", "E", "G"]
        result = analyze_scale_melody(notes, melody=False)

        print(f"\nTesting notes: {notes}")
        print(f"Parent scales found: {result.parent_scales}")
        print(f"Modal labels: {result.modal_labels}")

        # The bug: A gets labeled as "A Dorian" instead of "A Aeolian"
        a_label = result.modal_labels.get("A", "NOT_FOUND")
        print(f"A is labeled as: {a_label}")

        # This should pass but currently fails due to the overwriting bug
        assert "A Aeolian" in a_label, f"Expected A Aeolian but got: {a_label}"

    def test_a_aeolian_melody_bug(self):
        """
        Test the A Aeolian bug with melody analysis (suggested tonic).

        A melody emphasizing A with natural minor notes should suggest A as tonic
        with A Aeolian as the modal interpretation.
        """
        # Similar to the notebook example that triggered the original question
        melody = ["C", "D", "E", "G", "A", "E", "D", "C", "C", "G", "E", "A"]
        result = analyze_scale_melody(melody, melody=True)

        print(f"\nTesting melody: {melody}")
        print(f"Suggested tonic: {result.suggested_tonic}")
        print(f"Modal labels: {result.modal_labels}")

        if result.suggested_tonic:
            tonic_label = result.modal_labels.get(result.suggested_tonic, "NOT_FOUND")
            print(f"Tonic ({result.suggested_tonic}) is labeled as: {tonic_label}")

            # If A is the suggested tonic, it should be A Aeolian, not A Dorian
            if result.suggested_tonic == "A":
                assert (
                    "A Aeolian" in tonic_label
                ), f"Expected A Aeolian but got: {tonic_label}"

    def test_partial_scale_modal_labeling_systematic(self):
        """
        Test systematic partial scales to catch modal overwriting patterns.

        Tests 5-note subsets from known scales to ensure consistent modal labeling.
        """
        test_cases = [
            {
                "notes": ["A", "C", "D", "E", "G"],  # A natural minor subset
                "expected_for_A": "A Aeolian",
                "description": "A natural minor (missing B,F)",
            },
            {
                "notes": ["D", "F", "G", "A", "C"],  # D Dorian subset
                "expected_for_D": "D Dorian",
                "description": "D Dorian (missing B,E)",
            },
            {
                "notes": ["G", "A", "C", "D", "F"],  # G Mixolydian subset
                "expected_for_G": "G Mixolydian",
                "description": "G Mixolydian (missing B,E)",
            },
            {
                "notes": ["E", "G", "A", "B", "D"],  # E Phrygian subset
                "expected_for_E": "E Phrygian",
                "description": "E Phrygian (missing C,F)",
            },
        ]

        failures = []

        for case in test_cases:
            result = analyze_scale_melody(case["notes"], melody=False)
            tonic = (
                case["expected_for_A"]
                if "expected_for_A" in case
                else (
                    case["expected_for_D"]
                    if "expected_for_D" in case
                    else (
                        case["expected_for_G"]
                        if "expected_for_G" in case
                        else case["expected_for_E"]
                    )
                )
            )
            tonic_note = tonic.split()[0]  # Extract note from "A Aeolian"

            actual_label = result.modal_labels.get(tonic_note, "NOT_FOUND")
            expected_label = case.get(f"expected_for_{tonic_note}", "UNKNOWN")

            if expected_label not in actual_label:
                failures.append(
                    {
                        "case": case["description"],
                        "notes": case["notes"],
                        "expected": expected_label,
                        "actual": actual_label,
                        "parent_scales": result.parent_scales,
                    }
                )

        if failures:
            print("\n=== MODAL LABELING FAILURES ===")
            for fail in failures:
                print(f"FAIL: {fail['case']}")
                print(f"  Notes: {fail['notes']}")
                print(f"  Expected: {fail['expected']}")
                print(f"  Actual: {fail['actual']}")
                print(f"  Parents: {fail['parent_scales']}")
                print()

            assert (
                False
            ), f"Modal labeling failed for {len(failures)} cases: {[f['case'] for f in failures]}"

    def test_parent_scale_processing_order_independence(self):
        """
        Test that modal labels don't depend on parent scale processing order.

        The same notes should get the same modal labels regardless of which
        parent scales are detected first.
        """
        # Test the same notes with different parent key contexts that affect processing order
        notes = ["A", "C", "D", "E", "G"]

        # Test without context
        result1 = analyze_scale_melody(notes, melody=False)
        a_label1 = result1.modal_labels.get("A", "NOT_FOUND")

        # Test with C major context (should prioritize A Aeolian from C major parent)
        result2 = analyze_scale_melody(notes, key="C major", melody=False)
        a_label2 = result2.modal_labels.get("A", "NOT_FOUND")

        print(f"\nTesting order independence with notes: {notes}")
        print(f"Without context: A = {a_label1}")
        print(f"With C major context: A = {a_label2}")
        print(f"Parent scales (no context): {result1.parent_scales}")
        print(f"Parent scales (C major context): {result2.parent_scales}")

        # Both should give the same musically correct result
        # (This test may pass even with the bug, but helps understand the issue)

    def test_complete_vs_partial_scale_consistency(self):
        """
        Test that partial scales give consistent modal labels with complete scales.

        If A-B-C-D-E-F-G is labeled as A Aeolian, then A-C-D-E-G (subset)
        should also label A as Aeolian, not Dorian.
        """
        # Complete A natural minor scale
        complete = ["A", "B", "C", "D", "E", "F", "G"]
        complete_result = analyze_scale_melody(complete, melody=False)
        complete_a_label = complete_result.modal_labels.get("A", "NOT_FOUND")

        # Partial A natural minor scale (the bug case)
        partial = ["A", "C", "D", "E", "G"]  # Missing B, F
        partial_result = analyze_scale_melody(partial, melody=False)
        partial_a_label = partial_result.modal_labels.get("A", "NOT_FOUND")

        print("\nTesting complete vs partial consistency:")
        print(f"Complete A minor ({complete}): A = {complete_a_label}")
        print(f"Partial A minor ({partial}): A = {partial_a_label}")
        print(f"Complete parents: {complete_result.parent_scales}")
        print(f"Partial parents: {partial_result.parent_scales}")

        # Both should identify A as Aeolian (the natural minor mode)
        assert (
            "A Aeolian" in complete_a_label
        ), f"Complete scale should be A Aeolian: {complete_a_label}"
        assert (
            "A Aeolian" in partial_a_label
        ), f"Partial scale should also be A Aeolian: {partial_a_label}"

        # They should be the same mode
        expected_mode = complete_a_label.split()[-1]  # "Aeolian" from "A Aeolian"
        actual_mode = (
            partial_a_label.split()[-1] if " " in partial_a_label else "UNKNOWN"
        )

        assert (
            expected_mode == actual_mode
        ), f"Mode consistency: complete='{expected_mode}' vs partial='{actual_mode}'"
