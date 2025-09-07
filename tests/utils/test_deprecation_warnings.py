#!/usr/bin/env python3
"""
Test deprecation warnings for legacy chord progression analysis functions.

This verifies that users get appropriate warnings when using deprecated functions.
"""

import asyncio
import sys
import warnings

# Add src to Python path
sys.path.insert(0, "src")


async def test_deprecation_warnings():
    """Test that deprecated functions emit appropriate warnings."""
    print("🧪 Testing Deprecation Warnings for Legacy Functions")
    print("=" * 60)

    # Capture warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")  # Ensure all warnings are triggered

        # Test deprecated analyze_chord_progression
        print("\n1. Testing analyze_chord_progression() deprecation...")
        try:
            from harmonic_analysis import analyze_chord_progression
            result = await analyze_chord_progression(['C', 'F', 'G', 'C'])

            # Check if deprecation warning was issued
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            if deprecation_warnings:
                print(f"✅ DeprecationWarning issued: {deprecation_warnings[0].message}")
            else:
                print("❌ No DeprecationWarning issued")

        except Exception as e:
            print(f"❌ Error testing analyze_chord_progression: {e}")

        # Test deprecated analyze_progression_multiple
        print("\n2. Testing analyze_progression_multiple() deprecation...")
        try:
            from harmonic_analysis import analyze_progression_multiple
            result = await analyze_progression_multiple(['C', 'F', 'G', 'C'])

            # Check if deprecation warning was issued (should be 2 warnings now)
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            if len(deprecation_warnings) >= 2:
                print(f"✅ DeprecationWarning issued: {deprecation_warnings[-1].message}")
            else:
                print("❌ No additional DeprecationWarning issued")

        except Exception as e:
            print(f"❌ Error testing analyze_progression_multiple: {e}")

    # Test new PatternAnalysisService is available
    print("\n3. Testing new PatternAnalysisService availability...")
    try:
        from harmonic_analysis import PatternAnalysisService
        service = PatternAnalysisService()
        print("✅ PatternAnalysisService imported successfully")
        print(f"   Service type: {type(service).__name__}")

        # Test that it has the expected method
        if hasattr(service, 'analyze_with_patterns'):
            print("✅ analyze_with_patterns method available")
        else:
            print("❌ analyze_with_patterns method not found")

    except Exception as e:
        print(f"❌ Error importing PatternAnalysisService: {e}")

    # Test module docstring mentions deprecation
    print("\n4. Testing module documentation...")
    try:
        import harmonic_analysis
        if "DEPRECATION NOTICE" in harmonic_analysis.__doc__:
            print("✅ Module docstring includes deprecation notice")
        else:
            print("❌ Module docstring missing deprecation notice")

        if "PatternAnalysisService" in harmonic_analysis.__doc__:
            print("✅ Module docstring mentions PatternAnalysisService")
        else:
            print("❌ Module docstring doesn't mention PatternAnalysisService")

    except Exception as e:
        print(f"❌ Error checking module documentation: {e}")

    print(f"\n📊 Summary:")
    print(f"Total warnings captured: {len(w)}")
    deprecation_count = len([warning for warning in w if issubclass(warning.category, DeprecationWarning)])
    print(f"Deprecation warnings: {deprecation_count}")

    if deprecation_count >= 2:
        print("🎉 All deprecation warnings working correctly!")
        return True
    else:
        print("⚠️  Some deprecation warnings may be missing.")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_deprecation_warnings())
    sys.exit(0 if success else 1)
