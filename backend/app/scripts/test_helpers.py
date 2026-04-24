"""
app/scripts/test_helpers.py
Helpers: extract messages, print, build summaries.
"""
import json
from app.scripts.test_config import C


# ─────────────────────────────────────────────────────────────────────────────
# Message extractors
# ─────────────────────────────────────────────────────────────────────────────

def get_tool_calls(messages: list) -> list[dict]:
    calls = []
    for msg in messages:
        tcs = getattr(msg, "tool_calls", None)
        if tcs:
            for tc in tcs:
                name = tc.get("name") if isinstance(tc, dict) else getattr(tc, "name", "")
                args = tc.get("args") if isinstance(tc, dict) else getattr(tc, "args", {})
                calls.append({"name": name, "args": args or {}})
    return calls


def get_tool_results(messages: list) -> list[str]:
    return [
        getattr(msg, "content", "")
        for msg in messages
        if getattr(msg, "type", "") == "tool"
        and isinstance(getattr(msg, "content", ""), str)
    ]


def get_ai_response(messages: list) -> str:
    for msg in reversed(messages):
        if getattr(msg, "type", "") == "ai":
            c   = getattr(msg, "content", "")
            tcs = getattr(msg, "tool_calls", [])
            if isinstance(c, str) and c.strip() and not (tcs and not c.strip()):
                return c
    return ""


def args_summary(args: dict) -> dict:
    keep = ("request_type", "origin", "destination", "departureDate",
            "compare_airlines", "compare_flights", "preferred_airlines",
            "maxPrice", "nonStop", "sort_preference", "start_hour", "end_hour",
            "query", "airline_codes", "airline_code")
    return {k: v for k, v in args.items() if k in keep and v is not None}


def build_tool_results_summary(tool_results: list[str]) -> str:
    if not tool_results:
        return "Không có dữ liệu từ tool (bot không gọi tool nào)."
    return "\n".join(f"Tool {i}: {tr.strip()}" for i, tr in enumerate(tool_results, 1))


# ─────────────────────────────────────────────────────────────────────────────
# Print helpers
# ─────────────────────────────────────────────────────────────────────────────

def print_technical(tech: dict):
    label = f"{C.GREEN}PASS{C.RESET}" if tech["result"] == "PASS" else f"{C.RED}FAIL{C.RESET}"
    print(f"      [Tech] {label} {tech['passed']}/{tech['total']}")
    for chk in tech["checks"]:
        icon = f"{C.GREEN}✓{C.RESET}" if chk["pass"] else f"{C.RED}✗{C.RESET}"
        line = f"        {icon} {chk['name']}"
        if not chk["pass"] and chk.get("fail_reason"):
            line += f"  {C.RED}← {chk['fail_reason']}{C.RESET}"
        print(line)


def print_ux(judge_id: str, ux: dict):
    score = ux["score"]
    color = C.GREEN if score >= 4 else (C.YELLOW if score == 3 else C.RED)
    print(f"      [{judge_id}] {color}{score}/5{C.RESET} — {ux['reason']}")
    if ux.get("hallucination_found"):
        print(f"        {C.RED}⚠ HALLUCINATION: {ux.get('hallucination_detail','')}{C.RESET}")