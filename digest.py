"""Build and send the digest."""
import os
import smtplib
from datetime import date
from email.message import EmailMessage

import requests


def top(jobs, scores, n, min_score):
    ranked = [(scores[j["id"]], j) for j in jobs if j["id"] in scores and scores[j["id"]]["score"] >= min_score]
    ranked.sort(key=lambda x: -x[0]["score"])
    return ranked[:n]


def render(ranked, today=None):
    head = f"Job digest {today or date.today()} - {len(ranked)} match(es)"
    if not ranked:
        return head + "\n\nNothing new above your score threshold today."
    lines = [head, ""]
    for i, (s, j) in enumerate(ranked, 1):
        where = f" ({j['location']})" if j["location"] else ""
        lines += [f"{i}. [{s['score']}/10] {j['title']} - {j['company']}{where}", f"   {s['reason']}", f"   {j['url']} (via {j['source']})", ""]
    return "\n".join(lines).rstrip()


def send_telegram(text):
    token, chat = os.environ["TELEGRAM_BOT_TOKEN"], os.environ["TELEGRAM_CHAT_ID"]
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": text[:4000], "disable_web_page_preview": True}, timeout=20)
    if not r.ok:
        raise RuntimeError(f"Telegram HTTP {r.status_code}")  # never include r.url: it holds the token


def send_email(text):
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = text.splitlines()[0], os.environ["SMTP_USER"], os.environ["EMAIL_TO"]
    msg.set_content(text)
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", "587")), timeout=20) as s:
        s.starttls()
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
        s.send_message(msg)


def send(text):
    """Send to every channel that has env set. Returns the channels used."""
    used = []
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        send_telegram(text)
        used.append("telegram")
    if os.environ.get("SMTP_HOST") and os.environ.get("EMAIL_TO"):
        send_email(text)
        used.append("email")
    if not used:
        raise RuntimeError("No channel configured: set Telegram or SMTP vars in .env.local")
    return used
