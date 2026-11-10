import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import digest  # noqa: E402
import llm  # noqa: E402
import scorer  # noqa: E402
import sources  # noqa: E402


def job(url, title="Data Intern", company="Acme", desc="python"):
    return sources.make("t", title, company, url, "Remote", desc)


class TestSources(unittest.TestCase):
    def test_clean_strips_html(self):
        self.assertEqual(sources.clean("<p>Hi &amp; <b>bye</b></p>"), "Hi & bye")

    def test_dedupe_seen_and_repeats(self):
        a, b = job("http://a"), job("http://b", title="Other")
        dup_same_title = job("http://c")  # same company+title as a, different url
        out = sources.dedupe([a, b, dup_same_title, a], {b["id"]})
        self.assertEqual([j["url"] for j in out], ["http://a"])

    def test_one_source_failing_does_not_stop_others(self):
        with mock.patch.dict(sources.FETCHERS, {"remotive": mock.Mock(side_effect=OSError("down")),
                                               "arbeitnow": mock.Mock(return_value=[job("http://z")])}):
            jobs, errors = sources.fetch_all([{"type": "remotive"}, {"type": "arbeitnow"}])
        self.assertEqual(len(jobs), 1)
        self.assertIn("remotive", errors[0])


class TestScorer(unittest.TestCase):
    def test_prefilter_whole_words(self):
        profile = {"keywords": ["AI"]}
        keep, drop = job("http://k", desc="We use AI daily"), job("http://d", desc="send an email")
        self.assertEqual(scorer.prefilter([keep, drop], profile), [keep])

    def test_internship_passes_profile_keywords(self):
        profile = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
        j = job("http://i", title="Data Internship", desc="")
        self.assertEqual(scorer.prefilter([j], profile), [j])

    def test_bad_reply_skips_that_batch_only(self):
        a, b = job("http://a"), job("http://b")
        replies = [KeyError("candidates"), [{"id": b["id"], "score": 7, "reason": "ok"}]]

        def fake(prompt):
            r = replies.pop(0)
            if isinstance(r, Exception):
                raise r
            return r
        with mock.patch.object(scorer, "BATCH", 1), mock.patch.object(llm, "generate_json", fake):
            self.assertEqual(scorer.score([a, b], {}), {b["id"]: {"score": 7, "reason": "ok"}})

    def test_parse_clamps_and_ignores_bad_rows(self):
        a = job("http://a")
        result = [{"id": a["id"], "score": 14, "reason": "x"}, {"id": "unknown", "score": 5},
                  {"id": a["id"]}, "junk"]
        self.assertEqual(scorer.parse(result, [a]), {a["id"]: {"score": 10, "reason": "x"}})
        self.assertEqual(scorer.parse({"not": "a list"}, [a]), {})


class TestLLM(unittest.TestCase):
    def test_requires_env(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                llm.generate_json("hi")

    def test_error_message_never_contains_key(self):
        resp = mock.Mock(ok=False, status_code=400, text="bad request")
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "SECRETKEY", "GEMINI_MODEL": "m"}), \
                mock.patch("llm.requests.post", return_value=resp):
            with self.assertRaises(RuntimeError) as cm:
                llm.generate_json("hi")
        self.assertNotIn("SECRETKEY", str(cm.exception))

    def test_parses_json_reply_and_uses_header_key(self):
        resp = mock.Mock(ok=True, status_code=200)
        resp.json.return_value = {"candidates": [{"content": {"parts": [{"text": "[1, 2]"}]}}]}
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "k", "GEMINI_MODEL": "m"}), \
                mock.patch("llm.requests.post", return_value=resp) as post:
            self.assertEqual(llm.generate_json("hi"), [1, 2])
        self.assertEqual(post.call_args.kwargs["headers"], {"x-goog-api-key": "k"})
        self.assertNotIn("k", post.call_args.args[0].replace("generativelanguage", ""))


class TestDigest(unittest.TestCase):
    def test_top_orders_and_filters(self):
        jobs = [job("http://a", title="A"), job("http://b", title="B"), job("http://c", title="C")]
        scores = {jobs[0]["id"]: {"score": 7, "reason": ""}, jobs[1]["id"]: {"score": 9, "reason": ""},
                  jobs[2]["id"]: {"score": 3, "reason": ""}}
        ranked = digest.top(jobs, scores, n=5, min_score=6)
        self.assertEqual([j["title"] for _, j in ranked], ["B", "A"])

    def test_render_shows_source(self):
        j = sources.make("remotive", "T", "C", "http://x", "", "d")
        self.assertIn("(via remotive)", digest.render([({"score": 8, "reason": "r"}, j)], today="2026-01-01"))

    def test_render_empty(self):
        self.assertIn("Nothing new", digest.render([], today="2026-01-01"))

    def test_send_needs_a_channel(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                digest.send("x")


class TestProfileGuard(unittest.TestCase):
    def test_live_run_refuses_placeholder_summary(self):
        out = subprocess.run([sys.executable, str(ROOT / "main.py")], capture_output=True, text=True, encoding="utf-8",
                             env={**os.environ, "GEMINI_API_KEY": "", "GEMINI_MODEL": ""})
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("placeholder", out.stderr)


class TestDryRun(unittest.TestCase):
    def test_dry_run_prints_digest_without_keys_or_network(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("GEMINI", "TELEGRAM", "SMTP"))}
        out = subprocess.run([sys.executable, str(ROOT / "main.py"), "--dry-run"], capture_output=True,
                             text=True, env=env, encoding="utf-8", check=True).stdout
        self.assertIn("Job digest", out)
        self.assertIn("[8/10]", out)
        self.assertNotIn("Animator", out)  # score 2, below min_score


if __name__ == "__main__":
    unittest.main()
