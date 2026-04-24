"""
app/scripts/test_automation.py

Chạy test với 1 candidate model tại 1 thời điểm.
Đổi model: thay CANDIDATE_ID ở đầu file.

Chạy: python -m app.scripts.test_automation
"""
import asyncio
import json
import os
import sys
import uuid
import time
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from langchain_core.messages import HumanMessage

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# ── Chọn model chạy test ──────────────────────────────────────────────────────
# Đổi giá trị này để chạy model khác: "openai" | "gemini" | "claude"
CANDIDATE_ID = "openai"

# Mốc thời gian cố định cho toàn bộ test run
TEST_DATE = "2026-05-15 10:00"

from .test_config    import C, CANDIDATES, JUDGE_LABEL
from .test_judge     import build_judge_chains
from .test_technical import technical_check
from .test_helpers   import (
    get_tool_calls, get_tool_results, get_ai_response,
    args_summary, build_tool_results_summary,
    print_technical, print_ux,
)

# Lấy config của candidate đang chạy
CANDIDATE = next(c for c in CANDIDATES if c["id"] == CANDIDATE_ID)


# ─────────────────────────────────────────────────────────────────────────────
# Run 1 turn
# ─────────────────────────────────────────────────────────────────────────────

async def run_turn(graph, thread_id: str, user_msg: str) -> dict:
    import asyncio as _asyncio

    config = {
        "configurable": {
            "thread_id": thread_id,
            "test_date": TEST_DATE,
        },
        "metadata": {
            "candidate_id":    CANDIDATE_ID,
            "candidate_label": CANDIDATE["label"],
        },
        "tags": [CANDIDATE_ID],
    }

    inputs = {"messages": [HumanMessage(content=user_msg)]}

    # Retry tối đa 3 lần khi gặp 503
    for attempt in range(3):
        try:
            t0    = time.time()
            final = await graph.ainvoke(inputs, config=config)
            msgs  = final.get("messages", [])
            return {
                "tool_calls":   get_tool_calls(msgs),
                "tool_results": get_tool_results(msgs),
                "ai_response":  get_ai_response(msgs),
                "search_id":    final.get("current_search_id"),
                "action":       final.get("action"),
                "elapsed":      round(time.time() - t0, 1),
            }
        except Exception as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                wait = 10 * (attempt + 1)
                print(f"    {C.YELLOW}⚠ 503 UNAVAILABLE, retry sau {wait}s... (lần {attempt+1}/3){C.RESET}")
                await _asyncio.sleep(wait)
                continue
            raise  # lỗi khác thì raise luôn

    raise RuntimeError("Gemini 503 sau 3 lần retry")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

