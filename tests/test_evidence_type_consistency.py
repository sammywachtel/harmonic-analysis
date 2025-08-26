"""
Test evidence type consistency bug.

This test validates that evidence.type matches the actual type of evidence
being described, particularly for modal analysis evidence.
"""

import pytest

from harmonic_analysis import analyze_chord_progression
from harmonic_analysis.services.multiple_interpretation_service import EvidenceType


class TestEvidenceTypeConsistency:
    """Test that evidence types are consistent with their descriptions."""

    @pytest.mark.asyncio
    async def test_modal_evidence_type_consistency(self):
        """Test that modal evidence types match their descriptions."""
        # This progression triggers modal analysis that exhibits the bug
        progression = ["C", "Am", "F", "G", "A"]
        result = await analyze_chord_progression(progression)

        print(f"\nAnalyzing: {' - '.join(progression)}")
        print(f"Primary analysis: {result.primary_analysis.analysis}")
        print(f"Analysis type: {result.primary_analysis.type}")

        evidence_list = result.primary_analysis.evidence
        print(f"\nFound {len(evidence_list)} pieces of evidence:")

        inconsistencies = []

        for i, evidence in enumerate(evidence_list, 1):
            print(f"\nEvidence #{i}:")
            print(f"  Type: {evidence.type} ({evidence.type.value})")
            print(f"  Strength: {evidence.strength:.2f}")
            print(f"  Description: {evidence.description}")
            print(f"  Musical basis: {evidence.musical_basis}")

            # Check for the bug: stringified ModalEvidence in descriptions
            if "ModalEvidence(type=<EvidenceType." in evidence.description:
                # Extract the embedded type from the stringified ModalEvidence
                desc = evidence.description
                if "EvidenceType.CADENTIAL" in desc:
                    embedded_type = EvidenceType.CADENTIAL
                elif "EvidenceType.INTERVALLIC" in desc:
                    embedded_type = EvidenceType.INTERVALLIC
                elif "EvidenceType.HARMONIC" in desc:
                    embedded_type = EvidenceType.HARMONIC
                elif "EvidenceType.STRUCTURAL" in desc:
                    embedded_type = EvidenceType.STRUCTURAL
                elif "EvidenceType.CONTEXTUAL" in desc:
                    embedded_type = EvidenceType.CONTEXTUAL
                else:
                    embedded_type = None

                if embedded_type and embedded_type != evidence.type:
                    inconsistency = {
                        "evidence_num": i,
                        "outer_type": evidence.type,
                        "embedded_type": embedded_type,
                        "description": desc,
                        "should_be_type": embedded_type,
                    }
                    inconsistencies.append(inconsistency)
                    print(
                        f"  ❌ TYPE MISMATCH: Outer={evidence.type.value}, Embedded={embedded_type.value}"
                    )
                else:
                    print("  ✅ Types match")
            else:
                print("  ✅ No embedded evidence detected")

        # Report all inconsistencies
        if inconsistencies:
            print(
                f"\n🐛 BUG DETECTED: {len(inconsistencies)} evidence type inconsistencies found:"
            )
            for inc in inconsistencies:
                print(
                    f"  Evidence #{inc['evidence_num']}: "
                    f"outer={inc['outer_type'].value} but contains {inc['embedded_type'].value} content"
                )

            # This assertion will fail, exposing the bug
            assert (
                False
            ), f"Evidence type inconsistencies detected: {len(inconsistencies)} mismatches found"
        else:
            print("\n✅ All evidence types are consistent!")

    @pytest.mark.asyncio
    async def test_specific_modal_progression_evidence_types(self):
        """Test specific progressions known to trigger modal analysis."""
        test_cases = [
            (["G", "F", "C", "G"], "G Mixolydian with bVII"),
            (["Dm", "G", "Dm", "C"], "D Dorian progression"),
            (["C", "Am", "F", "G", "A"], "Mixed functional/modal with A extension"),
        ]

        for progression, description in test_cases:
            print(f"\n--- Testing: {description} ---")
            result = await analyze_chord_progression(progression)

            # Look specifically for evidence type mismatches
            for evidence in result.primary_analysis.evidence:
                # Check if description contains stringified evidence types
                desc = evidence.description.lower()

                # These patterns indicate the bug
                bug_patterns = [
                    "modalevidence(type=<evidencetype.",
                    "cadentialevidence(type=<evidencetype.",
                    "intervallicevidence(type=<evidencetype.",
                ]

                has_bug = any(pattern in desc for pattern in bug_patterns)

                if has_bug:
                    print(f"  🐛 BUG in evidence: {evidence.type.value}")
                    print(
                        f"     Description contains stringified evidence: {evidence.description[:100]}..."
                    )

                    # Fail the test to expose the bug
                    assert (
                        False
                    ), f"Evidence contains stringified objects: {evidence.description[:200]}"

    @pytest.mark.asyncio
    async def test_evidence_descriptions_are_clean_strings(self):
        """Test that evidence descriptions are clean, human-readable strings."""
        progression = ["C", "Am", "F", "G", "A"]
        result = await analyze_chord_progression(progression)

        for i, evidence in enumerate(result.primary_analysis.evidence, 1):
            desc = evidence.description

            # Evidence descriptions should NOT contain these technical artifacts
            forbidden_patterns = [
                "ModalEvidence(",
                "EvidenceType.",
                "<harmonic_analysis.",
                "strength=0.",
                "type=<",
                ")>",
            ]

            violations = [pattern for pattern in forbidden_patterns if pattern in desc]

            if violations:
                print(f"\nEvidence #{i} has technical artifacts in description:")
                print(f"  Type: {evidence.type.value}")
                print(f"  Description: {desc}")
                print(f"  Violations: {violations}")

                assert (
                    False
                ), f"Evidence #{i} description contains technical artifacts: {violations}"
