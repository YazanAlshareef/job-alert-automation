# Improvement log

## 2026-11-15, cycle 1

Baseline: 18 tests pass on main (0e2c005). Run them with `python -B -m unittest discover -s tests`. The tests make no network calls. No linter or type checker is configured.

### Done this cycle (branches awaiting review, not merged)

| Item | Branch | Commit | Result |
|---|---|---|---|
| The placeholder guard test ran against the real profile.json. It now uses its own temp profile (tests/test_all.py:133-138). Tests only, no behaviour change. | test/placeholder-guard-temp-profile | 95093c0 | 18 tests pass |
| Postings were marked seen even when they were never scored. Behaviour change: `seen.json` now records only scored postings. Prefiltered, over-limit and failed-batch postings are fetched again on the next run. | fix/mark-only-scored-seen | 69b2438 | 19 tests pass |
| A Telegram network error could carry the bot token in its message. Behaviour change: requests errors are re-raised as `RuntimeError` without the token, and the original traceback is dropped. | fix/redact-telegram-token | c8995f1 | 19 tests pass |

Each branch holds one commit on top of main. The test counts are per branch, not combined.

### Not verified

- Live Telegram and Gemini calls.
- A repo-wide scan for token leaks. Only the send path was changed.

### Backlog, top 5 not yet done

1. One failed model batch (network or HTTP error) aborts the whole run (scorer.py:48, llm.py:18, :19, :23). Effort S, risk medium. Needs the seen-marking branch to land first.
2. Partial send failure causes duplicates or a missed channel (digest.py:48-53, main.py:53 and :56-58). Effort S, risk low.
3. The n8n workflow marks postings seen before it scores or sends them (n8n/job-alert.workflow.json:64). Effort M, risk medium. Cannot be tested here.
4. One malformed item drops a whole source (sources.py:30-31, :37, :65-68; the RSS fetcher already skips bad items at :46-48). Effort S, risk low.
5. The keyword prefilter misses plurals and hyphenated forms (scorer.py:15, profile.json:9). Effort S, risk low to medium.

### Diagrams

Diagrams live on the `docs/diagrams` branch, in `docs/diagrams/` (bpmn.md, components.md, daily-alert.bpmn, sequence-daily-run.md, sequence-scoring.md). They are not on main.

### Lessons

- A test that depends on a committed file staying a placeholder breaks when the owner fills that file in. Give such a test its own temp file.
- Fixes that touch the same flow depend on order. The batch-failure item must wait for the seen-marking branch.

### Status

All branches are local. Nothing is pushed or merged. They await the owner's approval.
