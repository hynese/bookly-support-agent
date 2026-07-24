"""
Bookly Customer Support Agent — Decagon SE Take-Home Prototype
================================================================

THE THESIS (see pitch deck for full version):
A good CX agent should never guess when it can verify, and never take an
action when it should ask first. Concretely, that means:
  1. The model never invents order data — it must call a tool to get it.
  2. Before an irreversible action (a return), the agent confirms intent.
  3. When the request is ambiguous (no order ID, multiple matching orders),
     the agent asks a clarifying question instead of picking one.

ARCHITECTURE (matches the pitch deck's architecture slide):
  User message
      -> Claude (orchestrator), given a system prompt + tool definitions
      -> Claude decides: answer directly, ask a clarifying question,
         or call a tool
      -> If a tool call: our code runs it against MOCK_ORDERS (mocked
         "backend") and returns a real result
      -> Claude reads the tool result and responds to the user
      -> Loop continues (message history = the agent's "memory")

This is intentionally the simplest architecture that satisfies the three
minimum requirements:
  - multi-turn interaction   -> agent asks for an order ID / email before answering
  - tool use (mocked)        -> get_order_status / check_return_eligibility / etc.
  - clarifying question      -> ambiguous or missing info triggers a question,
                                 not a guess

IDENTITY VERIFICATION (added after initial review):
Every tool that reveals order details or takes an action requires the
customer's email to match the order on file. A mismatch is treated exactly
like "order not found" — the agent never confirms an order ID exists to
someone whose email doesn't match it. This closes the gap where the first
version would happily return status or file a return for any order ID
handed to it, regardless of who was asking.

SCOPE, COST, AND AUDIT AWARENESS (added after second review):
Three more things a Principal-level candidate should surface, not just a
prototype should have:
  1. AOP-style config: the rules the agent follows live in agent_policies.md,
     not hardcoded in this file. That mirrors Decagon's real differentiator —
     a CX ops person edits plain-language rules directly, without touching
     Python or filing an engineering ticket. Edit that file; this one doesn't
     need to change.
  2. Cost awareness: live mode tracks token usage per conversation and prints
     an estimated cost on exit. Enterprise buyers care about cost-per-resolution,
     not just resolution rate.
  3. Audit logging: every tool call is written to audit_log.jsonl with a
     hashed (not raw) email. F500 buyers with 10,000+ employees will ask about
     auditability and PII handling; this is a minimal, honest answer, not a
     production logging pipeline.

Run modes:
  python bookly_agent.py            -> live chat using the Claude API (needs
                                        ANTHROPIC_API_KEY set in your environment)
  python bookly_agent.py --demo     -> scripted walkthrough, no API key needed.
                                        Useful as a recording safety net; it
                                        exercises the same tool functions and
                                        prints the same three required cases.
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# AOP-STYLE POLICY LOADING: behavior rules live in agent_policies.md, a
# plain-language file a non-technical CX ops person could edit directly.
# This is the pattern Decagon's real Agent Operating Procedures follow —
# separating "what the agent should do" from "how the orchestration code
# works" so policy changes don't require an engineering ticket.
# ---------------------------------------------------------------------------

POLICIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_policies.md")


def load_policies() -> str:
    """Read the plain-language policy file the agent's instructions are
    built from. Raises a clear error if it's missing, rather than silently
    running with no rules."""
    with open(POLICIES_PATH, "r") as f:
        return f.read()


# ---------------------------------------------------------------------------
# COST AWARENESS: illustrative Sonnet 4.5 pricing (USD per million tokens),
# accurate as of mid-2026. Check anthropic.com/pricing before quoting this
# externally — the point is demonstrating cost-per-resolution awareness,
# not shipping a live price feed.
# ---------------------------------------------------------------------------

INPUT_COST_PER_MTOK = 3.00
OUTPUT_COST_PER_MTOK = 15.00

# ---------------------------------------------------------------------------
# AUDIT LOGGING: a minimal, honest answer to "how would you handle
# auditability and PII" — not a production logging/SIEM pipeline, but proof
# the pattern is understood. Emails are hashed, never written in the clear.
# ---------------------------------------------------------------------------

AUDIT_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit_log.jsonl")


def _hash_email(email: str) -> str:
    """Never write a raw customer email to a log file. A real deployment
    would follow Bookly's actual data retention policy; this is a stand-in
    that at least avoids storing PII in the clear."""
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()[:12]


def log_tool_call(tool_name: str, tool_input: dict, result: dict) -> None:
    """Append one line per tool call to a local audit log. Illustrative of
    the pattern an enterprise buyer would expect, not a production system."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "order_id": tool_input.get("order_id"),
        "email_hash": _hash_email(tool_input["email"]) if "email" in tool_input else None,
        "outcome": result.get("found", result.get("success")),
    }
    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

