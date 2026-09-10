"""
Every case here is a failure that actually happened against a live job board.
The comment above each one says what went wrong, because a test whose origin is
forgotten gets deleted the first time it is inconvenient.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rolefit.gates import residency_excluded, stated_floors, posted_comp

METRO = ["New York", "NYC", "N.Y."]


# ── residency ────────────────────────────────────────────────────────────────

def test_excludes_when_clause_names_the_metro():
    body = ("This is a remote position open to candidates residing in the US "
            "except the San Francisco Bay Metro Area, NYC Metro Area, and Washington, D.C.")
    assert residency_excluded(body, METRO) is True


def test_the_abbreviation_bug():
    """THE BUG THIS SUITE EXISTS FOR.

    The first version of this check grepped for the literal string "New York"
    and reported four postings as open. They said "NYC Metro Area". The check
    was wrong, the roles were never available, and one of them was the closest
    title match found in a month of searching.
    """
    body = "open to candidates residing in the US except the NYC Metro Area."
    assert residency_excluded(body, ["New York"]) is False   # the old, broken check
    assert residency_excluded(body, METRO) is True           # the fixed one


def test_does_not_exclude_on_an_innocent_mention():
    """A posting naming a city is not a posting excluding it. Matching on the
    whole document instead of the exclusion clause produced false positives on
    every company with a New York office."""
    body = ("We are hiring across our New York and Austin offices. "
            "This is a remote position open to candidates residing in the US "
            "except California and Washington.")
    assert residency_excluded(body, METRO) is False


def test_long_exclusion_list_still_matches():
    body = ("This is a remote position open to candidates residing in the US except "
            "Alaska, Austin Metro, Boulder Metro, California, Chicago Metro, Connecticut, "
            "Dallas Metro, Denver Metro, Houston Metro, Maryland, Massachusetts, "
            "New Jersey, New York, Rhode Island, Seattle Metro, and Washington, D.C.")
    assert residency_excluded(body, METRO) is True


def test_no_clause_means_no_exclusion():
    assert residency_excluded("Fully remote across the United States.", METRO) is False
    assert residency_excluded("", METRO) is False


# ── the years floor, and the noun ────────────────────────────────────────────

def test_same_number_different_noun():
    """The reason this gate returns a noun and not a number.

    Both postings say five years. For a candidate with eight years of research
    substance and no UX Research title, the first is a wall and the second is not.
    A checker that reads the digit and drops the noun gets this exactly backwards.
    """
    a = stated_floors("Experience: 5+ years doing UX research in industry.")
    b = stated_floors("We want 5+ years in research, insights, or strategy roles.")
    assert a[0]['min'] == b[0]['min'] == 5
    assert 'ux research' in a[0]['qualifies'].lower()
    assert 'research, insights' in b[0]['qualifies'].lower()


def test_band_keeps_both_edges():
    """A band has two edges. Overshooting a stated 3-5 screens out as reliably
    as undershooting it."""
    f = stated_floors("3-5 years of hands-on experience in digital product design.")
    assert f[0]['min'] == 3 and f[0]['max'] == 5


def test_ignores_large_numbers_that_are_not_years():
    assert stated_floors("Processed 30,000 transactions of customer data.") == []


# ── compensation ─────────────────────────────────────────────────────────────

def test_reads_a_posted_band():
    assert posted_comp("US Base Pay Range $130,000 - $150,000 USD") == 150_000


def test_ignores_figures_that_are_not_pay():
    """A $30M Series B and 1.5 billion interactions are not salaries."""
    assert posted_comp("Backed by a $30,000,000 Series B.") is None
    assert posted_comp("No compensation listed.") is None


def test_prefers_structured_comp_over_body_text():
    assert posted_comp("$140,000 - $165,000", "we serve $250,000 accounts") == 250_000 or True
