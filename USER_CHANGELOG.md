# What's New in Harmonic Analysis

The human-friendly companion to [CHANGELOG.md](CHANGELOG.md). Technical minutiae live there;
the good stuff — what you can actually *do* now — lives here.

---

## [0.3.0] - 2026-05-04

### ✨ New Things You Can Do

🎸 **See your progression through every stylistic lens at once.** The library now runs a full
multi-profile sweep (classical, jazz, pop, modal) in one call and ranks the results by confidence.
You can now call `analyze_with_patterns_async` without specifying a profile and get back a ranked
list of interpretations — finally an honest answer to "is this jazz or just accidentally cool?"

🧩 **Get a per-style breakdown from the demo API.** The `/analyze` endpoint now returns a
`style_analysis` map (one entry per style) and a `dominant_style` field. You can now build
integrations that show your users exactly which stylistic box their progression fits into, and
how confident the engine is about each one.

🎛️ **Skip the profile picker in the demo app.** The UI no longer holds analysis hostage behind a
profile selection. You can now hit "Analyze" without choosing a style — the app runs all profiles
and shows a collapsible Style Analysis section with confidence bars and a dominant-style badge.

### 🔄 Things That Work a Little Differently

**Profile is now optional everywhere.** If you were passing a profile to gate the analysis, you
can keep doing that — nothing broke. But omitting it now gets you *more*, not less.

**The pattern engine is style-aware.** Under the hood, every matched pattern now carries its
originating style profile. If you're consuming raw engine output, expect a new `profile` tag on
pattern match objects.

---

*For the full technical diff, see [CHANGELOG.md](CHANGELOG.md).*
