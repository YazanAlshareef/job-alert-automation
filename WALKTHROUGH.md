# Walkthrough

Each file in plain English, so I can explain it in an interview.

## The flow

Fetch postings, remove ones I have seen, keep ones that mention my keywords, ask Gemini to score them, keep the best few, send them to me.

## Files

- `main.py`: the entry point. Reads `profile.json`, runs the steps in order. `--dry-run` uses saved data and sends nothing. `--send` really sends. Without `--send` it only prints. It saves the seen list only after a real send, so a failed send does not lose postings.
- `sources.py`: one small function per source (Remotive, Arbeitnow, RSS). Each turns a posting into the same shape: id, title, company, url, location, description. `dedupe` drops postings I have seen or that repeat in the same batch. If one source is down, the others still run.
- `scorer.py`: `prefilter` keeps postings that mention my keywords. `prompt_for` builds the prompt. `parse` checks the model's reply and throws away rows that are broken, so bad output cannot crash the run. Postings go in batches of 15 to keep calls few.
- `llm.py`: the only file that talks to Gemini. The key and model name come from the environment. To use another model provider, change only this file. It retries on busy errors and never prints the key.
- `digest.py`: picks the top N above `min_score`, formats the text, and sends it by Telegram and/or email.
- `profile.json`: the file I edit. My profile for the model, keywords, how many results, minimum score, and the list of sources.
- `fixtures/`: saved real postings and sample scores for the dry run.
- `tools_make_fixtures.py`: the one-off script that saved the postings.
- `tests/test_all.py`: 12 tests with `unittest`. They cover dedupe, a source failing, the keyword filter, bad model output, the key never appearing in an error, the digest order, and the dry run end to end.
- `state/seen.json`: ids of postings already shown (created on the first send).
- `.github/workflows/daily.yml`: the free cron. Runs tests, runs `main.py --send`, commits the seen list back.
- `n8n/job-alert.workflow.json`: the same flow as an n8n workflow: schedule, two HTTP fetches, a code node to dedupe, a Gemini HTTP call, a code node to rank, a Telegram node.
- `.env.example`: the names of the settings. Real values go in `.env.local`, which git ignores.
- `requirements.txt`, `.gitignore`, `LICENSE` (MIT).

## Questions I should be able to answer

- **Why batch the model calls?** Fewer requests, lower cost, stays inside free limits.
- **Why validate the model's JSON?** Models sometimes return extra or wrong rows. Treat the output as untrusted input.
- **Why keyword prefilter first?** Cheap filter before the paid step.
- **Why two versions?** n8n is easy to see and change. The Action is free and needs no server.
- **How is dedupe done?** By a hash of the posting URL, plus company and title within one batch.
- **How are secrets handled?** Environment only: `.env.local` locally, GitHub secrets in the Action. Error messages never include the key or token.
- **What is not tested?** A real Gemini reply and a real Telegram or email send.
