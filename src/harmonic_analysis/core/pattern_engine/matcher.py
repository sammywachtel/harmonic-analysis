
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json

@dataclass
class Token:
    roman: str
    role: str
    flags: List[str] = field(default_factory=list)
    mode: Optional[str] = None
    bass_motion_from_prev: Optional[int] = None
    soprano_degree: Optional[int] = None
    secondary_of: Optional[str] = None

    def roman_root(self) -> str:
        r = self.roman
        if r.endswith(("6","65","64","43","42")):
            return r
        return r.replace("7","")

@dataclass
class StepSpec:
    role: Optional[str] = None
    roman_root_any_of: Optional[List[str]] = None
    quality_any_of: Optional[List[str]] = None
    flags_any_of: Optional[List[str]] = None
    secondary_of: Optional[str] = None
    optional: bool = False
    descriptor: Optional[str] = None

@dataclass
class Pattern:
    id: str
    family: str
    name: str
    window: Dict[str,int]
    sequence: List[StepSpec]
    constraints: Dict[str,Any] = field(default_factory=dict)
    substitutions: Dict[str,List[str]] = field(default_factory=dict)
    score: Dict[str,Any] = field(default_factory=dict)

class PatternLibrary:
    def __init__(self, patterns: List[Dict[str,Any]]):
        self.patterns: List[Pattern] = []
        for p in patterns:
            steps = [StepSpec(**s) for s in p.get("sequence", [])]
            self.patterns.append(Pattern(
                id=p["id"],
                family=p.get("family","misc"),
                name=p.get("name", p["id"]),
                window=p.get("window", {"min":1,"max":8}),
                sequence=steps,
                constraints=p.get("constraints",{}),
                substitutions=p.get("substitutions",{}),
                score=p.get("score",{"base":1.0})
            ))

class Matcher:
    def __init__(self, lib: PatternLibrary, profile: str = "default"):
        self.lib = lib
        self.profile = profile
        self.profile_subs = {
            "default": {},
            "classical": {},
            "jazz": {"V": ["♭II7"]},
            "pop": {}
        }

    def match(self, tokens: List[Token], best_cover: bool = True) -> List[Dict[str,Any]]:
        raw_hits = []
        for pat in self.lib.patterns:
            minw, maxw = pat.window.get("min",1), pat.window.get("max",8)
            for start in range(len(tokens)):
                for end in range(start+minw, min(len(tokens), start+maxw)+1):
                    window_tokens = tokens[start:end]
                    m = self._match_pattern(pat, window_tokens)
                    if m:
                        m.update({"pattern_id": pat.id, "name": pat.name, "family": pat.family,
                                  "start": start, "end": end, "len": end-start})
                        raw_hits.append(m)
        if not best_cover:
            return raw_hits
        return self._best_non_overlapping_cover(raw_hits)

    def _best_non_overlapping_cover(self, hits: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
        hits = sorted(hits, key=lambda h: (h["end"], h["start"]))
        def p(idx):
            s = hits[idx]["start"]
            lo, hi, ans = 0, idx-1, -1
            while lo <= hi:
                mid = (lo+hi)//2
                if hits[mid]["end"] <= s:
                    ans = mid; lo = mid+1
                else:
                    hi = mid-1
            return ans
        n = len(hits)
        dp = [0.0]*(n+1)
        choose = [False]*n
        for i in range(1, n+1):
            incl = hits[i-1].get("score",1.0) + dp[p(i-1)+1]
            excl = dp[i-1]
            if incl >= excl:
                dp[i] = incl; choose[i-1] = True
            else:
                dp[i] = excl
        sol = []
        i = n
        while i > 0:
            if choose[i-1]:
                sol.append(hits[i-1]); i = p(i-1) + 1
            else:
                i -= 1
        sol.reverse()
        return sol

    def _match_pattern(self, pat: Pattern, toks: List[Token]) -> Optional[Dict[str,Any]]:
        if any(s.descriptor for s in pat.sequence):
            if self._descriptor_ok(pat.sequence[0].descriptor, toks):
                return {"score": pat.score.get("base", 1.0), "evidence": "descriptor"}
            return None
        i = j = 0
        evidence = []
        while j < len(pat.sequence) and i <= len(toks):
            if j >= len(pat.sequence): break
            step = pat.sequence[j]
            if i >= len(toks):
                if all(s.optional for s in pat.sequence[j:]):
                    break
                return None
            tok = toks[i]
            if self._step_ok(step, tok, pat):
                evidence.append((j, tok.roman, tok.role, tok.flags))
                i += 1; j += 1
            else:
                if step.optional: j += 1
                else: return None
        if not self._constraints_ok(pat.constraints, toks):
            return None
        return {"score": pat.score.get("base", 1.0), "evidence": evidence}

    def _step_ok(self, step: StepSpec, tok: Token, pat: Pattern) -> bool:
        if step.descriptor: return False
        if step.role and step.role != tok.role and not (step.role == "T_or_D" and tok.role in ("T","D")):
            return False
        if step.roman_root_any_of:
            root = tok.roman_root()
            allowed = set(step.roman_root_any_of)
            for a in list(allowed): allowed.update(pat.substitutions.get(a, []))
            for a in list(allowed): allowed.update(self.profile_subs.get(self.profile, {}).get(a, []))
            if root not in allowed: return False
        if step.flags_any_of and not any(f in tok.flags for f in step.flags_any_of):
            return False
        if step.secondary_of:
            if step.secondary_of != "*" and step.secondary_of != tok.secondary_of:
                return False
        return True

    def _constraints_ok(self, cons: Dict[str,Any], toks: List[Token]) -> bool:
        if not cons: return True
        if "mode" in cons and not any(t.mode == cons["mode"] for t in toks): return False
        if cons.get("requires_secondary") and not any(t.secondary_of is not None for t in toks): return False
        if "bass_motion_any_of" in cons:
            if not any(t.bass_motion_from_prev in cons["bass_motion_any_of"] for t in toks if t.bass_motion_from_prev is not None):
                return False
        if "soprano_any_of" in cons:
            if not any((t.soprano_degree in cons["soprano_any_of"]) for t in toks if t.soprano_degree is not None):
                return False
        return True

    def _descriptor_ok(self, descriptor: str, toks: List[Token]) -> bool:
        if descriptor == "root_motion_-5_chain_min3":
            return len(toks) >= 3
        if descriptor == "pachelbel_core":
            # TODO: implement explicit root template check
            return False
        if descriptor == "chromatic_mediant":
            return len(toks) >= 1
        return False

def load_library(json_path: str) -> PatternLibrary:
    with open(json_path, "r") as f:
        data = json.load(f)
    return PatternLibrary(data)

if __name__ == "__main__":
    lib = load_library("patterns.json")
    matcher = Matcher(lib, profile="classical")
    tokens = [
        Token(roman="ii6", role="PD"),
        Token(roman="V7", role="D", bass_motion_from_prev=-5),
        Token(roman="I", role="T", soprano_degree=1),
    ]
    for h in matcher.match(tokens):
        print(h)
