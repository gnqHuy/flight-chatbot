"""
app/scripts/test_technical.py
Technical checker — deterministic, không dùng LLM.
"""


def _tool_names(tool_calls: list[dict]) -> set[str]:
    return {tc.get("name", "") for tc in tool_calls}


def _actual_req_types(tool_calls: list[dict]) -> list[str]:
    flight_tools = ("handle_flight", "search_flights", "filter_flights", "analyze_flights")
    return [
        tc.get("args", {}).get("request_type", "")
        for tc in tool_calls
        if tc.get("name") in flight_tools
    ]


def technical_check(
    actual_tool_calls: list[dict],
    actual_action: dict | None,
    actual_search_id: str | None,
    expected: dict,
) -> dict:
    """
    Kiểm tra technical ground truth.
    Trả về dict: result (PASS/FAIL), passed, total, checks[].
    """
    checks    = []
    names     = _tool_names(actual_tool_calls)
    req_types = _actual_req_types(actual_tool_calls)

    exp_tools        = expected.get("expected_tool_calls") or []
    exp_action       = expected.get("expected_action")
    exp_sid_behavior = expected.get("expected_search_id_behavior", "none")

    # ── Tool calls ────────────────────────────────────────────────────────────
    if not exp_tools:
        ok = len(actual_tool_calls) == 0
        checks.append({
            "name": "Không gọi tool", "pass": ok,
            "expected": "[]", "actual": list(names),
            "fail_reason": f"Gọi {list(names)} dù không nên" if not ok else None,
        })
    else:
        for exp in exp_tools:
            tool_name  = exp.get("tool")
            req_type   = exp.get("request_type")
            should_not = exp.get("should_not_call", False)
            if should_not:
                ok = tool_name not in names
                checks.append({
                    "name": f"KHÔNG gọi {tool_name}", "pass": ok,
                    "expected": f"NOT {tool_name}", "actual": list(names),
                    "fail_reason": f"Đã gọi {tool_name} dù bị cấm" if not ok else None,
                })
            else:
                ok = tool_name in names
                checks.append({
                    "name": f"Gọi {tool_name}", "pass": ok,
                    "expected": tool_name, "actual": list(names),
                    "fail_reason": f"Không gọi {tool_name}" if not ok else None,
                })
                if ok and req_type:
                    ok2 = req_type in req_types
                    checks.append({
                        "name": f"request_type={req_type}", "pass": ok2,
                        "expected": req_type, "actual": req_types,
                        "fail_reason": f"Thực tế: {req_types}" if not ok2 else None,
                    })

    # ── Action ────────────────────────────────────────────────────────────────
    actual_action_type = actual_action.get("type") if actual_action else None
    if exp_action is not None:
        ok = actual_action_type == exp_action
        checks.append({
            "name": f"action={exp_action}", "pass": ok,
            "expected": exp_action, "actual": actual_action_type,
            "fail_reason": f"Thực tế: {actual_action_type}" if not ok else None,
        })

    # ── search_id ─────────────────────────────────────────────────────────────
    has_sid = bool(actual_search_id and actual_search_id != "CLEAR")
    if exp_sid_behavior == "new":
        ok = has_sid
        checks.append({"name": "search_id=new", "pass": ok,
                        "expected": "có search_id mới", "actual": actual_search_id,
                        "fail_reason": "Không có search_id" if not ok else None})
    elif exp_sid_behavior == "reuse":
        ok = has_sid
        checks.append({"name": "search_id=reuse", "pass": ok,
                        "expected": "giữ search_id cũ", "actual": actual_search_id,
                        "fail_reason": "Không có search_id" if not ok else None})
    elif exp_sid_behavior == "none":
        ok = not has_sid
        checks.append({"name": "search_id=none", "pass": ok,
                        "expected": "không có search_id", "actual": actual_search_id,
                        "fail_reason": f"Có search_id: {actual_search_id}" if not ok else None})

    # ── Unexpected tool calls ─────────────────────────────────────────────────
    for unexp in (expected.get("unexpected_tool_calls") or []):
        tool_name = unexp.get("tool")
        if tool_name in names:
            checks.append({
                "name": f"KHÔNG gọi {tool_name} (unexpected)", "pass": False,
                "expected": f"NOT {tool_name}", "actual": list(names),
                "fail_reason": f"Gọi {tool_name} không cần thiết",
            })

    all_pass = all(c["pass"] for c in checks)
    return {
        "result": "PASS" if all_pass else "FAIL",
        "passed": sum(1 for c in checks if c["pass"]),
        "total":  len(checks),
        "checks": checks,
    }