# ---------------------------------------------------------------------------
# MOCK BACKEND: a tiny fake "orders database" standing in for Bookly's real
# order management system. In production this block would be replaced by
# real API calls (see "What I'd do differently" in the deck).
# ---------------------------------------------------------------------------

MOCK_ORDERS = {
    "BK-1001": {
        "email": "jsmith@example.com",
        "item": "The Midnight Library",
        "status": "delivered",
        "delivered_on": "2026-07-18",
        "order_date": "2026-07-10",
        "return_window_days": 30,
    },
    "BK-1002": {
        "email": "jsmith@example.com",
        "item": "Atomic Habits",
        "status": "in_transit",
        "delivered_on": None,
        "order_date": "2026-07-20",
        "return_window_days": 30,
    },
    "BK-2044": {
        "email": "afernandez@example.com",
        "item": "Project Hail Mary",
        "status": "delivered",
        "delivered_on": "2026-06-01",
        "order_date": "2026-05-25",
        "return_window_days": 30,
    },
}


def _verified_order(order_id: str, email: str):
    """Shared identity check: an order is only returned if the email on file
    matches. A wrong email produces the exact same result as a nonexistent
    order — we never confirm an order ID is real to someone who can't prove
    it's theirs. Returns the order dict if verified, else None."""
    order = MOCK_ORDERS.get(order_id.upper())
    if not order or order["email"].lower() != email.lower():
        return None
    return order


def get_order_status(order_id: str, email: str) -> dict:
    """Tool: look up the shipping status of one order. Requires the email on
    the order to match — see _verified_order."""
    order = _verified_order(order_id, email)
    if not order:
        return {
            "found": False,
            "error": f"No order found matching ID {order_id} and that email.",
        }
    return {
        "found": True,
        "order_id": order_id.upper(),
        "item": order["item"],
        "status": order["status"],
        "delivered_on": order["delivered_on"],
    }


def check_return_eligibility(order_id: str, email: str) -> dict:
    """Tool: determine whether an order is still inside its return window.
    Requires the email on the order to match."""
    order = _verified_order(order_id, email)
    if not order:
        return {
            "found": False,
            "error": f"No order found matching ID {order_id} and that email.",
        }
    if order["status"] != "delivered":
        return {
            "found": True,
            "eligible": False,
            "reason": "Order has not been delivered yet, so it can't be returned.",
        }
    # Simple day-count check against the mocked delivery date.
    from datetime import date

    delivered = date.fromisoformat(order["delivered_on"])
    days_since = (date(2026, 7, 23) - delivered).days  # "today" pinned for the demo
    eligible = days_since <= order["return_window_days"]
    return {
        "found": True,
        "eligible": eligible,
        "days_since_delivery": days_since,
        "return_window_days": order["return_window_days"],
    }


def initiate_return(order_id: str, email: str, reason: str) -> dict:
    """Tool: file a return request. This is the 'action' the agent takes.
    Requires the email on the order to match — the agent should also have
    called check_return_eligibility first, but this function re-verifies
    identity independently rather than trusting the caller."""
    order = _verified_order(order_id, email)
    if not order:
        return {
            "success": False,
            "error": f"No order found matching ID {order_id} and that email.",
        }
    # Mocked side effect — in production this would call Bookly's returns API.
    return {
        "success": True,
        "order_id": order_id.upper(),
        "confirmation_number": f"RTN-{order_id.upper()[3:]}",
        "reason_logged": reason,
    }


def lookup_orders_by_email(email: str) -> dict:
    """Tool: find all orders for a customer who doesn't have their order ID handy."""
    matches = [
        {"order_id": oid, "item": o["item"], "status": o["status"]}
        for oid, o in MOCK_ORDERS.items()
        if o["email"].lower() == email.lower()
    ]
    return {"count": len(matches), "orders": matches}


