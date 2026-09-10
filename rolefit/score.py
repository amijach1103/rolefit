"""
The judgment layer.

The gates in gates.py answer questions that have a right answer in the text.
This module asks the one question that does not: does the work this posting
actually describes match the work this profile has actually done?

That is a judgment, so a model makes it — and because a model makes it, it is
graded. evals.py runs this against labelled fixtures and fails the build when
agreement drops. A scorer nobody grades is a scorer nobody should trust.
"""
from dataclasses import dataclass
from typing import Optional, Callable
import json, re

VERDICTS = ("strong", "partial", "weak")

PROMPT = """You are grading how well a candidate profile matches a job posting.

Judge SUBSTRATE, not vocabulary. A posting and a profile can share every keyword
and describe different work; they can share no keywords and describe the same work.

Answer only about the work itself. Ignore:
- seniority words in the title
- how many years are stated (a separate gate handles floors)
- whether the candidate has held the exact job title before

PROFILE
{profile}

POSTING TITLE
{title}

POSTING BODY
{body}

Return JSON only:
{{"verdict": "strong" | "partial" | "weak",
  "reason": "<one sentence naming the specific work that does or does not match>"}}
"""


@dataclass
class Score:
    verdict: str
    reason: str

    @property
    def rank(self) -> int:
        return {"strong": 2, "partial": 1, "weak": 0}[self.verdict]


def build_prompt(profile: dict, title: str, body: str, max_body: int = 6000) -> str:
    return PROMPT.format(
        profile=json.dumps(profile, indent=2),
        title=title,
        body=(body or "")[:max_body],
    )


def parse(raw: str) -> Score:
    """Parse a model response. Strict about the verdict, forgiving about wrapping.

    Models wrap JSON in prose and in code fences. Neither is an error worth
    failing a run over; an unrecognised verdict is.
    """
    m = re.search(r'\{.*\}', raw or '', re.S)
    if not m:
        raise ValueError(f"no JSON object in model response: {raw[:120]!r}")
    obj = json.loads(m.group())
    verdict = str(obj.get("verdict", "")).strip().lower()
    if verdict not in VERDICTS:
        raise ValueError(f"verdict {verdict!r} not one of {VERDICTS}")
    return Score(verdict=verdict, reason=str(obj.get("reason", "")).strip())


def score(profile: dict, title: str, body: str, complete: Callable[[str], str]) -> Score:
    """Score one posting.

    `complete` is any callable taking a prompt and returning text, so the caller
    supplies the provider. This module has no vendor dependency and no API key,
    which is also why the whole gate layer runs offline.
    """
    return parse(complete(build_prompt(profile, title, body)))
