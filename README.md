# Bookly Support Agent — SE Take-Home Prototype

A minimal customer support agent for Bookly (fictional online bookstore),
built to demonstrate agent orchestration, tool use, and clarifying-question
behavior rather than a polished product.

## The thesis

A good CX agent should never guess when it can verify, and never act when it
should ask first. See the pitch deck for the full argument; this repo is the
implementation of that idea.

## What's here

- `bookly_agent.py` — the agent. Claude (via tool-calling) decides when to
  look up order data, ask a clarifying question, or take an action (filing a
  return). All "backend" data is mocked in-memory — see `MOCK_ORDERS`.
- `requirements.txt` — one dependency: the `anthropic` SDK.

## Running it — no Cursor, no GitHub, just Terminal

You don't need Cursor or a GitHub account to run or submit this. Everything
happens in the Mac Terminal app, which is already on your computer, plus a
screen recording as your "demo" deliverable (the assignment explicitly
accepts a recording instead of a repo).

**Step 1 — Open Terminal.** Press Cmd+Space, type `Terminal`, hit Enter. A
plain window with text opens — that's it.

**Step 2 — Move into this folder.** Type `cd ` (with a trailing space), then
drag the `Decagon SE Take-Home` folder from Finder directly into the Terminal
window — it will paste the full path in for you. Press Enter.

**Step 3 — Check Python is installed.**

```bash
python3 --version
```

If you see a version number (e.g. `Python 3.11.5`), you're set. If you get
"command not found," install Python from python.org (the macOS installer,
just click through it), then reopen Terminal and try again.

**Step 4 — Install the one dependency this script needs.**

```bash
pip3 install anthropic
```

**Step 5 — Run the offline walkthrough first** (no API key, no cost — proves
everything works before you touch the live version):

```bash
python3 bookly_agent.py --demo
```

You should see a scripted conversation print out. If that works, you're
ready for Step 6.

**Step 6 — Run it live** (this is what you'd screen-record). You need an
Anthropic API key — sign up free at console.anthropic.com, click "Create
Key," and copy it. Then, still in Terminal:

```bash
export ANTHROPIC_API_KEY=paste_your_key_here
python3 bookly_agent.py
```

Type messages at the `You:` prompt and hit Enter. Type `quit` to exit.

**Step 7 — Record it.** Open QuickTime Player (already on your Mac) →
File → New Screen Recording → select just the Terminal window → click record
→ run through the example conversation below → stop → save the file. That
video is your "demo" deliverable — no repo needed.

---

**Live mode, condensed** (once you're comfortable with the steps above):

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
python bookly_agent.py
```

Try asking things like:
- "Where's my order?" (no order ID yet — agent should ask for one)
- Give the email `jsmith@example.com` (two orders match — agent should ask
  which one)
- "I want to return BK-1001" (agent checks eligibility, confirms with you,
  then files the return)
- Something with no order ID or email you make up (agent should say it can't
  find it rather than inventing a status)

**Offline walkthrough** (no API key needed — a scripted rehearsal/recording
safety net that exercises the same tool functions):

```bash
python bookly_agent.py --demo
```

Mock order IDs available: `BK-1001`, `BK-1002` (both under
`jsmith@example.com`), `BK-2044` (`afernandez@example.com`).

## Scope and assumptions

- Covers two use cases in depth (order status, returns) rather than a
  shallow pass across everything Bookly's support inbox sees.
- Data is entirely mocked and in-memory; "today" is pinned to 2026-07-23 so
  the return-window math is deterministic for the demo.
- No auth/identity verification layer — assumed out of scope for a 4-hour
  prototype, called out explicitly in the deck as the first thing to add for
  production.
- Single-turn tool loop with no persistent memory across sessions (memory =
  the in-process message list only).

## What I'd change with more production time

See the last slide of the deck — short version: real order-management API
instead of the mock, identity verification before returning any account
data, and a human-escalation path for anything the agent isn't confident
about.
