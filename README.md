# rolefit

Reads job postings the way a careful reader would, instead of the way a search filter does.

Most job tooling matches on structured fields — location, title, salary. The
things that actually decide whether a role is available to you are written in
prose, in the middle of the description, where nobody reads them.

---

## Three things the structured fields get wrong

**1. "Remote — US" often isn't.**

Across 289 public job boards, 1,051 postings listed a remote US location. Sixty-two
of them excluded a specific metro area — and all sixty-two were one company, which
carried the same clause on every remote role it posted, from engineering to legal:

> "This is a remote position open to candidates residing in the US except the
> San Francisco Bay Metro Area, NYC Metro Area, and Washington, D.C."

The location field said `Remote - US`. The exclusion was in the fourth paragraph.
The best title match in the entire sweep was disqualified by one sentence.

**2. A stated years floor is not a number. It's a number attached to a noun.**

> "5+ years doing **UX research in industry**"
> "5+ years in **research, insights, or strategy roles**"

Same number. For someone with eight years of research inside other job titles and
no UX Research title, the first is a wall and the second isn't. A checker that
reads the digit and drops the noun gets this exactly backwards, which is why
`stated_floors()` returns the noun phrase and not just an integer.

**3. Keyword overlap and substrate match are different things.**

Two postings can share every word in your résumé and describe work you've never
done. One can share none of them and describe your last three years. Vocabulary
matching finds the first and misses the second.

---

## How it's built

Three layers, and the split is the design.

**Gates — `rolefit/gates.py`.** Questions with a right answer in the text. Does
an exclusion clause name your metro? What noun does the years floor qualify?
What's the posted band? No model is asked these, because a model would sometimes
get them wrong and there is no reason to accept that.

**Judgment — `rolefit/score.py`.** The one question with no right answer in the
text: does the work described match the work done? A model answers it. The module
takes any `complete(prompt) -> str` callable, so there's no vendor dependency and
no API key anywhere in the gate layer.

**Grading — `rolefit/evals.py`.** Because a model answers it, the answer is graded.
Labelled fixtures, an agreement threshold, and a non-zero exit below it, so a
drifting prompt fails a build instead of quietly returning confident nonsense.

```
python3 -m rolefit.evals      # runs against a stub scorer; checks the harness
python3 -m rolefit.evals --live   # grades a real scorer, exits non-zero under threshold
```

The stub always answers `partial` and scores 25% against four fixtures. That is
the point of running it: a harness that can't fail a bad scorer isn't a harness.

---

## What writing the tests found

Two defects in code that had already produced results:

- The residency check grepped for the literal string `New York`. Four postings
  said `NYC Metro Area` and were reported as open. They were never available.
- `$30,000,000 Series B` parsed as a `$30,000` salary, because the money pattern
  had no boundary after the match.

Both are now fixtures in `tests/test_gates.py` with the failure written above them,
because a test whose origin has been forgotten gets deleted the first time it's
inconvenient.

---

## Quickstart

```bash
cp profile.example.yaml profile.yaml     # gitignored
cp boards.example.txt boards.txt
python3 -m rolefit.evals                 # no API key needed
python3 run_tests.py                     # 11 gate tests, no dependencies
```

Everything about a candidate lives in `profile.yaml`. Nothing personal belongs in
source, and the repo ships a fictional profile.

## Design notes

- **No dependencies.** Standard library only. A tool that needs a virtualenv to
  read a job board is a tool nobody runs twice.
- **Per-board fault isolation.** A whole sweep once died on one board returning
  dicts where strings were expected.
- **Exclusion matching is per clause, not per document.** A posting naming a city
  is not a posting excluding it — matching the whole document flagged every
  company with an office there.

MIT.

---

The thinking behind this is at [aguedaschwartz.com/practice](https://aguedaschwartz.com/practice).
