"""Daily job alert. `python main.py --dry-run` prints a digest from cached fixtures, sends nothing."""
import argparse
import json
import sys
from pathlib import Path

import digest
import scorer
import sources

ROOT = Path(__file__).parent
SEEN = ROOT / "state" / "seen.json"
SEEN_MAX = 3000


def load(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def run(args):
    profile = load(args.profile, None)
    if profile is None:
        sys.exit(f"Missing {args.profile}")
    if not args.dry_run and str(profile.get("candidate", {}).get("summary", "")).startswith("EDIT ME"):
        sys.exit("profile.json still has the placeholder summary. Fill in candidate.summary before a live run.")
    if args.dry_run:
        jobs = load(ROOT / "fixtures" / "postings.json", [])
        scores = load(ROOT / "fixtures" / "scores.json", {})
        errors = []
    else:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env.local")
        seen = load(SEEN, [])
        jobs, errors = sources.fetch_all(profile["sources"])
        jobs = scorer.prefilter(sources.dedupe(jobs, set(seen)), profile)[: profile.get("max_to_score", 45)]
        scores = scorer.score(jobs, profile) if jobs else {}
    ranked = digest.top(jobs, scores, profile.get("top_n", 5), profile.get("min_score", 6))
    text = digest.render(ranked)
    print(text)
    for e in errors:
        print(f"warning: {e}", file=sys.stderr)
    if args.dry_run:
        return
    if args.send and not ranked:
        print("(nothing above min_score: no message sent)")
    elif args.send:
        print("sent via:", ", ".join(digest.send(text)))
    else:
        print("(not sent: add --send)")
    if args.send or args.save_seen:  # only mark seen once the digest really went out
        SEEN.parent.mkdir(exist_ok=True)
        SEEN.write_text(json.dumps((seen + [j["id"] for j in jobs])[-SEEN_MAX:]), encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="use cached fixtures, no network, no send")
    p.add_argument("--send", action="store_true", help="really send to the channels in .env.local")
    p.add_argument("--save-seen", action="store_true", help="record postings as seen without sending")
    p.add_argument("--profile", default=str(ROOT / "profile.json"))
    run(p.parse_args())
