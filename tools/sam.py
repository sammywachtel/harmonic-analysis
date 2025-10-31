import json

import harmonic_analysis as ha


def main():
    """Main function for the sam.py script."""
    s = ha.PatternAnalysisService()

    # test_prog = ['C', 'F', 'G', 'C']
    test_prog = ["C", "Am", "Dm", "G"]

    a = s.analyze_with_patterns(test_prog, key_hint="C")

    pretty_a = json.dumps(a.to_dict(), indent=4)
    print(pretty_a)


if __name__ == "__main__":
    main()
