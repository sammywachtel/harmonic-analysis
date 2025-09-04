from harmonic_analysis.services.pattern_analysis_service import PatternAnalysisService
from harmonic_analysis.core.pattern_engine.matcher import Matcher, load_library, PatternLibrary, Token

def dump_tokens(ts):
    rows = []
    for i, t in enumerate(ts):
        rows.append({
            "i": i, "roman": t.roman, "role": t.role, "flags": list(getattr(t, "flags", []) or []),
            "mode": getattr(t, "mode", None),
            "sop": getattr(t, "soprano_degree", None),
            "bassΔ": getattr(t, "bass_motion_from_prev", None),
            "sec": getattr(t, "secondary_of", None),
        })
    return rows

def try_case(chords, profile, pattern_ids=None, key_hint=None, best_cover=False):
    svc = PatternAnalysisService()
    # ensure profile is actually passed through to the matcher used for pattern detection
    result = svc.analyze_with_patterns(
        chords, profile=profile, key_hint=key_hint, best_cover=best_cover
    )
    # Try to access matcher via public or private hooks
    try:
        matcher = svc.get_pattern_matcher()
    except AttributeError:
        matcher = getattr(svc, "_pattern_matcher", None)

    # This should never happen, but just in case...
    if matcher is None:
        throw = ValueError("Could not access matcher")
        print(f"[error] {throw}")
        raise throw

    lib: PatternLibrary | None = getattr(matcher, "library", None) if matcher else None
    print(f"\n=== Case {chords} | profile={profile} ===")
    if lib is not None:
        print("Loaded pattern IDs (last 20):", [p.id for p in lib.patterns[-10:]])
    else:
        print("[note] Matcher/library not exposed by service; skipping library dump.")
    # get the exact token stream the matcher used
    tokens = getattr(svc, "_last_tokens", None)
    if tokens is None and hasattr(svc, "get_last_tokens"):
        tokens = svc.get_last_tokens()
    if tokens is None:
        print("[note] Service did not expose tokens; to enable, store them in service._last_tokens or add get_last_tokens().")
    else:
        print("TOKENS:")
        for row in dump_tokens(tokens):
            print(row)
    print("Found patterns:", [m["name"] for m in result.get("pattern_matches", [])])

    # Focused traces for specific patterns, if provided
    if pattern_ids and matcher is not None and lib is not None and tokens is not None:
        for pid in pattern_ids:
            pat = lib.get_pattern_by_id(pid)
            if not pat:
                print(f"[warn] pattern {pid} not found in library")
                continue
            # brute-force windows like the matcher
            print(f"\n-- Trace {pid} --")
            min_len = pat.window.get("min", 1)
            max_len = pat.window.get("max", 8)
            any_success = False
            for start in range(len(tokens)):
                for end in range(start + min_len, min(len(tokens), start + max_len) + 1):
                    window_tokens = tokens[start:end]
                    mr = matcher._try_match_pattern(pat, window_tokens)  # uses strategies
                    if mr.success:
                        any_success = True
                        print(f"  ✓ match @ [{start},{end}): score={mr.score}, evidence={mr.evidence}")
                    else:
                        # show first failing window in detail
                        if start == 0:
                            print(f"  x [{start},{end}) failed: reason={mr.failure_reason}, info={mr.debug_info}")
            if not any_success:
                print("  (no matches)")
    elif pattern_ids:
        print("[note] Detailed trace skipped: matcher/tokens are not accessible via the service.")
    return result

if __name__ == "__main__":
    # 1) Pop loop
    try_case(["Am","F","C","G"], profile="pop",
             pattern_ids=["pop_vi_IV_I_V"])

    # 2) ii–V–I
    try_case(["Dm7","G7","Cmaj7"], profile="jazz",
             pattern_ids=["ii_V_I_root_macro"])

    # 3) Phrygian (A minor): expect iv6 → V inside
    try_case(["Am","Dm/F","E"], profile="classical",
             pattern_ids=["cadence_phrygian_relaxed"])

    # 4) Pachelbel in D
    try_case(["D","A","Bm","F#m","G","D","G","A"], profile="pop",
             pattern_ids=["pachelbel_canon_core_roots"])

    try_case(["Am", "G", "F", "E"], profile="classical",
             pattern_ids=["cadence_andalusian_minor"])

    try_case(
        ["Am", "G", "F", "E"],
        profile="classical",
        pattern_ids=["cadence_andalusian_relaxed"],
    )

    try_case(
        chords=["Fm7", "Bb7", "Cmaj7"],
        profile="jazz",
        pattern_ids=["cadence_backdoor"],
        key_hint="C major",
    )
