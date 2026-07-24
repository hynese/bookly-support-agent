"""
Minimal sanity tests for the Bookly agent's tool functions.

No pytest dependency on purpose — this is meant to be runnable with nothing
but the Python that's already installed:

    python3 test_bookly_agent.py

These don't touch the LLM at all; they test the mocked backend functions
directly; the tool layer, so the parts of the code that would silently break
a demo if they had a bug.
"""

import os

from bookly_agent import (
    get_order_status,
    check_return_eligibility,
    initiate_return,
    lookup_orders_by_email,
    load_policies,
    log_tool_call,
    _hash_email,
    AUDIT_LOG_PATH,
)

passed = 0


def check(label, condition):
    global passed
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if condition:
        passed += 1
    else:
        raise AssertionError(f"Test failed: {label}")


# --- Nonexistent order ---
result = get_order_status("BK-9999", "nobody@example.com")
check("nonexistent order ID returns not found", result["found"] is False)

# --- Identity mismatch: real order, wrong email ---
result = get_order_status("BK-2044", "jsmith@example.com")
check(
    "real order + wrong email is rejected exactly like not-found",
    result["found"] is False,
)

# --- Identity match: real order, correct email ---
result = get_order_status("BK-2044", "afernandez@example.com")
check("real order + correct email succeeds", result["found"] is True)
check("correct lookup returns the right item", result.get("item") == "Project Hail Mary")

# --- Return eligibility: delivered + within window ---
elig = check_return_eligibility("BK-1001", "jsmith@example.com")
check("delivered order within window is eligible", elig.get("eligible") is True)

# --- Return eligibility: not yet delivered ---
elig = check_return_eligibility("BK-1002", "jsmith@example.com")
check("in-transit order is not return-eligible", elig.get("eligible") is False)

# --- Return eligibility: wrong email blocked ---
elig = check_return_eligibility("BK-1001", "afernandez@example.com")
check("return eligibility check blocks mismatched email", elig["found"] is False)

# --- Filing a return: wrong email blocked ---
action = initiate_return("BK-1001", "afernandez@example.com", "wrong owner attempt")
check("initiate_return blocks a mismatched email", action["success"] is False)

# --- Filing a return: correct email succeeds ---
action = initiate_return("BK-1001", "jsmith@example.com", "not what I expected")
check("initiate_return succeeds for the correct owner", action["success"] is True)
check("initiate_return returns a confirmation number", "confirmation_number" in action)

# --- Multi-order lookup by email ---
result = lookup_orders_by_email("jsmith@example.com")
check("jsmith@example.com has exactly two orders", result["count"] == 2)

result = lookup_orders_by_email("nobody@example.com")
check("unknown email returns zero orders, not an error", result["count"] == 0)

# --- AOP-style policy file is actually being loaded, not just present on disk ---
policies_text = load_policies()
check("policy file loads and is non-empty", len(policies_text) > 0)
check("policy file mentions the identity check rule", "Identity check" in policies_text)
check("policy file documents excluded scope", "Out of scope" in policies_text)

# --- Audit logging never writes raw email, and appends a line per call ---
check("email hashing does not return the raw email", _hash_email("jsmith@example.com") != "jsmith@example.com")
check("email hashing is deterministic", _hash_email("jsmith@example.com") == _hash_email("JSmith@Example.com"))

lines_before = 0
if os.path.exists(AUDIT_LOG_PATH):
    with open(AUDIT_LOG_PATH) as f:
        lines_before = len(f.readlines())
log_tool_call("get_order_status", {"order_id": "BK-1001", "email": "jsmith@example.com"}, {"found": True})
with open(AUDIT_LOG_PATH) as f:
    lines_after = len(f.readlines())
check("audit log gains exactly one line per tool call", lines_after == lines_before + 1)

print(f"\n{passed}/{passed} checks passed.")
