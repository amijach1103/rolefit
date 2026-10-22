# rolefit

A side project from September 2026. It reads job postings the way a careful reader would, instead of the way a search filter does. Most job tools match on structured fields like location, title and salary. The things that actually decide whether a role is open to you are written in the middle of the description, where nobody reads them.

## Three things the structured fields get wrong

**1. "Remote, US" often isn't.** Across 289 public job boards, 1,051 postings listed a remote US location. Sixty-two of them excluded a specific metro area, and all sixty-two were one company, which carried the same clause on every remote role it posted, from engineering to legal:

> "This is a remote position open to candidates residing in the US except the San Francisco Bay Metro Area, NYC Metro Area, and Washington, D.C."

The location field said `Remote - US`. The exclusion was in the fourth paragraph.

**2. A years requirement is a number attached to a noun.**

> "5+ years doing **UX research in industry**"
> "5+ years in **research, insights, or strategy roles**"

Same number. For someone with years of research inside other job titles but no UX Research title, the first is a wall and the second isn't. A checker that reads the digit and drops the noun gets this backwards, so `stated_floors()` returns the noun phrase, not just the number.

**3. Sharing words isn't the same as matching the work.** Two postings can share every word in your resume and describe work you've never done. Another can share none of them and describe your last three years. Keyword matching finds the first and misses the second.

## How it's built

Three layers, and the split is the design.

**Fixed checks, `rolefit/gates.py`.** Questions with a right answer in the text: does an exclusion clause name your metro, what does the years requirement apply to, what's the posted pay band. No model answers these, because a model would sometimes get them wrong and there's no reason to accept that.

**Judgment, `rolefit/score.py`.** The one question with no right answer in the text: does the work described match the work you've done? A model answers it. The module takes any `complete(prompt) -> str` function, so it doesn't depend on one vendor and there's no API key in the checks.

**Grading, `rolefit/evals.py`.** Because a model answers it, the answer gets graded: labeled test cases, an agreement threshold, and a failing exit code below it, so a drifting prompt fails the eval instead of quietly returning confident nonsense.

```
python3 -m rolefit.evals      # runs against a stub scorer; checks the harness
python3 -m rolefit.evals --live mymodule:complete   # grades your complete(prompt) -> str, exits non-zero under threshold
```

The stub always answers `partial` and scores 25% on the four test cases. That's why you run it: a grader that can't fail a bad scorer isn't doing its job.

## The test cases, and what each one catches

| Test case | Expected | What it catches |
|---|---|---|
| `keyword-rich-substrate-poor` | weak | A posting that shares the profile's entire vocabulary and describes different work. A design-systems req full of "adoption", "accessibility programs" and "framework adoption" reads as a match to anything counting keywords. |
| `substrate-match-no-title-match` | strong | The opposite error. A posting describing work the profile has done, under a title it has never held. A title-matching scorer calls this weak. It is the strongest case in the set. |
| `adjacent-but-not-the-same` | partial | Revenue Operations: real overlap on research and measurement, real gap on the commercial half. A scorer that only answers strong or weak is wrong here by construction. |
| `credential-wall` | weak | A Registered Nurse licence. No wording fixes a licence, and a scorer reasoning about transferable skills will try. |

Two of the four are traps pointing in opposite directions, because a scorer that always over-matches and one that always under-matches both score 50% on a set that only tests one direction. The eleven check tests carry their history in their names, like `the_abbreviation_bug` and `same_number_different_noun`. Each was a real bug before it was a test.

## What writing the tests found

Two bugs in code that had already produced results:

- The residency check searched for the exact words `New York`. Four postings said `NYC Metro Area` and were reported as open. They never were.
- `$30,000,000 Series B` was read as a `$30,000` salary, because the money pattern had no boundary after the match.

Both are now tests in `tests/test_gates.py`, with the failure written above them, so nobody deletes them later without knowing why they exist.

## Quickstart

```bash
cp profile.example.yaml profile.yaml     # gitignored
cp boards.example.txt boards.txt
python3 -m rolefit.evals                 # no API key needed
python3 run_tests.py                     # 11 gate tests, no dependencies
```

Everything about a candidate lives in `profile.yaml`, which git ignores. The repo ships a fictional profile.

## Design notes

- **No dependencies.** Standard library only. A tool that needs a setup step to read a job board is a tool nobody runs twice.
- **One bad board doesn't stop the run.** A whole sweep once died on a single board that returned data in the wrong shape.
- **Exclusions are matched sentence by sentence.** A posting that names a city isn't a posting that excludes it, and matching the whole document flagged every company with an office there.

---

More of my work: [github.com/amijach1103](https://github.com/amijach1103) · MIT license
