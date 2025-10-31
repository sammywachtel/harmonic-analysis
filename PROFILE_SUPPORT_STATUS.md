# Profile Support Status & Implementation

## Current Status: ⚠️ Profiles Not Connected

The `profile` parameter is being passed through the API but **is not currently being used** by the unified pattern engine.

## What Profiles Should Do

Profiles affect **chord substitution** during pattern matching, allowing different harmonic styles to recognize equivalent progressions:

### **Classical Profile** (Conservative)
- `IV` ↔ `ii6` (Predominant equivalence)
- `vi` ↔ `I6` (Relative minor/major tonic)

### **Jazz Profile** (Extensive)
- `V` ↔ `♭II7` (Tritone substitution - jazz hallmark)
- `V7` ↔ `♭II7`, `V9`, `V13`, `V7alt` (Extended dominants)
- `ii7` ↔ `ii`, `iiø7`, `ii9` (ii-V flexibility)
- Additional: I↔Imaj7, vi↔vi7, IV↔IVmaj7

### **Pop Profile** (Flexible Predominant)
- `IV` ↔ `ii`, `ii6`, `IV6` (Very flexible predominant)
- `vi` ↔ `vi7`, `I6` (Common pop variations)
- `I` ↔ `Iadd9`, `Isus2`

## Example: Jazz vs Classical

**Progression**: `Dm7` → `D♭7` → `Cmaj7`

**Classical Profile**:
- Might NOT recognize this as ii-V-I
- `D♭7` (♭II7) is not in classical substitutions

**Jazz Profile**:
- ✅ Recognizes as ii-V-I
- `D♭7` substitutes for `G7` (tritone sub)
- Common jazz cadence pattern detected

## Current Implementation Status

### ✅ What's Working:
1. **Frontend → Backend**: Profile parameter passed correctly from Tab1 → API
2. **API Routes**: Profile received at `/api/analyze` endpoint
3. **Service Layer**: Profile accepted by `PatternAnalysisService`
4. **Profile Classes**: `ClassicalProfile`, `JazzProfile`, `PopProfile` implemented in `matcher.py`

### ❌ What's Broken:
1. **UnifiedPatternService**: Line 170 says `profile: Analysis profile (currently ignored)`
2. **Pattern Engine**: Doesn't receive profile parameter
3. **Matcher**: Never has `set_profile()` called with user's selection

## Required Fix

The `UnifiedPatternService.analyze_with_patterns_async` method needs to pass the profile to the pattern engine. Here's what needs to happen:

### Current Flow (Broken):
```
User selects "jazz" → API → Service → Engine.analyze(context)
                                         ❌ Profile not passed
```

### Required Flow (Fixed):
```
User selects "jazz" → API → Service → Engine.analyze(context, profile="jazz")
                                         ✅ Profile used for substitutions
```

## Files to Modify

### 1. `src/harmonic_analysis/core/pattern_engine/pattern_engine.py`

**Add profile parameter to analyze method:**

```python
def analyze(self, context: AnalysisContext, profile: str = "classical") -> AnalysisEnvelope:
    """
    Analyze musical content using pattern matching.

    Args:
        context: Normalized analysis context
        profile: Analysis profile for chord substitutions
                ("classical", "jazz", "pop", "modal")
    """
    # ... existing code ...
```

**Pass profile to matcher if available:**

The pattern engine would need to configure any matchers it uses with the profile.

### 2. `src/harmonic_analysis/services/unified_pattern_service.py`

**Update analyze_with_patterns_async:**

```python
async def analyze_with_patterns_async(
    self,
    chords: Optional[List[str]] = None,
    key_hint: Optional[str] = None,
    profile: str = "classical",  # Remove "(currently ignored)" from docstring
    # ... other params ...
) -> AnalysisEnvelope:
    # ... existing code ...

    # Pass profile to engine
    envelope = self.engine.analyze(analysis_context, profile=profile)
```

## Expected Behavior After Fix

### Test Case: `Dm7` → `D♭7` → `Cmaj7`

**With Classical Profile:**
```
No ii-V-I pattern detected
D♭7 not recognized as dominant substitute
```

**With Jazz Profile:**
```
✅ ii-V-I pattern detected (score: 0.85+)
D♭7 recognized as tritone substitute for G7
Reasoning: "Jazz cadence with tritone substitution"
```

### Test Case: `C` → `Am` → `F` → `G`

**With Classical Profile:**
```
✅ I-vi-IV-V detected (exact match)
```

**With Jazz Profile:**
```
✅ I-vi-IV-V detected (same pattern)
Additional: Might recognize Fmaj7 variant
```

## Priority

**Medium-High**: This is user-visible functionality that's advertised in the UI but doesn't work.

## Workaround

Currently, all analyses use the "classical" profile regardless of user selection.

## Additional Considerations

- **Modal Profile**: A fourth profile could be added for modal harmony (different rules)
- **Custom Profiles**: Users might want to define custom substitution rules
- **Pattern Weights**: Different profiles might weight patterns differently (not just substitutions)

---

**Status**: Documented but not yet implemented
**Related Files**:
- `demo/frontend/src/tabs/Tab1.tsx` (UI)
- `demo/backend/rest_api/routes.py` (API)
- `src/harmonic_analysis/services/unified_pattern_service.py` (Service)
- `src/harmonic_analysis/core/pattern_engine/pattern_engine.py` (Engine)
- `src/harmonic_analysis/core/pattern_engine/matcher.py` (Profiles)
