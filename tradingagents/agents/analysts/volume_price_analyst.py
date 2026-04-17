from langchain_core.messages import HumanMessage, SystemMessage

from tradingagents.dataflows.config import get_config
from tradingagents.prompts import get_prompt
from tradingagents.graph.intent_parser import build_horizon_context
from tradingagents.agents.utils.agent_states import current_tracker_var, extract_verdict
from tradingagents.dataflows.trade_calendar import cn_market_phase, cn_today_str
from tradingagents.graph.data_collector import stock_data_to_markdown


def _market_phase_note(current_date: str) -> str:
    if current_date != cn_today_str():
        return ""
    phase = cn_market_phase()
    if phase == "pre_open":
        return "【数据说明】当前为盘前，今日尚无交易数据，以下指标基于昨日收盘，信号可靠。\n\n"
    if phase in ("in_session", "lunch_break"):
        return (
            "【数据说明】当前为盘中，今日K线为截至当前的不完整数据（volume未完成），"
            "量价指标（OBV/量比等）为临时值，信号不稳定。"
            "请以历史确认信号为主，今日盘中数据仅作参考。\n\n"
        )
    return ""  # post_close: 数据完整，无需特殊说明


def create_volume_price_analyst(llm, data_collector=None):
    async def volume_price_analyst_node(state):
        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        horizon = "short"
        user_intent = state.get("user_intent") or {}
        focus_areas = user_intent.get("focus_areas", [])
        specific_questions = user_intent.get("specific_questions", [])

        config = get_config()
        horizon_ctx = build_horizon_context(horizon, focus_areas, specific_questions, agent_type="volume_price")
        system_message = get_prompt("volume_price_system_message", config=config)

        if data_collector is not None:
            pool = data_collector.get(ticker, current_date)
            if pool is not None:
                windowed = data_collector.get_window(pool, horizon, current_date)
                vpa_data = windowed.get("vpa_indicators", "无数据")
                stock_data = windowed.get("stock_data", "无数据")
                data_window = windowed.get("_data_window", "14天")
            else:
                vpa_data, stock_data, data_window = "无数据", "无数据", "14天"
        else:
            vpa_data, stock_data, data_window = "无数据", "无数据", "14天"

        phase = cn_market_phase()
        is_intraday = phase in ("in_session", "lunch_break")

        if is_intraday and isinstance(vpa_data, str) and "\n" in vpa_data:
            vpa_lines = vpa_data.splitlines()
            fn_idx = next((i for i, l in enumerate(vpa_lines) if l.startswith("> ")), len(vpa_lines))
            history_part = "\n".join(vpa_lines[:fn_idx - 1])
            today_part   = "\n".join(vpa_lines[fn_idx - 1:])
            human_content = (
                f"以下是 {ticker} 在 {current_date} 的量价分析（数据窗口：{data_window}）。\n\n"
                f"### 第一部分：历史量价背景（已确认数据）\n{history_part}\n"
                f"> 请先评估历史区间整体趋势：底部吸筹、放量拉升、还是高位派发？\n\n"
                f"### 第二部分：今日盘中动态快照（量比已按时间进度投影修正）\n{today_part}\n"
                f"> 对比历史背景，今日预估量能是增强了趋势，还是产生了异动？\n\n"
                f"【原始 K 线数据参考】\n{stock_data_to_markdown(stock_data)}"
            )
        else:
            human_content = (
                f"以下是 {ticker} 在 {current_date} 的量价分析预计算数据（数据窗口：{data_window}）。\n\n"
                + _market_phase_note(current_date)
                + f"{vpa_data}\n\n"
                f"【原始 K 线数据参考】\n{stock_data_to_markdown(stock_data)}"
            )

        messages = [
            SystemMessage(content=horizon_ctx + system_message + "\n\n请全程使用中文。"),
            HumanMessage(content=human_content),
        ]

        tracker = current_tracker_var.get()
        full_content = ""
        async for chunk in llm.astream(messages):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            full_content += content
            if tracker:
                tracker._emit_token("Volume Price Analyst", "volume_price_report", content)

        verdict, confidence = extract_verdict(full_content)

        return {
            "volume_price_report": full_content,
            "analyst_traces": [{
                "agent": "volume_price_analyst",
                "horizon": horizon,
                "data_window": data_window,
                "key_finding": f"量价分析结论：{verdict}",
                "verdict": verdict,
                "confidence": confidence,
            }],
        }

    return volume_price_analyst_node
