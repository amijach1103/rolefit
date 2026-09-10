"""
Deterministic gates. These run before any model sees a posting.

Each gate answers a question that has a right answer in the text, so a model
should never be asked it. Everything a model *is* asked lives in score.py.
"""
import re

# ── Gate 1 · residency ────────────────────────────────────────────────────────
# A posting can say "Remote - US" in its location field and exclude your metro
# in the fourth paragraph of the body. The location field is metadata; the
# exclusion is prose. Only one of them is enforced at offer time.

_EXCLUSION_CLAUSE = re.compile(
    r'(?i)[^.]{0,220}'
    r'(?:except|excluding|unable to hire|cannot hire|not hiring|ineligible|'
    r'not able to employ|open to candidates residing)'
    r'[^.]{0,300}\.'
)

def residency_excluded(body: str, metro_terms) -> bool:
    """True when the body carries an exclusion clause naming the candidate's metro.

    Matching is on the CLAUSE, not the whole document: a posting may mention a
    city in a dozen innocent ways ("our New York office"). Only a mention inside
    an exclusion sentence disqualifies.
    """
    if not body:
        return False
    pattern = re.compile('|'.join(re.escape(t) for t in metro_terms), re.I)
    for m in _EXCLUSION_CLAUSE.finditer(body):
        clause = m.group()
        if pattern.search(clause) and _is_negative(clause):
            return True
    return False

_POSITIVE_ONLY = re.compile(r'(?i)open to candidates residing in\s+(?!the US except)')

def _is_negative(clause: str) -> bool:
    """"Open to candidates residing in X" without an 'except' is an allowlist,
    which needs the opposite reading. Treat it as exclusion only if the metro
    appears AFTER an except/excluding token."""
    m = re.search(r'(?i)\b(except|excluding|unable to hire|cannot hire|'
                  r'not hiring|ineligible|not able to employ)\b', clause)
    return m is not None


# ── Gate 2 · the years floor, and the noun it qualifies ───────────────────────
# A stated floor is not a number. It is a number attached to a noun, and the
# noun is the test.
#
#   "5+ years doing UX research in industry"          -> lane: ux research
#   "5+ years in research, insights, or strategy"     -> lane: research OR insights OR strategy
#
# Same number. One is a wall for a candidate with eight years of research
# substance and no UX Research title; the other is not. Reading the digit and
# skipping the noun is the single most expensive mistake in screening yourself.

_FLOOR = re.compile(
    r'(?i)(\d{1,2})\s*\+?\s*(?:to|-|–)?\s*(\d{1,2})?\s*\+?\s*years?'
    r'(?:\s+of)?(?:\s+\w+){0,3}?\s+'
    r'(?:in|of|doing|with|as)\s+'
    r'(?P<noun>[^.;\n]{3,90})'
)

def stated_floors(body: str):
    """Return every stated years floor with the noun phrase it qualifies.

    Returns [{'min': int, 'max': int|None, 'qualifies': str, 'text': str}]
    """
    out = []
    for m in _FLOOR.finditer(body or ''):
        lo = int(m.group(1))
        hi = int(m.group(2)) if m.group(2) else None
        if lo > 30:                      # "30,000 transactions", not a floor
            continue
        out.append({
            'min': lo,
            'max': hi,
            'qualifies': m.group('noun').strip(),
            'text': re.sub(r'\s+', ' ', m.group()).strip(),
        })
    return out


# ── Gate 3 · posted compensation ──────────────────────────────────────────────
_MONEY = re.compile(r'\$\s?(\d{2,3}),(\d{3})(?![\d,])')

def posted_comp(*texts):
    """Highest plausible salary figure across the given texts, or None.

    Filters out figures outside a sane salary band so transaction counts,
    funding rounds and customer numbers do not read as pay.
    """
    vals = []
    for t in texts:
        if not t:
            continue
        vals += [int(a + b) for a, b in _MONEY.findall(t)]
    vals = [v for v in vals if 30_000 <= v <= 600_000]
    return max(vals) if vals else None
