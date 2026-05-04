import json

import harmonic_analysis as ha


def progression():
    """Main function for the sam.py script."""
    s = ha.PatternAnalysisService()

    # test_prog = ['C', 'F', 'G', 'C']
    test_prog = ["Gm/Bb", "A7", "Dm"]

    a = s.analyze_with_patterns(test_prog, key_hint="D minor")

    pretty_a = json.dumps(a.to_dict(), indent=4)
    print(pretty_a)


def romans():
    """Main function for the sam.py script."""
    s = ha.PatternAnalysisService()

    test_prog = ["iv6", "V7", "i"]

    a = s.analyze_with_patterns(romans=test_prog, key_hint="D minor")

    pretty_a = json.dumps(a.to_dict(), indent=4)
    print(pretty_a)


def main():
    progression()
    # romans()


if __name__ == "__main__":
    main()
