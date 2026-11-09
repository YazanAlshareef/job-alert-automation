# Job Alert Automation

A daily job digest. It pulls postings from public sources, drops ones it has already shown, asks Gemini to score each against my profile (0-10 with a one-line reason), and sends the top few to Telegram or email.

There are two versions of the same flow:

- **n8n workflow** (`n8n/job-alert.workflow.json`): the visual one.
- **Python + GitHub Actions** (`main.py`): free fallback that runs on a cron with no server.

## How AI helped

Gemini does the scoring: it reads each posting and my `profile.json` and returns a score and a short reason. an AI coding assistant helped write the code and tests. I checked the sources' terms and the output myself.

## Run it (10 steps or fewer)

1. Install Python 3.12 and run `pip install -r requirements.txt`.
2. Try the demo: `python main.py --dry-run`. It uses saved sample postings and sample scores, needs no key, and sends nothing.
3. Edit `profile.json`: fill in `candidate.summary`, roles, skills, keywords.
4. Get a Gemini API key at https://aistudio.google.com/apikey.
5. Copy `.env.example` to `.env.local` and fill in `GEMINI_API_KEY` and `GEMINI_MODEL`.
6. Make a Telegram bot with @BotFather, message it once, and put the token and your chat id in `.env.local`. (Or fill the SMTP lines for email.)
7. Live run, nothing sent: `python main.py`. It fetches, scores, and prints the digest.
8. Send for real to the chat in `.env.local`: `python main.py --send`. For testing, point the chat id at a private test chat first.
9. Free daily schedule: push to GitHub, add secrets `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` and variable `GEMINI_MODEL` (Settings, Secrets and variables, Actions). `.github/workflows/daily.yml` then runs every day. Test it with the "Run workflow" button.
10. n8n instead: import `n8n/job-alert.workflow.json`, create credentials "Gemini API key" (Header Auth, name `x-goog-api-key`) and "Telegram bot", set your chat id in the last node, edit the profile in the "Normalize and dedupe" node, activate.

Run the tests with `python -m unittest discover -s tests`.

## Sources

- Remotive public API (https://remotive.com/api/remote-jobs). Their terms: link back to the posting, do not repost it elsewhere, and do not call it more than a few times a day. The digest links back to the original page and goes only to me.
- Arbeitnow public job board API (https://www.arbeitnow.com/api/job-board-api). Their robots.txt allows it.
- We Work Remotely public RSS feed (https://weworkremotely.com/remote-jobs.rss). Their robots.txt allows it. The n8n version does not include this feed.
- Not used: LinkedIn, anything that needs a login, anything that blocks bots.

Add a source by adding a fetcher to `sources.py` and an entry in `profile.json`. Check the site's robots.txt and terms first.

## What broke and how it was fixed

- Keyword filter matched "AI" inside "email" and passed almost everything. It now matches whole words only.
- The Windows console crashed on an en dash in a company name. `main.py` now forces UTF-8 output.
- The first We Work Remotely feed URL returned an empty body. I switched to their main feed.
- Docker was installed but its engine was not running on my machine, so I did not use it for n8n.

## Limits

- The dry-run scores in `fixtures/scores.json` are sample values I wrote by hand, not real Gemini output. The postings in `fixtures/postings.json` are real, saved from the live sources.
- A live Gemini call and a real Telegram or email send have not been tested yet, because the key and bot are not set up. See `WALKTHROUGH.md` for what is covered by tests.
- Scores are only as good as the profile text and the posting snippet (first 600 characters).
- n8n remembers seen postings only while the workflow is active. The Python version keeps them in `state/seen.json`, committed by the Action.
- Gemini model names change. If a call fails with 404, set `GEMINI_MODEL` to a current model.

## Licence

MIT
