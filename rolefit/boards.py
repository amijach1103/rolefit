"""
Job board readers.

Two public posting APIs, both returning the full description body. The body is
the point: everything this tool cares about — residency exclusions, stated
floors, the actual work — lives in prose the structured fields do not carry.
"""
import json, urllib.request, concurrent.futures as cf, re, html

GREENHOUSE = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
ASHBY = "https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"


def _get(url, timeout=30):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "rolefit/0.1"})
        return json.load(urllib.request.urlopen(req, timeout=timeout))
    except Exception:
        return None


def _text(markup):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(markup or "")))


def _greenhouse(slug):
    d = _get(GREENHOUSE.format(slug=slug)) or {}
    for j in d.get("jobs", []):
        yield {
            "board": slug, "ats": "greenhouse", "id": j.get("id"),
            "title": j.get("title") or "",
            "location": (j.get("location") or {}).get("name", ""),
            "body": _text(j.get("content")),
            "comp_field": "",
            "url": j.get("absolute_url", ""),
        }


def _ashby(slug):
    d = _get(ASHBY.format(slug=slug)) or {}
    for j in d.get("jobs", []):
        sec = [x.get("location", "") if isinstance(x, dict) else str(x)
               for x in (j.get("secondaryLocations") or [])]
        yield {
            "board": slug, "ats": "ashby", "id": j.get("id"),
            "title": j.get("title") or "",
            "location": " ".join([j.get("location") or ""] + sec).strip(),
            "body": _text(j.get("descriptionHtml")),
            "comp_field": (j.get("compensation") or {}).get("compensationTierSummary") or "",
            "url": j.get("jobUrl", ""),
        }


def fetch_board(slug):
    """All postings from one board. Never raises: one bad payload must not end a run.

    A whole sweep died on a single board returning dicts where strings were
    expected. Isolation is per board for that reason.
    """
    try:
        return list(_greenhouse(slug)) + list(_ashby(slug))
    except Exception as e:
        print(f"  ! {slug}: {type(e).__name__} {e}")
        return []


def fetch_all(slugs, workers=24):
    out = []
    with cf.ThreadPoolExecutor(workers) as pool:
        for rows in pool.map(fetch_board, slugs):
            out.extend(rows)
    return out
