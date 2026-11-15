# Walkthrough

My notes on every file, so I can explain the project in an interview without guessing.

## The flow

Fetch postings, drop the ones I've already seen, keep the ones that mention my keywords, ask Gemini to score them, keep the best few, send them to me.

## Files

- `main.py` is the entry point. It reads `profile.json` and runs the steps in order. `--dry-run` uses saved data and sends nothing. Without `--send` it only prints. With `--send` it sends, and only then saves the seen list, so a failed send doesn't lose postings. A live run stops early if the profile summary is still the placeholder. If `state/seen.json` is corrupt it is ignored with a warning.
- `sources.py` has one small function per source (Remotive, Arbeitnow, RSS). Each returns postings in the same shape: id, source, title, company, url, location, description. RSS items with no link are skipped. `dedupe` drops postings I've seen and repeats within the same batch. If one source is down, the others still run.
- `scorer.py` holds `prefilter`, which keeps postings that mention my keywords as whole words. `prompt_for` builds the prompt. `parse` checks the model's reply and drops broken rows, so bad output can't crash the run. Postings go to the model 15 at a time. If a whole reply is blocked, empty or not JSON, that batch is skipped with a warning and the rest still count.
- `llm.py` is the only file that talks to Gemini. The key and model name come from the environment. To switch provider I'd change only this file. It retries on busy errors and never prints the key.
- `digest.py` picks the top N above `min_score`, formats the text (with the source name on each line) and sends it by Telegram or email.
- `profile.json` is the file I edit: my profile for the model, keywords, how many results, the minimum score, and the sources.
- `fixtures/` holds made-up postings and hand-written scores for the dry run.
- `tests/test_all.py` has 18 `unittest` tests. They cover dedupe, a failing source, the keyword filter, bad model output, the key never showing up in an error, digest order and source names, the placeholder guard, and the dry run end to end. None of them call Gemini or Telegram.
- `state/seen.json` lists the ids I've already been shown. It appears after the first send.
- `.github/workflows/daily.yml` is the free cron. It runs the tests, runs `main.py --send` and commits the seen list back.
- `.github/workflows/ci.yml` runs the tests on every push, with no secrets.
- `n8n/job-alert.workflow.json` is the same flow as n8n nodes: a schedule, two HTTP fetches, a code node that dedupes, a Gemini HTTP call, a code node that ranks, and a Telegram node. I confirmed it imports into n8n but did not run it there.
- `.env.example` lists the setting names. Real values go in `.env.local`, which git ignores.
- `requirements.txt`, `.gitignore` and `LICENSE` (MIT).

## Questions I should be able to answer

- **Why batch the model calls?** Fewer requests, and I stay inside the free limits.
- **Why validate the model's JSON?** Models sometimes return extra or wrong rows, so I treat the reply as untrusted input.
- **Why filter by keyword first?** It's a cheap step that cuts how much the model has to read.
- **Why two versions?** n8n is easy to see and change. The Action is free and needs no server.
- **How does dedupe work?** A hash of the posting URL, plus company and title within one batch.
- **How are secrets handled?** Only through the environment: `.env.local` on my machine and GitHub secrets in the Action. Error messages never include the key or token.
- **What isn't tested?** A real Gemini reply and a real Telegram or email send. Nothing has run against the live APIs with my key yet.
