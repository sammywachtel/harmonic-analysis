#!/usr/bin/env python3
"""
Test script for Glossary Integration with Pattern Engine.

This script demonstrates how the glossary provides educational context
for pattern analysis results.
"""

import sys
import os
import json

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService


def print_educational_analysis(result):
    """Pretty print educational analysis results."""
    print(f"\n🎵 Analysis for: {result.get('chord_symbols', [])}")
    print(f"   Key detected: {result.get('functional_analysis', {}).get('key_center', 'unknown')}")
    print(f"   Analysis time: {result.get('analysis_time_ms', 0)}ms")

    # Show enhanced pattern matches with educational context
    enhanced_matches = result.get('enhanced_pattern_matches', [])
    print(f"\n📚 Enhanced Pattern Matches ({len(enhanced_matches)}):")

    for i, match in enumerate(enhanced_matches, 1):
        print(f"\n   {i}. {match['pattern_name']} (score: {match['score']:.2f})")
        print(f"      Family: {match['family']}")

        # Show educational context
        context = match.get('educational_context', {})

        # Cadence information
        if 'cadence_info' in context:
            cadence = context['cadence_info']
            print(f"      📖 Definition: {cadence.get('definition', 'N/A')}")
            print(f"      🎼 Example: {cadence.get('example_in_C_major', 'N/A')}")
            if 'soprano_context' in cadence:
                print(f"      🎶 Soprano: {cadence['soprano_context']}")

        # Chord function explanations
        if 'chord_functions' in context:
            print(f"      🔧 Chord Functions:")
            for func in context['chord_functions']:
                role_def = func.get('role_definition', 'N/A')
                print(f"         {func['roman']} ({func['role']}): {role_def}")

        # Pattern family explanation
        if 'pattern_family' in context:
            print(f"      🎯 Family Context: {context['pattern_family']}")

    # Show teaching points
    teaching_points = result.get('teaching_points', [])
    if teaching_points:
        print(f"\n🎓 Teaching Points:")
        for i, point in enumerate(teaching_points, 1):
            print(f"   {i}. {point}")

    # Show term definitions
    term_definitions = result.get('term_definitions', {})
    if term_definitions:
        print(f"\n📝 Key Terms:")
        for term, definition in term_definitions.items():
            print(f"   • {term.replace('_', ' ').title()}: {definition}")


def main():
    print("🎓 Glossary Integration Test - Educational Context for Pattern Analysis")
    print("=" * 80)

    # Initialize service
    try:
        service = PatternAnalysisService()
        print("✅ Pattern Analysis Service with Glossary initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return 1

    # Test cases with educational focus
    test_cases = [
        {
            "name": "Perfect Authentic Cadence Example",
            "chords": ["F", "G7", "C"],
            "description": "Classic PAC with strong resolution"
        },
        {
            "name": "Pop Progression with Multiple Patterns",
            "chords": ["Am", "F", "C", "G"],
            "description": "vi-IV-I-V containing multiple cadential patterns"
        },
        {
            "name": "Jazz ii-V-I Progression",
            "chords": ["Dm7", "G7", "Cmaj7"],
            "description": "Essential jazz progression with seventh chords"
        }
    ]

    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"📖 {test_case['name']}")
        print(f"   {test_case['description']}")
        print(f"{'='*60}")

        try:
            # Get educational analysis
            result = service.analyze_with_educational_context(test_case['chords'])
            print_educational_analysis(result)

        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()

    # Test standalone glossary features
    print(f"\n{'='*60}")
    print("🔍 Standalone Glossary Features Test")
    print(f"{'='*60}")

    try:
        # Test cadence explanations
        print("\n📚 Cadence Explanations:")
        cadence_types = ["PAC with soprano on 1", "Half Cadence", "Plagal Cadence"]
        for cadence in cadence_types:
            explanation = service.glossary_service.get_cadence_explanation(cadence)
            if explanation:
                print(f"\n   {cadence}:")
                print(f"   Definition: {explanation.get('definition', 'N/A')}")
                print(f"   Example: {explanation.get('example_in_C_major', 'N/A')}")

        # Test term definitions
        print("\n📖 Term Definitions:")
        terms = ["tonic", "dominant", "scale_degree", "soprano"]
        for term in terms:
            definition = service.glossary_service.get_term_definition(term)
            if definition:
                print(f"   • {term.title()}: {definition}")

        # Test scale degree information
        print("\n🎵 Scale Degree Information:")
        for degree in [1, 3, 5]:
            info = service.glossary_service.get_scale_degree_info(degree, "C major")
            if info:
                print(f"   • Degree {degree} ({info.get('name', 'Unknown')}): {info.get('description', 'N/A')}")

    except Exception as e:
        print(f"❌ Glossary features test failed: {e}")
        import traceback
        traceback.print_exc()

    print(f"\n🎉 Glossary integration test completed!")
    print("\n💡 The glossary enhances pattern analysis by providing:")
    print("   • Detailed explanations of musical terms and concepts")
    print("   • Educational context for pattern matches")
    print("   • Teaching points to help users understand harmonic function")
    print("   • Examples and definitions for complex music theory concepts")

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