TOOL_FUNCTIONS = {
    "get_order_status": get_order_status,
    "check_return_eligibility": check_return_eligibility,
    "initiate_return": initiate_return,
    "lookup_orders_by_email": lookup_orders_by_email,
}

# ---------------------------------------------------------------------------
# TOOL DEFINITIONS: this is the "phone book" Claude chooses from. The
# descriptions are doing real work here — they're how the model knows when
# to call what, so they're written the way you'd brief a new support rep.
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_order_status",
        "description": (
            "Look up the shipping status of a specific Bookly order. "
            "Requires the order ID AND the email on the order — this is an "
            "identity check, not just a lookup key. If the email doesn't match "
            "the order, this returns 'not found' rather than confirming the "
            "order exists. Use this whenever a customer asks 'where is my "
            "order' or similar, once you have both an order ID and their email."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "e.g. BK-1001"},
                "email": {"type": "string", "description": "The email the customer says the order was placed under"},
            },
            "required": ["order_id", "email"],
        },
    },
    {
        "name": "check_return_eligibility",
        "description": (
            "Check whether a delivered order is still within its return window. "
            "Requires the order ID and the email on the order (same identity "
            "check as get_order_status). Always call this before telling a "
            "customer they can or can't return an item — never assume."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "email": {"type": "string"},
            },
            "required": ["order_id", "email"],
        },
    },
    {
        "name": "initiate_return",
        "description": (
            "File a return for an order. Requires the order ID and the email on "
            "the order. Only call this after the customer has confirmed they "
            "want to proceed AND check_return_eligibility has returned "
            "eligible=true. Never call this speculatively."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "email": {"type": "string"},
                "reason": {"type": "string", "description": "Customer's stated reason for the return"},
            },
            "required": ["order_id", "email", "reason"],
        },
    },
    {
        "name": "lookup_orders_by_email",
        "description": (
            "Find all orders associated with a customer's email address. Use this "
            "when a customer doesn't know their order ID, or when there might be "
            "more than one order and you need to ask which one they mean."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
            },
            "required": ["email"],
        },
    },
]

SYSTEM_PROMPT = f"""You are Keats, Bookly's customer support agent. Bookly is an online bookstore.
Introduce yourself as Keats if a customer asks who they're talking to, but don't
lead with your name unprompted — you're a support agent, not a mascot.

{load_policies()}
"""


# ---------------------------------------------------------------------------
# LIVE MODE: real orchestration loop using Claude's tool-use API.
# ---------------------------------------------------------------------------

def run_live_chat():
    try:
        import anthropic
    except ImportError:
        sys.exit("Missing dependency. Run: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("Set ANTHROPIC_API_KEY in your environment before running live mode.")

    client = anthropic.Anthropic(api_key=api_key)
    messages = []
    total_input_tokens = 0
    total_output_tokens = 0

    print("Keats — Bookly Support (type 'quit' to exit)\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            if total_input_tokens or total_output_tokens:
                cost = (
                    total_input_tokens / 1_000_000 * INPUT_COST_PER_MTOK
                    + total_output_tokens / 1_000_000 * OUTPUT_COST_PER_MTOK
                )
                print(
                    f"\nSession usage: {total_input_tokens} input / "
                    f"{total_output_tokens} output tokens "
                    f"(~${cost:.4f} at Sonnet 4.5 list pricing). A real deployment "
                    f"would track this per resolution, not just per session."
                )
            break
        messages.append({"role": "user", "content": user_input})

        # Keep calling Claude until it stops requesting tools.
        while True:
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages,
                )
            except Exception as e:
                # A transient network/rate-limit error shouldn't crash a live
                # demo mid-conversation — surface it and let the customer retry.
                print(f"Keats: Sorry, I'm having trouble reaching the system right "
                      f"now ({e}). Could you try again in a moment?\n")
                messages.pop()  # drop the user turn we couldn't get a response to
                break

            messages.append({"role": "assistant", "content": response.content})
            total_input_tokens += response.usage.input_tokens
            total_output_tokens += response.usage.output_tokens

            # Print any text the model produced this turn.
            for block in response.content:
                if block.type == "text":
                    print(f"Keats: {block.text}\n")

            if response.stop_reason != "tool_use":
                break  # model is done, waiting on the next user message

            # Execute every requested tool call and feed results back.
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    fn = TOOL_FUNCTIONS[block.name]
                    result = fn(**block.input)
                    log_tool_call(block.name, block.input, result)
                    print(f"  [tool call] {block.name}({block.input}) -> {result}")
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result),
                        }
                    )
            messages.append({"role": "user", "content": tool_results})


