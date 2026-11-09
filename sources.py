"""Fetch postings from public sources that allow it. No scraping, no logins."""
import hashlib
import html
import re
import xml.etree.ElementTree as ET

import requests

UA = "job-alert-automation/0.1 (personal job digest; github.com/YazanAlshareef/job-alert-automation)"
TIMEOUT = 20


def clean(text, limit=1200):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def make(source, title, company, url, location, description):
    pid = hashlib.sha1(url.encode()).hexdigest()[:12]
    return {"id": pid, "source": source, "title": clean(title, 200), "company": clean(company, 100),
            "url": url, "location": clean(location, 100), "description": clean(description)}


def remotive(cfg):
    # Remotive terms: link back to the job url, do not repost elsewhere, call it a few times a day at most.
    r = requests.get("https://remotive.com/api/remote-jobs",
                     params={"category": cfg.get("category", "data"), "limit": cfg.get("limit", 50)},
                     headers={"User-Agent": UA}, timeout=TIMEOUT)
    r.raise_for_status()
    return [make("remotive", j["title"], j["company_name"], j["url"],
                 j.get("candidate_required_location", ""), j["description"]) for j in r.json()["jobs"]]


def arbeitnow(cfg):
    r = requests.get("https://www.arbeitnow.com/api/job-board-api", headers={"User-Agent": UA}, timeout=TIMEOUT)
    r.raise_for_status()
    return [make("arbeitnow", j["title"], j["company_name"], j["url"], j.get("location", ""), j["description"])
            for j in r.json()["data"][: cfg.get("limit", 100)]]


def rss(cfg):
    r = requests.get(cfg["url"], headers={"User-Agent": UA}, timeout=TIMEOUT)
    r.raise_for_status()
    out = []
    for item in ET.fromstring(r.content).iter("item"):
        title = item.findtext("title") or ""
        company, sep, role = title.partition(": ")  # WWR titles look like "Company: Role"
        if not sep:
            company, role = "", title
        out.append(make(cfg.get("name", "rss"), role, company, item.findtext("link") or "",
                        item.findtext("region") or "", item.findtext("description") or ""))
    return out


FETCHERS = {"remotive": remotive, "arbeitnow": arbeitnow, "rss": rss}


def fetch_all(sources):
    """sources: list of {"type": ..., ...}. One failing source never kills the run."""
    jobs, errors = [], []
    for cfg in sources:
        try:
            jobs += FETCHERS[cfg["type"]](cfg)
        except Exception as e:  # noqa: BLE001 - report and continue
            errors.append(f"{cfg.get('type')}: {type(e).__name__}: {e}")
    return jobs, errors


def dedupe(jobs, seen):
    """Drop ids already in `seen` and repeats inside this batch (same url or same company+title)."""
    out, keys = [], set()
    for j in jobs:
        key = (j["company"].lower(), j["title"].lower())
        if j["id"] in seen or j["id"] in keys or key in keys:
            continue
        keys.update([j["id"], key])
        out.append(j)
    return out
