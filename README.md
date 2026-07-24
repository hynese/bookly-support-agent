# Keats — Bookly Support Agent — SE Take-Home Prototype

A minimal customer support agent for Bookly (fictional online bookstore),
named Keats, built to demonstrate agent orchestration, tool use, and
clarifying-question behavior rather than a polished product. The name is a
small, deliberate branding choice, not a feature — see the pitch deck's
title slide for the one-line reasoning.

> **Note on deliverables:** this repo is the code prototype. The pitch deck
> (thesis, architecture, key decisions) is submitted separately alongside
> this repo link, per the assignment's two-part deliverable structure — it
> isn't duplicated in here.

## The thesis

A good CX agent should never guess when it can verify, and never act when it
should ask first. See the pitch deck for the full argument; this repo is the
implementation of that idea.

## What's here

- `bookly_agent.py` — the agent. Claude (via tool-calling) decides when to
  look up order data, ask a clarifying question, or take an action (filing a
  return). All "backend" data is mocked in-memory — see `MOCK_ORDERS`.
- `agent_policies.md` — the plain-language rules the agent follows, loaded
  at runtime rather than hardcoded in Python. See "AOP-style configuration"
  below for why.
- `test_bookly_agent.py` — a small set of assert-based checks on the tool
  functions (not-found, identity mismatch, ineligible returns, multi-order
  lookup, policy loading, audit logging). No LLM calls, no extra
  dependencies — run with `python3 test_bookly_agent.py`.
- `requirements.txt` — one dependency: the `anthropic` SDK.
- `.gitignore` — excludes `audit_log.jsonl` and `__pycache__/`, since those
  are runtime artifacts, not source.

## AOP-style configuration

Decagon's real differentiator is Agent Operating Procedures: a CX ops
person edits plain-language rules directly, without touching code or filing
an engineering ticket. This prototype mirrors that pattern in miniature —
every behavior rule (identity check, when to ask a clarifying question,
what's out of scope) lives in `agent_policies.md`, and `bookly_agent.py`
loads it at runtime. Change a rule in that file and the agent's behavior
changes on the next run; the Python file doesn't need to change. It's a
deliberate structural choice, not just a docs file — see `load_policies()`
in `bookly_agent.py`.

## Cost awareness

Live mode tracks input/output token usage per conversation and prints an
estimated cost on exit, using Sonnet 4.5's published per-token pricing
(check anthropic.com/pricing for current rates — this is illustrative, not
a live price feed). The point: an enterprise buyer cares about
cost-per-resolution, not just resolution rate, and the repo should be able
to answer that question even roughly.

## Audit logging

Every tool call is appended to `audit_log.jsonl` (git-ignored) with a
timestamp and a hashed — never raw — customer email. This isn't a
production logging/SIEM pipeline; it's a minimal, honest answer to the
question an F500 buyer with 10,000+ employees will actually ask: how do you
handle auditability and PII?

## Identity verification

Every tool that reveals order details or takes an action
(`get_order_status`, `check_return_eligibility`, `initiate_return`) requires
the customer's email to match the order on file. A real order ID paired
with the wrong email produces the exact same response as a nonexistent
order — the agent never confirms an order ID is valid to someone who can't
prove it's theirs. This is a deliberate fix for a gap in the first version,
where any order ID would work regardless of who was asking. It's still a
mocked, email-only check, not real authentication — see "What I'd change"
below.

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
- Ask about `BK-2044` while claiming to be `jsmith@example.com` (that order
  is real but belongs to a different customer — the agent should say it
  can't find a match, not reveal that the order ID itself is valid)

## Running the tests

```bash
python3 test_bookly_agent.py
```

No API key or network access needed — this checks the mocked backend
functions directly (identity verification, return eligibility, multi-order
lookup) and prints pass/fail for each case.

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
- Identity verification is email-match only (see above) — not real
  authentication (no password, session, or verification code). Good enough
  to prove the design pattern; not good enough for production.
- Single-turn tool loop with no persistent memory across sessions (memory =
  the in-process message list only).
- Live mode has basic error handling around the API call (a network hiccup
  prints a friendly message instead of crashing the conversation) but no
  retry logic — a real deployment would want that.
- Chat only, not voice. The assignment allows either; chat is where Bookly's
  order/returns volume actually lives, and a 4-hour build isn't enough time
  to also validate a voice turn-taking and transcription pipeline. Voice
  would be the second channel added, not the first — see `agent_policies.md`.
- The test suite covers the deterministic tool functions, not the LLM's
  conversational behavior (e.g., whether it accepts "yeah go ahead" as
  confirmation as reliably as "yes"). That's a real and known gap — LLM
  behavior isn't unit-testable the same way rule-based code is — rather
  than an oversight.
- Explicitly out of scope (see `agent_policies.md` for the full list):
  exchanges, partial refunds, gift returns, damaged/defective item claims,
  and non-English support. The agent is instructed to say it can't help
  with these rather than improvise a workflow for them.

## What I'd change with more production time

See the last slide of the deck — short version: real order-management API
instead of the mock, real customer authentication (not just an email match)
before returning any account data, and a human-escalation path for anything
the agent isn't confident about.
