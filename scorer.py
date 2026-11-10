"""Score postings against profile.json with the LLM; batch to keep calls few."""
import json
import re
import sys

import llm

BATCH = 15


def prefilter(jobs, profile):
    kws = profile.get("keywords", [])
    if not kws:
        return jobs
    pat = re.compile(r"\b(" + "|".join(re.escape(k) for k in kws) + r")\b", re.I)  # whole words: "AI" must not match "email"
    return [j for j in jobs if pat.search(j["title"] + " " + j["description"])]


def prompt_for(batch, profile):
    items = [{"id": j["id"], "title": j["title"], "company": j["company"], "location": j["location"],
              "description": j["description"][:600]} for j in batch]
    return ("You rate job postings for one candidate. Be strict and honest.\n"
            f"Candidate profile (JSON): {json.dumps(profile.get('candidate', {}))}\n"
            "For each posting give an integer fit score 0-10 and a reason of at most 15 words.\n"
            'Reply as a JSON array: [{"id": "...", "score": 7, "reason": "..."}]. Use the given ids.\n'
            f"Postings: {json.dumps(items)}")


def parse(result, batch):
    """Keep only valid rows for ids we asked about; clamp score to 0-10."""
    ids = {j["id"] for j in batch}
    out = {}
    for row in result if isinstance(result, list) else []:
        try:
            if row["id"] in ids:
                out[row["id"]] = {"score": max(0, min(10, int(row["score"]))), "reason": str(row.get("reason", ""))[:160]}
        except (KeyError, TypeError, ValueError):
            continue
    return out


def score(jobs, profile):
    scores = {}
    for i in range(0, len(jobs), BATCH):
        batch = jobs[i:i + BATCH]
        try:
            scores.update(parse(llm.generate_json(prompt_for(batch, profile)), batch))
        except (KeyError, IndexError, TypeError, ValueError) as e:  # blocked or empty reply, or not JSON
            print(f"warning: skipped a batch of {len(batch)}: bad model reply ({type(e).__name__})", file=sys.stderr)
    return scores
