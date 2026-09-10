"""
Grade the grader.

Runs score.py against fixtures/scoring.json and reports agreement. This exists
because a scoring prompt drifts silently: it keeps returning confident verdicts
long after it stopped returning correct ones, and nothing in the output says so.

    python3 -m rolefit.evals            # uses a stub, no API key, checks plumbing
    python3 -m rolefit.evals --live     # supply your own completion function

Exit code is non-zero below the threshold, so this can gate a release.
"""
import json, os, sys
from pathlib import Path
from rolefit.score import score, VERDICTS

THRESHOLD = 0.75
ROOT = Path(__file__).resolve().parent.parent


def load_fixtures():
    return json.loads((ROOT / "fixtures" / "scoring.json").read_text())


def stub(prompt: str) -> str:
    """A deliberately dumb completion so the harness is testable with no key.
    It is NOT a scorer. It proves the plumbing and nothing else."""
    return json.dumps({"verdict": "partial", "reason": "stub"})


def run(complete=stub, profile=None):
    profile = profile or {"summary": "example profile", "lanes": {}}
    rows, agree = [], 0
    for fx in load_fixtures():
        try:
            s = score(profile, fx["title"], fx["body"], complete)
            ok = s.verdict == fx["expect"]
        except Exception as e:
            s, ok = None, False
            print(f"  ERROR {fx['id']}: {type(e).__name__} {e}")
        agree += ok
        rows.append((fx["id"], fx["expect"], s.verdict if s else "—", ok, fx["why"]))

    print(f"\n{'fixture':<34} {'expect':<9} {'got':<9} ok")
    print("─" * 68)
    for fid, exp, got, ok, why in rows:
        print(f"{fid:<34} {exp:<9} {got:<9} {'✓' if ok else '✗'}")
        if not ok:
            print(f"    ↳ {why}")
    rate = agree / len(rows) if rows else 0
    print(f"\nagreement {agree}/{len(rows)} = {rate:.0%}   threshold {THRESHOLD:.0%}")
    return rate


if __name__ == "__main__":
    rate = run()
    if "--live" not in sys.argv:
        print("\n(stub scorer — this run checks plumbing, not judgment. Use --live "
              "with a real completion function to grade the prompt.)")
        sys.exit(0)
    sys.exit(0 if rate >= THRESHOLD else 1)