# ---------------------------------------------------------------------------
# DEMO MODE: scripted walkthrough exercising the same tool functions,
# no API key required. Not "the agent" — it's a rehearsal/recording aid
# that proves the tool layer works and narrates each requirement being hit.
# ---------------------------------------------------------------------------

def run_scripted_demo():
    def say(who, text):
        print(f"{who}: {text}\n")

    print("=" * 70)
    print("SCRIPTED WALKTHROUGH (offline — exercises the real tool functions)")
    print("=" * 70 + "\n")

    # --- Requirement: multi-turn interaction ---
    say("You", "Where's my order?")
    say("Keats", "Happy to check! Could you give me your order ID, or the email "
                   "the order was placed under?")
    say("You", "jsmith@example.com")
    result = lookup_orders_by_email("jsmith@example.com")
    log_tool_call("lookup_orders_by_email", {"email": "jsmith@example.com"}, result)
    print(f"  [tool call] lookup_orders_by_email('jsmith@example.com') -> {result}\n")

    # --- Requirement: clarifying question (more than one match) ---
    say("Keats", "I found two orders on that email: BK-1001 (The Midnight Library) "
                  "and BK-1002 (Atomic Habits). Which one are you asking about?")
    say("You", "BK-1002")
    result = get_order_status("BK-1002", "jsmith@example.com")
    log_tool_call("get_order_status", {"order_id": "BK-1002", "email": "jsmith@example.com"}, result)
    print(f"  [tool call] get_order_status('BK-1002', 'jsmith@example.com') -> {result}\n")
    say("Keats", "BK-1002 (Atomic Habits) is in transit — it hasn't been delivered yet.")

    print("-" * 70 + "\n")

    # --- Requirement: tool use / action (return flow) ---
    say("You", "I want to return BK-1001, it wasn't what I expected.")
    elig = check_return_eligibility("BK-1001", "jsmith@example.com")
    log_tool_call("check_return_eligibility", {"order_id": "BK-1001", "email": "jsmith@example.com"}, elig)
    print(f"  [tool call] check_return_eligibility('BK-1001', 'jsmith@example.com') -> {elig}\n")
    say("Keats", "That order is still within its 30-day return window. "
                  "Want me to go ahead and file the return?")
    say("You", "Yes, please.")
    action = initiate_return("BK-1001", "jsmith@example.com", "Not what I expected")
    log_tool_call(
        "initiate_return",
        {"order_id": "BK-1001", "email": "jsmith@example.com", "reason": "Not what I expected"},
        action,
    )
    print(f"  [tool call] initiate_return('BK-1001', 'jsmith@example.com', 'Not what I expected') -> {action}\n")
    say("Keats", f"Done — I've filed the return, confirmation number "
                  f"{action['confirmation_number']}. You'll get a refund once it's received.")

    print("-" * 70 + "\n")

    # --- Bonus: identity check rejects a mismatched email/order pair ---
    say("You", "Can you check on order BK-2044? My email is jsmith@example.com.")
    mismatch = get_order_status("BK-2044", "jsmith@example.com")
    log_tool_call("get_order_status", {"order_id": "BK-2044", "email": "jsmith@example.com"}, mismatch)
    print(f"  [tool call] get_order_status('BK-2044', 'jsmith@example.com') -> {mismatch}\n")
    say("Keats", "I couldn't find an order matching that ID and email — could you "
                  "double check both?")
    print("  (BK-2044 is real, but belongs to a different customer's email. The agent "
          "never confirms that — same response as a made-up order ID.)\n")

    print("=" * 70)
    print("All three minimum requirements demonstrated above, plus an identity guardrail:")
    print("  1. Multi-turn: asked for email before answering")
    print("  2. Clarifying question: asked which of two orders was meant")
    print("  3. Tool use / action: checked eligibility, then filed a real return")
    print("  4. Identity check: a real order ID paired with the wrong email is")
    print("     treated exactly like a nonexistent order")
    print("=" * 70)
    print(f"Every tool call above was also written to audit_log.jsonl, with the "
          f"email hashed rather than stored in the clear (see {AUDIT_LOG_PATH}).")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        run_scripted_demo()
    else:
        run_live_chat()
