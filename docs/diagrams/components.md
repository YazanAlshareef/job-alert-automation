# Components

Modules of the Python version and the outside systems they call.

```mermaid
flowchart LR
    GH["GitHub Actions<br>daily.yml"] -->|"python main.py --send"| MAIN["main.py<br>run()"]
    MAIN --> SRC["sources.py<br>fetch_all, dedupe"]
    MAIN --> SC["scorer.py<br>prefilter, score"]
    MAIN --> DG["digest.py<br>top, render, send"]
    SC --> LLM["llm.py<br>generate_json"]
    MAIN <--> FILES[("profile.json<br>state/seen.json<br>fixtures/")]
    SRC --> REM["Remotive API"]
    SRC --> ARB["Arbeitnow API"]
    SRC --> RSS["RSS feed<br>We Work Remotely"]
    LLM --> GEM["Gemini API"]
    DG --> TG["Telegram"]
    DG --> SMTP["SMTP email"]
```

Sources: [main.py](../../main.py), [sources.py](../../sources.py), [scorer.py](../../scorer.py), [llm.py](../../llm.py), [digest.py](../../digest.py), [daily.yml](../../.github/workflows/daily.yml)
