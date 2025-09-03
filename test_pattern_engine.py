#!/usr/bin/env python3
"""
Test script for Pattern Engine Phase 2A validation.

This script tests the pattern engine integration against core harmonic patterns.
"""

import sys
import os

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService


def main():
    print("🎵 Pattern Engine Phase 2A Validation")
    print("=" * 50)

    # Initialize pattern analysis service
    try:
        service = PatternAnalysisService()
        print("✅ Pattern Analysis Service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize service: {e}")
        return 1

    # Test basic pattern analysis
    print("\n📊 Testing Pattern Analysis:")
    test_progression = ["Am", "F", "C", "G"]

    try:
        result = service.analyze_with_patterns(test_progression)
        print(f"✅ Pattern analysis completed for {test_progression}")
        print(f"   Analysis time: {result.get('analysis_time_ms', 0)}ms")
        print(f"   Patterns found: {len(result.get('pattern_matches', []))}")

        for match in result.get('pattern_matches', []):
            print(f"   - {match.get('name', 'Unknown')}: {match.get('score', 0):.2f}")

    except Exception as e:
        print(f"❌ Pattern analysis failed: {e}")
        return 1

    # Test A/B comparison
    print("\n🔄 Testing A/B Analysis:")

    try:
        comparison = service.a_b_test_analysis(test_progression)
        print(f"✅ A/B testing completed")
        print(f"   Current approach time: {comparison['current_approach']['analysis_time_ms']}ms")
        print(f"   Pattern engine time: {comparison['pattern_engine']['analysis_time_ms']}ms")
        print(f"   Performance ratio: {comparison.get('performance_ratio', 0):.2f}x")

        comp_details = comparison.get('comparison', {})
        print(f"   Key agreement: {comp_details.get('key_agreement', False)}")
        print(f"   Current key: {comp_details.get('current_key', 'unknown')}")
        print(f"   Pattern key: {comp_details.get('pattern_key', 'unknown')}")

    except Exception as e:
        print(f"❌ A/B testing failed: {e}")
        return 1

    # Validate core patterns
    print("\n🎯 Validating Core Patterns:")

    try:
        validation = service.validate_core_patterns()
        print(f"✅ Core pattern validation completed")
        print(f"   Total tests: {validation['total_tests']}")
        print(f"   Passed: {validation['passed']}")
        print(f"   Failed: {validation['failed']}")
        print(f"   Success rate: {validation['success_rate']:.1%}")

        # Show failed tests
        for test in validation['test_results']:
            if not test.get('passed', False):
                print(f"   ❌ {test['name']}: {test.get('error', 'Pattern not found')}")
            else:
                print(f"   ✅ {test['name']}: {test.get('found_patterns', [])}")

    except Exception as e:
        print(f"❌ Core pattern validation failed: {e}")
        return 1

    print(f"\n🎉 Phase 2A validation completed!")

    # Summary
    pattern_success = len(result.get('pattern_matches', [])) > 0
    ab_success = comparison.get('performance_ratio', 0) > 0
    validation_success = validation.get('success_rate', 0) > 0.5

    if pattern_success and ab_success and validation_success:
        print("✅ Pattern engine integration successful - ready for Phase 2B!")
        return 0
    else:
        print("⚠️  Pattern engine integration needs refinement")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