async def main(input_file: str, output_file: str):
    print(f"\n{C.BOLD}{C.CYAN}{'═'*64}{C.RESET}")
    print(f"{C.BOLD}  FLIGHT CHATBOT — TEST AUTOMATION{C.RESET}")
    print(f"  Model    : {C.MAGENTA}{CANDIDATE['label']}{C.RESET}")
    print(f"  Judge    : {JUDGE_LABEL}")
    print(f"  TestDate : {TEST_DATE}")
    print(f"  Time     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{C.CYAN}{'═'*64}{C.RESET}\n")

    if not os.path.exists(input_file):
        print(f"{C.RED}❌ Không tìm thấy: {input_file}{C.RESET}")
        return
    with open(input_file, encoding="utf-8") as f:
        test_cases = json.load(f)
    print(f"📂 {len(test_cases)} test cases\n")

    # ── Init ──────────────────────────────────────────────────────────────────
    from app.database.checkpointer import async_pool, checkpointer
    await async_pool.open()
    await checkpointer.setup()

    from app.core.llm_setup import llm_openai, llm_gemini, llm_claude, llm_as_judge
    candidate_llms = {"openai": llm_openai, "gemini": llm_gemini, "claude": llm_claude}
    llm = candidate_llms[CANDIDATE_ID]

    # Project LangSmith được set trong .env (LANGSMITH_PROJECT)
    # Uncomment đúng project trước khi chạy

    print(f"⚙  Compile graph cho {CANDIDATE['label']}...")
    from app.ai_orchestrator.graph.flight_graph import build_graph_for_llm
    graph = await build_graph_for_llm(llm, checkpointer)
    print(f"✅ Graph ready\n")

    judge_chains = build_judge_chains()

    # ── Stats ─────────────────────────────────────────────────────────────────
    stats = {"tech_pass": 0, "tech_fail": 0, "ux_sum": 0.0, "ux_count": 0, "hall_count": 0}
    scenario_reports = []

    # ─────────────────────────────────────────────────────────────────────────
    for tc in test_cases:
        tc_id = tc.get("test_id", "UNKNOWN")
        diff  = tc.get("difficulty", "unknown")
        desc  = tc.get("description", "")

        diff_color = {"easy": C.GREEN, "basic_medium": C.CYAN,
                      "advanced_medium": C.YELLOW, "hard": C.RED}.get(diff, C.GRAY)
        print(f"{C.BOLD}{'─'*64}{C.RESET}")
        print(f"{C.BOLD}[{tc_id}]{C.RESET}  {diff_color}[{diff.upper()}]{C.RESET}  {desc}")

        thread_id  = f"{tc_id}_{CANDIDATE_ID}_{uuid.uuid4().hex[:6]}"
        tc_result  = {"tech_pass": True, "ux_scores": [], "turns": [], "conv_history": "", "elapsed_total": 0.0}

        for turn in tc.get("turns", []):
            t_num   = turn["turn_number"]
            query   = turn["user_query"]
            exp_beh = turn.get("expected_behavior", "")
            anti    = turn.get("anti_preference", "")

            print(f"\n  Turn {t_num}/{len(tc['turns'])}: {C.BOLD}\"{query}\"{C.RESET}")

            try:
                r = await run_turn(graph, thread_id, query)
                tc_result["elapsed_total"] += r["elapsed"]

                # Log tool calls
                for tc_call in r["tool_calls"]:
                    print(f"    {C.MAGENTA}⚙{C.RESET} {tc_call['name']}({json.dumps(args_summary(tc_call['args']), ensure_ascii=False)})")
                if not r["tool_calls"]:
                    print(f"    {C.GRAY}→ Không gọi tool{C.RESET}")
                action_type = r["action"]["type"] if r["action"] else None
                print(f"    {C.CYAN}→{C.RESET} sid={r['search_id']} | action={action_type} | {r['elapsed']}s")

                # Technical check
                tech = technical_check(r["tool_calls"], r["action"], r["search_id"], turn)
                print_technical(tech)
                if tech["result"] == "PASS":
                    stats["tech_pass"] += 1
                else:
                    stats["tech_fail"] += 1
                    tc_result["tech_pass"] = False

                # UX judge
                bot_response = r["ai_response"].strip() or "(không có phản hồi)"
                tool_summary = build_tool_results_summary(r["tool_results"]) or "(tool không trả về dữ liệu)"
                try:
                    ux_res = judge_chains["turn"](
                        user_query=query,
                        expected_behavior=exp_beh.strip() or "(không có mô tả)",
                        anti_preference=anti.strip() or "(không có)",
                        tool_results_summary=tool_summary,
                        bot_response=bot_response,
                    )
                    ux = {
                        "score":               ux_res.score,
                        "reason":              ux_res.reason,
                        "hallucination_found": ux_res.hallucination_found,
                        "hallucination_detail": ux_res.hallucination_detail,
                    }
                    print_ux(JUDGE_LABEL, ux)
                    tc_result["ux_scores"].append(ux_res.score)
                    stats["ux_sum"]   += ux_res.score
                    stats["ux_count"] += 1
                    if ux_res.hallucination_found:
                        stats["hall_count"] += 1
                except Exception as e:
                    print(f"    {C.YELLOW}⚠ Judge error: {e}{C.RESET}")
                    print(f"    {C.GRAY}  bot_response len={len(bot_response)} | tool_summary len={len(tool_summary)}{C.RESET}")
                    ux = {"score": 0, "reason": str(e), "hallucination_found": False, "hallucination_detail": ""}

                tc_result["conv_history"] += f"Q{t_num}: {query}\nA{t_num}: {r['ai_response'][:200]}\n\n"
                tc_result["turns"].append({
                    "turn_number": t_num,
                    "user_query":  query,
                    "technical": {
                        **tech,
                        "tool_calls":           [{"tool": tc_c["name"], "args": args_summary(tc_c["args"])} for tc_c in r["tool_calls"]],
                        "tool_results_preview": [tr.strip() for tr in r["tool_results"]],
                        "action":    r["action"],
                        "search_id": r["search_id"],
                        "elapsed":   r["elapsed"],
                    },
                    "ux": {**ux, "response_preview": r["ai_response"][:200].replace("\n", " ")},
                })

            except Exception as e:
                import traceback
                print(f"    {C.RED}✗ Exception: {e}{C.RESET}")
                traceback.print_exc()
                stats["tech_fail"] += 1
                tc_result["tech_pass"] = False
                tc_result["turns"].append({"turn_number": t_num, "user_query": query, "error": str(e)})

        # ── Scenario judge ────────────────────────────────────────────────────
        ux_avg = round(sum(tc_result["ux_scores"]) / len(tc_result["ux_scores"]), 1) if tc_result["ux_scores"] else 0
        try:
            sc_res = judge_chains["scenario"](
                    description=desc,
                    model_label=CANDIDATE["label"],
                    conversation_history=tc_result["conv_history"],
                )
            sc_score, sc_reason = sc_res.score, sc_res.reason
        except Exception as e:
            sc_score, sc_reason = 0, str(e)

        label = f"{C.GREEN}PASS{C.RESET}" if tc_result["tech_pass"] else f"{C.RED}FAIL{C.RESET}"
        print(f"\n  [{tc_id}] {label} | turn UX={ux_avg}/5 | scenario={sc_score}/5")
        print(f"  {C.GRAY}{sc_reason[:120]}{C.RESET}")

        scenario_reports.append({
            "scenario_id":        tc_id,
            "difficulty":         diff,
            "description":        desc,
            "result":             "PASS" if tc_result["tech_pass"] else "FAIL",
            "ux_avg_turn":        ux_avg,
            "ux_scenario_score":  sc_score,
            "ux_scenario_reason": sc_reason,
            "elapsed_total":      round(tc_result["elapsed_total"], 1),
            "turns":              tc_result["turns"],
        })

    # ── Summary ───────────────────────────────────────────────────────────────
    total     = stats["tech_pass"] + stats["tech_fail"]
    tech_rate = round(stats["tech_pass"] / total * 100, 1) if total else 0
    ux_avg    = round(stats["ux_sum"] / stats["ux_count"], 2) if stats["ux_count"] else 0
    hall_rate = round(stats["hall_count"] / stats["ux_count"] * 100, 1) if stats["ux_count"] else 0

    tc_c = C.GREEN if tech_rate >= 80 else (C.YELLOW if tech_rate >= 60 else C.RED)
    uc   = C.GREEN if ux_avg >= 4    else (C.YELLOW if ux_avg >= 3    else C.RED)
    hc   = C.GREEN if hall_rate <= 15 else (C.YELLOW if hall_rate <= 30 else C.RED)

    print(f"\n{C.BOLD}{C.CYAN}{'═'*64}{C.RESET}")
    print(f"{C.BOLD}  KẾT QUẢ — {CANDIDATE['label']}{C.RESET}")
    print(f"{C.CYAN}{'═'*64}{C.RESET}")
    print(f"  Tech pass : {tc_c}{tech_rate}%{C.RESET} ({stats['tech_pass']}/{total} turns)")
    print(f"  UX avg    : {uc}{ux_avg}/5.0{C.RESET}")
    print(f"  Halluc.   : {hc}{hall_rate}%{C.RESET} ({stats['hall_count']}/{stats['ux_count']} turns)")

    print(f"\n  {'Scenario':<30} {'Result':<8} {'UX':>4} {'Sc':>4}")
    print(f"  {'─'*50}")
    for sc in scenario_reports:
        diff_c = {"easy": C.GREEN, "basic_medium": C.CYAN,
                  "advanced_medium": C.YELLOW, "hard": C.RED}.get(sc["difficulty"], C.GRAY)
        icon = f"{C.GREEN}✓{C.RESET}" if sc["result"] == "PASS" else f"{C.RED}✗{C.RESET}"
        print(f"  {icon} {diff_c}{sc['scenario_id']:<28}{C.RESET} {sc['ux_avg_turn']:>4}/5 {sc['ux_scenario_score']:>4}/5")

    report = {
        "meta": {
            "generated_at":    datetime.now().isoformat(),
            "input_file":      input_file,
            "candidate":       CANDIDATE["label"],
            "candidate_id":    CANDIDATE_ID,
            "judge":           JUDGE_LABEL,
            "test_date":       TEST_DATE,
            "total_scenarios": len(test_cases),
            "total_turns":     total,
        },
        "summary": {
            "tech_pass_rate":     tech_rate,
            "tech_pass":          stats["tech_pass"],
            "tech_fail":          stats["tech_fail"],
            "ux_avg":             ux_avg,
            "hallucination_rate": hall_rate,
        },
        "scenarios": scenario_reports,
    }

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  📄 Report: {C.CYAN}{output_file}{C.RESET}\n")

    from app.database.checkpointer import async_pool as pool
    await pool.close()


if __name__ == "__main__":
    base        = os.path.dirname(os.path.abspath(__file__))
    INPUT_FILE  = os.path.join(base, "data_set", "test_cases.json")
    OUTPUT_FILE = os.path.join(
        base,
        f"report_{CANDIDATE_ID}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    asyncio.run(main(INPUT_FILE, OUTPUT_FILE))